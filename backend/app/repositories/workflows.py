from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models.entities import AgentEvent, StudentProfileRecord, User, WorkflowRun

class WorkflowRepository:
    def __init__(self, session: Session): self.session = session

    def profile_for_owner(self, profile_id: UUID, user_id: UUID) -> StudentProfileRecord | None:
        return self.session.scalar(select(StudentProfileRecord).where(StudentProfileRecord.id == profile_id, StudentProfileRecord.user_id == user_id))

    def ensure_user(self, user_id: UUID, subject: str) -> User:
        user = self.session.get(User, user_id)
        if user: return user
        user = User(id=user_id, external_subject=subject)
        self.session.add(user); self.session.commit()
        return user

    def get_for_owner(self, workflow_id: UUID, user_id: UUID) -> WorkflowRun | None:
        return self.session.scalar(select(WorkflowRun).where(WorkflowRun.id == workflow_id, WorkflowRun.user_id == user_id))

    def create_or_get(self, user_id: UUID, profile_id: UUID, key: str) -> WorkflowRun:
        existing = self.session.scalar(select(WorkflowRun).where(WorkflowRun.user_id == user_id, WorkflowRun.idempotency_key == key))
        if existing: return existing
        run = WorkflowRun(user_id=user_id, profile_id=profile_id, idempotency_key=key)
        self.session.add(run); self.session.commit(); self.session.refresh(run)
        return run

    def add_event(self, run: WorkflowRun, node: str, event_type: str, detail: str, attempt: int = 1) -> None:
        self.session.add(AgentEvent(workflow_id=run.id, node=node, event_type=event_type, detail=detail, attempt=attempt))
        self.session.commit()

    def transition(self, run: WorkflowRun, status: str, node: str | None, detail: str) -> WorkflowRun:
        """Persist status and its explanatory event atomically enough for polling clients."""
        run.status, run.current_node = status, node
        self.session.commit()
        self.add_event(run, node or "workflow", status, detail)
        return run
