from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from Schema.base_schema import BaseResponse
from Utils.Enums import AssignmentStatusEnum


class AssignmentCreate(BaseModel):
    team_id:              int               = Field(..., examples=[1])
    case_id:              Optional[UUID]    = None
    incident_cluster_id:  Optional[UUID]    = None
    assigned_at:          Optional[datetime] = None
    notes:                Optional[str]     = None


class AssignmentUpdate(BaseModel):
    status:               Optional[AssignmentStatusEnum] = None
    outcome:              Optional[str]                  = None
    notes:                Optional[str]                  = None


class AssignmentDTO(BaseModel):
    id:                   int
    team_id:              int
    case_id:              Optional[UUID]
    incident_cluster_id:  Optional[UUID]
    assigned_at:          Optional[datetime]
    status:               str
    outcome:              Optional[str]
    notes:                Optional[str]

    model_config = ConfigDict(from_attributes=True)


class AssignmentResponse(BaseResponse):
    assignment:  Optional[AssignmentDTO]       = None
    assignments: Optional[List[AssignmentDTO]] = None
