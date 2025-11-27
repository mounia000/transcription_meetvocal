from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# ================================
# Table Utilisateurs
# ================================
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id_user = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    fichiers_audio = relationship("FichierAudio", back_populates="user", cascade="all, delete")


# ================================
# Table Fichiers Audio
# ================================
class FichierAudio(Base):
    __tablename__ = "fichiers_audio"

    id_audio = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("utilisateurs.id_user", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    file_path = Column(String(500), nullable=False)

    num_speakers = Column(Integer)
    duration = Column(Float)
    date_upload = Column(TIMESTAMP, server_default=func.now())

    user = relationship("Utilisateur", back_populates="fichiers_audio")
    transcriptions = relationship("Transcription", back_populates="audio", cascade="all, delete")
    resumes = relationship("Resume", back_populates="audio", cascade="all, delete")


# ================================
# Table Transcriptions
# ================================
class Transcription(Base):
    __tablename__ = "transcriptions"

    id_transcription = Column(Integer, primary_key=True, index=True)
    id_audio = Column(Integer, ForeignKey("fichiers_audio.id_audio", ondelete="CASCADE"), nullable=False)

    text_brut = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    speaker = Column(String(50))
    sequence_number = Column(Integer, nullable=False)

    audio = relationship("FichierAudio", back_populates="transcriptions")


# ================================
# Table Résumés
# ================================
class Resume(Base):
    __tablename__ = "resumes"

    id_resume = Column(Integer, primary_key=True, index=True)
    id_audio = Column(Integer, ForeignKey("fichiers_audio.id_audio", ondelete="CASCADE"), nullable=False)

    summary_text = Column(Text, nullable=False)
    type_resume = Column(String(50), nullable=False)  # general | par_speaker
    speaker = Column(String(50))

    audio = relationship("FichierAudio", back_populates="resumes")
