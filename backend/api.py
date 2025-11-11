from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.DataBase import models, schemas, crud
from backend.DataBase import database

from backend.DataBase.database import SessionLocal, engine
import os

# Keep existing IA pipeline available
from .main import pipeline as existing_pipeline  # original pipeline function; left unchanged

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Transcription MeetVocal API (FastAPI port)")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple healthcheck
@app.get("/health")
def health():
    return {"status": "ok"}

# Users
@app.post("/users/", response_model=schemas.UserRead)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db, user)
    return db_user

@app.get("/users/", response_model=list[schemas.UserRead])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

# Meetings
@app.post("/meetings/", response_model=schemas.MeetingRead)
def create_meeting(meeting: schemas.MeetingCreate, db: Session = Depends(get_db)):
    return crud.create_meeting(db, meeting)

@app.get("/meetings/", response_model=list[schemas.MeetingRead])
def list_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_meetings(db, skip=skip, limit=limit)

# Transcription segments
@app.post("/segments/", response_model=schemas.TranscriptionSegmentRead)
def create_segment(seg: schemas.TranscriptionSegmentCreate, db: Session = Depends(get_db)):
    return crud.create_segment(db, seg)

@app.get("/meetings/{meeting_id}/segments", response_model=list[schemas.TranscriptionSegmentRead])
def get_segments(meeting_id: int, db: Session = Depends(get_db)):
    return crud.get_segments_for_meeting(db, meeting_id)

# Summaries
@app.post("/meetings/{meeting_id}/summaries", response_model=schemas.SummarizeRead)
def create_summary(meeting_id: int, summary: schemas.SummarizeCreate, db: Session = Depends(get_db)):
    if meeting_id != summary.meeting_id:
        raise HTTPException(status_code=400, detail="meeting_id mismatch")
    return crud.create_summary(db, summary)

@app.get("/meetings/{meeting_id}/summaries", response_model=list[schemas.SummarizeRead])
def get_summaries(meeting_id: int, db: Session = Depends(get_db)):
    return crud.get_summaries_for_meeting(db, meeting_id)

# Endpoint to trigger existing AI pipeline on an uploaded audio file path
@app.post("/pipeline/")
def run_pipeline(audio_path: str):
    """Run the original pipeline from backend/main.py. The function is kept unchanged."""
    try:
        existing_pipeline(audio_path)
        return {"status": "pipeline started", "audio": audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

