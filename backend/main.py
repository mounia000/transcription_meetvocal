# backend/main.py
import os
import platform
import subprocess
from IA.transcriptiondiarization import transcription_with_diarization
from IA.extractions import extract_pure_text, extract_by_speaker
from IA.cleaning import clean_text
from IA.resume import summarize_text_local
from IA.save_pdf import save_files

def pipeline(audio_file: str):
    """
    Pipeline complet :
    audio → transcription + diarisation → extraction texte pur → nettoyage → résumé → sauvegarde PDF/Word
    """

    # 1️⃣ Transcription avec diarisation (avec timestamps et speakers)
    print("\n" + "="*60)
    print("🎤 ÉTAPE 1 : TRANSCRIPTION + DIARISATION")
    print("="*60)
    
    transcription_complete = transcription_with_diarization(audio_file)
    
    raw_file = "transcription_brute_avec_meta.txt"
    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(transcription_complete)
    print(f"✅ Transcription complète (avec timestamps/speakers) : {raw_file}")

    # 2️⃣ Extraction du texte pur (sans timestamps ni speakers)
    print("\n" + "="*60)
    print("📝 ÉTAPE 2 : EXTRACTION DU TEXTE PUR")
    print("="*60)
    
    pure_text = extract_pure_text(transcription_complete)
    
    pure_file = "transcription_texte_pur.txt"
    with open(pure_file, "w", encoding="utf-8") as f:
        f.write(pure_text)
    print(f"✅ Texte pur extrait : {pure_file}")
    print(f"📊 Longueur : {len(pure_text)} caractères, {len(pure_text.split())} mots")

    # 3️⃣ Nettoyage du texte
    print("\n" + "="*60)
    print("🧹 ÉTAPE 3 : NETTOYAGE DU TEXTE")
    print("="*60)
    
    cleaned_text = clean_text(pure_text)
    
    cleaned_file = "transcription_nettoyee.txt"
    with open(cleaned_file, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"✅ Texte nettoyé : {cleaned_file}")
    print(f"📊 Réduction : {len(pure_text)} → {len(cleaned_text)} caractères")

    # 4️⃣ Résumé
    print("\n" + "="*60)
    print("📋 ÉTAPE 4 : GÉNÉRATION DU RÉSUMÉ")
    print("="*60)
    
    try:
        summary = summarize_text_local(cleaned_text, max_length=150, min_length=50)
        
        summary_file = "transcription_resume.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"✅ Résumé généré : {summary_file}")
        print(f"📊 Longueur résumé : {len(summary)} caractères, {len(summary.split())} mots")
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération du résumé : {e}")
        summary = cleaned_text  # Fallback : utiliser le texte nettoyé

    # 5️⃣ Organisation par locuteur (bonus)
    print("\n" + "="*60)
    print("👥 ÉTAPE 5 : ORGANISATION PAR LOCUTEUR")
    print("="*60)
    
    by_speaker = extract_by_speaker(transcription_complete)
    
    speaker_file = "transcription_par_locuteur.txt"
    with open(speaker_file, "w", encoding="utf-8") as f:
        for speaker, text in by_speaker.items():
            f.write(f"\n{'='*50}\n")
            f.write(f"{speaker}\n")
            f.write(f"{'='*50}\n")
            f.write(f"{text}\n")
    print(f"✅ Texte organisé par locuteur : {speaker_file}")
    print(f"👥 Nombre de locuteurs détectés : {len(by_speaker)}")

    # 6️⃣ Génération PDF et Word
    print("\n" + "="*60)
    print("📄 ÉTAPE 6 : GÉNÉRATION PDF/WORD")
    print("="*60)
    
    # Créer un document final combinant tout
    final_content = f"""TRANSCRIPTION DE LA RÉUNION
{'='*60}

COMPTE RENDU (résumé)
{'-'*60}
{summary}

{'='*60}

TRANSCRIPTION COMPLÈTE (nettoyée)
{'-'*60}
{cleaned_text}

{'='*60}

DÉTAILS PAR LOCUTEUR
{'-'*60}
"""
    
    for speaker, text in by_speaker.items():
        final_content += f"\n{speaker}:\n{text}\n\n"
    
    save_files(final_content, base_name="transcription_finale")

    # 7️⃣ Ouvrir le PDF automatiquement
    print("\n" + "="*60)
    print("🎉 TRAITEMENT TERMINÉ")
    print("="*60)
    
    pdf_file = "transcription_finale.pdf"
    try:
        if platform.system() == "Darwin":       # macOS
            subprocess.call(["open", pdf_file])
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", pdf_file])
        else:                                   # Windows
            os.startfile(pdf_file)
        print(f"📂 PDF ouvert : {pdf_file}")
    except Exception as e:
        print(f"⚠️ Impossible d'ouvrir le PDF automatiquement : {e}")
    
    print("\n✨ Tous les fichiers ont été générés avec succès !")
    print(f"📁 Dossier de sortie : {os.getcwd()}")


if __name__ == "__main__":
    # Chemin relatif vers le fichier audio
    base_dir = os.path.dirname(__file__)
    audio_file = os.path.join(base_dir, "IA", "audio", "meet1.mp3")

    print("🚀 DÉMARRAGE DU PIPELINE DE TRANSCRIPTION")
    print("="*60)
    print(f"📂 Chemin audio : {audio_file}")
    print(f"🟢 Fichier existe : {os.path.exists(audio_file)}")
    print("="*60)

    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"❌ Fichier audio introuvable : {audio_file}")

    pipeline(audio_file)