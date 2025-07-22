from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import asyncio
import os
import logging
from datetime import datetime

load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin

# Configuration du modèle
model = ChatAnthropic(
    model="claude-3-5-sonnet-20240620",
    max_tokens=6000,  # Limite la réponse à 6000 tokens
    temperature=0.1,  # Réponses plus précises  
    timeout=60.0      # Timeout après 60 secondes
)

server_params = StdioServerParameters(
    command="npx",
    env={
        "API_TOKEN": os.getenv("API_TOKEN"),
        "BROWSER_AUTH": os.getenv("BROWSER_AUTH"),
        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
    },
    args=["@brightdata/mcp@2.4.1"],
)

# Prompt système enrichi
SYSTEM_PROMPT = """Tu es un assistant spécialisé dans l'aide aux nouveaux arrivants en France. 

Tu aides les personnes qui viennent d'arriver sur diverses thématiques :
- 🏥 Santé (sécurité sociale, médecins, urgences)
- 🏠 Logement (recherche, droits, aides au logement)
- 📋 Administratif (cartes d'identité, permis, inscriptions)
- ⚖️ Juridique (droits, démarches légales, recours)
- 💼 Emploi (recherche d'emploi, formations, droits du travail)
- 🎓 Éducation (inscriptions scolaires, universités, formations)
- 🚗 Transport (permis de conduire, transports en commun)
- 💰 Finances (banques, impôts, aides sociales)

MÉTHODE DE RECHERCHE OBLIGATOIRE :
1. 🔍 TOUJOURS commencer par search_engine pour trouver les URLs pertinentes
2. 📄 ENSUITE utiliser scrape_as_markdown sur les URLs officielles trouvées
3. 🎯 Priorité aux sites : service-public.fr, ameli.fr, pole-emploi.fr, caf.fr, etc.
4. 📋 Si scrape_as_markdown échoue, utiliser scrape_as_html ou extract
5. ✅ OBLIGATOIRE : Récupérer le contenu COMPLET des pages, pas juste les résultats de recherche

STRATÉGIE POUR SITES DYNAMIQUES :
Si scrape_as_markdown/scrape_as_html échouent ou retournent peu de contenu :
1. 🌐 Utiliser scraping_browser_navigate(URL) pour charger la page avec JavaScript
2. ⏱️ Attendre que le contenu se charge (les outils attendent automatiquement)
3. 🔗 Utiliser scraping_browser_links() pour voir les éléments interactifs
4. 🖱️ Si nécessaire, utiliser scraping_browser_click(selector) pour interactions
5. 📱 Ces outils gèrent : JavaScript, React, Vue, Angular, contenu dynamique

SITES PROBLÉMATIQUES COURANTS :
- Sites gouvernementaux avec JavaScript : utiliser scraping_browser_navigate
- Formulaires dynamiques : scraping_browser_click pour navigation
- Contenu chargé par AJAX : les outils navigateur attendent le chargement
- Sites avec authentification : scraping_browser peut gérer les cookies

RÈGLES IMPORTANTES :
1. Réponds toujours en français, de manière claire et accessible
2. WORKFLOW OBLIGATOIRE : search_engine → scrape_as_markdown → (si échec: scraping_browser_navigate) → réponse structurée
3. OBLIGATOIRE : Cite TOUJOURS tes sources à la fin de chaque réponse
4. OBLIGATOIRE : Formate ta réponse en Markdown structuré et propre
5. Propose des actions concrètes et des liens SPÉCIFIQUES (pas génériques)
6. Donne des informations DÉTAILLÉES extraites du contenu scraped
7. Sois empathique et rassurant
8. Donne des liens directs vers les formulaires, pages spécifiques, pas les pages d'accueil
9. Indique le nom exact des documents à télécharger avec leurs URLs précises

EXEMPLE DE WORKFLOW :
- Question: "Comment obtenir une carte vitale ?"
- Étape 1: search_engine("carte vitale obtenir France")
- Étape 2: scrape_as_markdown(https://www.service-public.fr/particuliers/vosdroits/F750)
- Étape 3: Si peu de contenu → scraping_browser_navigate(URL) pour JavaScript
- Étape 4: Extraire les informations détaillées et formater la réponse

EXEMPLE SITE DYNAMIQUE :
- Question: "Comment s'inscrire sur Parcoursup ?"
- Étape 1: search_engine("Parcoursup inscription étapes")
- Étape 2: scrape_as_markdown échoue (site React)
- Étape 3: scraping_browser_navigate(https://www.parcoursup.fr)
- Étape 4: scraping_browser_links() pour voir les sections
- Étape 5: Extraire le contenu complet et répondre

FORMAT MARKDOWN OBLIGATOIRE :
- Utilise des titres avec # ## ### pour structurer
- Utilise des listes à puces - ou numérotées 1. 2. 3.
- Utilise **gras** pour les éléments importants
- Utilise `code` pour les noms de formulaires/documents
- Utilise > pour les citations importantes
- Utilise des tableaux | si nécessaire
- Utilise des émojis pour rendre visuellement agréable
- Structure logique : Titre principal → Sous-sections → Étapes → Sources

EXEMPLE DE STRUCTURE MARKDOWN :
```markdown
# 🏥 Titre Principal

## 📋 Sous-section 1

### Étapes à suivre :
1. **Première étape** : Description détaillée
   - Point important
   - Autre détail

2. **Deuxième étape** : Description
   - Élément à retenir

## ⚠️ Points importants

> **Attention** : Information cruciale à retenir

## 📚 Sources consultées

- [Nom PRÉCIS du document](URL-complète)
- [Autre source spécifique](URL-directe)
```

EXEMPLES de bons liens :
✅ [Formulaire Cerfa n°15186*03](https://www.service-public.fr/particuliers/vosdroits/R56618)
✅ [Prise RDV Préfecture Paris](https://www.rdv.paris.fr/prendre-rdv)
❌ Éviter : service-public.fr (trop générique)
"""

