from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# 接收前端請求的格式
class NoteCreate(BaseModel):
    title: str
    content: Optional[str] = None

# API 回應前端的格式
class NoteResponse(BaseModel):
    id: int
    title: str
    content: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True