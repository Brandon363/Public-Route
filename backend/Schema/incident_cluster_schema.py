from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from Schema.base_schema import BaseResponse
from Utils.Enums import SeverityEnum, CaseStatusEnum


class IncidentClusterCreate(BaseModel):
    category:       str           = Field(..., examples=["water_sanitation"])
    subcategory:    Optional[str] = None
    description:    Optional[str] = None
    severity:       SeverityEnum  = SeverityEnum.MEDIUM
    signature:      Optional[str] = None
    geography_json: Optional[Any] = Field(default_factory=dict)


class IncidentClusterUpdate(BaseModel):
    status:         Optional[CaseStatusEnum] = None
    severity:       Optional[SeverityEnum]   = None
    description:    Optional[str]            = None
    geography_json: Optional[Any]            = None
    closed_at:      Optional[datetime]       = None


class IncidentClusterDTO(BaseModel):
    id:             UUID
    category:       str
    subcategory:    Optional[str]
    description:    Optional[str]
    status:         str
    severity:       str
    signature:      Optional[str]
    geography_json: Optional[Any]
    opened_at:      Optional[datetime]
    closed_at:      Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class IncidentClusterResponse(BaseResponse):
    cluster:  Optional[IncidentClusterDTO]       = None
    clusters: Optional[List[IncidentClusterDTO]] = None
