from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from Schema.base_schema import BaseResponse
from Utils.Enums import ModelStatusEnum


class ModelVersionCreate(BaseModel):
    purpose:            str              = Field(..., examples=["service_classifier"])
    version_tag:        str              = Field(..., examples=["v1.0.0"])
    feature_schema:     Optional[Any]   = Field(default_factory=dict)
    metrics:            Optional[Any]   = Field(default_factory=dict)
    threshold:          Optional[float] = Field(None, ge=0.0, le=1.0)
    training_data_ref:  Optional[str]   = None


class ModelVersionUpdate(BaseModel):
    status:      Optional[ModelStatusEnum] = None
    metrics:     Optional[Any]             = None
    threshold:   Optional[float]           = Field(None, ge=0.0, le=1.0)
    deployed_at: Optional[datetime]        = None


class ModelVersionDTO(BaseModel):
    id:                 int
    purpose:            str
    version_tag:        str
    feature_schema:     Optional[Any]
    metrics:            Optional[Any]
    threshold:          Optional[float]
    training_data_ref:  Optional[str]
    status:             str
    deployed_at:        Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ModelVersionResponse(BaseResponse):
    model_version:  Optional[ModelVersionDTO]       = None
    model_versions: Optional[List[ModelVersionDTO]] = None
