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
        "NPM_CONFIG_LOGLEVEL": "silent",  # Logs npm complètement silencieux
        "NPM_CONFIG_AUDIT": "false",      # Désactiver l'audit
        "NPM_CONFIG_FUND": "false",       # Désactiver les messages de financement
        "NPM_CONFIG_PROGRESS": "false",   # Désactiver la barre de progression
    },
    args=["--yes", "--silent", "--no-audit", "--no-fund", "--no-progress", "@brightdata/mcp@2.4.1"],
)

# Configuration des sites de référence par thématique
REFERENCE_SITES = {
    'logement': ['https://www.actionlogement.fr/'],
    'sante': [],  # À définir
    'administratif': [],  # À définir
    'juridique': [],  # À définir
    'emploi': [],  # À définir
    'education': [],  # À définir
    'transport': [],  # À définir
    'finances': []  # À définir
}

# Configuration des prompts par catégorie
CATEGORY_PROMPTS = {
    'logement': {
        'title': '🏠 MÉTHODE SPÉCIFIQUE POUR LE LOGEMENT',
        'description': 'Tu DOIS utiliser EXCLUSIVEMENT le site de référence prédéfini',
        'site_label': 'SITE UNIQUE AUTORISÉ',
        'procedure': [
            'OBLIGATOIRE : Commencer par scraping_browser_navigate sur le site de référence',
            'Utiliser scraping_browser_links() pour identifier toutes les sections disponibles',
            'Naviguer vers les sections pertinentes avec scraping_browser_click',
            'Utiliser scrape_as_markdown sur les pages spécifiques trouvées',
            'Explorer en profondeur : aides, formulaires, conditions d\'éligibilité',
            'INTERDIT : Utiliser search_engine ou d\'autres sites web'
        ],
        'workflow_example': {
            'question': 'Comment obtenir des aides au logement ?',
            'steps': [
                'scraping_browser_navigate(site_reference) pour charger le site',
                'scraping_browser_links() pour voir toutes les sections disponibles',
                'Identifier les sections "Aides", "Logement", "Formulaires"',
                'scraping_browser_click sur les liens pertinents',
                'scrape_as_markdown sur chaque page explorée',
                'Extraire les informations détaillées sur les aides',
                'Répondre avec les détails trouvés et les liens directs'
            ]
        },
        'rules': [
            'OBLIGATOIRE : Commencer par scraping_browser_navigate',
            'Explorer TOUTES les sections pertinentes du site',
            'Ne pas se contenter de la page d\'accueil',
            'Chercher spécifiquement : aides, formulaires, conditions',
            'Extraire les informations détaillées sur les aides disponibles',
            'Donner les liens directs vers les formulaires d\'aide',
            'Expliquer les conditions d\'éligibilité trouvées sur le site',
            'Utiliser UNIQUEMENT le site de référence'
        ]
    }
}

# Prompt de base réutilisable
BASE_PROMPT = """Tu es un assistant spécialisé dans l'aide aux nouveaux arrivants en France. 

Tu aides les personnes qui viennent d'arriver sur diverses thématiques :
- 🏥 Santé (sécurité sociale, médecins, urgences)
- 🏠 Logement (recherche, droits, aides au logement)
- 📋 Administratif (cartes d'identité, permis, inscriptions)
- ⚖️ Juridique (droits, démarches légales, recours)
- 💼 Emploi (recherche d'emploi, formations, droits du travail)
- 🎓 Éducation (inscriptions scolaires, universités, formations)
- 🚗 Transport (permis de conduire, transports en commun)
- 💰 Finances (banques, impôts, aides sociales)

RÈGLES IMPORTANTES :
1. Réponds toujours en français, de manière claire et accessible
2. OBLIGATOIRE : Cite TOUJOURS tes sources à la fin de chaque réponse
3. OBLIGATOIRE : Formate ta réponse en Markdown structuré et propre
4. Propose des actions concrètes et des liens SPÉCIFIQUES (pas génériques)
5. Donne des informations DÉTAILLÉES extraites du contenu scraped
6. Sois empathique et rassurant
7. Donne des liens directs vers les formulaires, pages spécifiques, pas les pages d'accueil
8. Indique le nom exact des documents à télécharger avec leurs URLs précises
9. OBLIGATOIRE : Explore les sites en profondeur, ne te contente pas de la page d'accueil
10. Utilise les outils de navigation pour trouver les informations spécifiques

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

# Prompt pour méthode standard
STANDARD_METHOD_PROMPT = """

