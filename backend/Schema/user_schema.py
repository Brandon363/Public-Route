from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from Schema.base_schema import BaseResponse
from Utils.permissions import ALL_ROLES


class UserCreate(BaseModel):
    email:     EmailStr = Field(..., examples=["admin@serviceflow.ai"])
    full_name: Optional[str] = Field(None, examples=["Alice Mwangi"])
    password:  str      = Field(..., min_length=8, examples=["Str0ngP@ssword"])
    role:      str      = Field(..., examples=["administrator"],
                                description=f"Must be one of: {ALL_ROLES}")


class UserUpdate(BaseModel):
    email:     Optional[EmailStr] = Field(None, examples=["newemail@serviceflow.ai"])
    full_name: Optional[str]      = None
    password:  Optional[str]      = Field(None, min_length=8)
    is_active: Optional[bool]     = Field(None, examples=[True])


class UserDTO(BaseModel):
    id:            int
    email:         str
    full_name:     Optional[str]
    role:          str
    is_active:     bool
    token_version: int

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """
    Standard OAuth2 token response structure.
    Returned directly (not wrapped in BaseResponse) so that FastAPI's
    integrated Swagger UI 'Authorize' button can parse and store the token.
    """
    access_token: str
    token_type:   str = "bearer"


class UserResponse(BaseResponse):
    user:  Optional[UserDTO]       = None
    users: Optional[List[UserDTO]] = None
