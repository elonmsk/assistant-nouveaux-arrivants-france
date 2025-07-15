#!/usr/bin/env python3
"""
Script de test pour l'API Assistant Nouveaux Arrivants France
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8080"

def test_api_status():
    """Test de l'endpoint de status"""
    print("🔍 Test du status de l'API...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API active - Version: {data['version']}")
            print(f"   Service: {data['service']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Erreur status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API. Assurez-vous qu'elle tourne sur le port 8080")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_api_categories():
    """Test de l'endpoint des catégories"""
    print("\n🔍 Test des catégories...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/categories")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data['categories'])} catégories disponibles:")
            for cat in data['categories']:
                print(f"   • {cat['name']}: {cat['description']}")
            return True
        else:
            print(f"❌ Erreur catégories: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_api_help():
    """Test de l'endpoint d'aide"""
    print("\n🔍 Test de la documentation...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/help")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Documentation disponible - {len(data['endpoints'])} endpoints:")
            for endpoint in data['endpoints']:
                print(f"   • {endpoint['method']} {endpoint['endpoint']}: {endpoint['description']}")
            return True
        else:
            print(f"❌ Erreur documentation: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_api_chat(message, context=None):
    """Test de l'endpoint de chat"""
    print(f"\n🔍 Test du chat avec le message: '{message[:50]}...'")
    
    payload = {"message": message}
    if context:
        payload["context"] = context
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Réponse reçue en {end_time - start_time:.2f}s")
                print(f"📝 Réponse (premiers 200 caractères):")
                print(f"   {data['response'][:200]}...")
                return True
            else:
                print(f"❌ Erreur dans la réponse: {data.get('error')}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Message: {error_data.get('error', 'Erreur inconnue')}")
            except:
                print(f"   Réponse brute: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_error_handling():
    """Test de la gestion d'erreurs"""
    print("\n🔍 Test de la gestion d'erreurs...")
    
    # Test message vide
    response = requests.post(f"{BASE_URL}/api/chat", json={"message": ""})
    if response.status_code == 400:
        print("✅ Gestion message vide OK")
    else:
        print("❌ Gestion message vide échouée")
    
    # Test format JSON invalide
    response = requests.post(f"{BASE_URL}/api/chat", data="invalid json")
    if response.status_code == 400:
        print("✅ Gestion JSON invalide OK")
    else:
        print("❌ Gestion JSON invalide échouée")
    
    # Test endpoint inexistant
    response = requests.get(f"{BASE_URL}/api/inexistant")
    if response.status_code == 404:
        print("✅ Gestion endpoint inexistant OK")
    else:
        print("❌ Gestion endpoint inexistant échouée")

def run_comprehensive_test():
    """Lance une série de tests complets"""
    print("🚀 Début des tests de l'API Assistant Nouveaux Arrivants France")
    print("=" * 60)
    
    # Tests basiques
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Status
    total_tests += 1
    if test_api_status():
        tests_passed += 1
    
    # Test 2: Catégories
    total_tests += 1
    if test_api_categories():
        tests_passed += 1
    
    # Test 3: Documentation
    total_tests += 1
    if test_api_help():
        tests_passed += 1
    
    # Test 4: Chat simple
    total_tests += 1
    if test_api_chat("Comment obtenir une carte vitale ?"):
        tests_passed += 1
    
    # Test 5: Chat avec contexte
    total_tests += 1
    if test_api_chat(
        "Quelles sont les étapes pour ouvrir un compte bancaire ?", 
        "Je suis étudiant étranger en France"
    ):
        tests_passed += 1
    
    # Test 6: Gestion d'erreurs
    test_error_handling()
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"📊 Résultats des tests: {tests_passed}/{total_tests} réussis")
    
    if tests_passed == total_tests:
        print("🎉 Tous les tests sont passés avec succès !")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
    
    return tests_passed == total_tests

def interactive_test():
    """Mode interactif pour tester l'API"""
    print("\n🎮 Mode interactif - Testez l'API avec vos propres questions")
    print("Tapez 'quit' pour quitter")
    
    while True:
        print("\n" + "-" * 40)
        message = input("💬 Votre question: ").strip()
        
        if message.lower() in ['quit', 'exit', 'q']:
            break
        
        if not message:
            print("⚠️  Veuillez entrer une question")
            continue
        
        context = input("📝 Contexte (optionnel): ").strip()
        context = context if context else None
        
        test_api_chat(message, context)

if __name__ == "__main__":
    print("🔧 Script de test pour l'API Assistant Nouveaux Arrivants France")
    print("\nOptions disponibles:")
    print("1. Tests automatiques complets")
    print("2. Mode interactif")
    print("3. Test rapide")
    
    choice = input("\nVotre choix (1/2/3): ").strip()
    
    if choice == "1":
        run_comprehensive_test()
    elif choice == "2":
        if test_api_status():
            interactive_test()
        else:
            print("❌ L'API n'est pas accessible. Lancez d'abord l'application.")
    elif choice == "3":
        test_api_status()
        test_api_chat("Comment obtenir un RIB en France ?")
    else:
        print("❌ Choix invalide") 