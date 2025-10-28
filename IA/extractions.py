# backend/IA/extractions.py
import re

def extract_pure_text(transcription_with_meta: str) -> str:
    """
    Extrait uniquement le texte parlé d'une transcription avec timestamps et speakers.
    
    Entrée :
        [00:00.0 - 00:06.5] [UNKNOWN] Salut Julien, tu as deux minutes...
    
    Sortie :
        Salut Julien, tu as deux minutes...
    """
    lines = transcription_with_meta.split("\n")
    pure_text = []
    
    for line in lines:
        # Pattern pour extraire le texte après [TIMESTAMP] [SPEAKER]
        match = re.search(r'\]\s*\[.*?\]\s*(.*)', line)
        if match:
            text = match.group(1).strip()
            if text:
                pure_text.append(text)
    
    return " ".join(pure_text)


def extract_by_speaker(transcription_with_meta: str) -> dict:
    """
    Organise la transcription par locuteur.
    
    Retourne un dict : {"SPEAKER_00": "texte complet", "SPEAKER_01": "texte complet"}
    """
    lines = transcription_with_meta.split("\n")
    speakers = {}
    
    for line in lines:
        # Extraire [SPEAKER] et le texte
        match = re.search(r'\[([^\]]+)\]\s*\[([^\]]+)\]\s*(.*)', line)
        if match:
            timestamp = match.group(1)
            speaker = match.group(2)
            text = match.group(3).strip()
            
            if speaker not in speakers:
                speakers[speaker] = []
            
            speakers[speaker].append(text)
    
    # Fusionner les textes de chaque speaker
    return {speaker: " ".join(texts) for speaker, texts in speakers.items()}