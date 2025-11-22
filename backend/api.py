from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.DataBase import models, schemas, crud
from backend.DataBase import database
from backend.DataBase.database import SessionLocal, engine
import os
import shutil

#from .main import pipeline as existing_pipeline
from .pipeline_service import run_pipeline_service

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Transcription MeetVocal API (FastAPI port)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer le dossier uploads s'il n'existe pas
UPLOAD_DIR = "backend/IA/audio/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
@app.post("/meetings/", response_model=schemas.AudioFileRead)
def create_meeting(meeting: schemas.AudioFileCreate, db: Session = Depends(get_db)):
    return crud.create_audio_file(db, meeting)

@app.get("/meetings/", response_model=list[schemas.AudioFileRead])
def list_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_audio_files(db, skip=skip, limit=limit)

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

# 🆕 Upload de fichier audio
@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload un fichier audio depuis le PC de l'utilisateur"""
    try:
        # Vérifier le type de fichier
        allowed_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Type de fichier non supporté. Utilisez: {', '.join(allowed_extensions)}"
            )
        
        # Créer un nom de fichier unique
        import time
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "status": "success",
            "message": "Fichier uploadé avec succès",
            "filename": safe_filename,
            "path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🆕Pipeline avec upload
@app.post("/pipeline-upload/")
async def run_pipeline_upload(file: UploadFile = File(...)):
    try:
        upload_result = await upload_audio(file)
        audio_path = upload_result["path"]

        result = run_pipeline_service(audio_path)

        return {
            "status": "success",
            "audio": audio_path,
            "pipeline_result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/")
def run_pipeline(audio_path: str):
    """Run the original pipeline from backend/main.py"""
    try:
        run_pipeline_service(audio_path)
        return {"status": "pipeline started", "audio": audio_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))