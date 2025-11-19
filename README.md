# 🎙️ MeetVocal - Transcription Automatique de Réunions

## 📋 Description du Projet

MeetVocal est une application de transcription automatique qui transforme vos enregistrements audio de réunions en comptes-rendus professionnels structurés. Le système utilise l'intelligence artificielle pour :

- ✅ Transcrire automatiquement les enregistrements audio
- 👥 Identifier et séparer les différents intervenants (diarisation)
- 🧹 Nettoyer le texte (suppression des hésitations, correction de la ponctuation)
- 📝 Générer des comptes-rendus structurés
- 💾 Exporter en PDF et DOCX

---

## 🏗️ Architecture du Projet

```
transcription_meetvocal/
│
├── backend/
│   └── IA/
│       ├── transcriptiondiarization.py  # Transcription + identification des locuteurs
│       ├── extractions.py               # Extraction et organisation du texte
│       ├── cleaning.py                  # Nettoyage du texte transcrit
│       ├── resume.py                    # Génération de résumés (BART + Groq)
│       ├── pipeline_service.py          # Orchestration complète du pipeline
│       └── save_pdf.py                  # Export PDF et DOCX
│
├── database/
│   └── SQL_File.sql                     # Schéma de la base de données PostgreSQL
│
├── main.py                              # Point d'entrée de l'application
├── .env                                 # Variables d'environnement (à créer)
└── README.md                            # Ce fichier
```

---

## 🚀 Installation et Configuration

### 1️⃣ Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- **Python 3.8+** ([Télécharger Python](https://www.python.org/downloads/))
- **FFmpeg** (pour la conversion audio)
- **PostgreSQL** (pour la base de données)

#### Installation de FFmpeg :

**Windows :**
```bash
# Avec Chocolatey
choco install ffmpeg

# Ou télécharger depuis : https://ffmpeg.org/download.html
```

**macOS :**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2️⃣ Cloner le Projet

```bash
git clone https://github.com/votre-username/transcription_meetvocal.git
cd transcription_meetvocal
```

### 3️⃣ Installer les Dépendances Python

Créez un environnement virtuel et installez les packages :

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows :
venv\Scripts\activate
# macOS/Linux :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

**Liste des dépendances principales :**
```txt
groq>=0.4.0
pyannote.audio>=3.0.0
transformers>=4.30.0
torch>=2.0.0
python-dotenv>=1.0.0
fpdf>=1.7.2
python-docx>=0.8.11
```

### 4️⃣ Configuration des Clés API

Créez un fichier `.env` à la racine du projet :

```bash
touch .env
```

Ajoutez-y vos clés API :

```env
# Clé API Groq (pour la transcription Whisper)
GROQ_API_KEY=votre_cle_groq_ici

# Token Hugging Face (pour la diarisation Pyannote)
HUGGINGFACE_TOKEN=votre_token_huggingface_ici
```

#### Où obtenir les clés ?

