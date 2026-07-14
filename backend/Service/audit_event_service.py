from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from Repository.audit_event_repository import AuditEventRepository
from Entity.audit_event_entity import AuditEvent
from Utils.hashing import hash_snapshot


class AuditEventService:
    """
    Append-only audit trail writer (FR-022, NFR-001).

    Every state-changing action across the intake/case pipeline calls
    .log(...) here rather than touching AuditEvent directly, so the
    before/after hashing and timestamping stay consistent in one place.
    """

    def __init__(self, db: Session):
        self.repository = AuditEventRepository(db)

    def log(
        self,
        action: str,
        object_type: str,
        object_id: str,
        actor_user_id: Optional[int] = None,
        actor_channel: Optional[str] = None,
        before: Optional[dict] = None,
        after: Optional[dict] = None,
        ip_address: Optional[str] = None,
        detail: Optional[dict] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_user_id=actor_user_id,
            actor_channel=actor_channel,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            before_hash=hash_snapshot(before),
            after_hash=hash_snapshot(after),
            ip_address=ip_address,
            detail=detail,
            timestamp=datetime.now(timezone.utc),
        )
        return self.repository.create(event)

    def list_for_object(self, object_type: str, object_id: str) -> list[AuditEvent]:
        return self.repository.list_for_object(object_type, str(object_id))

    def list_all(
        self, skip: int = 0, limit: int = 200, object_type: Optional[str] = None
    ) -> list[AuditEvent]:
        return self.repository.list_all(skip=skip, limit=limit, object_type=object_type)
