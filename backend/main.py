# backend/main.py
import os
import platform
import subprocess
from IA.transcription import speach_to_text
from IA.cleaning import clean_text
from IA.resume import summarize_text_local
from IA.save_pdf import save_files

def pipeline(audio_file: str):
    """
    Pipeline complet :
    audio → transcription via Groq → nettoyage → résumé → sauvegarde PDF/Word
    """

    # 1️⃣ Transcription brute
    raw_text = speach_to_text(audio_file)
    raw_file = "transcription_brute.txt"
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(raw_text)
    print(f"✅ Transcription brute sauvegardée : {raw_file}")

    # 2️⃣ Nettoyage
    cleaned_text = clean_text(raw_text)
    cleaned_file = "transcription_nettoyee.txt"
    with open(cleaned_file, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"✅ Texte nettoyé sauvegardé : {cleaned_file}")

    # 3️⃣ Résumé
    summary = summarize_text_local(cleaned_text, max_length=150, min_length=50)
    summary_file = "transcription_resume.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"✅ Résumé sauvegardé : {summary_file}")

    # 4️⃣ Fichier final texte propre
    final_file = "transcription_finale.txt"
    with open(final_file, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"✅ Fichier final sauvegardé : {final_file}")

    # 5️⃣ Génération PDF et Word
    save_files(cleaned_text, base_name="transcription_finale")

    # 6️⃣ Ouvrir le PDF automatiquement
    pdf_file = "transcription_finale.pdf"
    try:
        if platform.system() == "Darwin":       # macOS
            subprocess.call(["open", pdf_file])
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", pdf_file])
        else:                                   # Windows
            os.startfile(pdf_file)
    except Exception as e:
        print(f"⚠️ Impossible d'ouvrir le PDF automatiquement : {e}")


if __name__ == "__main__":
    # Chemin relatif vers le fichier audio
    base_dir = os.path.dirname(__file__)
    audio_file = os.path.join(base_dir, "IA", "audio", "meet.m4a")

    print("📂 Chemin audio :", audio_file)
    print("🟢 Fichier existe :", os.path.exists(audio_file))

    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Fichier audio introuvable : {audio_file}")

    pipeline(audio_file)
