# backend/api.py

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from backend.DataBase import models, schemas, crud
from backend.DataBase.database import engine, SessionLocal
import bcrypt
import os, shutil, time
from backend.pipeline_service import run_pipeline_service


# =====================================================================
# INITIALISATION
# =====================================================================
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="MeetRecap - API de Transcription")


# =====================================================================
# CORS
# =====================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# PASSWORD - Utilisation directe de bcrypt
# =====================================================================
def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    try:
        plain_bytes = plain.encode('utf-8')
        # Tronquer à 72 octets si nécessaire
        if len(plain_bytes) > 72:
            plain_bytes = plain_bytes[:72]
        return bcrypt.checkpw(plain_bytes, hashed.encode('utf-8'))
    except:
        return False

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    password_bytes = password.encode('utf-8')
    # Tronquer à 72 octets pour bcrypt
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


# =====================================================================
# DATABASE
# =====================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# CHEMINS DES DOSSIERS
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "IA", "audio", "uploads")

EXPORT_DIR = os.path.join(BASE_DIR, "IA", "exports")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

app.mount("/exports", StaticFiles(directory=EXPORT_DIR), name="exports")

# =====================================================================
# AUTH
# =====================================================================
@app.post("/register")
def register(name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email):
        raise HTTPException(400, "Cet email est déjà utilisé.")

    user = crud.create_user(
        db,
        schemas.UserCreate(
            name=name,
            email=email,
            password=hash_password(password)
        )
    )

    return {"message": "OK", "user_id": user.id_user}


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)

    if not user:
        raise HTTPException(401, "Utilisateur introuvable")

    if not verify_password(password, user.password):
        raise HTTPException(401, "Mot de passe incorrect")

    return {
        "message": "Connexion réussie",
        "user": {"id": user.id_user, "name": user.name, "email": user.email}
    }


