# backend/pipeline_service.py

from backend.IA.transcriptiondiarization import transcription_with_diarization
from backend.IA.extractions import extract_pure_text, extract_by_speaker
from backend.IA.cleaning import clean_text
from backend.IA.resume import summarize_text_local, generate_compte_rendu
from backend.IA.save_pdf import save_files


def format_speaker_summaries(speaker_summaries: dict) -> str:
    output = ""
    for speaker, summary in speaker_summaries.items():
        output += f"{speaker}\n"
        output += f"{summary}\n\n"
    return output.strip()


def run_pipeline_service(audio_path: str):
    """
    Pipeline réutilisable par L'API.
    """

    # 1. Transcription + diarisation
    transcription_complete = transcription_with_diarization(audio_path)

    # 2. Extraction texte pur
    pure_text = extract_pure_text(transcription_complete)

    # 3. Nettoyage général
    cleaned_text = clean_text(pure_text)

    # 4. Organisation par locuteur + résumé par speaker
    by_speaker = extract_by_speaker(transcription_complete)
    speaker_summaries = {}

    for speaker, text in by_speaker.items():
        cleaned_speaker = clean_text(text)
        try:
            speaker_summaries[speaker] = summarize_text_local(cleaned_speaker)
        except:
            speaker_summaries[speaker] = cleaned_speaker[:200]

    # 5.Compte-rendu structuré (Groq)
    try:
        compte_rendu = generate_compte_rendu(
            cleaned_text=cleaned_text,
            speakers_summaries=speaker_summaries
        )
    except Exception as e:
        print(f"⚠️ Erreur Groq → fallback BART : {e}")
        fallback = summarize_text_local(cleaned_text)
        compte_rendu = {
            "compte_rendu_complet": fallback,
            "resume_court": fallback
        }

    # 6. Génération du contenu final
    sections_content = []
    
    # Section 1 : RÉSUMÉ COURT
    sections_content.append(f"RÉSUMÉ COURT\n{compte_rendu['resume_court']}")
    
    # Section 2 : COMPTE-RENDU COMPLET
    sections_content.append(f"COMPTE-RENDU COMPLET\n{compte_rendu['compte_rendu_complet']}")
    
    # Section 3 : RÉSUMÉS PAR INTERVENANT
    sections_content.append(f"RÉSUMÉS PAR INTERVENANT\n{format_speaker_summaries(speaker_summaries)}")
    
    # Section 4 : TRANSCRIPTION
    sections_content.append(f"TRANSCRIPTION AVEC LOCUTEURS ET TIMESTAMPS\n{transcription_complete}")
    
    # Joindre avec le séparateur =====
    final_content = "\n=====\n".join(sections_content)

    # DEBUG
    print("=" * 80)
    print("CONTENU ENVOYÉ À save_as_pdf:")
    print("=" * 80)
    print(final_content[:500])
    print("\n... (contenu tronqué) ...\n")
    print(final_content[-500:])
    print("=" * 80)

    file_path = save_files(final_content, base_name="compte_rendu_reunion")

    # 7. Retour API
    return {
        "resume_court": compte_rendu["resume_court"],
        "compte_rendu": compte_rendu["compte_rendu_complet"],
        "speakers": speaker_summaries,
        "cleaned_text": cleaned_text,
        "output_file": file_path
    }