1. **Groq API** : [https://console.groq.com](https://console.groq.com)
   - Créez un compte gratuit
   - Générez une clé API dans les paramètres

2. **Hugging Face** : [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Créez un compte
   - Générez un token d'accès
   - Acceptez les conditions d'utilisation de `pyannote/speaker-diarization`

### 5️⃣ Configuration de la Base de Données (Optionnel)

Si vous souhaitez utiliser la persistance des données :

```bash
# Connectez-vous à PostgreSQL
psql -U postgres

# Créez la base de données
CREATE DATABASE transcription_db;

# Exécutez le script SQL
\c transcription_db
\i backend/SQL_File.sql
```

---

## 🎯 Utilisation

### Utilisation Basique

```python
from backend.IA.pipeline_service import TranscriptionPipeline

# Initialiser le pipeline avec votre fichier audio
pipeline = TranscriptionPipeline(
    audio_file="chemin/vers/votre/audio.m4a",
    output_dir="./resultats"
)

# Lancer le traitement complet
results = pipeline.run(save_intermediary_files=True)

# Accéder aux résultats
print(results["cleaned_text"])
print(results["summary"])
print(results["pdf_path"])
```

### Exécution via le Script Principal

```bash
python main.py
```

---

## 📊 Pipeline de Traitement

Le système suit un pipeline en 6 étapes :

```
1. 🎤 Transcription + Diarisation
   ↓ (Groq Whisper + Pyannote)
   
2. 📄 Extraction du Texte Pur
   ↓ (Suppression des métadonnées)
   
3. 🧹 Nettoyage du Texte
   ↓ (Suppression hésitations, correction ponctuation)
   
4. 📋 Génération du Résumé
   ↓ (Groq LLM + BART)
   
5. 👥 Organisation par Locuteur
   ↓ (Séparation et résumés individuels)
   
6. 💾 Export PDF/DOCX
   ↓ (Génération des fichiers finaux)
```

---

## 📁 Structure de la Base de Données

### Tables Principales

**utilisateurs** : Gestion des utilisateurs
```sql
- id_user (PRIMARY KEY)
- name
- email
- password
```

**fichiers_audio** : Enregistrements audio uploadés
```sql
- id_audio (PRIMARY KEY)
- id_user (FOREIGN KEY)
- title
- file_path
- status
- num_speakers
- duration
- date_upload
```

**transcriptions** : Segments de transcription
```sql
- id_transcription (PRIMARY KEY)
- id_audio (FOREIGN KEY)
- text_brut
- start_time
- end_time
- speaker
- sequence_number
```

**resumes** : Résumés générés
```sql
- id_resume (PRIMARY KEY)
- id_audio (FOREIGN KEY)
- summary_text
- type_resume ('general' ou 'par_speaker')
- speaker
```

---

## 🔧 Modules Détaillés

### `transcriptiondiarization.py`
- Convertit l'audio en WAV (16kHz, mono)
- Utilise **Groq Whisper** pour la transcription
- Utilise **Pyannote** pour identifier les locuteurs
- Fusionne timestamps + speakers + texte

### `cleaning.py`
- Supprime les mots de remplissage (euh, hum, etc.)
- Corrige la ponctuation
- Gère les connecteurs logiques
- Élimine les répétitions

### `resume.py`
- **Méthode 1** : Résumé local avec BART (Facebook)
- **Méthode 2** : Compte-rendu structuré avec Groq (LLaMA 3.3)
- Format professionnel avec sections :
  - Résumé exécutif
  - Contexte et objectif
  - Points clés
  - Décisions prises
  - Actions à entreprendre
  - Prochaines étapes

### `pipeline_service.py`
- Classe `TranscriptionPipeline` qui orchestre tout le processus
- Gère les fichiers intermédiaires
- Retourne un dictionnaire de résultats complet

### `save_pdf.py`
- Export en PDF avec FPDF
- Export en DOCX avec python-docx

---

## 🐛 Résolution de Problèmes

### Erreur : "GROQ_API_KEY manquante"
➡️ Vérifiez que votre fichier `.env` est bien à la racine et contient les clés

### Erreur : "ffmpeg not found"
➡️ Installez FFmpeg (voir section Installation)

### Erreur lors de la diarisation
➡️ Vérifiez que vous avez accepté les conditions sur le modèle Pyannote :
   [https://huggingface.co/pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)

### Performance lente
➡️ La diarisation et la transcription peuvent prendre du temps selon la longueur de l'audio
➡️ Utilisez un GPU si disponible (modification du code nécessaire)

---

## 🤝 Contribution

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Pushez vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

---

## 📝 TODO / Améliorations Futures

- [ ] Interface web avec FastAPI ou Flask
- [ ] Support de plus de langues
- [ ] Intégration d'un système d'authentification complet
- [ ] Tableau de bord utilisateur
- [ ] Export en formats supplémentaires (JSON, Markdown)
- [ ] Amélioration de la détection des speakers (noms réels)
- [ ] Support GPU pour accélérer le traitement

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 👥 Auteurs

Développé par l'équipe MeetRecap

---

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation des APIs utilisées

---
