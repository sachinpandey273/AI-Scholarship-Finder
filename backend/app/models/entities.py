import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base

class Timestamped(Base):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Timestamped):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    external_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)

class StudentProfileRecord(Timestamped):
    __tablename__ = "student_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class WorkflowRun(Timestamped):
    __tablename__ = "workflow_runs"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_workflow_user_key"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id", ondelete="RESTRICT"))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    current_node: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class AgentEvent(Timestamped):
    __tablename__ = "agent_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    node: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(32))
    detail: Mapped[str] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(default=1)

class ResearchOpportunity(Timestamped):
    __tablename__ = "research_opportunities"
    __table_args__ = (UniqueConstraint("provider", "program_identity", "degree_level", "application_cycle", name="uq_opportunity_cycle"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(255), index=True)
    program_identity: Mapped[str] = mapped_column(String(255))
    degree_level: Mapped[str] = mapped_column(String(64))
    application_cycle: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSON)

class UploadedDocument(Timestamped):
    __tablename__ = "uploaded_documents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending")

class StudentFact(Timestamped):
    __tablename__ = "student_facts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_profiles.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("uploaded_documents.id", ondelete="SET NULL"))
    field_name: Mapped[str] = mapped_column(String(100))
    value: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float]

class SourceRecord(Timestamped):
    __tablename__ = "source_records"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_opportunities.id", ondelete="CASCADE"), index=True)
    canonical_url: Mapped[str] = mapped_column(String(2048), unique=True)
    host: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    http_status: Mapped[int | None]
    verification_state: Mapped[str] = mapped_column(String(32))
    excerpt: Mapped[str] = mapped_column(Text)

class FieldEvidenceRecord(Timestamped):
    __tablename__ = "field_evidence"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("source_records.id", ondelete="CASCADE"), index=True)
    field_name: Mapped[str] = mapped_column(String(100))
    extracted_value: Mapped[str] = mapped_column(Text)
    exact_quote: Mapped[str] = mapped_column(Text)
    verification_state: Mapped[str] = mapped_column(String(32))

class EligibilityRecord(Timestamped):
    __tablename__ = "eligibility_assessments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_opportunities.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32))
    evidence: Mapped[dict] = mapped_column(JSON)

class MatchScoreRecord(Timestamped):
    __tablename__ = "match_scores"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_opportunities.id", ondelete="CASCADE"), index=True)
    scoring_version: Mapped[str] = mapped_column(String(32))
    total_score: Mapped[float]
    breakdown: Mapped[dict] = mapped_column(JSON)

class ApplicationDraftRecord(Timestamped):
    __tablename__ = "application_drafts"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), index=True)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_opportunities.id", ondelete="RESTRICT"))
    version: Mapped[int] = mapped_column(default=1)
    content: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON)

class AuditEvent(Timestamped):
    __tablename__ = "audit_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(100))
    target_type: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

Index("ix_events_workflow_created", AgentEvent.workflow_id, AgentEvent.created_at)