async def get_agent_response(user_message, context=None):
    """Fonction pour obtenir la réponse de l'agent"""
    try:
        # Vérifier la taille du message utilisateur
        if len(user_message) > 10000:  # ~7500 tokens approximativement
            return "❌ Votre message est trop long. Veuillez le raccourcir (maximum ~7500 tokens)."
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()
                    tools = await load_mcp_tools(session)
                    agent = create_react_agent(model, tools)

                    # Messages avec prompt système
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT}
                    ]
                    
                    # Ajouter le contexte si fourni
                    if context:
                        messages.append({"role": "system", "content": f"Contexte supplémentaire : {context}"})
                    
                    messages.append({"role": "user", "content": user_message})

                    # Log de la taille approximative des tokens
                    total_chars = sum(len(msg["content"]) for msg in messages)
                    estimated_tokens = total_chars // 4  # Approximation : 4 chars = 1 token
                    logger.info(f"📊 Estimation tokens input: ~{estimated_tokens}")

                    # Appel de l'agent
                    agent_response = await agent.ainvoke({"messages": messages})
                    
                    # Extraction de la réponse
                    ai_message = agent_response["messages"][-1].content
                    
                    # Log de la taille de la réponse
                    response_tokens = len(ai_message) // 4
                    logger.info(f"📊 Estimation tokens output: ~{response_tokens}")
                    
                    return ai_message
                    
                except Exception as mcp_error:
                    logger.error(f"Erreur MCP: {str(mcp_error)}")
                    if "List roots not supported" in str(mcp_error):
                        return "❌ Erreur de configuration MCP. Le serveur BrightData n'est pas compatible avec cette version. Veuillez contacter l'administrateur."
                    else:
                        raise mcp_error
                
    except Exception as e:
        import traceback
        logger.error(f"Erreur dans get_agent_response: {str(e)}\n{traceback.format_exc()}")
        error_msg = str(e).lower()
        if "tokens" in error_msg or "context" in error_msg or "limit" in error_msg:
            logger.error(f"❌ Erreur de tokens: {str(e)}")
            return f"❌ Limite de tokens atteinte. Essayez une question plus courte ou plus spécifique.\n\nDétails: {str(e)}"
        elif "rate" in error_msg or "529" in error_msg:
            logger.error(f"❌ Erreur de rate limiting: {str(e)}")
            return f"❌ Trop de requêtes simultanées. Veuillez patienter quelques secondes et réessayer.\n\nDétails: {str(e)}"
        elif "mcp" in error_msg or "brightdata" in error_msg:
            logger.error(f"❌ Erreur MCP/BrightData: {str(e)}")
            return f"❌ Erreur de configuration des outils de recherche web. Veuillez réessayer dans quelques instants.\n\nDétails: {str(e)}"
        else:
            logger.error(f"Erreur dans get_agent_response: {str(e)}")
            return f"❌ Erreur lors du traitement de votre demande : {str(e)}\n\nVeuillez vérifier que vos clés API sont correctement configurées dans le fichier .env"

# ============ ROUTES WEB ============

@app.route('/')
def index():
    """Page d'accueil avec interface web"""
    return render_template('index.html')

# ============ API ENDPOINTS ============

