# 🚀 API Assistant Nouveaux Arrivants France

Assistant IA avec API REST pour aider les nouveaux arrivants en France avec des informations actualisées en temps réel via les outils Bright Data.

## 🎯 Fonctionnalités

- **API REST complète** avec endpoints multiples
- **Assistant IA spécialisé** pour les nouveaux arrivants en France
- **Recherche web en temps réel** via Bright Data MCP
- **Interface web moderne** et API programmatique
- **Documentation automatique** intégrée
- **Gestion d'erreurs robuste** et logging

## 📋 Catégories d'Aide

- 🏥 **Santé** : Sécurité sociale, carte vitale, médecins
- 🏠 **Logement** : Recherche, aides CAF, droits locataires
- 📋 **Administratif** : Cartes d'identité, préfecture, inscriptions
- ⚖️ **Juridique** : Droits, démarches légales, recours
- 💼 **Emploi** : Pôle Emploi, formations, droits du travail
- 🎓 **Éducation** : Inscriptions scolaires, universités
- 🚗 **Transport** : Permis de conduire, transports publics
- 💰 **Finances** : Banques, impôts, aides sociales

## 🚀 Installation et Configuration

1. **Cloner le projet**
   ```bash
   git clone <repository-url>
   cd BrightDataMCPServerAgent
   ```

2. **Configurer les variables d'environnement**
   ```bash
   cp sample.env .env
   # Éditer .env avec vos clés API Bright Data
   ```

3. **Installer les dépendances**
   ```bash
   uv sync
   ```

4. **Lancer l'application**
   ```bash
   uv run python app.py
   ```

L'API sera disponible sur `http://127.0.0.1:8080`

## 🔗 Endpoints API Disponibles

### Status de l'API
```http
GET /api/status
```

### Chat avec l'Assistant
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Comment obtenir une carte vitale ?",
  "context": "Je viens d'arriver d'Allemagne"
}
```

### Catégories d'Aide
```http
GET /api/categories
```

### Documentation Complète
```http
GET /api/help
```

## 🧪 Tests

### Lancer les tests automatisés
```bash
uv run python test_api.py
```

### Tests disponibles
- **Tests automatiques complets** : Teste tous les endpoints
- **Mode interactif** : Testez avec vos propres questions
- **Test rapide** : Vérification de base

## 📖 Documentation

- **Documentation API** : Consultez `/api/help` ou le fichier `api_documentation.md`
- **Interface Web** : Accessible sur `http://127.0.0.1:8080`

## 🔧 Utilisation Programmatique

### Version ligne de commande
```bash
# Utiliser l'assistant en mode CLI
uv run python cli.py
```

### Python
```python
import requests

# Status de l'API
response = requests.get('http://127.0.0.1:8080/api/status')

# Question à l'assistant
response = requests.post('http://127.0.0.1:8080/api/chat', json={
    'message': 'Comment ouvrir un compte bancaire en France ?',
    'context': 'Étudiant étranger'
})
```

### JavaScript
```javascript
// Question à l'assistant
fetch('http://127.0.0.1:8080/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
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
  -d '{"message": "Comment m'\''inscrire à Pôle Emploi ?"}'
```

## 🛠️ Architecture

- **Flask** : Framework web principal
- **MCP (Model Context Protocol)** : Interface avec Bright Data
- **Claude Anthropic** : Modèle de langage IA
- **Bright Data** : Outils de recherche web en temps réel

## 📊 Logging et Monitoring

L'application enregistre automatiquement :
- Requêtes reçues
- Erreurs et exceptions
- Performance des réponses
- Activité générale

## 🔄 Compatibilité

L'ancien endpoint `/chat` reste disponible pour maintenir la compatibilité avec les versions précédentes.

## 🤝 Support

Pour toute question ou problème :
1. Consultez la documentation API : `/api/help`
2. Vérifiez les logs de l'application
3. Testez avec le script `test_api.py`