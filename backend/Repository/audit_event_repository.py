from sqlalchemy.orm import Session
from Entity.audit_event_entity import AuditEvent


class AuditEventRepository:
    """
    Data access layer for the append-only AuditEvent table.
    No update()/delete() — audit rows are never mutated or removed.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, event: AuditEvent) -> AuditEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_for_object(
        self, object_type: str, object_id: str, skip: int = 0, limit: int = 200
    ) -> list[AuditEvent]:
        return (
            self.db.query(AuditEvent)
            .filter(
                AuditEvent.object_type == object_type,
                AuditEvent.object_id == object_id,
            )
            .order_by(AuditEvent.timestamp.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(
        self,
        skip: int = 0,
        limit: int = 200,
        object_type: str | None = None,
    ) -> list[AuditEvent]:
        query = self.db.query(AuditEvent)
        if object_type is not None:
            query = query.filter(AuditEvent.object_type == object_type)
        return (
            query.order_by(AuditEvent.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
