from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from Schema.base_schema import BaseResponse
from Utils.Enums import ApprovalDecisionEnum


class ApprovalCreate(BaseModel):
    recommendation_id:  int                 = Field(..., examples=[1])
    decision:           ApprovalDecisionEnum
    reason:             str                 = Field(..., min_length=5,
                                                     examples=["Approved after reviewing capacity data."])
    decided_at:         datetime


class ApprovalDTO(BaseModel):
    id:                 int
    recommendation_id:  int
    reviewer_user_id:   int
    decision:           str
    reason:             str
    decided_at:         datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalResponse(BaseResponse):
    approval:  Optional[ApprovalDTO]       = None
    approvals: Optional[List[ApprovalDTO]] = None
