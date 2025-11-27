# backend/pipeline_service.py

from IA.transcriptiondiarization import transcription_with_diarization
from IA.extractions import extract_pure_text, extract_by_speaker
from IA.cleaning import clean_text
from IA.resume import summarize_text_local, generate_compte_rendu
from IA.save_pdf import save_files


def format_speaker_summaries(speaker_summaries: dict) -> str:
    """Formatte les résumés de chaque intervenant."""
    output = ""
    for speaker, summary in speaker_summaries.items():
        output += f"{speaker}\n"
        output += f"{summary}\n\n"
    return output.strip()


def run_pipeline_service(audio_path: str):
    """
    Pipeline principal utilisé par l'API.
    """
    # 1. Transcription + diarisation
    transcription_complete = transcription_with_diarization(audio_path)

    # 2. Extraction du texte pur
    pure_text = extract_pure_text(transcription_complete)

    # 3. Nettoyage
    cleaned_text = clean_text(pure_text)

    # 4. Organisation par locuteurs + résumé individuel
    by_speaker = extract_by_speaker(transcription_complete)
    speaker_summaries = {}

    for speaker, text in by_speaker.items():
        cleaned_speaker_text = clean_text(text)
        try:
            speaker_summaries[speaker] = summarize_text_local(cleaned_speaker_text)
        except Exception:
            speaker_summaries[speaker] = cleaned_speaker_text[:200]

    # 5. Génération du compte-rendu général
    try:
        compte_rendu = generate_compte_rendu(
            cleaned_text=cleaned_text,
            speakers_summaries=speaker_summaries
        )
    except Exception as e:
        print(f"⚠️ Erreur Groq : {e}")
        fallback = summarize_text_local(cleaned_text)
        compte_rendu = {
            "compte_rendu_complet": fallback,
            "resume_court": fallback
        }

    # 6. Construire le contenu final du PDF
    sections = []

    # Résumé court
    sections.append(f"RÉSUMÉ COURT\n{compte_rendu['resume_court']}")

    # Compte-rendu complet
    sections.append(f"COMPTE-RENDU COMPLET\n{compte_rendu['compte_rendu_complet']}")

    # Résumés par intervenant
    sections.append(
        f"RÉSUMÉS PAR INTERVENANT\n{format_speaker_summaries(speaker_summaries)}"
    )

    # Transcription brute mais structurée
    sections.append(
        f"TRANSCRIPTION AVEC LOCUTEURS ET TIMESTAMPS\n{transcription_complete}"
    )

    final_content = "\n=====\n".join(sections)

    # DEBUG
    print("=" * 80)
    print("CONTENU ENVOYÉ À save_as_pdf:")
    print("=" * 80)
    print(final_content[:500])
    print("\n... (contenu tronqué) ...\n")
    print(final_content[-500:])
    print("=" * 80)

    # 7. Sauvegarde PDF + DOCX (⚠️ ICI — CORRIGÉ)
    file_paths = save_files(final_content, filename="compte_rendu_reunion")

    # 8. Résultat renvoyé à l'API
    return {
        "resume_court": compte_rendu["resume_court"],
        "compte_rendu": compte_rendu["compte_rendu_complet"],
        "speakers": speaker_summaries,
        "cleaned_text": cleaned_text,
        "output_file": file_paths
    }
