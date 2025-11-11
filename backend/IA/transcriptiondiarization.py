# backend/IA/transcriptiondiarization.py
import os
import subprocess
from dotenv import load_dotenv
from groq import Groq
from pyannote.audio import Pipeline

# 1️⃣ Charger les variables d'environnement
load_dotenv()
print("✅ Clés API chargées correctement.")

# 2️⃣ Vérifier les clés API
groq_api_key = os.getenv("GROQ_API_KEY")
hf_token = os.getenv("HUGGINGFACE_TOKEN")

if not groq_api_key or not hf_token:
    raise ValueError("❌ Clés API manquantes (Groq ou Hugging Face)")

# 3️⃣ Répertoire audio
base_dir = os.path.dirname(__file__)
audio_dir = os.path.join(base_dir, "audio")
os.makedirs(audio_dir, exist_ok=True)

# 4️⃣ Conversion en WAV
def convert_to_wav(audio_path: str) -> str:
    """Convertit un fichier audio en WAV mono 16kHz."""
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
    return wav_path

# 5️⃣ Chargement du pipeline Pyannote (une seule fois)
print("⏳ Chargement du pipeline de diarisation (pyannote)...")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
print("✅ Pipeline chargé avec succès !")

# 6️⃣ Formatage du temps
def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"

# 7️⃣ Fusion diarisation + transcription
def match_speaker_to_text(diar_segments, text_segments):
    result = []
    for txt in text_segments:
        start = txt["start"]
        end = txt["end"]
        text = txt["text"].strip()

        speaker = "UNKNOWN"
        for d in diar_segments:
            if d["start"] <= start <= d["end"]:
                speaker = d["speaker"]
                break

        result.append(f"[{format_time(start)} - {format_time(end)}] [{speaker}] {text}")
    return result

# 8️⃣ Fonction principale : exécution sur un fichier uploadé
def transcription_with_diarization(audio_file: str):
    """
    Exécute la transcription + diarisation sur un fichier audio uploadé.
    - audio_file : chemin complet du fichier audio (mp3, wav, etc.)
    """
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"❌ Fichier introuvable : {audio_file}")

    # Conversion en WAV
    wav_path = convert_to_wav(audio_file)

    # Étape 1 : Diarisation
    print("🎧 Détection des intervenants...")
    diarization = pipeline(wav_path)
    diar_segments = [{"start": t.start, "end": t.end, "speaker": s}
                     for t, _, s in diarization.itertracks(yield_label=True)]
    print(f"👥 Intervenants détectés : {set(d['speaker'] for d in diar_segments)}")

    # Étape 2 : Transcription (Groq)
    print("🎙️ Lancement de la transcription complète (Groq)...")
    client = Groq(api_key=groq_api_key)
    with open(wav_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="fr"
        )

    # Étape 3 : Fusion
    fusion = match_speaker_to_text(diar_segments, transcription.segments)

    # Étape 4 : Sauvegarde du résultat
    output_path = os.path.join(audio_dir, "transcription_avec_diarisation.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fusion))
    print(f"✅ Transcription enregistrée : {output_path}")

    return "\n".join(fusion)
