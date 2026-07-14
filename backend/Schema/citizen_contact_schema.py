from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from Schema.base_schema import BaseResponse


class CitizenContactCreate(BaseModel):
    encrypted_phone:            Optional[str]  = Field(None, description="Tokenised/encrypted phone")
    preferred_channel:          Optional[str]  = None
    language_code:              Optional[str]  = Field(None, max_length=10)
    accessibility_preferences:  Optional[Any]  = Field(default_factory=dict)


class CitizenContactUpdate(BaseModel):
    preferred_channel:          Optional[str]  = None
    language_code:              Optional[str]  = Field(None, max_length=10)
    accessibility_preferences:  Optional[Any]  = None


class CitizenContactDTO(BaseModel):
    id:                         int
    preferred_channel:          Optional[str]
    language_code:              Optional[str]
    accessibility_preferences:  Optional[Any]
    # encrypted_phone intentionally excluded from DTO — never exposed via API

    model_config = ConfigDict(from_attributes=True)


class CitizenContactResponse(BaseResponse):
    contact:  Optional[CitizenContactDTO]       = None
    contacts: Optional[List[CitizenContactDTO]] = None
