# 🚀 GUIDE DE DÉMARRAGE RAPIDE

## ⚡ Lancer le projet en 5 minutes

### 1️⃣ Prérequis

Assurez-vous d'avoir :
- ✅ Node.js 18+ installé (`node --version`)
- ✅ npm installé (`npm --version`)
- ✅ Le backend FastAPI en cours d'exécution sur `http://localhost:8000`

### 2️⃣ Installation

```bash
# 1. Aller dans le dossier frontend
cd frontend-transcription

# 2. Installer les dépendances
npm install

# 3. Créer le fichier de configuration
cp .env.example .env

# 4. Lancer le serveur de développement
npm run dev
```

### 3️⃣ Accéder à l'application

Ouvrez votre navigateur : **http://localhost:3000**

### 4️⃣ Premier test

1. **Créer un compte**
   - Cliquez sur "S'inscrire"
   - Remplissez le formulaire
   - Validez

2. **Se connecter**
   - Utilisez vos identifiants
   - Vous êtes redirigé vers le dashboard

3. **Uploader un fichier**
   - Cliquez sur la zone d'upload
   - Sélectionnez un fichier audio (MP3, WAV, M4A, OGG, FLAC)
   - Attendez la fin de l'upload
   - Le traitement démarre automatiquement (5-15 minutes)

4. **Voir le résultat**
   - Une fois le statut "Terminé", cliquez sur "Voir"
   - Explorez les onglets : Résumé / Par participant / Transcription
   - Téléchargez le PDF si besoin

---

## 🔍 Vérification du Backend

Avant de lancer le frontend, vérifiez que le backend fonctionne :

```bash
# Tester l'API
curl http://localhost:8000/health

# Résultat attendu :
# {"status":"ok","database":"✅ Connected","env_loaded":"✅"}
```

Si vous obtenez une erreur, assurez-vous que :
1. Le backend est bien lancé
2. PostgreSQL est en cours d'exécution
3. Les variables d'environnement du backend sont correctes

---

## 🛠️ Commandes utiles

```bash
# Développement
npm run dev

# Build pour production
npm run build

# Prévisualiser le build
npm run preview

# Installer une nouvelle dépendance
npm install nom-du-package
```

---

## 📁 Structure des fichiers clés

```
frontend-transcription/
├── src/
│   ├── pages/
│   │   ├── LoginPage.jsx         # 🔐 Page de connexion
│   │   ├── RegisterPage.jsx      # 📝 Page d'inscription
│   │   ├── DashboardPage.jsx     # 🏠 Dashboard principal
│   │   └── TranscriptionDetailPage.jsx  # 📄 Détails transcription
│   ├── services/
│   │   └── api.js                # 🔌 Communication avec le backend
│   ├── contexts/
│   │   └── AuthContext.jsx       # 👤 Gestion authentification
│   └── App.jsx                   # 🚦 Routing principal
└── .env                          # ⚙️ Configuration
```

---

## 🎯 Points d'attention

### CORS
Le backend doit avoir CORS activé (déjà configuré dans votre `main_simple.py`) :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### JWT
Les tokens JWT sont automatiquement gérés par le frontend et stockés dans `localStorage`.

### Uploads
Les uploads sont envoyés en `multipart/form-data` avec une barre de progression.

---

## ❓ Problèmes fréquents

### ❌ "Cannot connect to backend"

**Solution** :
1. Vérifiez que le backend tourne : `curl http://localhost:8000/health`
2. Vérifiez l'URL dans `.env` : `VITE_API_URL=http://localhost:8000`
3. Redémarrez le frontend : `npm run dev`

### ❌ "401 Unauthorized"

**Solution** :
1. Reconnectez-vous (le token a peut-être expiré)
2. Vérifiez que la `SECRET_KEY` du backend n'a pas changé

### ❌ "Upload failed"

**Solution** :
1. Vérifiez le format du fichier (MP3, WAV, M4A, OGG, FLAC uniquement)
2. Vérifiez la taille (max 500MB)
3. Consultez les logs du backend

### ❌ "npm install" échoue

**Solution** :
```bash
# Nettoyer le cache npm
npm cache clean --force

# Supprimer node_modules et package-lock.json
rm -rf node_modules package-lock.json

# Réinstaller
npm install
```

---

## 🎉 Vous êtes prêt !

Votre application de transcription audio est maintenant opérationnelle !

**Prochaines étapes** :
- 📤 Testez l'upload d'un fichier audio
- 📊 Explorez les différentes vues (résumé, participants, transcription)
- 💾 Téléchargez le PDF généré
- 🎨 Personnalisez le design si nécessaire

**Besoin d'aide ?**
Consultez le `README.md` complet pour plus de détails.
