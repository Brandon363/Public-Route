from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from Schema.base_schema import BaseResponse
from Utils.Enums import ChannelEnum, ConsentStatusEnum


class SubmissionCreate(BaseModel):
    channel:                    ChannelEnum
    received_at:                datetime
    service_description:        str          = Field(..., min_length=5)
    location_text:              Optional[str] = None
    language_code:              Optional[str] = Field(None, max_length=10)
    language_confidence:        Optional[float] = Field(None, ge=0.0, le=1.0)
    consent_status:             ConsentStatusEnum = ConsentStatusEnum.NOT_REQUIRED
    citizen_contact_token:      Optional[str] = None
    transcript:                 Optional[str] = None
    raw_text_ref:               Optional[str] = None
    attachment_refs:            Optional[List[str]] = Field(default_factory=list)
    accessibility_preferences:  Optional[Any]       = Field(default_factory=dict)
    source_metadata:            Any                 = Field(default_factory=dict)
    citizen_contact_id:         Optional[int]       = None
    district_id:                Optional[int]       = None
    contact_email:              Optional[str]       = None
    contact_phone:              Optional[str]       = None


class SubmissionUpdate(BaseModel):
    district_id:                Optional[int]       = None
    transcript:                 Optional[str]       = None
    language_code:              Optional[str]       = None
    language_confidence:        Optional[float]     = Field(None, ge=0.0, le=1.0)
    consent_status:             Optional[ConsentStatusEnum] = None
    attachment_refs:            Optional[List[str]] = None


class SubmissionDTO(BaseModel):
    id:                         UUID
    channel:                    str
    received_at:                datetime
    service_description:        str
    location_text:              Optional[str]
    language_code:              Optional[str]
    language_confidence:        Optional[float]
    consent_status:             str
    district_id:                Optional[int]
    citizen_contact_id:         Optional[int]
    attachment_refs:            Optional[List[str]]
    accessibility_preferences:  Optional[Any]
    source_metadata:            Optional[Any]
    contact_email:              Optional[str]       = None
    contact_phone:              Optional[str]       = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionResponse(BaseResponse):
    submission:  Optional[SubmissionDTO]       = None
    submissions: Optional[List[SubmissionDTO]] = None
