from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from Schema.base_schema import BaseResponse


class ResourceTeamCreate(BaseModel):
    name:                  str            = Field(..., examples=["Alpha Field Team"])
    skills:                List[str]      = Field(default_factory=list,
                                                   examples=[["plumbing", "electrical"]])
    service_categories:    List[str]      = Field(default_factory=list,
                                                   examples=[["water", "sanitation"]])
    capacity:              int            = Field(1, ge=1, examples=[5])
    base_district_id:      Optional[int]  = None
    availability_schedule: Optional[Any]  = Field(default_factory=dict)
    is_active:             bool           = True


class ResourceTeamUpdate(BaseModel):
    name:                  Optional[str]       = None
    skills:                Optional[List[str]] = None
    service_categories:    Optional[List[str]] = None
    capacity:              Optional[int]       = Field(None, ge=1)
    base_district_id:      Optional[int]       = None
    availability_schedule: Optional[Any]       = None
    is_active:             Optional[bool]      = None


class ResourceTeamDTO(BaseModel):
    id:                    int
    name:                  str
    skills:                Optional[List[str]]
    service_categories:    Optional[List[str]]
    capacity:              int
    base_district_id:      Optional[int]
    availability_schedule: Optional[Any]
    is_active:             bool

    model_config = ConfigDict(from_attributes=True)


class ResourceTeamResponse(BaseResponse):
    team:  Optional[ResourceTeamDTO]       = None
    teams: Optional[List[ResourceTeamDTO]] = None
