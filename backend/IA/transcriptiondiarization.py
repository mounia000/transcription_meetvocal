# backend/IA/transcriptiondiarization.py
import os
import subprocess
import torch
import requests
from dotenv import load_dotenv
from pyannote.audio import Pipeline

# ============================================================
# 🔐 Chargement des variables d'environnement
# ============================================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

if not GROQ_API_KEY:
    raise ValueError("❌ Clé API Groq manquante (.env)")
if not HF_TOKEN:
    raise ValueError("❌ Token HuggingFace manquant (.env)")


# ============================================================
# 🎵 Conversion audio → WAV
# ============================================================
def convert_to_wav(audio_path: str) -> str:
    base, _ = os.path.splitext(audio_path)
    wav_path = base + ".wav"

    print(f"🎧 Conversion audio → {wav_path}")
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ar", "16000",
        "-ac", "1",
        wav_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"❌ Erreur FFmpeg : {result.stderr.strip()}")

    return wav_path


# ============================================================
# 🧠 Initialisation du pipeline Pyannote
# ============================================================
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        print("🔹 Chargement du pipeline Pyannote (cela peut prendre un moment)...")
        _pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=HF_TOKEN)

        if torch.cuda.is_available():
            print("✅ GPU détecté → utilisation de CUDA")
            _pipeline.to(torch.device("cuda"))
        else:
            print("⚙️ Utilisation du CPU")
    return _pipeline


# ============================================================
# ⏱️ Fonctions utilitaires
# ============================================================
def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def calculate_overlap(start1, end1, start2, end2):
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    if overlap_start >= overlap_end:
        return 0.0
    return (overlap_end - overlap_start) / (end1 - start1 + 1e-6)


def match_speaker_to_text(diar_segments, text_segments, overlap_threshold=0.5):
    result = []
    previous_speaker = None
    detected_speakers = sorted(set(d["speaker"] for d in diar_segments))

    for txt in text_segments:
        start, end, text = txt["start"], txt["end"], txt["text"].strip()
        candidates = []

        for d in diar_segments:
            overlap = calculate_overlap(start, end, d["start"], d["end"])
            if overlap > 0:
                continuity_bonus = 0.2 if d["speaker"] == previous_speaker else 0.0
                candidates.append({
                    "speaker": d["speaker"],
                    "score": overlap + continuity_bonus,
                    "overlap": overlap
                })

        if candidates:
            candidates.sort(key=lambda x: x["score"], reverse=True)
            best = candidates[0]
            if best["overlap"] >= overlap_threshold:
                speaker = best["speaker"]
            else:
                speaker = previous_speaker or best["speaker"]
        else:
            speaker = previous_speaker or (detected_speakers[0] if detected_speakers else "SPEAKER_00")

        previous_speaker = speaker
        result.append(f"[{format_time(start)} - {format_time(end)}] [{speaker}] {text}")

    return result


def merge_consecutive_segments(segments):
    if not segments:
        return []
    merged = []
    current_speaker, current_start, current_texts = None, None, []

    for line in segments:
        parts = line.split("] ", 2)
        if len(parts) < 3:
            continue
        time_range = parts[0][1:]
        speaker = parts[1][1:]
        text = parts[2]
        start_time = time_range.split(" - ")[0]

        if speaker == current_speaker:
            current_texts.append(text)
        else:
            if current_speaker:
                merged.append(f"[{current_start} - ...] [{current_speaker}] {' '.join(current_texts)}")
            current_speaker, current_start, current_texts = speaker, start_time, [text]

    if current_speaker:
        merged.append(f"[{current_start} - ...] [{current_speaker}] {' '.join(current_texts)}")
    return merged


# ============================================================
# 🧩 Transcription directe via API HTTP Groq (contournement du bug)
# ============================================================
def transcribe_with_groq(file_path: str):
    """Envoie le fichier audio directement à l’API Groq (sans SDK buggué)."""
    print("🧠 Transcription via API HTTP Groq...")
    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f, "audio/wav")
        }
        data = {
            "model": "whisper-large-v3-turbo",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "segment",
            "language": "fr"
        }

        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code != 200:
            raise RuntimeError(f"❌ Erreur API Groq : {response.status_code} {response.text}")

        result = response.json()
        return result["segments"]


# ============================================================
# 🎙️ Fonction principale
# ============================================================
def transcription_with_diarization(audio_file, min_speakers=None, max_speakers=None, merge_segments=True):
    print(f"🎧 Traitement du fichier : {audio_file}")

    wav_path = convert_to_wav(audio_file)
    print(f"✅ Converti en WAV → {wav_path}")

    pipeline = get_pipeline()
    diar_params = {}
    if min_speakers:
        diar_params["min_speakers"] = min_speakers
    if max_speakers:
        diar_params["max_speakers"] = max_speakers

    print("🔎 Diarisation en cours...")
    diarization = pipeline(wav_path, **diar_params)
    diar_segments = [
        {"start": t.start, "end": t.end, "speaker": s}
        for t, _, s in diarization.itertracks(yield_label=True)
    ]
    print(f"✅ Diarisation terminée ({len(diar_segments)} segments détectés)")

    # Étape 3 : Transcription via API HTTP
    try:
        text_segments = transcribe_with_groq(wav_path)
        print(f"✅ Transcription terminée ({len(text_segments)} segments texte)")
    except Exception as e:
        print(f"❌ Erreur transcription : {e}")
        raise

    fusion = match_speaker_to_text(diar_segments, text_segments)
    if merge_segments:
        fusion = merge_consecutive_segments(fusion)

    print(f"📝 Fusion finale : {len(fusion)} lignes générées")
    return "\n".join(fusion)
