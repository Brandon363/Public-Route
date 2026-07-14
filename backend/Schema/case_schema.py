from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from Schema.base_schema import BaseResponse
from Schema.submission_schema import SubmissionDTO
from Utils.Enums import CaseStatusEnum, UrgencyEnum


class CaseCreate(BaseModel):
    reference_number:           str           = Field(..., examples=["SF-2026-00001"])
    category:                   str           = Field(..., examples=["water_sanitation"])
    subcategory:                Optional[str] = None
    urgency:                    UrgencyEnum   = UrgencyEnum.MEDIUM
    description:                str           = Field(..., min_length=5)
    classification_confidence:  Optional[float] = Field(None, ge=0.0, le=1.0)
    sla_deadline:               Optional[datetime] = None
    submission_id:              Optional[UUID] = None
    district_id:                Optional[int] = None
    queue_id:                   Optional[int] = None
    incident_cluster_id:        Optional[UUID] = None
    english_description:        Optional[str] = None
    contact_email:              Optional[str] = None
    contact_phone:              Optional[str] = None


class CaseUpdate(BaseModel):
    category:                   Optional[str]           = None
    subcategory:                Optional[str]           = None
    urgency:                    Optional[UrgencyEnum]   = None
    status:                     Optional[CaseStatusEnum] = None
    description:                Optional[str]           = None
    classification_confidence:  Optional[float]         = Field(None, ge=0.0, le=1.0)
    sla_deadline:               Optional[datetime]      = None
    queue_id:                   Optional[int]           = None
    district_id:                Optional[int]           = None
    incident_cluster_id:        Optional[UUID]          = None
    opened_at:                  Optional[datetime]      = None
    closed_at:                  Optional[datetime]      = None


class CaseDTO(BaseModel):
    id:                         UUID
    reference_number:           str
    category:                   str
    subcategory:                Optional[str]
    urgency:                    str
    status:                     str
    description:                str
    classification_confidence:  Optional[float]
    sla_deadline:               Optional[datetime]
    opened_at:                  Optional[datetime]
    closed_at:                  Optional[datetime]
    submission_id:              Optional[UUID]
    district_id:                Optional[int]
    queue_id:                   Optional[int]
    incident_cluster_id:        Optional[UUID]
    english_description:        Optional[str] = None
    contact_email:              Optional[str] = None
    contact_phone:              Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaseResponse(BaseResponse):
    case:  Optional[CaseDTO]       = None
    cases: Optional[List[CaseDTO]] = None


class ClassificationCorrection(BaseModel):
    category:    str           = Field(..., examples=["water_sanitation"])
    subcategory: Optional[str] = None
    urgency:     UrgencyEnum   = UrgencyEnum.MEDIUM


class RouteCaseRequest(BaseModel):
    queue_id: Optional[int] = Field(
        None, description="Explicit queue to route to; omit to use the auto-recommendation."
    )


class CaseStatusUpdate(BaseModel):
    status: CaseStatusEnum
    reason: str = Field(..., min_length=3)


class CaseSummaryRow(BaseModel):
    key:   Optional[Any]
    count: int


class CaseSummaryResponse(BaseResponse):
    counts: Optional[List[CaseSummaryRow]] = None


class SubmissionIntakeResponse(BaseResponse):
    submission: Optional[SubmissionDTO] = None
    case:       Optional[CaseDTO]       = None
