from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from Schema.base_schema import BaseResponse
from Utils.Enums import RecommendationStatusEnum


class RecommendationCreate(BaseModel):
    scenario_label:     str           = Field(..., examples=["Q3 Water District Reallocation"])
    action_description: str           = Field(..., min_length=10)
    expected_impact:    Optional[str] = None
    rationale:          Optional[str] = None
    assumptions:        Optional[str] = None
    forecast_id:        Optional[int] = None
    model_version_id:   Optional[int] = None


class RecommendationUpdate(BaseModel):
    status:             Optional[RecommendationStatusEnum] = None
    action_description: Optional[str]                      = None
    expected_impact:    Optional[str]                      = None
    rationale:          Optional[str]                      = None
    assumptions:        Optional[str]                      = None


class RecommendationDTO(BaseModel):
    id:                 int
    scenario_label:     str
    action_description: str
    expected_impact:    Optional[str]
    rationale:          Optional[str]
    assumptions:        Optional[str]
    status:             str
    forecast_id:        Optional[int]
    model_version_id:   Optional[int]

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseResponse):
    recommendation:  Optional[RecommendationDTO]       = None
    recommendations: Optional[List[RecommendationDTO]] = None
