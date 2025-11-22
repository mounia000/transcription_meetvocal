from pydantic import BaseModel, Field
from typing import Optional

# Users
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserRead(BaseModel):
    id_user: int
    name: str
    email: str

    model_config = {"from_attributes": True}

# Audio files (Meetings)
class AudioFileCreate(BaseModel):
    id_user: int
    title: str
    status: str = "pending"
    file_path: str
    num_speakers: Optional[int] = None
    duration: Optional[float] = None

class AudioFileRead(AudioFileCreate):
    id_audio: int
    model_config = {"from_attributes": True}

# Transcription segments
class TranscriptionSegmentCreate(BaseModel):
    id_audio: int
    text_brut: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    sequence_number: int

class TranscriptionSegmentRead(TranscriptionSegmentCreate):
    id_transcription: int
    model_config = {"from_attributes": True}

# Summaries
class SummarizeCreate(BaseModel):
    id_audio: int
    summary_text: str
    type_resume: str
    speaker: Optional[str] = None

class SummarizeRead(SummarizeCreate):
    id_resume: int
    model_config = {"from_attributes": True}
