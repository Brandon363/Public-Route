from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from Schema.base_schema import BaseResponse


class OrganisationUnitCreate(BaseModel):
    name:                str            = Field(..., examples=["Harare City Council – Water Dept"])
    jurisdiction:        List[Any]      = Field(default_factory=list,
                                                examples=[[1, 2, 3]])
    service_categories:  List[str]      = Field(default_factory=list,
                                                examples=[["water", "sanitation"]])
    escalation_path:     Optional[List[int]] = Field(default_factory=list)
    is_active:           bool           = True


class OrganisationUnitUpdate(BaseModel):
    name:                Optional[str]       = None
    jurisdiction:        Optional[List[Any]] = None
    service_categories:  Optional[List[str]] = None
    escalation_path:     Optional[List[int]] = None
    is_active:           Optional[bool]      = None


class OrganisationUnitDTO(BaseModel):
    id:                  int
    name:                str
    jurisdiction:        List[Any]
    service_categories:  List[str]
    escalation_path:     Optional[List[Any]]
    is_active:           bool

    model_config = ConfigDict(from_attributes=True)


class OrganisationUnitResponse(BaseResponse):
    unit:  Optional[OrganisationUnitDTO]        = None
    units: Optional[List[OrganisationUnitDTO]]  = None
