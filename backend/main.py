from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil

from backend.DataBase.DB import Base, engine, SessionLocal
from backend.DataBase import Models, repository
from backend.IA import transcribe, summarize, make_pdf

# Crée la base au démarrage
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MeetRecap API")

UPLOAD_DIR = Path("backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Dépendance DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload/")
def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = UPLOAD_DIR / file.filename
    base, ext = file.filename.rsplit(".", 1)
    counter = 1
    while file_path.exists():
        new_name = f"{base}_{counter}.{ext}"
        file_path = UPLOAD_DIR / new_name
        counter += 1

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    audio = repository.create_audio(db, filename=file_path.name)
    return {"id": audio.id, "filename": file_path.name, "status": "uploaded"}

@app.post("/process/{audio_id}")
def process_audio(audio_id: int, db: Session = Depends(get_db)):
    audio = repository.get_audio(db, audio_id)
    if not audio:
        return {"error": "Audio not found"}

    file_path = UPLOAD_DIR / audio.filename

    transcription = transcribe.transcribe_file(file_path)
    summary = summarize.summarize_text(transcription)
    pdf_path = UPLOAD_DIR / f"{audio.filename}.pdf"
    make_pdf.make_pdf(pdf_path, "Résumé de la réunion", summary, transcription)

    repository.update_audio(
        db, audio_id,
        transcription=transcription,
        summary=summary,
        pdf_path=str(pdf_path),
        status="done"
    )
    return {"message": "Traitement terminé", "pdf_path": str(pdf_path)}

@app.get("/download/{audio_id}")
def download_pdf(audio_id: int, db: Session = Depends(get_db)):
    audio = repository.get_audio(db, audio_id)
    if not audio or not audio.pdf_path:
        return {"error": "PDF non trouvé"}
    return FileResponse(audio.pdf_path, filename=Path(audio.pdf_path).name)
