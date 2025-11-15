# 🎤 MeetVocal - Système de Transcription et Analyse de Réunions

Application web complète pour la transcription automatique de réunions avec diarisation (identification des locuteurs), génération de résumés et export en PDF/Word.

## 📋 Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [API Endpoints](#api-endpoints)
- [Structure du projet](#structure-du-projet)
- [Technologies utilisées](#technologies-utilisées)
- [Dépannage](#dépannage)

---

## ✨ Fonctionnalités

### 🎯 Pipeline de Transcription
- **Upload de fichiers audio** depuis votre PC (MP3, WAV, M4A, OGG, FLAC)
- **Transcription automatique** avec Whisper AI
- **Diarisation** : identification automatique des différents locuteurs
- **Nettoyage du texte** : suppression des répétitions et hésitations
- **Génération de résumés** : résumé général + résumés par locuteur
- **Export automatique** en PDF et Word

### 👥 Gestion
- **Utilisateurs** : création et gestion des utilisateurs
- **Réunions** : création et suivi des réunions
- **Segments** : stockage des segments transcrits avec timestamps
- **Résumés** : consultation des résumés générés

### 📊 Interface
- Dashboard avec statistiques en temps réel
- Barre de progression pour l'upload
- Interface moderne et responsive
- Notifications en temps réel

---

## 🏗️ Architecture
```
Frontend (React) <---> Backend (FastAPI) <---> Database (SQLite)
                              |
                              v
                    Pipeline IA (Whisper + Pyannote)
                              |
                              v
                    Exports (PDF + Word)
```

---

## 📦 Prérequis

- **Python** : 3.8 ou supérieur
- **FFmpeg** (pour le traitement audio)
- **Compte Hugging Face** (pour les modèles IA)

---

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone https://github.com/mounia000/transcription_meetvocal.git
cd transcription_meetvocal
```

### 2. Créer l'environnement virtuel
```bash
# Avec Anaconda (recommandé)
conda create -n nom_env python=3.10
conda activate nom_env

# Ou avec venv
python -m venv nom_env
# Windows
meet\Scripts\activate
# Linux/Mac
source nom_env/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Installer FFmpeg

**Windows :**
```bash
# Avec Chocolatey
choco install ffmpeg

# Ou télécharger depuis : https://ffmpeg.org/download.html
```

**Linux :**
```bash
sudo apt-get install ffmpeg
```

**Mac :**
```bash
brew install ffmpeg
```

### 5. Configuration Hugging Face

1. Créez un compte sur [Hugging Face](https://huggingface.co/)
2. Acceptez les conditions pour :
   - [Pyannote Segmentation](https://huggingface.co/pyannote/segmentation)
   - [Pyannote Speaker Diarization](https://huggingface.co/pyannote/speaker-diarization)
3. Créez un token d'accès : https://huggingface.co/settings/tokens

### 6. Fichier `.env`

Créez un fichier `.env` à la racine du projet :
```env
HUGGINGFACE_TOKEN=votre_token_ici
GROQ_API_KEY=votre_cle_ici
```

## 🎮 Utilisation

### 1. Lancer le Backend
```bash
# Depuis la racine du projet
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

Le backend sera accessible sur : `http://localhost:8000`

### 2. Lancer le Frontend

**Option A : Serveur Python (Recommandé)**
```bash
cd frontend
python -m http.server 3000
```

**Option B : Node.js**
```bash
cd frontend
npx serve -p 3000
```

**Option C : Live Server (VS Code)**
- Installez l'extension "Live Server"
- Clic droit sur `frontend/index.html` > "Open with Live Server"

Le frontend sera accessible sur : `http://localhost:3000`

### 3. Utiliser l'application

#### 📊 Tableau de bord
- Vue d'ensemble des statistiques
- Réunions récentes
- Statut du système

#### 🎤 Transcription
1. Cliquez sur l'onglet **"Transcription"**
2. Cliquez sur la zone d'upload
3. Sélectionnez un fichier audio (MP3, WAV, M4A, OGG, FLAC)
4. Cliquez sur **"Lancer le Pipeline"**
5. Attendez la fin du traitement (barre de progression)
6. Les fichiers PDF et Word seront générés automatiquement

#### 👥 Utilisateurs
1. Allez dans l'onglet **"Utilisateurs"**
2. Remplissez le formulaire (nom, email)
3. Cliquez sur **"Créer l'Utilisateur"**

#### 📅 Réunions
1. Allez dans l'onglet **"Réunions"**
2. Remplissez le formulaire (titre, date, durée)
3. Cliquez sur **"Créer la Réunion"**

---

## 🔌 API Endpoints

### Health Check
```http
GET /health
```

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : Framework web moderne et rapide
- **SQLAlchemy** : ORM pour la base de données
- **Uvicorn** : Serveur ASGI
- **OpenAI Whisper** : Transcription audio
- **Pyannote.audio** : Diarisation des locuteurs
- **PyTorch** : Deep learning
- **FPDF** : Génération de PDF
- **python-docx** : Génération de Word

### Frontend
- **React 18** : Framework JavaScript
- **Tailwind CSS** : Framework CSS
- **Fetch API** : Requêtes HTTP

### Base de données
- **SQLite** : Base de données légère

## 📝 Notes importantes

### Performance
- **Première transcription** : Peut prendre 2-5 minutes (téléchargement des modèles)
- **Transcriptions suivantes** : Plus rapides (modèles en cache)
- **Diarisation** : Gourmande en ressources (CPU/GPU recommandé)

### Limitations
- Formats supportés : MP3, WAV, M4A, OGG, FLAC
- Langues : Toutes (Whisper supporte 99 langues)



**Fait par  Youssouf,Hafsa,Mounia,Manal**