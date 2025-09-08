#!/usr/bin/env python3
"""
Script para testar os endpoints hierárquicos
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Obter token de autenticação"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin@proteamcare.com", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None

def test_hierarchical_endpoints():
    """Testar todos os endpoints hierárquicos"""
    
    print("🔐 Fazendo login...")
    token = get_auth_token()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Testar informações da hierarquia atual
    print("\n📊 Testando informações da hierarquia...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/hierarchy-info", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Hierarquia: {data.get('hierarchy_level', 'Unknown')}")
        print(f"   Usuário: {data.get('user_email')}")
        print(f"   Usuários acessíveis: {data.get('accessible_users_count', 0)}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
    
    # 2. Testar listagem hierárquica
    print("\n👥 Testando listagem hierárquica...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/hierarchical", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Usuários encontrados: {data.get('total', 0)}")
        print(f"   Nível do solicitante: {data.get('requesting_user_hierarchy')}")
        
        for user in data.get('users', [])[:3]:  # Mostrar apenas os primeiros 3
            print(f"   - {user.get('person_name')} ({user.get('user_email')}) - {user.get('hierarchy_level', 'N/A')}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
    
    # 3. Testar usuário específico
    print("\n🔍 Testando acesso a usuário específico...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/1/hierarchical", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Usuário acessado: {data.get('person_name', 'N/A')}")
        print(f"   Email: {data.get('user_email', 'N/A')}")
        print(f"   Motivo do acesso: {data.get('_access_metadata', {}).get('access_reason', 'N/A')}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
    
    # 4. Testar resumo de usuários acessíveis
    print("\n📈 Testando resumo de usuários acessíveis...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/accessible-users-summary", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Total de usuários acessíveis: {data.get('total_accessible_users', 0)}")
        print(f"   Por hierarquia: {data.get('by_hierarchy', {})}")
        print(f"   Por nível de acesso: {data.get('by_access_level', {})}")
    else:
        print(f"❌ Erro: {response.status_code} - {response.text}")
    
    # 5. Testar com filtros
    print("\n🔎 Testando filtros...")
    response = requests.get(f"{BASE_URL}/api/v1/hierarchical-users/hierarchical?search=admin", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Busca por 'admin': {data.get('total', 0)} usuários encontrados")
    else:
        print(f"❌ Erro na busca: {response.status_code} - {response.text}")

def test_sql_function():
    """Testar função SQL diretamente"""
    print("\n🗄️ Testando função SQL...")
    import subprocess
    
    try:
        result = subprocess.run([
            'psql', '-h', '192.168.11.62', '-p', '5432', '-U', 'postgres', '-d', 'pro_team_care_11',
            '-c', 'SELECT count(*) as total FROM master.get_accessible_users_hierarchical(5);'
        ], env={'PGPASSWORD': 'Jvc@1702'}, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Função SQL funcionando: {result.stdout.strip()}")
        else:
            print(f"❌ Erro na função SQL: {result.stderr}")
    except Exception as e:
        print(f"❌ Erro ao executar psql: {e}")

if __name__ == "__main__":
    print("🚀 TESTANDO SISTEMA HIERÁRQUICO")
    print("=" * 50)
    
    test_hierarchical_endpoints()
    test_sql_function()
    
    print("\n✅ Testes concluídos!")
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")