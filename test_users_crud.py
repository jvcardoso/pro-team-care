#!/usr/bin/env python3
"""
Teste completo do CRUD de usuários
Testa todos os endpoints implementados
"""

import asyncio
import asyncpg
from passlib.context import CryptContext
import requests
import json

# Configurações
BASE_URL = "http://localhost:8000/api/v1"
DB_CONFIG = {
    "host": "192.168.11.62",
    "port": 5432,
    "user": "postgres", 
    "password": "Jvc@1702",
    "database": "pro_team_care_11"
}

# Hash de senha correto (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def setup_admin_user():
    """Criar usuário admin com hash bcrypt correto"""
    email = "admin@proteamcare.com"
    password = "admin123"
    hashed_password = hash_password(password)
    
    conn = await asyncpg.connect(**DB_CONFIG, server_settings={'search_path': 'master, public'})
    
    try:
        # Atualizar/criar usuário admin
        await conn.execute("""
            INSERT INTO users (id, person_id, email_address, password, is_active, is_system_admin, created_at, updated_at)
            VALUES (999, 999, $1, $2, true, true, now(), now())
            ON CONFLICT (email_address) 
            DO UPDATE SET password = $2, is_active = true, is_system_admin = true
        """, email, hashed_password)
        
        # Criar pessoa se não existir
        await conn.execute("""
            INSERT INTO people (id, name, tax_id, person_type, status, created_at, updated_at)
            VALUES (999, 'Admin Sistema', '00000000000', 'PF', 'active', now(), now())
            ON CONFLICT (id) DO NOTHING
        """)
        
        print("✅ Admin user criado/atualizado com bcrypt")
        return email, password
        
    finally:
        await conn.close()

def login(email: str, password: str) -> str:
    """Fazer login e retornar token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={email}&password={password}"
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Login realizado: {token_data}")
        return token_data["access_token"]
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def test_users_endpoints(token: str):
    """Testar todos os endpoints de usuários"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n=== TESTANDO ENDPOINTS USERS ===")
    
    # 1. GET /users/count
    response = requests.get(f"{BASE_URL}/users/count", headers=headers)
    print(f"GET /users/count: {response.status_code} - {response.text}")
    
    # 2. GET /users/ (listar)
    response = requests.get(f"{BASE_URL}/users/?skip=0&limit=5", headers=headers)
    print(f"GET /users/: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"  Usuários encontrados: {len(users.get('users', []))}")
    else:
        print(f"  Erro: {response.text}")
    
    # 3. GET /users/me/profile
    response = requests.get(f"{BASE_URL}/users/me/profile", headers=headers)
    print(f"GET /users/me/profile: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"  Profile: {profile.get('name')} - {profile.get('email_address')}")
    
    # 4. POST /users/ (criar usuário)
    new_user_data = {
        "person": {
            "name": "João Teste",
            "tax_id": "12345678901",
            "person_type": "PF",
            "status": "active"
        },
        "email_address": "joao.teste@example.com",
        "password": "teste123",
        "is_active": True,
        "phones": [
            {
                "number": "11999999999",
                "phone_type": "mobile"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/users/",
        headers={**headers, "Content-Type": "application/json"},
        json=new_user_data
    )
    print(f"POST /users/: {response.status_code}")
    if response.status_code == 201:
        user = response.json()
        user_id = user["user"]["id"]
        print(f"  Usuário criado: ID {user_id}")
        
        # 5. GET /users/{user_id} (buscar por ID)
        response = requests.get(f"{BASE_URL}/users/{user_id}", headers=headers)
        print(f"GET /users/{user_id}: {response.status_code}")
        
        # 6. PUT /users/{user_id} (atualizar)
        update_data = {
            "person": {
                "name": "João Teste Atualizado",
                "tax_id": "12345678901",
                "person_type": "PF", 
                "status": "active"
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/users/{user_id}",
            headers={**headers, "Content-Type": "application/json"},
            json=update_data
        )
        print(f"PUT /users/{user_id}: {response.status_code}")
        
        # 7. POST /users/{user_id}/password (alterar senha)
        password_data = {
            "current_password": "teste123",
            "new_password": "novasenha123", 
            "confirm_password": "novasenha123"
        }
        
        response = requests.post(
            f"{BASE_URL}/users/{user_id}/password",
            headers={**headers, "Content-Type": "application/json"},
            json=password_data
        )
        print(f"POST /users/{user_id}/password: {response.status_code}")
        
        # 8. DELETE /users/{user_id} (deletar)
        response = requests.delete(f"{BASE_URL}/users/{user_id}", headers=headers)
        print(f"DELETE /users/{user_id}: {response.status_code}")
        
    else:
        print(f"  Erro ao criar usuário: {response.text}")

async def main():
    """Função principal"""
    print("🚀 Iniciando teste completo do CRUD Users")
    
    # 1. Configurar usuário admin
    email, password = await setup_admin_user()
    
    # 2. Fazer login
    token = login(email, password)
    if not token:
        print("❌ Falha na autenticação. Teste abortado.")
        return
        
    # 3. Testar endpoints
    test_users_endpoints(token)
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    asyncio.run(main())