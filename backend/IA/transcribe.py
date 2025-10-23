import os
import whisper
from pathlib import Path

# Charger le modèle Whisper 
model = whisper.load_model("base")

def transcribe_file(file_path):
    """
    Transcrit un fichier audio avec Whisper
    """
    # Convertir en Path et obtenir le chemin absolu
    file_path = Path(file_path).resolve()

    # Vérifier l’existence du fichier
    if not file_path.exists():
        raise FileNotFoundError(f"❌ Fichier introuvable : {file_path}")

    # Conversion en format str 
    file_path_str = str(file_path).replace("\\", "/")

    print(f"🎧 Début de la transcription du fichier : {file_path_str}")

    try:
        # Transcrire l’audio
        result = model.transcribe(file_path_str)
        transcription = result.get("text", "").strip()

        print(f"✅ Transcription terminée ({len(transcription)} caractères)")
        return transcription

    except Exception as e:
        print(f"⚠️ Erreur pendant la transcription : {e}")
        return ""
