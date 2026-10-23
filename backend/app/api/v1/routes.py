from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ...core.security import Principal, current_principal
from ...db.session import get_session
from ...models.entities import AgentEvent, StudentProfileRecord, UploadedDocument
from ...schemas.contracts import EventResponse, ProfileInput, ProfileResponse, UploadResponse, WorkflowCreate, WorkflowResponse
from ...services.workflow_service import WorkflowService
from ...services.uploads import LocalUploadStore
from ...core.config import Settings, get_settings
from ...workers.tasks import execute_workflow

router = APIRouter()

def profile_response(record: StudentProfileRecord) -> ProfileResponse:
    return ProfileResponse(id=record.id, confirmed_at=record.confirmed_at, **record.data)

@router.post("/profiles", response_model=ProfileResponse, status_code=201)
def create_profile(body: ProfileInput, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    WorkflowService(session).repo.ensure_user(principal.user_id, principal.subject)
    record = StudentProfileRecord(user_id=principal.user_id, data=body.model_dump())
    session.add(record); session.commit(); session.refresh(record)
    return profile_response(record)

@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: UUID, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    record = WorkflowService(session).repo.profile_for_owner(profile_id, principal.user_id)
    if not record: raise HTTPException(404, "Profile not found")
    return profile_response(record)

@router.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: UUID, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    record = WorkflowService(session).repo.profile_for_owner(profile_id, principal.user_id)
    if not record: raise HTTPException(404, "Profile not found")
    session.delete(record); session.commit()
    return Response(status_code=204)

@router.post("/profiles/{profile_id}/confirm", response_model=ProfileResponse)
def confirm_profile(profile_id: UUID, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    record = WorkflowService(session).repo.profile_for_owner(profile_id, principal.user_id)
    if not record: raise HTTPException(404, "Profile not found")
    record.confirmed_at = datetime.now(timezone.utc)
    session.commit(); session.refresh(record)
    return profile_response(record)

@router.post("/documents", response_model=UploadResponse, status_code=201)
async def upload_document(upload: UploadFile = File(...), principal: Principal = Depends(current_principal), session: Session = Depends(get_session), settings: Settings = Depends(get_settings)):
    repo = WorkflowService(session).repo
    repo.ensure_user(principal.user_id, principal.subject)
    key, digest, size, original_name = await LocalUploadStore(settings).save(upload)
    record = UploadedDocument(user_id=principal.user_id, storage_key=key, original_filename=original_name[:255], content_type=upload.content_type or "", size_bytes=size, sha256=digest, processing_status="pending")
    session.add(record); session.commit(); session.refresh(record)
    return record

@router.post("/workflows", response_model=WorkflowResponse, status_code=202)
def create_workflow(body: WorkflowCreate, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    try: run = WorkflowService(session).start(principal.user_id, body.profile_id, body.idempotency_key)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    execute_workflow.delay(str(run.id))
    return run

@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: UUID, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    run = WorkflowService(session).repo.get_for_owner(workflow_id, principal.user_id)
    if not run: raise HTTPException(404, "Workflow not found")
    return run

@router.post("/workflows/{workflow_id}/cancel", response_model=WorkflowResponse)
def cancel_workflow(workflow_id: UUID, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    try: return WorkflowService(session).cancel(principal.user_id, workflow_id)
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc

@router.get("/workflows/{workflow_id}/events", response_model=list[EventResponse])
def workflow_events(workflow_id: UUID, principal: Principal = Depends(current_principal), session: Session = Depends(get_session)):
    run = WorkflowService(session).repo.get_for_owner(workflow_id, principal.user_id)
    if not run: raise HTTPException(404, "Workflow not found")
    return session.scalars(select(AgentEvent).where(AgentEvent.workflow_id == workflow_id).order_by(AgentEvent.created_at)).all()
