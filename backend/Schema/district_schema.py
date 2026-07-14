from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from Schema.base_schema import BaseResponse
from Utils.Enums import SettlementTypeEnum


class DistrictCreate(BaseModel):
    name:             str               = Field(..., examples=["Harare Central"])
    province:         str               = Field(..., examples=["Harare"])
    settlement_type:  SettlementTypeEnum = Field(SettlementTypeEnum.URBAN)
    latitude:         Optional[float]  = None
    longitude:        Optional[float]  = None


class DistrictUpdate(BaseModel):
    name:             Optional[str]              = None
    province:         Optional[str]              = None
    settlement_type:  Optional[SettlementTypeEnum] = None
    latitude:         Optional[float]            = None
    longitude:        Optional[float]            = None


class DistrictDTO(BaseModel):
    id:              int
    name:            str
    province:        str
    settlement_type: str
    latitude:        Optional[float]
    longitude:       Optional[float]

    model_config = ConfigDict(from_attributes=True)


class DistrictResponse(BaseResponse):
    district:  Optional[DistrictDTO]       = None
    districts: Optional[List[DistrictDTO]] = None
