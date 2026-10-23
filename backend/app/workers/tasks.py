from uuid import UUID
from .celery_app import celery_app
from ..db.session import SessionLocal
from ..models.entities import WorkflowRun
from ..repositories.workflows import WorkflowRepository

@celery_app.task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
def execute_workflow(self, workflow_id: str) -> str:
    """Advance a durable workflow only in the worker process.

    The confirmation boundary is deliberate: no discovery or model request runs
    until the student has reviewed extracted facts. Each outcome remains visible
    through the events endpoint and is safe to retry.
    """
    try:
        workflow_uuid = UUID(workflow_id)
    except ValueError:
        return workflow_id  # queue connectivity smoke probe
    session = SessionLocal()
    try:
        repo = WorkflowRepository(session)
        run = session.get(WorkflowRun, workflow_uuid)
        if run is None: return workflow_id
        if run.status == "cancelled": return workflow_id
        repo.transition(run, "running", "intake", "Worker started durable workflow")
        profile = repo.profile_for_owner(run.profile_id, run.user_id)
        if profile is None:
            run.failure_reason = "Profile was deleted before execution"
            repo.transition(run, "failed", None, run.failure_reason)
            return workflow_id
        if profile.confirmed_at is None:
            repo.transition(run, "waiting_for_profile_review", "profile_review", "Student profile confirmation is required before research")
            return workflow_id
        # The full node runner is injected here once research adapters are
        # configured. Keep the workflow paused rather than fabricate results.
        repo.transition(run, "waiting_for_selection", "human_selection", "Profile confirmed; select an evidence-backed opportunity to draft an SOP")
        return workflow_id
    finally:
        session.close()
