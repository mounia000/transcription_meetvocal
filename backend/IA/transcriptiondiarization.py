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

# 3️⃣ Configuration de base
base_dir = os.path.dirname(__file__)
audio_path = os.path.join(base_dir, "audio", "meet1.mp3")

# 4️⃣ Conversion en WAV
def convert_to_wav(audio_path):
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

wav_path = convert_to_wav(audio_path)
print(f"✅ Fichier WAV prêt : {wav_path}")

# 5️⃣ Charger le pipeline Pyannote    
print("⏳ Chargement du pipeline de diarisation (pyannote)...")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
print("✅ Pipeline chargé avec succès !")

# 6️⃣ Fonction utilitaire pour formater le temps en mm:ss.s
def format_time(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"

# 7️⃣ Fusion diarisation + transcription avec timestamps
def match_speaker_to_text(diar_segments, text_segments):
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

        # Ajout du timestamp formaté
        start_f = format_time(start)
        end_f = format_time(end)
        result.append(f"[{start_f} - {end_f}] [{speaker}] {text}")
    return result

# 8️⃣ Fonction principale
def transcription_with_diarization(audio_file=None):
    """
    Retourne le texte complet avec diarisation et timestamps.
    Si audio_file est fourni, on l'utilise à la place du fichier par défaut.
    """
    global audio_path, wav_path

    if audio_file:
        audio_path = audio_file
        wav_path = convert_to_wav(audio_path)

    # Diarisation
    print("🎧 Détection des intervenants...")
    diarization = pipeline(wav_path)
    segments = [{"start": t.start, "end": t.end, "speaker": s} for t, _, s in diarization.itertracks(yield_label=True)]
    print(f"👥 Intervenants détectés : {set(seg['speaker'] for seg in segments)}")

    # Transcription Groq
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

    fusion = match_speaker_to_text(segments, transcription.segments)

    # Sauvegarde dans un fichier texte
    output_path = os.path.join(base_dir, "transcription_avec_diarisation.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fusion))
    print(f"\n✅ Transcription avec timestamps enregistrée ici : {output_path}\n")

    # Retour du texte fusionné
    return "\n".join(fusion)
