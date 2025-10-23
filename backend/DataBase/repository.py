from sqlalchemy.orm import Session
from . import Models

def create_audio(db: Session, filename: str):
    audio = models.AudioFile(filename=filename)
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio

def get_audio(db: Session, audio_id: int):
    return db.query(models.AudioFile).filter(models.AudioFile.id == audio_id).first()

def update_audio(db: Session, audio_id: int, **kwargs):
    audio = get_audio(db, audio_id)
    if not audio:
        return None
    for key, value in kwargs.items():
        setattr(audio, key, value)
    db.commit()
    db.refresh(audio)
    return audio
