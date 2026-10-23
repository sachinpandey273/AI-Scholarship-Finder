from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ProfileInput(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    nationality: str = Field(min_length=2, max_length=100)
    current_degree: str = Field(min_length=2, max_length=200)
    target_degree: str = Field(min_length=2, max_length=120)
    target_subject: str = Field(min_length=2, max_length=160)
    preferred_countries: list[str] = Field(min_length=1, max_length=10)
    target_intake: str = Field(min_length=2, max_length=60)
    cgpa: float = Field(ge=0, le=100)
    gpa_scale: float = Field(gt=0, le=100)
    skills: list[str] = Field(default_factory=list, max_length=50)
    projects: list[str] = Field(default_factory=list, max_length=50)

class ProfileResponse(ProfileInput):
    id: UUID
    confirmed_at: datetime | None

class WorkflowCreate(BaseModel):
    profile_id: UUID
    idempotency_key: str = Field(min_length=8, max_length=128)

class WorkflowResponse(BaseModel):
    id: UUID
    status: str
    current_node: str | None
    failure_reason: str | None = None
    created_at: datetime

class EventResponse(BaseModel):
    id: UUID
    node: str
    event_type: str
    detail: str
    attempt: int
    created_at: datetime

class UploadResponse(BaseModel):
    id: UUID
    processing_status: str
    original_filename: str
