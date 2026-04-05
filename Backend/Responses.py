from pydantic import BaseModel
from typing import List, Optional


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    created_at: Optional[str] = None
    progress: Optional[int] = None
    errors: Optional[List[str]] = None
    resources: Optional[dict] = None


class ScanStatusResponse(BaseModel):
    status: str
    progress: int
    results: Optional[dict] = None
    errors: Optional[List[str]] = None


class ScanResultResponse(BaseModel):
    scan_id: str
    results: Optional[dict] = None
    created_at: Optional[str] = None
    errors: Optional[List[str]] = None


class AuditResponse(BaseModel):
    audit_id: str
    vulnerabilities: Optional[List[dict]] = None
    created_at: Optional[str] = None


class CloudRegisterResponse(BaseModel):
    message: str
    id: str


class MessageResponse(BaseModel):
    message: str


class BoolResponse(BaseModel):
    success: bool


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    username: str
    email: str
    isVerified: bool = False
    id: Optional[str] = None

class StartScanResponse(BaseModel):
    scan_id: str
    message: str = "Scan started successfully"