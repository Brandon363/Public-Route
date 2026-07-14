from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from Schema.base_schema import BaseResponse


class ForecastCreate(BaseModel):
    period_start:     datetime
    period_end:       datetime
    model_version_id: int              = Field(..., examples=[1])
    value:            float            = Field(..., examples=[42.5])
    lower_bound:      Optional[float]  = None
    upper_bound:      Optional[float]  = None
    district_id:      Optional[int]    = None
    category:         Optional[str]    = None
    subcategory:      Optional[str]    = None


class ForecastDTO(BaseModel):
    id:               int
    period_start:     datetime
    period_end:       datetime
    district_id:      Optional[int]
    category:         Optional[str]
    subcategory:      Optional[str]
    value:            float
    lower_bound:      Optional[float]
    upper_bound:      Optional[float]
    model_version_id: int

    model_config = ConfigDict(from_attributes=True)


class ForecastResponse(BaseResponse):
    forecast:  Optional[ForecastDTO]       = None
    forecasts: Optional[List[ForecastDTO]] = None