# =====================================================================
# UPLOAD AUDIO + PIPELINE
# =====================================================================
@app.post("/upload")
async def upload_audio(
    id_user: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    allowed = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed:
        raise HTTPException(400, "Format de fichier non supporté")

    timestamp = int(time.time())
    safe_name = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Sauvegarde audio
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ENREGISTRER AVANT TRAITEMENT
    new_audio = crud.create_audio_file(
        db,
        schemas.AudioFileCreate(
            id_user=id_user,
            title=file.filename,
            file_path=file_path,
            status="processing"
        )
    )

    print(f"🚀 Pipeline lancé pour : {file.filename}")

    try:
        result = run_pipeline_service(file_path)

        # Sauvegarder le résumé court
        if "resume_court" in result and result["resume_court"]:
            crud.create_resume(
                db, 
                new_audio.id_audio, 
                result["resume_court"], 
                "resume_court"
            )

        # Sauvegarder le compte rendu complet
        if "compte_rendu" in result and result["compte_rendu"]:
            crud.create_resume(
                db,
                new_audio.id_audio,
                result["compte_rendu"],
                "compte_rendu_complet"
            )

        # Sauvegarder les résumés par speaker
        if "speakers" in result:
            for speaker, summary in result["speakers"].items():
                crud.create_resume(
                    db,
                    new_audio.id_audio,
                    summary,
                    "par_speaker",
                    speaker
                )

        crud.update_audio_status(db, new_audio.id_audio, "completed")

    except Exception as e:
        print("❌ ERREUR PIPELINE :", e)
        crud.update_audio_status(db, new_audio.id_audio, "failed")
        raise HTTPException(500, f"Erreur pipeline : {e}")

    pdf_url = "http://127.0.0.1:8000/exports/compte_rendu_reunion.pdf"
    doc_url = "http://127.0.0.1:8000/exports/compte_rendu_reunion.docx"

    return {
        "message": "Traitement OK",
        "resume_court": result["resume_court"],
        "compte_rendu": result["compte_rendu"],
        "pdf_url": pdf_url,
        "word_url": doc_url,
        "audio": file.filename,
        "id_audio": new_audio.id_audio
    }



# =====================================================================
# LISTE FICHIERS (FILTRÉS PAR UTILISATEUR)
# =====================================================================
@app.get("/fichiers")
def fichiers(id_user: int, db: Session = Depends(get_db)):
    return db.query(models.FichierAudio).filter(
        models.FichierAudio.id_user == id_user
    ).order_by(models.FichierAudio.date_upload.desc()).all()


# =====================================================================
# DETAIL FICHIER
# =====================================================================
@app.get("/fichiers/{id}/detail")
def fichier_detail(id: int, db: Session = Depends(get_db)):
    f = crud.get_audio_file_by_id(db, id)

    if not f:
        raise HTTPException(404, "Fichier introuvable")

    # Récupérer les résumés
    resumes = []
    for r in f.resumes:
        resumes.append({
            "type": r.type_resume,
            "speaker": r.speaker,
            "text": r.summary_text
        })

    # Récupérer les transcriptions
    transcriptions = []
    for t in f.transcriptions:
        transcriptions.append({
            "speaker": t.speaker,
            "text": t.text_brut,
            "start_time": t.start_time,
            "end_time": t.end_time
        })

    return {
        "id_audio": f.id_audio,
        "title": f.title,
        "file_path": f.file_path,
        "status": f.status,
        "date_upload": f.date_upload,
        "duree": f.duration,
        "user": {
            "name": f.user.name,
            "email": f.user.email
        },
        "pdf_url": "http://localhost:8000/exports/compte_rendu_reunion.pdf",
        "word_url": "http://localhost:8000/exports/compte_rendu_reunion.docx",
        "resumes": resumes,
        "transcriptions": transcriptions
    }


# =====================================================================
# SUPPRESSION
# =====================================================================
@app.delete("/fichiers/{id_audio}")
def delete_fichier(id_audio: int, db: Session = Depends(get_db)):
    deleted = crud.delete_audio_file(db, id_audio)
    if not deleted:
        raise HTTPException(404, "Fichier introuvable")
    return {"message": "Fichier supprimé"}


# =====================================================================
# TÉLÉCHARGEMENT FORCÉ DES FICHIERS
# =====================================================================
@app.get("/download/pdf/{id_audio}")
def download_pdf(id_audio: int, db: Session = Depends(get_db)):
    # Vérifier que le fichier audio existe
    audio = crud.get_audio_file_by_id(db, id_audio)
    if not audio:
        raise HTTPException(404, "Fichier audio introuvable")
    
    # Chercher le fichier PDF (nom basé sur l'ID ou nom générique)
    pdf_path = os.path.join(EXPORT_DIR, f"compte_rendu_{id_audio}.pdf")
    
    # Si le fichier spécifique n'existe pas, utiliser le fichier générique
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(EXPORT_DIR, "compte_rendu_reunion.pdf")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF non trouvé. Le document n'a peut-être pas encore été généré.")
    
    filename = f"compte_rendu_{audio.title.replace(' ', '_')}.pdf" if audio.title else "compte_rendu_reunion.pdf"
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/download/word/{id_audio}")
def download_word(id_audio: int, db: Session = Depends(get_db)):
    # Vérifier que le fichier audio existe
    audio = crud.get_audio_file_by_id(db, id_audio)
    if not audio:
        raise HTTPException(404, "Fichier audio introuvable")
    
    # Chercher le fichier DOCX (nom basé sur l'ID ou nom générique)
    word_path = os.path.join(EXPORT_DIR, f"compte_rendu_{id_audio}.docx")
    
    # Si le fichier spécifique n'existe pas, utiliser le fichier générique
    if not os.path.exists(word_path):
        word_path = os.path.join(EXPORT_DIR, "compte_rendu_reunion.docx")
    
    if not os.path.exists(word_path):
        raise HTTPException(404, "DOCX non trouvé. Le document n'a peut-être pas encore été généré.")
    
    filename = f"compte_rendu_{audio.title.replace(' ', '_')}.docx" if audio.title else "compte_rendu_reunion.docx"
    
    return FileResponse(
        word_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
