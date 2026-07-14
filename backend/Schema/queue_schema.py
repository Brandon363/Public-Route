from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from Schema.base_schema import BaseResponse


class QueueCreate(BaseModel):
    unit_id:        int               = Field(..., examples=[1])
    name:           str               = Field(..., examples=["Water – Priority Queue"])
    priority_rules: Optional[Any]     = Field(default_factory=dict)
    capacity:       Optional[int]     = Field(None, examples=[50])
    is_active:      bool              = True


class QueueUpdate(BaseModel):
    name:           Optional[str]  = None
    priority_rules: Optional[Any]  = None
    capacity:       Optional[int]  = None
    is_active:      Optional[bool] = None


class QueueDTO(BaseModel):
    id:             int
    unit_id:        int
    name:           str
    priority_rules: Optional[Any]
    capacity:       Optional[int]
    is_active:      bool

    model_config = ConfigDict(from_attributes=True)


class QueueResponse(BaseResponse):
    queue:  Optional[QueueDTO]       = None
    queues: Optional[List[QueueDTO]] = None
