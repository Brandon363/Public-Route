from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from Schema.base_schema import BaseResponse


class AuditEventCreate(BaseModel):
    """
    Created programmatically by service/middleware — never by direct user input.
    actor_user_id and ip_address are injected from the request context.
    """
    action:        str    = Field(..., examples=["case.status_changed"])
    object_type:   str    = Field(..., examples=["case"])
    object_id:     str    = Field(..., examples=["some-uuid-or-int"])
    before_hash:   Optional[str] = None
    after_hash:    Optional[str] = None
    actor_channel: Optional[str] = None
    actor_user_id: Optional[int] = None
    ip_address:    Optional[str] = None
    timestamp:     datetime


class AuditEventDTO(BaseModel):
    id:            UUID
    actor_user_id: Optional[int]
    # Resolved server-side from actor_user_id (User.full_name or email) so
    # the UI never has to show a bare numeric ID or make its own lookup —
    # not a real column, populated by the controller at read time.
    actor_name:    Optional[str] = None
    actor_channel: Optional[str]
    action:        str
    object_type:   str
    object_id:     str
    before_hash:   Optional[str]
    after_hash:    Optional[str]
    ip_address:    Optional[str]
    # Human-readable, non-PII summary of what changed (e.g. old/new status
    # or classification result) — see Entity/audit_event_entity.py.
    detail:        Optional[dict] = None
    timestamp:     datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseResponse):
    event:  Optional[AuditEventDTO]       = None
    events: Optional[List[AuditEventDTO]] = None
