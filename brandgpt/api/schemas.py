from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionCreate(BaseModel):
    prompt_id: Optional[int] = None
    system_prompt: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    user_id: int
    prompt_id: Optional[int]
    system_prompt: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)


class PromptResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content: str
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    session_id: str
    content_type: str = Field(..., pattern=r"^(pdf|text|url|json)$")
    url: Optional[str] = None
    max_depth: Optional[int] = Field(
        None, 
        ge=1, 
        le=10, 
        description="Depth parameter for URL scraping. 1=only provided URL, 2=URL + all links it contains, etc. Default is 1."
    )


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    use_system_prompt: bool = True


class QueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    error: Optional[str] = None


class IngestionStatus(BaseModel):
    document_id: int
    status: str
    message: Optional[str] = None