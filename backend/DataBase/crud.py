
from sqlalchemy.orm import Session
from . import models, schemas

# ================================
# UTILISATEURS
# ================================
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.Utilisateur(
        name=user.name,
        email=user.email,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Utilisateur).offset(skip).limit(limit).all()

# ================================
# FICHIERS AUDIO / MEETINGS
# ================================
def create_audio_file(db: Session, audio_file: schemas.AudioFileCreate):
    db_file = models.FichierAudio(
        id_user=audio_file.id_user,
        title=audio_file.title,
        status=audio_file.status,
        file_path=audio_file.file_path,
        num_speakers=audio_file.num_speakers,
        duration=audio_file.duration
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_audio_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FichierAudio).offset(skip).limit(limit).all()

def get_audio_file(db: Session, file_id: int):
    return db.query(models.FichierAudio).filter(models.FichierAudio.id_audio == file_id).first()

# ================================
# TRANSCRIPTIONS
# ================================
def create_segment(db: Session, seg: schemas.TranscriptionSegmentCreate):
    db_seg = models.Transcription(
        id_audio=seg.id_audio,
        text_brut=seg.text_brut,
        start_time=seg.start_time,
        end_time=seg.end_time,
        speaker=seg.speaker,
        sequence_number=seg.sequence_number
    )
    db.add(db_seg)
    db.commit()
    db.refresh(db_seg)
    return db_seg

def get_segments_for_meeting(db: Session, meeting_id: int):
    return (
        db.query(models.Transcription)
        .filter(models.Transcription.id_audio == meeting_id)
        .order_by(models.Transcription.sequence_number.asc())
        .all()
    )

# ================================
# RESUMES / SUMMARIES
# ================================
def create_summary(db: Session, summary: schemas.SummarizeCreate):
    db_sum = models.Resume(
        id_audio=summary.id_audio,
        summary_text=summary.summary_text,
        type_resume=summary.type_resume,
        speaker=summary.speaker
    )
    db.add(db_sum)
    db.commit()
    db.refresh(db_sum)
    return db_sum

def get_summaries_for_meeting(db: Session, meeting_id: int):
    return (
        db.query(models.Resume)
        .filter(models.Resume.id_audio == meeting_id)
        .all()
    )
