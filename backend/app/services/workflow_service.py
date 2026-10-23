from uuid import UUID
from sqlalchemy.orm import Session
from ..repositories.workflows import WorkflowRepository

class WorkflowService:
    """Application service: authorization, idempotency, and durable status transitions."""
    def __init__(self, session: Session):
        self.session, self.repo = session, WorkflowRepository(session)

    def start(self, user_id: UUID, profile_id: UUID, idempotency_key: str):
        if not self.repo.profile_for_owner(profile_id, user_id):
            raise LookupError("Profile not found")
        run = self.repo.create_or_get(user_id, profile_id, idempotency_key)
        if run.status == "queued": self.repo.add_event(run, "intake", "queued", "Workflow accepted for background processing")
        return run

    def cancel(self, user_id: UUID, workflow_id: UUID):
        run = self.repo.get_for_owner(workflow_id, user_id)
        if not run: raise LookupError("Workflow not found")
        if run.status in {"completed", "failed", "cancelled"}: return run
        run.status, run.current_node = "cancelled", None
        self.session.commit(); self.repo.add_event(run, "workflow", "cancelled", "Cancelled by student")
        return run