MÉTHODE DE RECHERCHE STANDARD (pour les autres thématiques) :
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

EXEMPLE WORKFLOW STANDARD :
- Question: "Comment obtenir une carte vitale ?"
- Étape 1: search_engine("carte vitale obtenir France")
- Étape 2: scrape_as_markdown(https://www.service-public.fr/particuliers/vosdroits/F750)
- Étape 3: Si peu de contenu → scraping_browser_navigate(URL) pour JavaScript
- Étape 4: Extraire les informations détaillées et formater la réponse
"""

async def get_agent_response(user_message, context=None, category=None, max_retries=3):
    """Fonction pour obtenir la réponse de l'agent avec retry automatique"""
    try:
        # Vérifier la taille du message utilisateur
        if len(user_message) > 10000:  # ~7500 tokens approximativement
            return "❌ Votre message est trop long. Veuillez le raccourcir (maximum ~7500 tokens)."
        
        # Générer le prompt système selon la catégorie
        system_prompt = generate_system_prompt(category)
        
        for attempt in range(max_retries):
            try:
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        try:
                            await session.initialize()
                            tools = await load_mcp_tools(session)
                            agent = create_react_agent(model, tools)

                            # Messages avec prompt système dynamique
                            messages = [
                                {"role": "system", "content": system_prompt}
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
                    error_msg = str(mcp_error).lower()
                    
                    if "List roots not supported" in str(mcp_error):
                        return "❌ Erreur de configuration MCP. Le serveur BrightData n'est pas compatible avec cette version. Veuillez contacter l'administrateur."
                    elif "529" in str(mcp_error) or "overloaded" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                            logger.warning(f"⚠️ Service surchargé (tentative {attempt + 1}/{max_retries}), attente de {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return "❌ Service temporairement surchargé. Le service de recherche web est actuellement très sollicité. Veuillez réessayer dans quelques minutes."
                    elif "rate" in error_msg or "limit" in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 1  # 1s, 2s, 3s
                            logger.warning(f"⚠️ Rate limit atteint (tentative {attempt + 1}/{max_retries}), attente de {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return "❌ Limite de requêtes atteinte. Trop de demandes simultanées. Veuillez patienter quelques secondes et réessayer."
                    else:
                        raise mcp_error
                        
                # Si on arrive ici, la tentative a réussi
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée: {str(e)}")
                    await asyncio.sleep(1)  # Attendre 1s entre les tentatives
                    continue
                else:
                    # Dernière tentative échouée
                    import traceback
                    logger.error(f"Erreur dans get_agent_response après {max_retries} tentatives: {str(e)}\n{traceback.format_exc()}")
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

def get_category_info(category_id):
    """Récupère les informations d'une catégorie par son ID"""
    categories = {
        'sante': {
            'id': 'sante',
            'name': '🏥 Santé',
            'description': 'Sécurité sociale, médecins, urgences, carte vitale',
            'reference_sites': REFERENCE_SITES.get('sante', [])
        },
        'logement': {
            'id': 'logement',
            'name': '🏠 Logement',
            'description': 'Recherche, droits, aides au logement, CAF',
            'reference_sites': REFERENCE_SITES.get('logement', [])
        },
        'administratif': {
            'id': 'administratif',
            'name': '📋 Administratif',
            'description': 'Cartes d\'identité, permis, inscriptions officielles',
            'reference_sites': REFERENCE_SITES.get('administratif', [])
        },
        'juridique': {
            'id': 'juridique',
            'name': '⚖️ Juridique',
            'description': 'Droits, démarches légales, recours',
            'reference_sites': REFERENCE_SITES.get('juridique', [])
        },
        'emploi': {
            'id': 'emploi',
            'name': '💼 Emploi',
            'description': 'Recherche d\'emploi, formations, droits du travail',
            'reference_sites': REFERENCE_SITES.get('emploi', [])
        },
        'education': {
            'id': 'education',
            'name': '🎓 Éducation',
            'description': 'Inscriptions scolaires, universités, formations',
            'reference_sites': REFERENCE_SITES.get('education', [])
        },
        'transport': {
            'id': 'transport',
            'name': '🚗 Transport',
            'description': 'Permis de conduire, transports en commun',
            'reference_sites': REFERENCE_SITES.get('transport', [])
        },
        'finances': {
            'id': 'finances',
            'name': '💰 Finances',
            'description': 'Banques, impôts, aides sociales',
            'reference_sites': REFERENCE_SITES.get('finances', [])
        }
    }
    return categories.get(category_id)

def generate_system_prompt(category=None):
    """Génère le prompt système selon la catégorie"""
    # Utiliser le prompt de base
    prompt = BASE_PROMPT
    
    # Vérifier si la catégorie a des sites de référence
    if category and category in REFERENCE_SITES and REFERENCE_SITES[category]:
        # Générer le prompt spécifique à la catégorie
        category_config = CATEGORY_PROMPTS.get(category, {})
        if category_config:
            sites = REFERENCE_SITES[category]
            sites_list = '\n'.join([f"- {site}" for site in sites])
            
            category_prompt = f"""

{category_config.get('title', f'🎯 MÉTHODE SPÉCIFIQUE POUR {category.upper()}')} :
{category_config.get('description', 'Tu DOIS utiliser EXCLUSIVEMENT le(s) site(s) de référence prédéfini(s)')} :

{category_config.get('site_label', 'SITE(S) AUTORISÉ(S)')} :
{sites_list}

PROCÉDURE OBLIGATOIRE :
"""
            # Ajouter les étapes de procédure
            for i, step in enumerate(category_config.get('procedure', []), 1):
                category_prompt += f"{i}. 📄 {step}\n"
            
            # Ajouter l'exemple de workflow
            workflow = category_config.get('workflow_example', {})
            if workflow:
                category_prompt += f"""
EXEMPLE WORKFLOW {category.upper()} :
- Question: "{workflow.get('question', 'Comment obtenir de l aide ?')}"
"""
                for i, step in enumerate(workflow.get('steps', []), 1):
                    # Remplacer les placeholders par les vrais sites
                    step = step.replace('site_reference', sites[0] if sites else 'URL_du_site')
                    category_prompt += f"- Étape {i}: {step}\n"
            
            # Ajouter les règles spécifiques
            rules = category_config.get('rules', [])
            if rules:
                category_prompt += f"""
RÈGLES SPÉCIFIQUES {category.upper()} :
"""
                for rule in rules:
                    category_prompt += f"- {rule}\n"
        else:
            # Configuration par défaut si pas de config spécifique
            sites = REFERENCE_SITES[category]
            sites_list = '\n'.join([f"- {site}" for site in sites])
            category_prompt = f"""

🎯 MÉTHODE SPÉCIFIQUE POUR {category.upper()} :
Tu DOIS utiliser EXCLUSIVEMENT le(s) site(s) de référence prédéfini(s) :

SITE(S) AUTORISÉ(S) :
{sites_list}

PROCÉDURE OBLIGATOIRE :
1. 🌐 OBLIGATOIRE : Commencer par scraping_browser_navigate sur le(s) site(s) de référence
2. 🔗 Utiliser scraping_browser_links() pour identifier toutes les sections disponibles
3. 🖱️ Naviguer vers les sections pertinentes avec scraping_browser_click
4. 📄 Utiliser scrape_as_markdown sur les pages spécifiques trouvées
5. 🔍 Explorer en profondeur : chercher les sections aides, formulaires, conditions
6. ❌ INTERDIT : Utiliser search_engine ou d'autres sites web

RÈGLES SPÉCIFIQUES :
- OBLIGATOIRE : Commencer par scraping_browser_navigate
- Explorer TOUTES les sections pertinentes du site
- Ne pas se contenter de la page d'accueil
- Chercher spécifiquement : aides, formulaires, conditions d'éligibilité
- Extraire les informations détaillées disponibles
- Donner les liens directs vers les formulaires
- Expliquer les conditions trouvées sur le site
- Utiliser UNIQUEMENT le(s) site(s) de référence
"""
    else:
        # Utiliser la méthode standard
        category_prompt = STANDARD_METHOD_PROMPT
    
    return prompt + category_prompt

def add_reference_sites(category, sites):
    """Ajoute des sites de référence pour une catégorie"""
    if category not in REFERENCE_SITES:
        REFERENCE_SITES[category] = []
    REFERENCE_SITES[category].extend(sites)

def add_category_prompt(category, config):
    """Ajoute une configuration de prompt pour une catégorie"""
    CATEGORY_PROMPTS[category] = config

def get_available_categories():
    """Retourne la liste des catégories disponibles avec leurs sites de référence"""
    return {
        category: {
            'info': get_category_info(category),
            'reference_sites': REFERENCE_SITES.get(category, []),
            'has_custom_prompt': category in CATEGORY_PROMPTS
        }
        for category in ['sante', 'logement', 'administratif', 'juridique', 'emploi', 'education', 'transport', 'finances']
    }

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
        },
        'retry_system': {
            'max_retries': 3,
            'overloaded_wait': '2s, 4s, 6s',
            'rate_limit_wait': '1s, 2s, 3s'
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
        category = data.get('category', '')
        
        if not user_message:
            return jsonify({'error': 'Le champ "message" est requis et ne peut pas être vide'}), 400
        
        # Log de la requête
        logger.info(f"Nouvelle requête chat: {user_message[:100]}... (catégorie: {category})")
        
        # Construire le contexte enrichi avec la catégorie
        enriched_context = context
        if category:
            category_info = get_category_info(category)
            if category_info:
                enriched_context = f"Catégorie: {category_info['name']} - {category_info['description']}\n{context}".strip()
        
        # Exécution asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(get_agent_response(user_message, enriched_context, category))
            
            return jsonify({
                'success': True,
                'response': response,
                'timestamp': datetime.now().isoformat(),
                'category': category
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
        get_category_info('sante'),
        get_category_info('logement'),
        get_category_info('administratif'),
        get_category_info('juridique'),
        get_category_info('emploi'),
        get_category_info('education'),
        get_category_info('transport'),
        get_category_info('finances')
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
                'context': 'string (optionnel) - Contexte supplémentaire',
                'category': 'string (optionnel) - Catégorie thématique (sante, logement, administratif, juridique, emploi, education, transport, finances)'
            },
            'example': {
                'message': 'Comment obtenir des aides au logement en tant que réfugié syrien ?',
                'context': 'Personne ayant obtenu le statut de réfugié ou protection internationale',
                'category': 'logement'
            }
        },
        {
            'endpoint': '/api/categories',
            'method': 'GET',
            'description': 'Obtenir la liste des catégories d\'aide disponibles'
        },
        {
            'endpoint': '/api/reference-sites',
            'method': 'GET',
            'description': 'Obtenir la configuration des sites de référence par catégorie'
        }
    ]
    
    return jsonify({
        'service': 'API Assistant Nouveaux Arrivants France',
        'version': '1.0.0',
        'endpoints': endpoints
    })

@app.route('/api/reference-sites', methods=['GET'])
def api_reference_sites():
    """Endpoint pour obtenir la configuration des sites de référence"""
    return jsonify({
        'success': True,
        'reference_sites': REFERENCE_SITES,
        'category_prompts': list(CATEGORY_PROMPTS.keys()),
        'categories': get_available_categories()
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
        response = loop.run_until_complete(get_agent_response(user_message, category=None))
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