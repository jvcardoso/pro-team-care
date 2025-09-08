#!/usr/bin/env python3
"""Teste final do sistema de usuários"""

import requests
import json

def test_login_and_users():
    base_url = "http://localhost:8000"
    
    print("🔍 Testando login e endpoints de usuários...")
    
    # 1. Fazer login
    print("\n1️⃣ Fazendo login...")
    login_data = {
        "username": "admin@proteamcare.com", 
        "password": "password"
    }
    
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login",
        data=login_data,  # usando form data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Status login: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.text}")
        return
        
    token_data = login_response.json()
    token = token_data.get("access_token")
    
    if not token:
        print("❌ Token não encontrado na resposta")
        return
    
    print(f"✅ Login OK - Token recebido: {token[:30]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Testar /users/count
    print("\n2️⃣ Testando users/count...")
    count_response = requests.get(f"{base_url}/api/v1/users/count", headers=headers)
    print(f"Status: {count_response.status_code}")
    
    if count_response.status_code == 200:
        print(f"✅ Count OK: {count_response.json()}")
    else:
        print(f"❌ Erro: {count_response.text}")
        return
        
    # 3. Testar listagem de usuários
    print("\n3️⃣ Testando users (listagem)...")
    list_response = requests.get(f"{base_url}/api/v1/users/?skip=0&limit=5", headers=headers)
    print(f"Status: {list_response.status_code}")
    
    if list_response.status_code == 200:
        users = list_response.json()
        print(f"✅ Listagem OK: {len(users)} usuários encontrados")
        if users:
            print(f"   Primeiro usuário: ID={users[0].get('id')}, Email={users[0].get('email_address')}")
    else:
        print(f"❌ Erro: {list_response.text}")
        return
        
    # 4. Testar detalhes de um usuário
    if users:
        user_id = users[0]['id']
        print(f"\n4️⃣ Testando users/{user_id} (detalhes)...")
        detail_response = requests.get(f"{base_url}/api/v1/users/{user_id}", headers=headers)
        print(f"Status: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            user_detail = detail_response.json()
            print(f"✅ Detalhes OK: {user_detail.get('email_address')}")
            print(f"   Person data: {user_detail.get('person', {}).get('name')}")
        else:
            print(f"❌ Erro: {detail_response.text}")
            return
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")

if __name__ == "__main__":
    test_login_and_users()