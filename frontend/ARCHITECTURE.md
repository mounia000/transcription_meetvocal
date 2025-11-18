# 🏗️ ARCHITECTURE COMPLÈTE DU SYSTÈME

## 📊 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR                               │
│                     (Navigateur Web)                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/REST
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      FRONTEND                                    │
│                   (React + Vite)                                 │
│                                                                  │
│  • Pages : Login, Register, Dashboard, Detail                   │
│  • Services : API Client (Axios)                                │
│  • Context : Authentication                                      │
│  • Styling : Tailwind CSS                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/REST + JWT
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      BACKEND API                                 │
│                   (FastAPI + Python)                             │
│                                                                  │
│  • Auth : JWT avec bcrypt                                       │
│  • Endpoints : /register, /login, /upload, /fichiers            │
│  • CORS : Activé pour le frontend                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          │              │              │
┌─────────▼─────┐ ┌─────▼─────┐ ┌──────▼──────┐
│  PostgreSQL   │ │  Pipeline  │ │  File       │
│  Database     │ │  IA        │ │  Storage    │
│               │ │            │ │             │
│ • users       │ │ • Whisper  │ │ • uploads/  │
│ • fichiers    │ │ • Pyannote │ │ • outputs/  │
│ • transcripts │ │ • Groq     │ │             │
│ • resumes     │ │ • BART     │ │             │
└───────────────┘ └────────────┘ └─────────────┘
```

---

## 🎯 Flux de données complet

### 1️⃣ Inscription / Connexion

```
User → Frontend → Backend → PostgreSQL
                      ↓
                   JWT Token
                      ↓
                  Frontend
                      ↓
                 localStorage
```

**Détails** :
- Le mot de passe est hashé avec bcrypt
- Un token JWT est généré (validité 24h)
- Le token est stocké dans localStorage
- Chaque requête authentifiée inclut : `Authorization: Bearer <token>`

---

### 2️⃣ Upload et traitement d'un fichier audio

```
User sélectionne fichier
         ↓
Frontend (Upload avec progression)
         ↓
Backend /upload endpoint
         ↓
Sauvegarde fichier → uploads/
         ↓
Création entrée DB (status: processing)
         ↓
┌────────────────────────────────────┐
│    PIPELINE IA (5-15 minutes)      │
│                                    │
│ 1. Transcription (Whisper/Groq)   │
│ 2. Diarisation (Pyannote)         │
│ 3. Extraction texte                │
│ 4. Nettoyage                       │
│ 5. Résumé (Groq/BART)              │
│ 6. Génération PDF/DOCX             │
└────────────────────────────────────┘
         ↓
Mise à jour DB (status: completed)
         ↓
Fichiers sauvegardés → outputs/audio_<id>/
         ↓
Retour au frontend (JSON)
```

---

### 3️⃣ Consultation des résultats

```
User → Dashboard
         ↓
GET /fichiers
         ↓
Liste des transcriptions
         ↓
User clique "Voir"
         ↓
GET /fichiers/{id}/compte-rendu
         ↓
Affichage :
  • Résumé général
  • Résumés par participant
  • Transcription complète avec timestamps
         ↓
User clique "PDF"
         ↓
GET /fichiers/{id}/pdf
         ↓
