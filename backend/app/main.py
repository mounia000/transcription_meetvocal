# backend/app/main_simple.py
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

# Import du pipeline IA
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from IA.pipeline_service import TranscriptionPipeline

# ============ CHARGEMENT VARIABLES D'ENVIRONNEMENT ============
load_dotenv()

# ============ CONFIGURATION ============

# Schéma de sécurité pour Swagger
security = HTTPBearer()

app = FastAPI(
    title="API Compte-Rendu de Réunion",
    description="Upload un audio de réunion → Reçois un compte-rendu complet",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration DB depuis .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "transcription_db")
    
    if not db_password:
        raise ValueError("❌ DB_PASSWORD ou DATABASE_URL manquant dans .env")
    
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"✅ Connexion DB configurée")

# JWT depuis .env
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY manquant dans .env")

print(f"✅ Secret JWT configuré")

# Dossiers
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============ CONNEXION DB ============

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

# ============ SCHEMAS PYDANTIC ============

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ============ HELPERS ============

def hash_password(password: str) -> str:
    """Hasher un mot de passe avec bcrypt"""
    # Encoder en bytes et hasher
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Vérifier un mot de passe"""
    password_bytes = plain.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_token(email: str) -> str:
    """Créer un token JWT"""
    data = {"sub": email, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials, conn):
    """Récupérer l'utilisateur depuis le token JWT"""
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
        raise HTTPException(401, f"Token invalide: {str(e)}")

def extract_segments_from_raw(raw_transcription: str):
    """Extraire les segments avec timestamps depuis la transcription brute"""
    lines = raw_transcription.split('\n')
    segments = []
    
    for line in lines:
        # Pattern: [MM:SS.S - MM:SS.S] [SPEAKER] texte
        pattern = r'\[(\d{2}:\d{2}\.\d)\s*-\s*(\d{2}:\d{2}\.\d)\]\s*\[([^\]]+)\]\s*(.*)'
        match = re.match(pattern, line)
        
        if match:
            start_str, end_str, speaker, text = match.groups()
            
            # Convertir MM:SS.S en secondes
            def time_to_seconds(time_str):
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            
            segments.append({
                'start_time': time_to_seconds(start_str),
                'end_time': time_to_seconds(end_str),
                'speaker': speaker,
                'text': text.strip()
            })
    
    return segments

# ============ ENDPOINTS ============

@app.get("/")
def home():
    """Page d'accueil de l'API"""
    return {
        "message": "🎤 API Compte-Rendu de Réunion",
        "description": "Upload un audio → Reçois transcription + résumé",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /login",
            "upload": "POST /upload (Auth required)",
            "fichiers": "GET /fichiers (Auth required)",
            "compte_rendu": "GET /fichiers/{id}/compte-rendu (Auth required)"
        },
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Vérifier que l'API fonctionne"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        db_status = "✅ Connected"
    except:
        db_status = "❌ Connection failed"
    
    return {
        "status": "ok",
        "database": db_status,
        "env_loaded": "✅" if SECRET_KEY else "❌"
    }

@app.post("/register")
def register(user: UserRegister, conn=Depends(get_db)):
    """Créer un compte utilisateur"""
    cur = conn.cursor()
    
    # Vérifier si email existe
    cur.execute("SELECT * FROM utilisateurs WHERE email = %s", (user.email,))
    if cur.fetchone():
        cur.close()
        raise HTTPException(400, "Email déjà utilisé")
    
    # Créer utilisateur
    hashed = hash_password(user.password)
    cur.execute(
        "INSERT INTO utilisateurs (name, email, password) VALUES (%s, %s, %s) RETURNING id_user",
        (user.name, user.email, hashed)
    )
    user_id = cur.fetchone()['id_user']
    conn.commit()
    cur.close()
    
    return {
        "id_user": user_id,
        "name": user.name,
        "email": user.email,
        "message": "✅ Compte créé avec succès"
    }

