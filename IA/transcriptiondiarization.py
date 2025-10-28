# ============================================================
# 📁 backend/IA/transcriptiondiarization.py
# ============================================================

import os
import subprocess
from dotenv import load_dotenv
from groq import Groq
from pyannote.audio import Pipeline

# ============================================================
# 1️⃣ Charger les variables d'environnement (.env)
# ============================================================
load_dotenv()
print("✅ Clés API chargées correctement.")

# ============================================================
# 2️⃣ Vérifier la présence des clés API
# ============================================================
groq_api_key = os.getenv("GROQ_API_KEY")
hf_token = os.getenv("HUGGINGFACE_TOKEN")

if not groq_api_key or not hf_token:
    raise ValueError("❌ Clés API manquantes (Groq ou Hugging Face)")

# ============================================================
# 3️⃣ Définir les chemins de base (dossier courant, audio, etc.)
# ============================================================
base_dir = os.path.dirname(__file__)
audio_dir = os.path.join(base_dir, "audio")

# On crée le dossier 'audio' s’il n’existe pas encore
os.makedirs(audio_dir, exist_ok=True)

# Fichier audio par défaut (à titre d’exemple, mais pas utilisé automatiquement)
audio_path = os.path.join(audio_dir, "meet1.mp3")
wav_path = None  # ⚠️ on ne convertit plus automatiquement au chargement du module

# ============================================================
# 4️⃣ Fonction : conversion MP3 → WAV (avec vérifications)
# ============================================================
def convert_to_wav(audio_path):
    """
    Convertit un fichier audio en WAV (16kHz mono).
    Lève une erreur si le fichier source n'existe pas.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"❌ Fichier audio introuvable : {audio_path}")

    base, ext = os.path.splitext(audio_path)
    wav_path = base + ".wav"

    if not os.path.exists(wav_path):
        print(f"🎧 Conversion du fichier {audio_path} en {wav_path} ...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", audio_path,
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ], check=True)
        print(f"✅ Fichier WAV prêt : {wav_path}")
    else:
        print(f"ℹ️ Le fichier WAV existe déjà : {wav_path}")

    return wav_path

# ============================================================
# 5️⃣ Initialisation du pipeline Pyannote
# ============================================================
print("⏳ Chargement du pipeline de diarisation (pyannote)...")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
print("✅ Pipeline chargé avec succès !")

# ============================================================
# 6️⃣ Fonction utilitaire pour formater le temps (mm:ss.s)
# ============================================================
def format_time(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"

# ============================================================
# 7️⃣ Fusion diarisation + transcription
# ============================================================
def match_speaker_to_text(diar_segments, text_segments):
    """
    Associe les segments de texte aux locuteurs détectés.
    """
    result = []
    for txt in text_segments:
        start = txt["start"]
        end = txt["end"]
        text = txt["text"].strip()

        # Trouver le locuteur le plus probable
        speaker = "UNKNOWN"
        for d in diar_segments:
            if d["start"] <= start <= d["end"]:
                speaker = d["speaker"]
                break

        start_f = format_time(start)
        end_f = format_time(end)
        result.append(f"[{start_f} - {end_f}] [{speaker}] {text}")
    return result

# ============================================================
# 8️⃣ Fonction principale : transcription avec diarisation
# ============================================================
def transcription_with_diarization(audio_file=None):
    """
    Retourne le texte complet avec diarisation et timestamps.
    Si audio_file est fourni, on l'utilise à la place du fichier par défaut.
    """
    global audio_path, wav_path

    # 🧩 Utiliser le fichier reçu ou celui par défaut
    if audio_file:
        audio_path = audio_file
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"❌ Aucun fichier audio trouvé à : {audio_path}")

    # 🎧 Conversion en WAV
    wav_path = convert_to_wav(audio_path)

    # 👥 Diarisation
    print("🎧 Détection des intervenants...")
    diarization = pipeline(wav_path)
    segments = [
        {"start": t.start, "end": t.end, "speaker": s}
        for t, _, s in diarization.itertracks(yield_label=True)
    ]
    print(f"👥 Intervenants détectés : {set(seg['speaker'] for seg in segments)}")

    # 🎙️ Transcription via Groq
    print("\n🎙️ Lancement de la transcription complète (Groq)...")
    client = Groq(api_key=groq_api_key)
    with open(wav_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="fr"
        )

    # 🧠 Fusion des résultats
    fusion = match_speaker_to_text(segments, transcription.segments)

    # 💾 Sauvegarde du texte final
    output_path = os.path.join(base_dir, "transcription_avec_diarisation.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fusion))

    print(f"\n✅ Transcription avec timestamps enregistrée ici : {output_path}\n")

    return "\n".join(fusion)
