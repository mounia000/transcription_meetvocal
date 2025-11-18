#!/bin/bash

echo "🚀 Installation du Frontend de Transcription Audio"
echo "=================================================="
echo ""

# Vérifier Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js n'est pas installé."
    echo "📥 Installez Node.js depuis : https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Vérifier npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm n'est pas installé."
    exit 1
fi

echo "✅ npm version: $(npm --version)"
echo ""

# Installer les dépendances
echo "📦 Installation des dépendances..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

echo ""
echo "✅ Dépendances installées avec succès !"
echo ""

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "⚙️  Création du fichier .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé"
else
    echo "ℹ️  Le fichier .env existe déjà"
fi

echo ""
echo "🎉 Installation terminée !"
echo ""
echo "📝 Prochaines étapes :"
echo "  1. Vérifiez que le backend tourne sur http://localhost:8000"
echo "  2. Lancez le frontend avec : npm run dev"
echo "  3. Accédez à l'application : http://localhost:3000"
echo ""
echo "📚 Documentation disponible :"
echo "  - README.md          : Documentation complète"
echo "  - QUICKSTART.md      : Guide de démarrage rapide"
echo "  - ARCHITECTURE.md    : Architecture système"
echo ""
