#!/usr/bin/env python3
"""Teste direto dos endpoints users com token JWT manual"""

import requests
import jwt
from datetime import datetime, timedelta

# Configurações
BASE_URL = "http://localhost:8000/api/v1"
SECRET_KEY = "79722d3f4ca30f6c8de510467e2f452d440cb42d68fc99293dc02ef81c2f9c8f"

def create_test_token():
    """Criar token JWT manualmente para teste"""
    payload = {
        "sub": "admin@empresa.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "user_id": 1,
        "email": "admin@empresa.com",
        "is_superuser": True
    }
    
    # Token simples para teste (sem validação de assinatura no desenvolvimento)
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def test_users_endpoints():
    """Testar endpoints users com token manual"""
    
    # Criar token de teste
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🚀 Testando endpoints Users com token manual")
    print(f"Token: {token[:50]}...")
    
    # 1. Count
    print("\n1. GET /users/count")
    response = requests.get(f"{BASE_URL}/users/count", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # 2. List users
    print("\n2. GET /users/")
    response = requests.get(f"{BASE_URL}/users/?skip=0&limit=5", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Usuários: {len(data.get('users', []))}")
        print(f"   Total: {data.get('total')}")
    else:
        print(f"   Error: {response.text}")
    
    # 3. User profile
    print("\n3. GET /users/me/profile")
    response = requests.get(f"{BASE_URL}/users/me/profile", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"   Name: {profile.get('name')}")
        print(f"   Email: {profile.get('email_address')}")
    else:
        print(f"   Error: {response.text}")
    
    # 4. Teste sem autenticação (deve falhar)
    print("\n4. GET /users/ (sem auth)")
    response = requests.get(f"{BASE_URL}/users/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    test_users_endpoints()