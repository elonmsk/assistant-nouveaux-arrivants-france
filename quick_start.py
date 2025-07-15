#!/usr/bin/env python3
"""
Guide de démarrage rapide pour l'API Assistant Nouveaux Arrivants France
"""

import requests
import json

def quick_test():
    """Test rapide de l'API"""
    base_url = "http://127.0.0.1:8080"
    
    print("🚀 Test rapide de votre nouvelle API")
    print("=" * 50)
    
    # Test 1: Status
    print("1️⃣ Test du status...")
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API active - Version: {data['version']}")
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ L'API n'est pas accessible!")
        print("   💡 Lancez d'abord: uv run python app.py")
        return False
    
    # Test 2: Catégories
    print("\n2️⃣ Test des catégories...")
    response = requests.get(f"{base_url}/api/categories")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {len(data['categories'])} catégories disponibles")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    # Test 3: Question simple
    print("\n3️⃣ Test d'une question...")
    question = "Comment obtenir une carte vitale ?"
    response = requests.post(f"{base_url}/api/chat", json={
        "message": question
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"   ✅ Réponse reçue!")
            print(f"   📝 Question: {question}")
            print(f"   💬 Réponse (extrait): {data['response'][:150]}...")
        else:
            print(f"   ❌ Erreur dans la réponse: {data.get('error')}")
    else:
        print(f"   ❌ Erreur HTTP: {response.status_code}")
    
    print("\n🎉 Test terminé! Votre API est prête à utiliser.")
    print("\n📋 Prochaines étapes:")
    print("   • Consultez la doc complète: http://127.0.0.1:8080/api/help")
    print("   • Interface web: http://127.0.0.1:8080")
    print("   • Tests complets: uv run python test_api.py")
    
    return True

def show_examples():
    """Affiche des exemples d'utilisation"""
    print("\n💡 Exemples d'utilisation de votre API:")
    print("=" * 50)
    
    examples = [
        {
            "title": "🏥 Santé",
            "question": "Comment obtenir une carte vitale en France ?",
            "context": "Je viens d'arriver d'Espagne"
        },
        {
            "title": "🏠 Logement", 
            "question": "Quelles aides au logement puis-je obtenir ?",
            "context": "Étudiant, 800€ de revenus"
        },
        {
            "title": "💼 Emploi",
            "question": "Comment m'inscrire à Pôle Emploi ?",
            "context": "Diplômé en informatique"
        },
        {
            "title": "🚗 Transport",
            "question": "Comment échanger mon permis de conduire européen ?",
            "context": "Permis allemand valide"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   Question: {example['question']}")
        print(f"   Contexte: {example['context']}")
        print(f"   ```bash")
        print(f"   curl -X POST http://127.0.0.1:8080/api/chat \\")
        print(f"     -H 'Content-Type: application/json' \\")
        json_data = json.dumps({"message": example["question"], "context": example["context"]}, ensure_ascii=False)
        print(f"     -d '{json_data}'")
        print(f"   ```")

if __name__ == "__main__":
    print("🎯 Guide de démarrage rapide")
    print("Choisissez une option:")
    print("1. Test rapide de l'API")
    print("2. Voir des exemples d'utilisation")
    print("3. Les deux")
    
    choice = input("\nVotre choix (1/2/3): ").strip()
    
    if choice in ["1", "3"]:
        success = quick_test()
        if not success:
            exit(1)
    
    if choice in ["2", "3"]:
        show_examples()
    
    if choice not in ["1", "2", "3"]:
        print("❌ Choix invalide") 