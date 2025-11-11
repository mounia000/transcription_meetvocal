from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    hashed_password: Optional[str] = None

class UserRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    owner_id: Optional[int] = None

class MeetingRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    owner_id: Optional[int]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class TranscriptionSegmentCreate(BaseModel):
    meeting_id: int
    speaker: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    text: Optional[str] = None

class TranscriptionSegmentRead(BaseModel):
    id: int
    meeting_id: int
    speaker: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    text: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class SummarizeCreate(BaseModel):
    meeting_id: int
    summary_text: Optional[str] = None
    by_ai: Optional[bool] = True

class SummarizeRead(BaseModel):
    id: int
    meeting_id: int
    summary_text: Optional[str]
    by_ai: bool
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
