from uuid import UUID
from fastapi import APIRouter, Depends, status, Path, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user, RoleChecker, get_optional_current_user
from Schema.submission_schema import SubmissionCreate, SubmissionResponse
from Schema.document_schema import DocumentResponse
from Schema.case_schema import SubmissionIntakeResponse
from Service.submission_service import SubmissionService
from Service.case_service import CaseService
from Service.document_service import DocumentService
from Utils.permissions import CAN_CREATE_SUBMISSIONS, CAN_PROCESS_INTAKE
from Entity.user_entity import User
from Service.voice_service import VoiceService

router = APIRouter(prefix="/intake", tags=["Intake"])

_require_submitter = RoleChecker(CAN_CREATE_SUBMISSIONS)
_require_intake_officer = RoleChecker(CAN_PROCESS_INTAKE)


@router.post("/submissions", response_model=SubmissionIntakeResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user),
):
    """
    Web/API channel intake (FR-004). Creates the Submission and immediately
    drives it through classification and routing in the same request — the
    golden-path demo endpoint. See POST /intake/submissions/{id}/process
    for the equivalent two-step flow used by async channels.
    """
    submission_service = SubmissionService(db)
    case_service = CaseService(db)
    try:
        actor_user_id = current_user.id if current_user else None
        actor_channel = "web_portal" if current_user else "web_public"
        
        submission = submission_service.create_submission(data, actor_user_id=actor_user_id)
        case = case_service.create_case_from_submission(
            submission.id, 
            actor_user_id=actor_user_id,
            actor_channel=actor_channel
        )
        return SubmissionIntakeResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="Submission received and processed.",
            submission=submission,
            case=case,
        )
    except ValueError as e:
        return SubmissionIntakeResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return SubmissionIntakeResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.post("/voice-chat")
async def voice_chat(
    audio: UploadFile = File(...),
    accumulated_description: str = Form(""),
    accumulated_location: str = Form(""),
):
    """
    Process citizen voice note: transcribe (STT), translate, check for required fields,
    and return translated audio response (TTS).
    """
    service = VoiceService()
    try:
        audio_bytes = await audio.read()
        mime_type = audio.content_type or "audio/webm"
        result = service.process_voice_message(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            accumulated_description=accumulated_description,
            accumulated_location=accumulated_location
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }



@router.post(
    "/submissions/{submission_id}/process",
    response_model=SubmissionIntakeResponse,
    status_code=status.HTTP_200_OK,
)
def process_submission(
    submission_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_intake_officer),
):
    """
    Drive an already-created Submission through classification/routing.
    For channels that intake asynchronously (e.g. a future WhatsApp/USSD
    adapter) and process separately from the intake event.
    """
    submission_service = SubmissionService(db)
    case_service = CaseService(db)
    try:
        submission = submission_service.get_submission(submission_id)
        case = case_service.create_case_from_submission(submission_id, actor_user_id=current_user.id)
        return SubmissionIntakeResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Submission processed.",
            submission=submission,
            case=case,
        )
    except ValueError as e:
        return SubmissionIntakeResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "submission_id", "message": str(e)}],
        )
    except Exception as e:
        return SubmissionIntakeResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    submission_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_intake_officer),
):
    """
    Upload a scanned/photographed report (FR-005). OCR extraction is not
    performed in this environment — no OCR provider credentials are
    configured; ocr_text/extraction_json stay null pending pilot integration.
    """
    service = DocumentService(db)
    try:
        file_bytes = await file.read()
        document = service.upload_document(
            submission_id=submission_id,
            file_bytes=file_bytes,
            mime_type=file.content_type or "application/octet-stream",
            original_filename=file.filename,
        )
        return DocumentResponse(
            status_code=status.HTTP_201_CREATED,
            success=True,
            message="Document uploaded.",
            document=document,
        )
    except ValueError as e:
        return DocumentResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            message=str(e),
            errors=[{"field": "validation", "message": str(e)}],
        )
    except Exception as e:
        return DocumentResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to upload document.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse, status_code=status.HTTP_200_OK)
def get_submission(
    submission_id: UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_intake_officer),
):
    service = SubmissionService(db)
    try:
        submission = service.get_submission(submission_id)
        return SubmissionResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Submission retrieved successfully.",
            submission=submission,
        )
    except ValueError as e:
        return SubmissionResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            message=str(e),
            errors=[{"field": "id", "message": str(e)}],
        )
    except Exception as e:
        return SubmissionResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="An unexpected error occurred.",
            errors=[{"field": "general", "message": str(e)}],
        )


@router.get("/submissions", response_model=SubmissionResponse, status_code=status.HTTP_200_OK)
def list_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    channel: str | None = Query(None, description="Filter by channel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_intake_officer),
):
    service = SubmissionService(db)
    try:
        submissions = service.list_submissions(skip=skip, limit=limit, channel=channel)
        return SubmissionResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Submissions retrieved successfully.",
            submissions=submissions,
        )
    except Exception as e:
        return SubmissionResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve submissions.",
            errors=[{"field": "general", "message": str(e)}],
        )