@app.post("/login")
def login(credentials: UserLogin, conn=Depends(get_db)):
    """Se connecter et obtenir un token JWT"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM utilisateurs WHERE email = %s", (credentials.email,))
    user = cur.fetchone()
    cur.close()
    
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(401, "Email ou mot de passe incorrect")
    
    token = create_token(credentials.email)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id_user": user['id_user'],
            "name": user['name'],
            "email": user['email']
        }
    }

@app.post("/upload")
def upload(
    file: UploadFile = File(...),
    title: str = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn = Depends(get_db)
):
    """
    Upload un fichier audio de réunion et génère le compte-rendu complet.
    
    ⏳ Traitement : 5-15 minutes selon la taille du fichier
    
    Retourne :
    - Transcription complète avec timestamps
    - Résumé général de la réunion
    - Résumés par participant (speakers)
    """
    
    # Vérifier utilisateur avec le token
    user = get_current_user(credentials, conn)
    
    # Vérifier extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]:
        raise HTTPException(400, f"Format non supporté. Utilisez: .mp3, .wav, .m4a, .ogg, .flac")
    
    # Sauvegarder fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    audio_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    cur = conn.cursor()
    
    try:
        # 1️⃣ Créer l'entrée Fichier_Audio
        cur.execute(
        """INSERT INTO fichiers_audio 
            (id_user, title, status, file_path) 
            VALUES (%s, %s, 'processing', %s) 
            RETURNING id_audio""",
        (user['id_user'], title or file.filename, audio_path)
        )
        audio_id = cur.fetchone()['id_audio']
        conn.commit()
    
        print(f"🚀 Démarrage du pipeline pour fichier {audio_id}...")
        print(f"📁 Fichier : {file.filename}")

        # Dossier de sortie unique par audio_id
        output_dir = os.path.join("outputs", f"audio_{audio_id}")

        # Supprimer l'ancien dossier s'il existe
        if os.path.exists(output_dir):
            print(f"🗑️ Suppression de l'ancien dossier {output_dir}...")
            shutil.rmtree(output_dir)

        # Créer un nouveau dossier propre
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 Dossier de sortie créé : {output_dir}")

        # 2️⃣ Exécuter le pipeline IA avec output_dir spécifique
        pipeline = TranscriptionPipeline(
            audio_file=audio_path,
            output_dir=output_dir
            )
        results = pipeline.run(save_intermediary_files=False)
    
        # DEBUG: Voir le format exact
        print("="*60)
        print("📄 FORMAT DE LA TRANSCRIPTION BRUTE (5 premières lignes):")
        print("="*60)
        for i, line in enumerate(results["raw_transcription"].split('\n')[:5]):
            print(f"Ligne {i}: {repr(line)}")
            print("="*60)
    
        print(f"✅ Pipeline terminé pour {audio_id}")
    
        # 3️⃣ Extraire et sauvegarder les segments
        print(f"📝 Extraction des segments...")
        segments = extract_segments_from_raw(results["raw_transcription"])
        print(f"📊 Nombre de segments extraits : {len(segments)}")

        if len(segments) == 0:
            print("⚠️ ATTENTION : Aucun segment extrait !")
            print(f"📄 Transcription brute (100 premiers caractères) : {results['raw_transcription'][:100]}")
    
        for seq, segment in enumerate(segments):
            print(f"💾 Insertion segment {seq}: {segment['speaker']} - {segment['text'][:30]}...")
            cur.execute(
            """INSERT INTO transcriptions 
                (id_audio, text_brut, start_time, end_time, speaker, sequence_number) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
            (audio_id, segment['text'], segment['start_time'], 
            segment['end_time'], segment['speaker'], seq)
            )
    
        print(f"✅ {len(segments)} segments insérés")
    
        # 4️⃣ Sauvegarder le résumé GÉNÉRAL
        print(f"💾 Insertion résumé général...")
        cur.execute(
        """INSERT INTO resumes (id_audio, summary_text, type_resume) 
            VALUES (%s, %s, 'general')""",
        (audio_id, results["summary"])
        )
        print(f"✅ Résumé général inséré")
    
        # 5️⃣ Sauvegarder les résumés PAR SPEAKER
        print(f"💾 Insertion résumés par speaker...")
        print(f"📊 speaker_summaries : {results.get('speaker_summaries')}")

        if results.get("speaker_summaries"):
            for speaker, summary in results["speaker_summaries"].items():
                print(f"💾 Insertion résumé pour {speaker}...")
                cur.execute(
                """INSERT INTO resumes (id_audio, summary_text, type_resume, speaker) 
                    VALUES (%s, %s, 'par_speaker', %s)""",
                (audio_id, summary, speaker)
                )   
            print(f"✅ {len(results['speaker_summaries'])} résumés par speaker insérés")
        else:
            print("⚠️ Aucun résumé par speaker trouvé")

        
        # 6️⃣ Calculer durée et nombre de speakers
        duration = segments[-1]['end_time'] if segments else 0
        speakers_set = set(seg['speaker'] for seg in segments)
        num_speakers = len(speakers_set)
        
        # 7️⃣ Mettre à jour le fichier audio
        cur.execute(
            """UPDATE fichiers_audio 
            SET status = 'completed', 
                duration = %s,
                num_speakers = %s
            WHERE id_audio = %s""",
            (duration, num_speakers, audio_id)
        )
        
        conn.commit()
        
        print(f"✅ Traitement terminé : {audio_id}")
        print(f"📊 Durée : {duration:.1f}s | Speakers : {num_speakers} | Segments : {len(segments)}")
        
        # 8️⃣ Récupérer et formater le compte-rendu complet
        cur.execute(
            """SELECT summary_text, type_resume, speaker 
            FROM resumes 
            WHERE id_audio = %s""",
            (audio_id,)
        )
        resumes = cur.fetchall()
        
        resume_general = next((r['summary_text'] for r in resumes if r['type_resume'] == 'general'), "")
        resumes_speakers = {r['speaker']: r['summary_text'] for r in resumes if r['type_resume'] == 'par_speaker'}
        
        cur.close()
        
        # 9️⃣ Retourner le compte-rendu
        return {
            "message": "✅ Compte-rendu généré avec succès !",
            "id_audio": audio_id,
            "title": title or file.filename,
            "duree_minutes": round(duration / 60, 2),
            "nombre_participants": num_speakers,
            "participants": list(speakers_set),
            
            "resume_general": resume_general,
            "resumes_par_participant": resumes_speakers,
            
            "transcription_complete": {
                "nombre_segments": len(segments),
                "segments": [
                    {
                        "temps": f"{int(s['start_time']//60):02d}:{int(s['start_time']%60):02d} - {int(s['end_time']//60):02d}:{int(s['end_time']%60):02d}",
                        "participant": s['speaker'],
                        "texte": s['text']
                    }
                    for s in segments[:10]  # Premiers 10 segments
                ] + ([{"message": f"... et {len(segments)-10} segments supplémentaires"}] if len(segments) > 10 else [])
            }
        }
        
    except Exception as e:
        if 'audio_id' in locals():
            cur.execute(
                "UPDATE fichiers_audio SET status = 'failed' WHERE id_audio = %s",
                (audio_id,)
            )
            conn.commit()
        cur.close()
        raise HTTPException(500, f"❌ Erreur: {str(e)}")

