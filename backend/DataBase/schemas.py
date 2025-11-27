from pydantic import BaseModel
from typing import Optional

# ================================
# UTILISATEURS
# ================================
class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserRead(UserBase):
    id_user: int
    model_config = {"from_attributes": True}


# ================================
# FICHIERS AUDIO
# ================================
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


# ================================
# SEGMENTS
# ================================
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


# ================================
# RÉSUMÉS
# ================================
class SummarizeCreate(BaseModel):
    id_audio: int
    summary_text: str
    type_resume: str
    speaker: Optional[str] = None

class SummarizeRead(SummarizeCreate):
    id_resume: int
    model_config = {"from_attributes": True}
