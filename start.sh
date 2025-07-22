#!/bin/bash

# Script de démarrage pour l'Assistant Nouveaux Arrivants France

echo "🚀 Démarrage de l'Assistant Nouveaux Arrivants France..."

# Vérifier que les variables d'environnement sont définies
if [ -z "$API_TOKEN" ]; then
    echo "❌ Erreur: API_TOKEN non défini"
    exit 1
fi

if [ -z "$BROWSER_AUTH" ]; then
    echo "❌ Erreur: BROWSER_AUTH non défini"
    exit 1
fi

if [ -z "$WEB_UNLOCKER_ZONE" ]; then
    echo "❌ Erreur: WEB_UNLOCKER_ZONE non défini"
    exit 1
fi

echo "✅ Variables d'environnement configurées"

# Installer les dépendances npm si package.json existe
if [ -f "package.json" ]; then
    echo "📦 Installation des dépendances npm..."
    npm install --production
    echo "✅ Dépendances npm installées"
fi

# Démarrer l'application Python
echo "🐍 Démarrage de l'application Python..."
python app.py 