Téléchargement du fichier
```

---

## 🔐 Sécurité

### Backend
- ✅ Mots de passe hashés avec bcrypt
- ✅ Tokens JWT signés avec SECRET_KEY
- ✅ Validation des types de fichiers
- ✅ Vérification de la propriété des fichiers
- ✅ CORS configuré

### Frontend
- ✅ Routes protégées avec `<ProtectedRoute>`
- ✅ Token stocké en localStorage
- ✅ Déconnexion automatique si token invalide
- ✅ Intercepteur Axios pour les erreurs 401

---

## 💾 Base de données PostgreSQL

### Tables principales

#### 1. `utilisateurs`
```sql
CREATE TABLE utilisateurs (
    id_user SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `fichiers_audio`
```sql
CREATE TABLE fichiers_audio (
    id_audio SERIAL PRIMARY KEY,
    id_user INTEGER REFERENCES utilisateurs(id_user),
    title VARCHAR(500),
    file_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'processing',
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration FLOAT,
    num_speakers INTEGER
);
```

#### 3. `transcriptions`
```sql
CREATE TABLE transcriptions (
    id_transcription SERIAL PRIMARY KEY,
    id_audio INTEGER REFERENCES fichiers_audio(id_audio),
    text_brut TEXT,
    start_time FLOAT,
    end_time FLOAT,
    speaker VARCHAR(100),
    sequence_number INTEGER
);
```

#### 4. `resumes`
```sql
CREATE TABLE resumes (
    id_resume SERIAL PRIMARY KEY,
    id_audio INTEGER REFERENCES fichiers_audio(id_audio),
    summary_text TEXT,
    type_resume VARCHAR(50),
    speaker VARCHAR(100)
);
```

---

## 🤖 Pipeline IA

### Étapes du traitement

1. **Transcription + Diarisation**
   - Outil : Whisper (Groq) + Pyannote
   - Input : Fichier audio
   - Output : Texte avec timestamps et speakers
   - Format : `[00:00.0 - 00:06.5] [SPEAKER_00] Texte...`

2. **Extraction du texte pur**
   - Suppression des métadonnées
   - Conservation uniquement du texte parlé

3. **Nettoyage**
   - Suppression des mots de remplissage ("euh", "hum", etc.)
   - Correction de la ponctuation
   - Gestion des majuscules

4. **Génération du résumé**
   - Résumé général (Groq LLaMA)
   - Résumés par participant (BART)
   - Format structuré professionnel

5. **Génération des documents**
   - PDF avec compte-rendu complet
   - DOCX pour édition

---

## 📡 API REST - Endpoints

### Authentification

#### POST `/register`
```json
Request:
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}

Response:
{
  "id_user": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "message": "✅ Compte créé avec succès"
}
```

#### POST `/login`
```json
Request:
{
  "email": "john@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id_user": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### Gestion des fichiers

#### POST `/upload`
```
Headers:
Authorization: Bearer <token>
Content-Type: multipart/form-data

Body:
- file: <audio_file>
- title: "Réunion Q1 2024"

Response:
{
  "message": "✅ Compte-rendu généré avec succès !",
  "id_audio": 1,
  "duree_minutes": 15.5,
  "nombre_participants": 3,
  "resume_general": "...",
  "resumes_par_participant": {...},
  "transcription_complete": {...}
}
```

#### GET `/fichiers`
```
Headers:
Authorization: Bearer <token>

Response:
[
  {
    "id_audio": 1,
    "title": "Réunion Q1 2024",
    "status": "completed",
    "date_upload": "2024-01-15T10:30:00",
    "duration": 930.5,
    "num_speakers": 3
  }
]
```

#### GET `/fichiers/{id}/compte-rendu`
```
Headers:
Authorization: Bearer <token>

Response:
{
  "titre": "Réunion Q1 2024",
  "date": "2024-01-15",
  "duree_minutes": 15.5,
  "nombre_participants": 3,
  "resume_general": "...",
  "resumes_par_participant": {...},
  "transcription_complete": [...]
}
```

#### GET `/fichiers/{id}/pdf`
```
Headers:
Authorization: Bearer <token>

Response:
Fichier PDF (binary)
```

---

## 🎨 Stack Technique

### Frontend
- **Framework** : React 18
- **Build Tool** : Vite
- **Routing** : React Router v6
- **HTTP** : Axios
- **Styling** : Tailwind CSS
- **Icons** : Lucide React
- **State** : Context API

### Backend
- **Framework** : FastAPI
- **Language** : Python 3.10+
- **Auth** : JWT + bcrypt
- **Database** : PostgreSQL + psycopg2
- **CORS** : fastapi.middleware.cors

### IA/ML
- **Transcription** : Whisper (Groq API)
- **Diarisation** : Pyannote Audio
- **Résumé** : Groq LLaMA + BART
- **PDF/DOCX** : fpdf + python-docx

### Infrastructure
- **Database** : PostgreSQL 14+
- **Storage** : Système de fichiers local
- **Environment** : python-dotenv

---

## 🔄 Workflow de développement

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
uvicorn app.main_simple:app --reload --port 8000
```

### Frontend
```bash
cd frontend-transcription
npm install
npm run dev
```

### Database
```bash
psql -U postgres
CREATE DATABASE transcription_db;
\c transcription_db
# Exécuter les scripts SQL de création de tables
```

---

## 📈 Évolutions possibles

### Court terme
- [ ] Système de notifications en temps réel (WebSocket)
- [ ] Pagination de la liste des fichiers
- [ ] Filtres et recherche dans les transcriptions
- [ ] Support de plus de langues

### Moyen terme
- [ ] Édition en ligne des transcriptions
- [ ] Partage de comptes-rendus
- [ ] Export en d'autres formats (TXT, JSON)
- [ ] Dashboard d'analytics

### Long terme
- [ ] Application mobile (React Native)
- [ ] API publique pour intégrations
- [ ] Multi-tenant / organisations
- [ ] IA conversationnelle sur les transcriptions

---

## 📚 Documentation complémentaire

- [README Frontend](./README.md)
- [Guide de démarrage rapide](./QUICKSTART.md)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation React](https://react.dev/)
- [Documentation Tailwind CSS](https://tailwindcss.com/)
