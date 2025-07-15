# 🚀 API Assistant Nouveaux Arrivants France

## Description
API pour aider les nouveaux arrivants en France avec des informations actualisées sur les démarches administratives, logement, santé, emploi, etc.

## 🔗 Base URL
```
http://127.0.0.1:8080
```

## 📋 Endpoints Disponibles

### 1. Status de l'API
```http
GET /api/status
```

**Réponse :**
```json
{
  "status": "active",
  "timestamp": "2025-01-14T12:00:00.000Z",
  "version": "1.0.0",
  "service": "Assistant Nouveaux Arrivants France"
}
```

### 2. Chat avec l'Assistant
```http
POST /api/chat
```

**Corps de la requête :**
```json
{
  "message": "Comment obtenir une carte vitale ?",
  "context": "Je viens d'arriver d'Allemagne" // optionnel
}
```

**Réponse :**
```json
{
  "success": true,
  "response": "🏥 **Obtenir votre carte vitale**\n\n...",
  "timestamp": "2025-01-14T12:00:00.000Z"
}
```

### 3. Catégories d'Aide
```http
GET /api/categories
```

**Réponse :**
```json
{
  "success": true,
  "categories": [
    {
      "id": "sante",
      "name": "🏥 Santé",
      "description": "Sécurité sociale, médecins, urgences, carte vitale"
    },
    // ... autres catégories
  ]
}
```

### 4. Documentation
```http
GET /api/help
```

Retourne la documentation complète de l'API.

## 🛠️ Exemples d'utilisation

### Python avec requests
```python
import requests

# Status
response = requests.get('http://127.0.0.1:8080/api/status')
print(response.json())

# Chat
response = requests.post('http://127.0.0.1:8080/api/chat', json={
    'message': 'Comment ouvrir un compte bancaire en France ?',
    'context': 'Étudiant étranger'
})
print(response.json())
```

### JavaScript/Fetch
```javascript
// Status
fetch('http://127.0.0.1:8080/api/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Chat
fetch('http://127.0.0.1:8080/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Quelles sont les étapes pour obtenir un permis de conduire ?',
    context: 'J\'ai un permis européen'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL
```bash
# Status
curl -X GET http://127.0.0.1:8080/api/status

# Chat
curl -X POST http://127.0.0.1:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Comment m'\''inscrire à Pôle Emploi ?",
    "context": "Je viens de terminer mes études"
  }'
```

## 🎯 Catégories de Questions Supportées

- **🏥 Santé** : Sécurité sociale, médecins, urgences, carte vitale
- **🏠 Logement** : Recherche, droits, aides au logement, CAF
- **📋 Administratif** : Cartes d'identité, permis, inscriptions officielles
- **⚖️ Juridique** : Droits, démarches légales, recours
- **💼 Emploi** : Recherche d'emploi, formations, droits du travail
- **🎓 Éducation** : Inscriptions scolaires, universités, formations
- **🚗 Transport** : Permis de conduire, transports en commun
- **💰 Finances** : Banques, impôts, aides sociales

## ⚠️ Gestion d'Erreurs

### Erreurs Communes
```json
// Message vide
{
  "error": "Le champ \"message\" est requis et ne peut pas être vide"
}

// Format JSON invalide
{
  "error": "Format JSON requis"
}

// Erreur serveur
{
  "success": false,
  "error": "Erreur serveur: ..."
}
```

## 🔄 Compatibilité

L'ancien endpoint `/chat` reste disponible pour la compatibilité avec les versions précédentes.

## 📊 Logging

L'API enregistre automatiquement :
- Les requêtes reçues
- Les erreurs survenues
- L'activité générale

Les logs sont visibles dans la console lors du démarrage avec `uv run python app.py`.

## 🚀 Démarrage

```bash
# Installer les dépendances
uv sync

# Configurer les variables d'environnement
cp sample.env .env
# Éditer .env avec vos clés API

# Lancer l'application
uv run python app.py
```

L'API sera disponible sur `http://127.0.0.1:8080` 