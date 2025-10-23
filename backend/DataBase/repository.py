from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from .DB import Base

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(String, default="uploaded")
    transcription = Column(Text)
    summary = Column(Text)
    pdf_path = Column(String)
    duration = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
