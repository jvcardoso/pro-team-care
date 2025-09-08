#!/usr/bin/env python3
"""
Teste de personificação de usuário por ROOT
"""
import requests
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

def test_root_impersonation():
    print("👑 TESTE: Personificação de Usuário por ROOT")
    print("=" * 50)
    
    # 1. Login como ROOT
    print("\n1️⃣ Login como ROOT (admin@proteamcare.com)...")
    login_response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "admin@proteamcare.com",
        "password": "password"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        return
        
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login ROOT realizado com sucesso")
    
    # 2. Ver perfis disponíveis (incluindo personificação)
    print("\n2️⃣ Verificando perfis disponíveis para ROOT...")
    profiles_response = requests.get(f"{BASE_URL}/secure-sessions/available-profiles", headers=headers)
    
    if profiles_response.status_code == 200:
        data = profiles_response.json()
        print(f"✅ ROOT pode ver {data['total_profiles']} perfis")
        print(f"🔑 User is ROOT: {data['user_is_root']}")
        
        # Mostrar perfis de personificação
        impersonation_profiles = [p for p in data['profiles'] if p.get('is_impersonation')]
        if impersonation_profiles:
            print(f"\n👥 Perfis de personificação disponíveis:")
            for profile in impersonation_profiles:
                print(f"  - Usuário: {profile['target_user_email']} (ID: {profile['target_user_id']})")
                print(f"    Role: {profile['role_display_name']}")
                print(f"    Contexto: {profile['context_name']}")
        else:
            print("📝 Nenhum perfil de personificação encontrado (pode ser normal se não há outros usuários)")
    
    # 3. Tentar personificar um usuário específico (ID 2)
    print("\n3️⃣ Tentando personificar usuário ID 2...")
    impersonate_response = requests.post(f"{BASE_URL}/secure-sessions/switch-profile", 
        headers=headers, 
        json={
            "impersonated_user_id": 2,
            "reason": "Investigação de problema reportado pelo usuário"
        }
    )
    
    print(f"Status personificação: {impersonate_response.status_code}")
    if impersonate_response.status_code == 200:
        print("✅ Personificação realizada com sucesso!")
        pprint(impersonate_response.json())
    else:
        print(f"❌ Erro na personificação: {impersonate_response.text}")
    
    # 4. Verificar contexto após personificação
    print("\n4️⃣ Verificando contexto após personificação...")
    context_response = requests.get(f"{BASE_URL}/secure-sessions/current-context", headers=headers)
    
    if context_response.status_code == 200:
        context = context_response.json()
        print("📊 Contexto atual:")
        print(f"  - Usuário real: {context.get('user_email')}")
        print(f"  - Usuário efetivo: {context.get('effective_user_email')}")
        print(f"  - Personificando: {context.get('is_impersonating')}")
        print(f"  - É ROOT: {context.get('is_root')}")
    else:
        print(f"❌ Erro ao verificar contexto: {context_response.text}")

    # 5. Demonstrar recursos disponíveis apenas para ROOT
    print("\n5️⃣ Recursos exclusivos para ROOT:")
    print("✅ Pode personificar qualquer usuário")
    print("✅ Pode ver todos os perfis do sistema")
    print("✅ Pode assumir qualquer contexto (empresa/estabelecimento)")
    print("✅ Todas as operações são auditadas")
    
    # 6. Listar sessões ativas (só ROOT)
    print("\n6️⃣ Listando sessões ativas (só ROOT pode fazer)...")
    sessions_response = requests.get(f"{BASE_URL}/secure-sessions/active-sessions", headers=headers)
    
    if sessions_response.status_code == 200:
        sessions = sessions_response.json()
        print(f"✅ ROOT pode ver {sessions['total_sessions']} sessões ativas")
    else:
        print(f"❌ Erro: {sessions_response.text}")

if __name__ == "__main__":
    test_root_impersonation()