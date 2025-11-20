# backend/IA/pipeline_service.py
import os
from typing import Dict, Tuple
from datetime import datetime
from .transcriptiondiarization import transcription_with_diarization
from .extractions import extract_pure_text, extract_by_speaker
from .cleaning import clean_text
from .resume import summarize_text_local
from .save_pdf import save_files
from .resume import generate_compte_rendu


class TranscriptionPipeline:
    """
    Service encapsulant tout le pipeline de transcription.
    Peut être utilisé par l'API ou en standalone.
    """
    
    def __init__(self, audio_file: str, output_dir: str = None):
        self.audio_file = audio_file
        self.output_dir = output_dir or os.getcwd()
        
        # Résultats du pipeline
        self.raw_transcription = None
        self.pure_text = None
        self.cleaned_text = None
        self.summary = None
        self.by_speaker = None
        self.speaker_summaries = {}
        self.pdf_path = None
        self.docx_path = None
        self.num_speakers = 0
        
    def run(self, save_intermediary_files: bool = False) -> Dict:
        """
        Exécute le pipeline complet et retourne tous les résultats.
        
        Args:
            save_intermediary_files: Si True, sauvegarde les fichiers intermédiaires
            
        Returns:
            Dict contenant tous les résultats du pipeline
        """
        
        # Transcription avec diarisation
        print("\n" + "="*60)
        print("ÉTAPE 1 : TRANSCRIPTION + DIARISATION")
        print("="*60)
        
        self.raw_transcription = transcription_with_diarization(self.audio_file)
        
        if save_intermediary_files:
            raw_file = os.path.join(self.output_dir, "transcription_brute_avec_meta.txt")
            with open(raw_file, "w", encoding="utf-8") as f:
                f.write(self.raw_transcription)
            print(f"Transcription complète sauvegardée : {raw_file}")
        
        #  Extraction du texte pur
        print("\n" + "="*60)
        print("ÉTAPE 2 : EXTRACTION DU TEXTE PUR")
        print("="*60)
        
        self.pure_text = extract_pure_text(self.raw_transcription)
        
        if save_intermediary_files:
            pure_file = os.path.join(self.output_dir, "transcription_texte_pur.txt")
            with open(pure_file, "w", encoding="utf-8") as f:
                f.write(self.pure_text)
            print(f"Texte pur extrait : {pure_file}")
        
        print(f"Longueur : {len(self.pure_text)} caractères, {len(self.pure_text.split())} mots")
        
        # Nettoyage du texte
        print("\n" + "="*60)
        print("ÉTAPE 3 : NETTOYAGE DU TEXTE")
        print("="*60)
        
        self.cleaned_text = clean_text(self.pure_text)
        
        if save_intermediary_files:
            cleaned_file = os.path.join(self.output_dir, "transcription_nettoyee.txt")
            with open(cleaned_file, "w", encoding="utf-8") as f:
                f.write(self.cleaned_text)
            print(f"Texte nettoyé : {cleaned_file}")
        
        print(f"Réduction : {len(self.pure_text)} → {len(self.cleaned_text)} caractères")
        
        # Résumé
        print("\n" + "="*60)
        print("ÉTAPE 4 : GÉNÉRATION DU RÉSUMÉ")
        print("="*60)
        
        try:
            print("Génération du compte-rendu structuré...")
            compte_rendu_data = generate_compte_rendu(
            self.cleaned_text, 
            self.speaker_summaries
            )
            self.summary = compte_rendu_data["compte_rendu_complet"]
            self.resume_court = compte_rendu_data["resume_court"]
        except Exception as e:
            print(f"Erreur génération compte-rendu: {e}")
            self.summary = self.cleaned_text[:500] + "..."
            self.resume_court = self.summary
        
        # 5️⃣ Organisation par locuteur
        print("\n" + "="*60)
        print("👥 ÉTAPE 5 : ORGANISATION PAR LOCUTEUR")
        print("="*60)
        
        self.by_speaker = extract_by_speaker(self.raw_transcription)
        self.num_speakers = len(self.by_speaker)
        
        for speaker, text in self.by_speaker.items():
            print(f"Génération du résumé pour {speaker}...")
            try:
                cleaned_speaker_text = clean_text(text)
                speaker_summary = summarize_text_local(cleaned_speaker_text, max_length=100, min_length=30)
                self.speaker_summaries[speaker] = speaker_summary
            except Exception as e:
                print(f"Erreur résumé {speaker}: {e}")
                cleaned_speaker_text = clean_text(text)
                self.speaker_summaries[speaker] = cleaned_speaker_text[:200] + "..."
        
        if save_intermediary_files:
            speaker_file = os.path.join(self.output_dir, "résumé_par_locuteur.txt")
            with open(speaker_file, "w", encoding="utf-8") as f:
                for speaker, text in self.by_speaker.items():
                    f.write(f"\n{'='*50}\n")
                    f.write(f"{speaker}\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"{text}\n")
            print(f"Résumés par locuteur : {speaker_file}")
        
        print(f"Nombre de locuteurs : {self.num_speakers}")
        
        # Génération PDF et Word
        print("\n" + "="*60)
        print("📄 ÉTAPE 6 : GÉNÉRATION PDF/WORD")
        print("="*60)
        
        final_content = self._build_final_content()
        
        base_name = os.path.join(self.output_dir, "transcription_finale")
        save_files(final_content, base_name=base_name)
        
        self.pdf_path = f"{base_name}.pdf"
        self.docx_path = f"{base_name}.docx"
        
        print("\n" + "="*60)
        print("TRAITEMENT TERMINÉ")
        print("="*60)
        print(f"Tous les fichiers ont été générés avec succès !")
        print(f"Dossier de sortie : {self.output_dir}")
        
        return self.get_results()
    
    def _build_final_content(self) -> str:
        """Construit le contenu final pour PDF/Word avec format professionnel"""
    
        final_content = f"""COMPTE-RENDU DE RÉUNION
Date : {datetime.now().strftime("%d/%m/%Y")}
Nombre de participants : {self.num_speakers}

{'='*70}

{self.summary}

{'='*70}

TRANSCRIPTION COMPLÈTE

{self.cleaned_text}
"""
        return final_content

    
    def get_results(self) -> Dict:
        """Retourne tous les résultats du pipeline"""
        return {
            "raw_transcription": self.raw_transcription,
            "pure_text": self.pure_text,
            "cleaned_text": self.cleaned_text,
            "summary": self.summary,
            "by_speaker": self.by_speaker,
            "speaker_summaries": self.speaker_summaries,
            "num_speakers": self.num_speakers,
            "pdf_path": self.pdf_path,
            "docx_path": self.docx_path
        }
    
    def get_speaker_data(self) -> list:
        """Retourne les données des speakers dans un format structuré"""
        speakers_data = []
        for speaker_label, text in self.by_speaker.items():
            speakers_data.append({
                "speaker_label": speaker_label,
                "raw_text": text,
                "cleaned_text": clean_text(text),
                "summary": self.speaker_summaries.get(speaker_label, ""),
                "word_count": len(text.split())
            })
        return speakers_data
