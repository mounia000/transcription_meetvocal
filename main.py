
import os
import platform
import subprocess
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# Import IA Pipeline 
from IA.transcriptiondiarization import transcription_with_diarization
from IA.extractions import extract_pure_text, extract_by_speaker
from IA.cleaning import clean_text
from IA.resume import summarize_text_local
from IA.save_pdf import save_files

#  Import des routes d’authentification 
from routes import auth


# 1Configuration FastAPI


app = FastAPI(title="MeetRecap Backend API")

# Autoriser le frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # ton front local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes d’authentification
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "🚀 Backend MeetRecap est bien en ligne !"}



#2 Pipeline IA (inchangé)


def pipeline(audio_file: str):
    """
    Pipeline complet :
    audio → transcription + diarisation → extraction texte pur → nettoyage → résumé → sauvegarde PDF/Word
    """

    # 1 Transcription avec diarisation
    print("\n" + "="*60)
    print("🎤 ÉTAPE 1 : TRANSCRIPTION + DIARISATION")
    print("="*60)
    transcription_complete = transcription_with_diarization(audio_file)

    raw_file = "transcription_brute_avec_meta.txt"
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(transcription_complete)
    print(f"✅ Transcription complète : {raw_file}")

    # 2 Extraction du texte pur
    pure_text = extract_pure_text(transcription_complete)
    pure_file = "transcription_texte_pur.txt"
    with open(pure_file, "w", encoding="utf-8") as f:
        f.write(pure_text)
    print(f"✅ Texte pur extrait : {pure_file}")

    # 3 Nettoyage
    cleaned_text = clean_text(pure_text)
    cleaned_file = "transcription_nettoyee.txt"
    with open(cleaned_file, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"✅ Texte nettoyé : {cleaned_file}")

    # 4 Résumé global
    try:
        summary = summarize_text_local(cleaned_text, max_length=150, min_length=50)
    except Exception as e:
        print(f"⚠️ Erreur résumé global : {e}")
        summary = cleaned_text

    # 5 Résumés par locuteur
    by_speaker = extract_by_speaker(transcription_complete)
    speaker_summaries = {}

    for speaker, text in by_speaker.items():
        try:
            cleaned_speaker_text = clean_text(text)
            speaker_summary = summarize_text_local(cleaned_speaker_text, max_length=100, min_length=30)
            speaker_summaries[speaker] = speaker_summary
        except Exception as e:
            print(f"⚠️ Erreur résumé {speaker}: {e}")
            speaker_summaries[speaker] = text[:200] + "..."

    # 6Contenu final
    final_content = f"""TRANSCRIPTION DE LA RÉUNION
{'='*60}

RESUME GENERAL
{'-'*60}
{summary}

{'='*60}

RÉSUMÉS PAR LOCUTEUR
{'-'*60}
"""

    for speaker, speaker_summary in speaker_summaries.items():
        final_content += f"\n{speaker}:\n{speaker_summary}\n\n"

    final_content += f"""
{'='*60}

TRANSCRIPTION COMPLÈTE (nettoyée)
{'-'*60}
{cleaned_text}
"""

    save_files(final_content, base_name="transcription_finale")

    print("✅ Tous les fichiers ont été générés avec succès !")
    return {
        "summary": summary,
        "speakers": speaker_summaries,
        "text_length": len(cleaned_text),
    }



#Nouvelle route API : upload audio

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload un fichier audio MP3 depuis le frontend et lance tout le pipeline IA.
    """
    try:
        audio_dir = os.path.join(os.path.dirname(__file__), "IA", "audio")
        os.makedirs(audio_dir, exist_ok=True)

        file_path = os.path.join(audio_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        print(f"✅ Fichier reçu et sauvegardé : {file_path}")
        result = pipeline(file_path)

        return {
            "status": "success",
            "message": "Traitement terminé avec succès 🎉",
            "result": result,
        }

    except Exception as e:
        print(f"❌ Erreur upload/pipeline : {e}")
        return {"status": "error", "message": str(e)}



#Lancement du serveur


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
