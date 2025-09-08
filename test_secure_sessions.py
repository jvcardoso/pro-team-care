#!/usr/bin/env python3
"""
Teste completo do sistema de sessões seguras com troca de perfil
"""
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

def test_secure_sessions():
    print("🔐 TESTE COMPLETO: Sistema de Sessões Seguras")
    print("=" * 60)
    
    # 1. Login para obter token JWT
    print("\n1️⃣ Fazendo login para obter token...")
    login_response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "admin@proteamcare.com",
        "password": "password"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(login_response.text)
        return
        
    login_data = login_response.json()
    token = login_data["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("✅ Login realizado com sucesso")
    
    # 2. Testar endpoints de sessão segura
    print("\n2️⃣ Testando endpoints de sessão segura...")
    
    # Verificar se os endpoints estão disponíveis
    endpoints_to_test = [
        "/secure-sessions/available-profiles",
        "/secure-sessions/current-context"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testando: {endpoint}")
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Endpoint funcionando")
            data = response.json()
            print("📊 Resposta:")
            pprint(data, width=80)
        else:
            print(f"❌ Erro: {response.text}")
    
    # 3. Testar troca de perfil
    print(f"\n3️⃣ Testando troca de perfil...")
    switch_response = requests.post(f"{BASE_URL}/secure-sessions/switch-profile", 
        headers=headers, 
        json={
            "context_type": "establishment",
            "context_id": 1,
            "reason": "Teste de troca de perfil"
        }
    )
    
    print(f"Status troca de perfil: {switch_response.status_code}")
    if switch_response.status_code == 200:
        print("✅ Troca de perfil realizada")
        pprint(switch_response.json(), width=80)
    else:
        print(f"❌ Erro na troca: {switch_response.text}")
    
    # 4. Verificar contexto atual
    print(f"\n4️⃣ Verificando contexto atual após troca...")
    context_response = requests.get(f"{BASE_URL}/secure-sessions/current-context", headers=headers)
    print(f"Status contexto: {context_response.status_code}")
    
    if context_response.status_code == 200:
        print("✅ Contexto obtido com sucesso")
        pprint(context_response.json(), width=80)
    else:
        print(f"❌ Erro: {context_response.text}")
    
    # 5. Testar terminação da sessão
    print(f"\n5️⃣ Testando terminação da sessão...")
    terminate_response = requests.post(f"{BASE_URL}/secure-sessions/terminate", headers=headers)
    print(f"Status terminação: {terminate_response.status_code}")
    
    if terminate_response.status_code == 200:
        print("✅ Sessão terminada com sucesso")
        pprint(terminate_response.json(), width=80)
    else:
        print(f"❌ Erro: {terminate_response.text}")
    
    print(f"\n✨ Teste completo finalizado!")

if __name__ == "__main__":
    test_secure_sessions()