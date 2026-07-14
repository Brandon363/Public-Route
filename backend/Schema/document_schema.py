from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from uuid import UUID
from Schema.base_schema import BaseResponse
from Utils.Enums import MalwareStatusEnum


class DocumentCreate(BaseModel):
    submission_id:      UUID
    mime_type:          str   = Field(..., examples=["application/pdf"])
    original_filename:  Optional[str]  = None
    storage_ref:        Optional[str]  = None
    file_hash:          Optional[str]  = None


class DocumentUpdateScan(BaseModel):
    """Written back by the malware scan worker."""
    malware_status: MalwareStatusEnum


class DocumentUpdateOCR(BaseModel):
    """Written back by the OCR extraction pipeline."""
    ocr_text:        Optional[str]  = None
    extraction_json: Optional[Any]  = None


class DocumentDTO(BaseModel):
    id:                UUID
    submission_id:     UUID
    mime_type:         str
    original_filename: Optional[str]
    file_hash:         Optional[str]
    ocr_text:          Optional[str]
    extraction_json:   Optional[Any]
    malware_status:    str
    storage_ref:       Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseResponse):
    document:  Optional[DocumentDTO]       = None
    documents: Optional[List[DocumentDTO]] = None
