from sqlalchemy.orm import Session
from . import models, schemas

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(full_name=user.full_name, email=user.email, hashed_password=user.hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_meeting(db: Session, meeting: schemas.MeetingCreate):
    db_meeting = models.Meeting(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def get_meetings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Meeting).offset(skip).limit(limit).all()

def create_segment(db: Session, seg: schemas.TranscriptionSegmentCreate):
    db_seg = models.TranscriptionSegment(**seg.dict())
    db.add(db_seg)
    db.commit()
    db.refresh(db_seg)
    return db_seg

def get_segments_for_meeting(db: Session, meeting_id: int):
    return db.query(models.TranscriptionSegment).filter(models.TranscriptionSegment.meeting_id == meeting_id).all()

def create_summary(db: Session, s: schemas.SummarizeCreate):
    db_s = models.Summarize(**s.dict())
    db.add(db_s)
    db.commit()
    db.refresh(db_s)
    return db_s

def get_summaries_for_meeting(db: Session, meeting_id: int):
    return db.query(models.Summarize).filter(models.Summarize.meeting_id == meeting_id).all()
