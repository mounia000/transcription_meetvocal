# backend/IA/transcriptiondiarization.py
import os
import subprocess
from dotenv import load_dotenv
from groq import Groq
from pyannote.audio import Pipeline

# Déclaration du pipeline en global
pipeline = None

# 1️⃣ Charger les variables d'environnement
load_dotenv()
print("✅ Clés API chargées correctement.")

# 2️⃣ Vérifier les clés API
groq_api_key = os.getenv("GROQ_API_KEY")
hf_token = os.getenv("HUGGINGFACE_TOKEN")

if not groq_api_key or not hf_token:
    raise ValueError("❌ Clés API manquantes (Groq ou Hugging Face)")

# 3️⃣ Charger le pipeline Pyannote (global)
try:
    print("⏳ Chargement du pipeline de diarisation (pyannote)...")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
    print("✅ Pipeline chargé avec succès !")
except Exception as e:
    print(f"⚠️ Erreur lors du chargement du pipeline Pyannote : {e}")
    pipeline = None

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

# 5️⃣ Formater le temps
def format_time(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"

# 6️⃣ Associer les segments texte ↔ locuteurs
def match_speaker_to_text(diar_segments, text_segments):
    result = []
    detected_speakers = sorted(set(d["speaker"] for d in diar_segments))
    for txt in text_segments:
        start, end, text = txt["start"], txt["end"], txt["text"].strip()
        speaker = None
        min_distance = float('inf')
        for d in diar_segments:
            if d["start"] <= start <= d["end"] or d["start"] <= end <= d["end"]:
                speaker = d["speaker"]
                break
            distance = min(abs(d["start"] - start), abs(d["end"] - end))
            if distance < min_distance:
                min_distance = distance
                speaker = d["speaker"]
        if not speaker:
            speaker = detected_speakers[0] if detected_speakers else "SPEAKER_00"
        start_f, end_f = format_time(start), format_time(end)
        result.append(f"[{start_f} - {end_f}] [{speaker}] {text}")
    return result

# 7️⃣ Transcription + Diarisation principale
def transcription_with_diarization(audio_file=None):
    global pipeline  # <<----- 🔥 IMPORTANT

    if not pipeline:
        raise RuntimeError("❌ Le pipeline Pyannote n'est pas initialisé.")

    base_dir = os.path.dirname(__file__)
    if audio_file:
        audio_path = audio_file
    else:
        audio_path = os.path.join(base_dir, "audio", "reunion_projet_meetrecap.m4a")

    wav_path = convert_to_wav(audio_path)

    # 🔹 Étape 1 : Diarisation
    print("🎧 Détection des intervenants...")
    diarization = pipeline(wav_path)
    segments = [
        {"start": t.start, "end": t.end, "speaker": s}
        for t, _, s in diarization.itertracks(yield_label=True)
    ]
    print(f"👥 Intervenants détectés : {set(seg['speaker'] for seg in segments)}")

    # 🔹 Étape 2 : Transcription
    print("\n🎙️ Transcription complète (Groq)...")
    client = Groq(api_key=groq_api_key)
    with open(wav_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="fr"
        )

    # 🔹 Étape 3 : Fusion
    fusion = match_speaker_to_text(segments, transcription.segments)

    output_path = os.path.join(base_dir, "transcription_avec_diarisation.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fusion))

    print(f"\n✅ Transcription enregistrée ici : {output_path}")
    return "\n".join(fusion)
