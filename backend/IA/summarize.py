import re
from transformers import pipeline

# Charger un modèle de résumé pré-entraîné
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def clean_text(text: str) -> str:
    """
    Nettoie la transcription avant le résumé.
    """
    text = re.sub(r"\s+", " ", text)  
    text = re.sub(r"\[.*?\]", "", text) 
    text = re.sub(r"\b(um+|euh+|ah+)\b", "", text, flags=re.IGNORECASE)
    text = text.strip()
    return text


def summarize_text(transcription: str) -> str:
    """
    Résume la transcription de la réunion 
    """
    if not transcription or len(transcription.strip()) == 0:
        return "Aucun contenu à résumer."

    # Nettoyage du texte brut
    transcription = clean_text(transcription)

    
    max_chunk = 2000  
    chunks = [transcription[i:i + max_chunk] for i in range(0, len(transcription), max_chunk)]

    summaries = []

    for chunk in chunks:
        try:
            summary = summarizer(
                chunk,
                max_length=180,
                min_length=60,
                do_sample=False
            )[0]['summary_text']
            summaries.append(summary)
        except Exception as e:
            print(f"⚠️ Erreur pendant la génération d’un résumé : {e}")
            continue

    # Fusionner les sous-résumés en un résumé global structuré
    final_summary = "\n\n".join(summaries)

    final_summary = (
        "### Résumé global de la réunion\n\n"
        + final_summary
        + "\n\n### Points clés :\n"
        + "\n- ".join(re.findall(r'([A-Z][^.!?]*[.!?])', final_summary)[:5])
        + "\n\n### Conclusion :\nCette réunion a permis de clarifier les points essentiels abordés."
    )

    return final_summary
