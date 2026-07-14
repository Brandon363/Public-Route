from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from Config.database import get_db
from Config.dependencies import get_current_user
from Schema.audit_event_schema import AuditEventResponse
from Service.audit_event_service import AuditEventService
from Service.case_service import CaseService
from Utils.permissions import CAN_VIEW_AUDIT, ROLE_CITIZEN
from Entity.user_entity import User

router = APIRouter(prefix="/audit-events", tags=["Audit"])


def _citizen_owns_case(db: Session, object_id: str | None, user_id: int) -> bool:
    if not object_id:
        return False
    try:
        case = CaseService(db).get_case(UUID(object_id))
    except (ValueError, Exception):
        return False
    return CaseService.is_owned_by_citizen(case, user_id)


def _resolve_actor_names(db: Session, actor_user_ids: set[int]) -> dict[int, str]:
    if not actor_user_ids:
        return {}
    users = db.query(User).filter(User.id.in_(actor_user_ids)).all()
    return {u.id: (u.full_name or u.email) for u in users}


def _to_dto_dict(event, actor_names: dict[int, str], redact: bool) -> dict:
    """
    Shapes one AuditEvent row into an AuditEventDTO-ready dict.

    redact=True strips actor identity and forensic fields (used for the
    citizen-owner carve-out) but always keeps `detail` — it's a non-PII
    summary of what changed, which is the whole point of a citizen-visible
    case roadmap.
    """
    return {
        "id": event.id,
        "action": event.action,
        "object_type": event.object_type,
        "object_id": event.object_id,
        "timestamp": event.timestamp,
        "detail": event.detail,
        "actor_user_id": None if redact else event.actor_user_id,
        "actor_name": None if redact else actor_names.get(event.actor_user_id),
        "actor_channel": None if redact else event.actor_channel,
        "before_hash": None if redact else event.before_hash,
        "after_hash": None if redact else event.after_hash,
        "ip_address": None if redact else event.ip_address,
    }


@router.get("/", response_model=AuditEventResponse, status_code=status.HTTP_200_OK)
def list_audit_events(
    object_type: str | None = Query(None),
    object_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Read-only immutable audit trail (FR-022). No create/update/delete
    endpoint is exposed here — audit rows are written internally by
    AuditEventService as a side effect of state-changing actions elsewhere.

    Access:
    - Auditor/administrator (CAN_VIEW_AUDIT): full events for any object,
      with actor identity resolved to a display name — unchanged behaviour
      plus the actor_name enrichment.
    - Citizen: only events for a case they submitted themselves
      (object_type="case", ownership checked against the submission), and
      only a *redacted* view — actor identity and forensic fields (hash/IP)
      stripped, but the human-readable "what changed" detail kept — so the
      case roadmap can be citizen-visible without exposing who-did-what.
    - Everyone else: empty result, not an error, so this list endpoint
      never confirms or denies whether events exist for an object the
      caller isn't entitled to see.
    """
    is_auditor = current_user.role in CAN_VIEW_AUDIT
    is_citizen_owner = (
        not is_auditor
        and current_user.role == ROLE_CITIZEN
        and object_type == "case"
        and _citizen_owns_case(db, object_id, current_user.id)
    )

    if not (is_auditor or is_citizen_owner):
        return AuditEventResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Audit events retrieved successfully.",
            events=[],
        )

    service = AuditEventService(db)
    try:
        if object_type is not None and object_id is not None:
            events = service.list_for_object(object_type, object_id)
        else:
            events = service.list_all(skip=skip, limit=limit, object_type=object_type)

        actor_names = _resolve_actor_names(
            db, {e.actor_user_id for e in events if e.actor_user_id is not None}
        )
        events_out = [_to_dto_dict(e, actor_names, redact=is_citizen_owner) for e in events]

        return AuditEventResponse(
            status_code=status.HTTP_200_OK,
            success=True,
            message="Audit events retrieved successfully.",
            events=events_out,
        )
    except Exception as e:
        return AuditEventResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            message="Failed to retrieve audit events.",
            errors=[{"field": "general", "message": str(e)}],
        )
