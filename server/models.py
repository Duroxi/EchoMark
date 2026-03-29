from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request models
class RatingSubmit(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=255)
    accuracy: int = Field(..., ge=1, le=5)
    efficiency: int = Field(..., ge=1, le=5)
    usability: int = Field(..., ge=1, le=5)
    stability: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=20)

class RatingResponse(BaseModel):
    id: str
    success: bool
    message: str

class AgentRegisterResponse(BaseModel):
    api_key: str

class ToolStatsResponse(BaseModel):
    tool_name: str
    stats: dict

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail