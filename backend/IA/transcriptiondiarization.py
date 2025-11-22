# backend/IA/transcriptiondiarization.py

import os
import subprocess
from dotenv import load_dotenv
from groq import Groq
from pyannote.audio import Pipeline
import torch

# Charger les variables d'environnement
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
hf_token = os.getenv("HUGGINGFACE_TOKEN")

if not groq_api_key or not hf_token:
    raise ValueError("❌ Clés API manquantes (Groq ou Hugging Face)")


# -------------------------------
# 1️⃣ Convertir audio → WAV
# -------------------------------

def convert_to_wav(audio_path):
    base, ext = os.path.splitext(audio_path)
    wav_path = base + ".wav"

    command = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ar", "16000",
        "-ac", "1",
        wav_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"❌ FFmpeg error: {result.stderr}")

    return wav_path


# ---------------------------
# 2️⃣ Charger pyannote
# ---------------------------

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization",  # Version stable
            use_auth_token=hf_token
        )
        
        # Paramètres optimisés pour réduire la confusion
        if torch.cuda.is_available():
            _pipeline.to(torch.device("cuda"))
        
    return _pipeline


# -------------------------------
# 3️⃣ Fusion améliorée avec score de confiance
# -------------------------------

def format_time(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:04.1f}"


def calculate_overlap(start1, end1, start2, end2):
    """Calcule le pourcentage de chevauchement entre deux segments"""
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    
    if overlap_start >= overlap_end:
        return 0.0
    
    overlap_duration = overlap_end - overlap_start
    segment_duration = end1 - start1
    
    return overlap_duration / segment_duration if segment_duration > 0 else 0.0


def match_speaker_to_text(diar_segments, text_segments, overlap_threshold=0.5):
    """
    Amélioration de l'attribution des locuteurs avec:
    - Calcul du chevauchement temporel
    - Gestion des segments ambigus
    - Continuité des locuteurs
    """
    result = []
    previous_speaker = None
    
    detected_speakers = sorted(set(d["speaker"] for d in diar_segments))

    for txt in text_segments:
        start = txt["start"]
        end = txt["end"]
        text = txt["text"].strip()

        # Trouver tous les speakers qui chevauchent ce segment
        candidates = []
        
        for d in diar_segments:
            overlap = calculate_overlap(start, end, d["start"], d["end"])
            
            if overlap > 0:
                continuity_bonus = 0.2 if d["speaker"] == previous_speaker else 0.0
                score = overlap + continuity_bonus
                
                candidates.append({
                    "speaker": d["speaker"],
                    "score": score,
                    "overlap": overlap
                })
        
        
        if candidates:
            # Trier par score décroissant
            candidates.sort(key=lambda x: x["score"], reverse=True)
            best_candidate = candidates[0]
            
            # Vérifier si le chevauchement est suffisant
            if best_candidate["overlap"] >= overlap_threshold:
                speaker = best_candidate["speaker"]
            else:
                # Si chevauchement faible, privilégier la continuité
                speaker = previous_speaker if previous_speaker else best_candidate["speaker"]
        else:
            # Aucun chevauchement: utiliser le speaker précédent ou le plus proche
            if previous_speaker:
                speaker = previous_speaker
            else:
                # Trouver le speaker le plus proche temporellement
                min_distance = float('inf')
                closest_speaker = detected_speakers[0] if detected_speakers else "SPEAKER_00"
                
                for d in diar_segments:
                    distance = min(abs(d["start"] - start), abs(d["end"] - end))
                    if distance < min_distance:
                        min_distance = distance
                        closest_speaker = d["speaker"]
                
                speaker = closest_speaker

        previous_speaker = speaker
        
        result.append(
            f"[{format_time(start)} - {format_time(end)}] [{speaker}] {text}"
        )

    return result


def merge_consecutive_segments(formatted_segments):
    """
    Fusionne les segments consécutifs du même locuteur
    """
    if not formatted_segments:
        return []
    
    merged = []
    current_speaker = None
    current_start = None
    current_texts = []
    
    for line in formatted_segments:
        # Parser la ligne: [time] [speaker] text
        parts = line.split("] ", 2)
        if len(parts) < 3:
            merged.append(line)
            continue
        
        time_range = parts[0][1:]  
        speaker = parts[1][1:]      
        text = parts[2]
        
        start_time = time_range.split(" - ")[0]
        
        if speaker == current_speaker:
            # Même locuteur: ajouter le texte
            current_texts.append(text)
        else:
            # Nouveau locuteur: sauvegarder le segment précédent
            if current_speaker:
                merged_text = " ".join(current_texts)
                merged.append(f"[{current_start} - ...] [{current_speaker}] {merged_text}")
            
            # Commencer un nouveau segment
            current_speaker = speaker
            current_start = start_time
            current_texts = [text]
    
    # Ajouter le dernier segment
    if current_speaker and current_texts:
        merged_text = " ".join(current_texts)
        merged.append(f"[{current_start} - ...] [{current_speaker}] {merged_text}")
    
    return merged


# --------------------------
# 4️⃣ Fonction principale
# --------------------------

def transcription_with_diarization(audio_file, min_speakers=None, max_speakers=None, merge_segments=True):
    """
    Transcription + diarisation
    
    Args:
        audio_file: Chemin vers le fichier audio
        min_speakers: Nombre minimum de locuteurs attendus
        max_speakers: Nombre maximum de locuteurs attendus
        merge_segments: Fusionner les segments consécutifs du même locuteur
    """

    # 1. Convertir en wav
    wav_path = convert_to_wav(audio_file)

    # 2. Détection des speakers
    pipeline = get_pipeline()
    
    # Configurer les paramètres de diarisation
    diarization_params = {}
    if min_speakers:
        diarization_params["min_speakers"] = min_speakers
    if max_speakers:
        diarization_params["max_speakers"] = max_speakers
    
    diarization = pipeline(wav_path, **diarization_params)

    diar_segments = [
        {"start": t.start, "end": t.end, "speaker": s}
        for t, _, s in diarization.itertracks(yield_label=True)
    ]

    # 3. Transcription Groq
    client = Groq(api_key=groq_api_key)

    with open(wav_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="fr"
        )

    # 4. Fusion
    fusion = match_speaker_to_text(diar_segments, transcription.segments)
    
    # 5.Fusionner les segments consécutifs
    if merge_segments:
        fusion = merge_consecutive_segments(fusion)

    return "\n".join(fusion)