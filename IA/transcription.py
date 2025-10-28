# backend/IA/transcription.py
import os
import subprocess
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

# ---------------------------
# Conversion audio en WAV
# ---------------------------
def convert_to_wav(audio_path):
    base, ext = os.path.splitext(audio_path)
    wav_path = base + ".wav"
    if not os.path.exists(wav_path):
        print(f"🎧 Conversion automatique du fichier {audio_path} en {wav_path} ...")
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ], check=True)
    return wav_path

# ---------------------------
# Transcription audio (Groq)
# ---------------------------
def speach_to_text(audio_path, language="fr"):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Fichier audio introuvable : {audio_path}")

    if not audio_path.lower().endswith(".wav"):
        audio_path = convert_to_wav(audio_path)

    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            prompt="Transcris l'audio le plus fidèlement possible.",
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            language=language,
            temperature=0.0
        )
    return transcription.text



# ---------------------------
# Exécution principale
# ---------------------------
if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    audio_path = os.path.join(base_dir, "audio", "meetvoc.m4a")

    print("📂 Chemin audio :", audio_path)
    print("🟢 Fichier existe :", os.path.exists(audio_path))

    # Transcription
    text = speach_to_text(audio_path, language="fr")
    print("\n=== TEXTE TRANSCRIT ===\n")
    print(text)

  
