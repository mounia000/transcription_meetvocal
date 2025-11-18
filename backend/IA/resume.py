# backend/IA/resume.py
import os
from transformers import pipeline
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ============ ANCIENNE FONCTION (pour compatibilité) ============

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text_local(text: str, max_length: int = 150, min_length: int = 50) -> str:
    """
    Résumé local avec BART (ancienne méthode - toujours disponible)
    """
    sentences = text.split(". ")
    segments = []
    current_segment = ""

    for s in sentences:
        if len(current_segment.split()) + len(s.split()) <= 200:
            current_segment += s + ". "
        else:
            segments.append(current_segment.strip())
            current_segment = s + ". "
    if current_segment:
        segments.append(current_segment.strip())

    summaries = []
    for seg in segments:
        summary_list = summarizer(seg, max_length=max_length, min_length=min_length, do_sample=False)
        summaries.append(summary_list[0]['summary_text'])

    return " ".join(summaries)


# ============ NOUVELLE FONCTION (compte-rendu structuré) ============

def generate_compte_rendu(cleaned_text: str, speakers_summaries: dict = None) -> dict:
    """
    Génère un compte-rendu de réunion structuré avec Groq
    
    Retourne:
    {
        "compte_rendu_complet": "...",
        "resume_court": "..."
    }
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Préparer le contexte avec les résumés par speaker si disponible
    context_speakers = ""
    if speakers_summaries:
        context_speakers = "\n\nRésumés par intervenant:\n"
        for speaker, summary in speakers_summaries.items():
            context_speakers += f"- {speaker}: {summary}\n"
    
    prompt = f"""Tu es un assistant qui génère des comptes-rendus de réunion professionnels.

Voici la transcription d'une réunion :

{cleaned_text[:3000]}
{context_speakers}

Génère un compte-rendu structuré au format suivant (en français correct, sans anglicismes) :

# RÉSUMÉ EXÉCUTIF
[2-3 phrases résumant l'essentiel de la réunion]

# CONTEXTE ET OBJECTIF
[Pourquoi cette réunion ? Quel était l'objectif ?]

# POINTS CLÉS DISCUTÉS
- [Point 1]
- [Point 2]
- [Point 3]

# DÉCISIONS PRISES
- [Décision 1]
- [Décision 2]

# ACTIONS À ENTREPRENDRE
- [Action 1 - Responsable si mentionné]
- [Action 2 - Responsable si mentionné]

# PROCHAINES ÉTAPES
- [Étape 1 avec date si mentionnée]
- [Étape 2]

Sois concis, professionnel et factuel. Ne mentionne que ce qui est réellement dit dans la transcription."""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant expert en rédaction de comptes-rendus de réunion. Tu produis des résumés structurés, clairs et professionnels en français."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        compte_rendu = completion.choices[0].message.content
        
        # Extraire le résumé exécutif pour le résumé court
        resume_court = compte_rendu.split('\n\n')[1] if '\n\n' in compte_rendu else compte_rendu[:300]
        
        return {
            "compte_rendu_complet": compte_rendu,
            "resume_court": resume_court
        }
        
    except Exception as e:
        print(f"⚠️ Erreur génération compte-rendu Groq: {e}")
        # Fallback sur résumé BART
        try:
            fallback_summary = summarize_text_local(cleaned_text, max_length=200, min_length=50)
            return {
                "compte_rendu_complet": fallback_summary,
                "resume_court": fallback_summary
            }
        except:
            return {
                "compte_rendu_complet": cleaned_text[:1000] + "...",
                "resume_court": cleaned_text[:300] + "..."
            }