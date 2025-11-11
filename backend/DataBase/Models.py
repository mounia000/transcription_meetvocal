from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(256), nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meetings = relationship("Meeting", back_populates="owner")

class Meeting(Base):
    __tablename__ = "meeting"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="meetings")
    transcription_segments = relationship("TranscriptionSegment", back_populates="meeting")
    summaries = relationship("Summarize", back_populates="meeting")

class TranscriptionSegment(Base):
    __tablename__ = "transcription_segment"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id"))
    speaker = Column(String(128), nullable=True)
    start_time = Column(String(64), nullable=True)
    end_time = Column(String(64), nullable=True)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="transcription_segments")

class Summarize(Base):
    __tablename__ = "summarize"
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meeting.id"))
    summary_text = Column(Text, nullable=True)
    by_ai = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="summaries")
