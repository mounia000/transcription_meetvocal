from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import shutil
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import traceback  # pour afficher les erreurs dans la console

# =====================================================
# INITIALISATION FASTAPI
# =====================================================
app = FastAPI(
    title="API Compte-Rendu de Réunion",
    description="Upload un audio de réunion → Reçois un compte-rendu complet",
    version="1.0.0"
)

# Servir les fichiers PDF générés
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# =====================================================
# IMPORT DU PIPELINE IA
# =====================================================
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from IA.pipeline_service import TranscriptionPipeline

# =====================================================
# CHARGEMENT DES VARIABLES D’ENVIRONNEMENT
# =====================================================
load_dotenv()

# =====================================================
# CONFIGURATION DE BASE
# =====================================================
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre plus tard
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# =====================================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "meetrecap_db")

    if not db_password:
        raise ValueError("DB_PASSWORD ou DATABASE_URL manquant dans .env")

    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print("Connexion DB configurée")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY manquant dans .env")

print("Secret JWT configuré")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =====================================================
# CONNEXION À LA BASE
# =====================================================
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

# =====================================================
# SCHÉMAS PYDANTIC
# =====================================================
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# =====================================================
# FONCTIONS UTILITAIRES
# =====================================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_token(email: str) -> str:
    payload = {"sub": email, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials, conn):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")

        cur = conn.cursor()
        cur.execute("SELECT * FROM utilisateurs WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            raise HTTPException(401, "Utilisateur non trouvé")
        return user
    except Exception as e:
        raise HTTPException(401, f"Token invalide : {str(e)}")

def extract_segments_from_raw(raw_text: str):
    """Extraire les segments avec timestamps et locuteurs"""
    pattern = r"\[(\d{2}:\d{2}\.\d)\s*-\s*(\d{2}:\d{2}\.\d)\]\s*\[([^\]]+)\]\s*(.*)"
    segments = []
    for line in raw_text.splitlines():
        match = re.match(pattern, line)
        if match:
            start, end, speaker, text = match.groups()
            def to_sec(t): 
                m, s = t.split(":")
                return int(m)*60 + float(s)
            segments.append({
                "start_time": to_sec(start),
                "end_time": to_sec(end),
                "speaker": speaker,
                "text": text.strip()
            })
    return segments

# =====================================================
# ROUTES
# =====================================================
@app.get("/")
def home():
    return {
        "message": "API MeetRecap fonctionne !",
        "routes": {
            "register": "/register",
            "login": "/login",
            "upload": "/upload",
            "fichiers": "/fichiers",
        },
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        db = "Connected"
    except:
        db = "Failed"
    return {"status": "OK", "database": db, "secret": bool(SECRET_KEY)}

# =====================================================
# REGISTER + LOGIN
# =====================================================
@app.post("/register")
def register(user: UserRegister, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM utilisateurs WHERE email = %s", (user.email,))
    if cur.fetchone():
        cur.close()
        raise HTTPException(400, "Email déjà utilisé")

    hashed_pw = hash_password(user.password)
    cur.execute(
        "INSERT INTO utilisateurs (name, email, password) VALUES (%s, %s, %s) RETURNING id_user",
        (user.name, user.email, hashed_pw)
    )
    new_user = cur.fetchone()
    conn.commit()
    cur.close()

    token = create_token(user.email)
    return {
        "id_user": new_user["id_user"],
        "name": user.name,
        "email": user.email,
        "access_token": token,
        "message": "Compte créé avec succès"
    }

@app.post("/login")
def login(credentials: UserLogin, conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT * FROM utilisateurs WHERE email = %s", (credentials.email,))
    user = cur.fetchone()
    cur.close()

    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(401, "Email ou mot de passe incorrect")

    token = create_token(credentials.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": user["id_user"],
            "name": user["name"],
            "email": user["email"]
        }
    }

# =====================================================
# UPLOAD AUDIO + TRAITEMENT IA
# =====================================================
@app.post("/upload")
def upload_audio(
    file: UploadFile = File(...),
    title: str = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn=Depends(get_db)
):
    user = get_current_user(credentials, conn)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".flac"]:
        raise HTTPException(400, "Format non supporté (.mp3, .wav, .m4a, .flac)")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("uploads", f"{timestamp}_{file.filename}")

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO fichiers_audio (id_user, title, status, file_path, date_upload)
           VALUES (%s, %s, 'processing', %s, NOW())
           RETURNING id_audio""",
        (user["id_user"], title or file.filename, filepath)
    )
    audio_id = cur.fetchone()["id_audio"]
    conn.commit()

    print(f"Traitement du fichier {audio_id} lancé...")

    output_dir = os.path.join("outputs", f"audio_{audio_id}")
    os.makedirs(output_dir, exist_ok=True)

    try:
        pipeline = TranscriptionPipeline(audio_file=filepath, output_dir=output_dir)
        results = pipeline.run(save_intermediary_files=False)
        segments = extract_segments_from_raw(results["raw_transcription"])

        for seq, s in enumerate(segments):
            cur.execute(
                """INSERT INTO transcriptions (id_audio, text_brut, start_time, end_time, speaker, sequence_number)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (audio_id, s["text"], s["start_time"], s["end_time"], s["speaker"], seq)
            )

        cur.execute(
            """INSERT INTO resumes (id_audio, summary_text, type_resume)
               VALUES (%s, %s, 'general')""",
            (audio_id, results["summary"])
        )
        conn.commit()

        cur.execute("""UPDATE fichiers_audio SET status='completed' WHERE id_audio=%s""", (audio_id,))
        conn.commit()
        cur.close()

        print("Traitement IA terminé avec succès.")
        return {"message": "Traitement terminé", "id_audio": audio_id}

    except Exception as e:
        print("ERREUR IA :", e)
        traceback.print_exc()
        cur.execute("""UPDATE fichiers_audio SET status='failed' WHERE id_audio=%s""", (audio_id,))
        conn.commit()
        cur.close()
        raise HTTPException(500, f"Erreur IA : {str(e)}")

# =====================================================
# LISTE DES FICHIERS
# =====================================================
@app.get("/fichiers")
def list_files(credentials: HTTPAuthorizationCredentials = Depends(security), conn=Depends(get_db)):
    user = get_current_user(credentials, conn)
    cur = conn.cursor()
    cur.execute(
        """SELECT id_audio, title, status, date_upload
           FROM fichiers_audio
           WHERE id_user = %s
           ORDER BY date_upload DESC""",
        (user["id_user"],)
    )
    files = cur.fetchall()
    cur.close()
    return files

# =====================================================
# SUPPRESSION D’UN FICHIER
# =====================================================
@app.delete("/fichiers/{id_audio}")
def delete_file(id_audio: int, credentials: HTTPAuthorizationCredentials = Depends(security), conn=Depends(get_db)):
    user = get_current_user(credentials, conn)
    cur = conn.cursor()

    cur.execute("SELECT file_path FROM fichiers_audio WHERE id_audio = %s AND id_user = %s", (id_audio, user["id_user"]))
    fichier = cur.fetchone()

    if not fichier:
        cur.close()
        raise HTTPException(404, "Fichier introuvable ou non autorisé")

    # Supprimer le fichier physique
    try:
        if os.path.exists(fichier["file_path"]):
            os.remove(fichier["file_path"])
    except Exception as e:
        print(f"Impossible de supprimer le fichier local : {e}")

    # Supprimer les données liées
    cur.execute("DELETE FROM transcriptions WHERE id_audio = %s", (id_audio,))
    cur.execute("DELETE FROM resumes WHERE id_audio = %s", (id_audio,))
    cur.execute("DELETE FROM fichiers_audio WHERE id_audio = %s", (id_audio,))
    conn.commit()
    cur.close()

    print(f"Fichier {id_audio} supprimé avec succès")
    return {"message": "Fichier supprimé avec succès"}

# =====================================================
# LANCEMENT DU SERVEUR
# =====================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