@app.get("/fichiers/{audio_id}/pdf")
def download_pdf(
    audio_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn = Depends(get_db)
):
    """Télécharger le PDF d'une transcription"""
    user = get_current_user(credentials, conn)
    
    cur = conn.cursor()
    
    # Vérifier que le fichier appartient à l'utilisateur
    cur.execute(
        """SELECT * FROM fichiers_audio 
        WHERE id_audio = %s AND id_user = %s""",
        (audio_id, user['id_user'])
    )
    fichier = cur.fetchone()
    cur.close()
    
    if not fichier:
        raise HTTPException(404, "Fichier non trouvé")
    
    # Chemin du PDF
    pdf_path = os.path.join("outputs", f"audio_{audio_id}", "transcription_finale.pdf")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF non disponible. Le traitement est peut-être en cours.")
    
    # Retourner le fichier
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{fichier['title']}.pdf"
    )

@app.get("/fichiers")
def list_fichiers(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn = Depends(get_db)
):
    """Liste tous les fichiers audio de l'utilisateur"""
    user = get_current_user(credentials, conn)
    
    cur = conn.cursor()
    cur.execute(
        """SELECT id_audio, title, status, date_upload, duration, num_speakers
        FROM fichiers_audio
        WHERE id_user = %s 
        ORDER BY date_upload DESC""",
        (user['id_user'],)
    )
    fichiers = cur.fetchall()
    cur.close()
    
    return [dict(f) for f in fichiers]

@app.get("/fichiers/{audio_id}/compte-rendu")
def get_compte_rendu(
    audio_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn = Depends(get_db)
):
    """
    Récupérer le compte-rendu complet d'une réunion.
    
    Retourne :
    - Résumé général
    - Résumés par participant
    - Transcription complète avec timestamps
    """
    user = get_current_user(credentials, conn)
    
    cur = conn.cursor()
    
    # Vérifier que le fichier appartient à l'utilisateur
    cur.execute(
        """SELECT * FROM fichiers_audio 
        WHERE id_audio = %s AND id_user = %s""",
        (audio_id, user['id_user'])
    )
    fichier = cur.fetchone()
    
    if not fichier:
        cur.close()
        raise HTTPException(404, "Fichier non trouvé")
    
    # Récupérer les résumés
    cur.execute(
        """SELECT summary_text, type_resume, speaker 
        FROM resumes 
        WHERE id_audio = %s""",
        (audio_id,)
    )
    resumes = cur.fetchall()
    
    # Récupérer la transcription
    cur.execute(
        """SELECT text_brut, start_time, end_time, speaker, sequence_number
        FROM transcriptions 
        WHERE id_audio = %s 
        ORDER BY sequence_number""",
        (audio_id,)
    )
    segments = cur.fetchall()
    
    cur.close()
    
    # Formater
    resume_general = next((r['summary_text'] for r in resumes if r['type_resume'] == 'general'), "")
    resumes_speakers = {r['speaker']: r['summary_text'] for r in resumes if r['type_resume'] == 'par_speaker'}
    
    return {
        "titre": fichier['title'],
        "date": str(fichier['date_upload']),
        "duree_minutes": round(fichier['duration'] / 60, 2) if fichier['duration'] else None,
        "nombre_participants": fichier['num_speakers'],
        
        "resume_general": resume_general,
        "resumes_par_participant": resumes_speakers,
        
        "transcription_complete": [
            {
                "temps": f"{int(s['start_time']//60):02d}:{int(s['start_time']%60):02d}",
                "participant": s['speaker'],
                "texte": s['text_brut']
            }
            for s in segments
        ]
    }