@app.route('/api/status', methods=['GET'])
def api_status():
    """Endpoint pour vérifier le statut de l'API"""
    return jsonify({
        'status': 'active',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'Assistant Nouveaux Arrivants France',
        'model_config': {
            'model': 'claude-3-5-sonnet-20240620',
            'max_tokens_output': 6000,
            'max_tokens_context': 200000,
            'temperature': 0.1,
            'timeout': '60s'
        },
        'token_limits': {
            'prompt_system_approx': '~2000 tokens',
            'user_message_max': '~7500 tokens', 
            'total_context_max': '200k tokens',
            'response_max': '6k tokens'
        }
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Endpoint principal pour les conversations"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Format JSON requis'}), 400
            
        user_message = data.get('message', '').strip()
        context = data.get('context', '')
        
        if not user_message:
            return jsonify({'error': 'Le champ "message" est requis et ne peut pas être vide'}), 400
        
        # Log de la requête
        logger.info(f"Nouvelle requête chat: {user_message[:100]}...")
        
        # Exécution asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(get_agent_response(user_message, context))
            
            return jsonify({
                'success': True,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Erreur dans api_chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/api/categories', methods=['GET'])
def api_categories():
    """Endpoint pour obtenir les catégories d'aide disponibles"""
    categories = [
        {
            'id': 'sante',
            'name': '🏥 Santé',
            'description': 'Sécurité sociale, médecins, urgences, carte vitale'
        },
        {
            'id': 'logement',
            'name': '🏠 Logement',
            'description': 'Recherche, droits, aides au logement, CAF'
        },
        {
            'id': 'administratif',
            'name': '📋 Administratif',
            'description': 'Cartes d\'identité, permis, inscriptions officielles'
        },
        {
            'id': 'juridique',
            'name': '⚖️ Juridique',
            'description': 'Droits, démarches légales, recours'
        },
        {
            'id': 'emploi',
            'name': '💼 Emploi',
            'description': 'Recherche d\'emploi, formations, droits du travail'
        },
        {
            'id': 'education',
            'name': '🎓 Éducation',
            'description': 'Inscriptions scolaires, universités, formations'
        },
        {
            'id': 'transport',
            'name': '🚗 Transport',
            'description': 'Permis de conduire, transports en commun'
        },
        {
            'id': 'finances',
            'name': '💰 Finances',
            'description': 'Banques, impôts, aides sociales'
        }
    ]
    
    return jsonify({
        'success': True,
        'categories': categories
    })

@app.route('/api/help', methods=['GET'])
def api_help():
    """Documentation de l'API"""
    endpoints = [
        {
            'endpoint': '/api/status',
            'method': 'GET',
            'description': 'Vérifier le statut de l\'API'
        },
        {
            'endpoint': '/api/chat',
            'method': 'POST',
            'description': 'Envoyer un message à l\'assistant',
            'parameters': {
                'message': 'string (requis) - Votre question',
                'context': 'string (optionnel) - Contexte supplémentaire'
            },
            'example': {
                'message': 'Comment obtenir une carte vitale ?',
                'context': 'Je viens d\'arriver d\'Allemagne'
            }
        },
        {
            'endpoint': '/api/categories',
            'method': 'GET',
            'description': 'Obtenir la liste des catégories d\'aide disponibles'
        }
    ]
    
    return jsonify({
        'service': 'API Assistant Nouveaux Arrivants France',
        'version': '1.0.0',
        'endpoints': endpoints
    })

# ============ COMPATIBILITÉ ANCIENNE API ============

@app.route('/chat', methods=['POST'])
def chat():
    """Ancien endpoint chat pour compatibilité"""
    user_message = request.json.get('message', '')
    
    if not user_message.strip():
        return jsonify({'error': 'Message vide'}), 400
    
    # Rediriger vers la nouvelle API
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = loop.run_until_complete(get_agent_response(user_message))
        return jsonify({'response': response})
    finally:
        loop.close()

# ============ GESTION D'ERREURS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint non trouvé',
        'message': 'Consultez /api/help pour voir les endpoints disponibles'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Méthode non autorisée',
        'message': 'Vérifiez la méthode HTTP utilisée (GET/POST)'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Erreur serveur interne',
        'message': 'Une erreur est survenue côté serveur'
    }), 500

if __name__ == '__main__':
    logger.info("Démarrage de l'API Assistant Nouveaux Arrivants France")
    
    # Vérifier les variables d'environnement critiques
    required_env_vars = ['API_TOKEN', 'BROWSER_AUTH', 'WEB_UNLOCKER_ZONE']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        logger.error("Veuillez configurer ces variables dans votre fichier .env ou dans les variables d'environnement Render")
        exit(1)
    
    logger.info("✅ Toutes les variables d'environnement sont configurées")
    
    # Utiliser le port Render par défaut ou 8080 en local
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Démarrage sur le port {port}")
    
    app.run(host='0.0.0.0', debug=False, port=port) 