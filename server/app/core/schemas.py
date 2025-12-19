from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    hwid_hash: str = Field(min_length=64, max_length=64, description="sha256 hex")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: EmailStr
    session_expires_at: datetime

class LogoutResponse(BaseModel):
    ok: bool

class ProductResponse(BaseModel):
    code: str
    name: str
    is_paid: bool

class RedeemRequest(BaseModel):
    product_code: str
    license_code: str
    hwid_hash: str = Field(min_length=64, max_length=64)

class RedeemResponse(BaseModel):
    ok: bool
    product_code: str
    expires_at: Optional[datetime] = None
    bound_hwid_hash: str

class LicenseValidateRequest(BaseModel):
    product_code: str
    hwid_hash: str = Field(min_length=64, max_length=64)

class LicenseValidateResponse(BaseModel):
    valid: bool
    product_code: str
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
