from sqlalchemy.orm import Session
from . import models, schemas

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


def get_user_by_email(db: Session, email: str):
    return db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first()


# ============================================================
# FICHIERS AUDIO
# ============================================================

def create_audio_file(db: Session, audio: schemas.AudioFileCreate):
    db_audio = models.FichierAudio(
        id_user=audio.id_user,
        title=audio.title,
        file_path=audio.file_path,
        status=audio.status,
        num_speakers=audio.num_speakers,
        duration=audio.duration
    )
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


def get_audio_file_by_id(db: Session, id_audio: int):
    return db.query(models.FichierAudio).filter(models.FichierAudio.id_audio == id_audio).first()


def delete_audio_file(db: Session, id_audio: int):
    audio = get_audio_file_by_id(db, id_audio)
    if audio:
        db.delete(audio)
        db.commit()
        return True
    return False


def update_audio_status(db: Session, id_audio: int, status: str):
    audio = db.query(models.FichierAudio).filter(
        models.FichierAudio.id_audio == id_audio
    ).first()

    if not audio:
        return None

    audio.status = status
    db.commit()
    db.refresh(audio)
    return audio
