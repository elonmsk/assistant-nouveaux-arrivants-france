from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

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
    # Make sure to update to the full absolute path to your math_server.py file
    args=["@brightdata/mcp"],
)


async def chat_with_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model, tools)

            # Start conversation history
            messages = [
                {
                    "role": "system",
                    "content": """Tu es un assistant spécialisé dans l'aide aux nouveaux arrivants en France. 
                    
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
                    2. Utilise des outils de recherche pour obtenir des informations à jour
                    3. OBLIGATOIRE : Cite TOUJOURS tes sources à la fin de chaque réponse
                    4. Structure tes réponses avec des émojis et des sections claires
                    5. Propose des actions concrètes et des liens utiles
                    6. Pense étape par étape et utilise plusieurs outils si nécessaire
                    7. Sois empathique et rassurant
                    
                    Format de citation des sources :
                    📚 **Sources consultées :**
                    - [Nom du site/document] : URL ou référence
                    - [Autre source] : URL ou référence
                    """,
                }
            ]

            print("Type 'exit' or 'quit' to end the chat.")
            while True:
                user_input = input("\nYou: ")
                if user_input.strip().lower() in {"exit", "quit"}:
                    print("Goodbye!")
                    break

                # Add user message to history
                messages.append({"role": "user", "content": user_input})

                # Call the agent with the full message history
                agent_response = await agent.ainvoke({"messages": messages})

                # Extract agent's reply and add to history
                ai_message = agent_response["messages"][-1].content
                print(f"Agent: {ai_message}")


if __name__ == "__main__":
    asyncio.run(chat_with_agent())
