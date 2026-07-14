from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from Schema.base_schema import BaseResponse
from Utils.Enums import ChannelEnum, DeliveryStatusEnum


class NotificationCreate(BaseModel):
    channel:             ChannelEnum
    message:             str           = Field(..., min_length=1)
    submission_id:       Optional[UUID] = None
    citizen_contact_id:  Optional[int]  = None


class NotificationUpdateDelivery(BaseModel):
    """Written back by the notification delivery worker."""
    delivery_status:  DeliveryStatusEnum
    delivered_at:     Optional[datetime] = None
    failure_reason:   Optional[str]      = None


class NotificationDTO(BaseModel):
    id:                  int
    channel:             str
    message:             str
    delivery_status:     str
    submission_id:       Optional[UUID]
    citizen_contact_id:  Optional[int]
    sent_at:             Optional[datetime]
    delivered_at:        Optional[datetime]
    failure_reason:      Optional[str]

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseResponse):
    notification:  Optional[NotificationDTO]       = None
    notifications: Optional[List[NotificationDTO]] = None
