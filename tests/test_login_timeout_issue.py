"""
Teste Específico para o Problema de Timeout no Login
====================================================

Este teste reproduz exatamente o erro relatado pelo usuário:
"timeout of 10000ms exceeded" no endpoint /api/v1/auth/login

Cenário de teste:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Erro: Axios timeout após 10 segundos
"""

import time
from typing import Any, Dict

import pytest
import requests


class TestLoginTimeoutIssue:
    """Testes específicos para o problema de timeout no login"""

    FRONTEND_URL = "http://localhost:3000"
    BACKEND_URL = "http://localhost:8000"
    TIMEOUT_FRONTEND = 10  # Mesmo timeout do frontend (10s)
    TIMEOUT_TEST = 5  # Timeout menor para testes rápidos

    def test_exact_login_scenario(self):
        """Reproduz exatamente o cenário de erro do usuário"""
        # Simula os dados que o frontend envia
        login_data = {
            "username": "admin@example.com",  # Usuário padrão
            "password": "password",
        }

        # Headers que o frontend usa
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        print("🔍 Testando login via proxy do frontend...")
        print(f"URL: {self.FRONTEND_URL}/api/v1/auth/login")
        print(f"Data: {login_data}")
        print(f"Timeout: {self.TIMEOUT_FRONTEND}s")

        start_time = time.time()

        try:
            # Requisição idêntica ao que o frontend faz
            response = requests.post(
                f"{self.FRONTEND_URL}/api/v1/auth/login",
                data=login_data,
                headers=headers,
                timeout=self.TIMEOUT_FRONTEND,
            )

            elapsed = time.time() - start_time
            print(".2f")
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ Login bem-sucedido via proxy!")
                return True
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            pytest.fail(
                f"❌ TIMEOUT EXATO REPRODUZIDO: {elapsed:.2f}s\n"
                "Problema confirmado: Frontend não consegue conectar ao backend via proxy.\n"
                "Solução: Corrigir vite.config.ts para apontar para localhost:8000"
            )

        except requests.exceptions.ConnectionError as e:
            pytest.fail(
                f"❌ Erro de conexão: {e}\n"
                "Verificar se o frontend está rodando na porta 3000"
            )

        except Exception as e:
            pytest.fail(f"❌ Erro inesperado: {e}")

    def test_backend_login_direct(self):
        """Verifica se o backend responde diretamente ao login"""
        login_data = {"username": "admin@example.com", "password": "password"}

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                f"{self.BACKEND_URL}/api/v1/auth/login",
                data=login_data,
                headers=headers,
                timeout=self.TIMEOUT_TEST,
            )

            print(f"✅ Backend direto: {response.status_code}")
            return response.status_code in [200, 401, 422]  # Sucesso ou erro esperado

        except Exception as e:
            print(f"❌ Backend direto falhou: {e}")
            return False

    def test_cors_headers(self):
        """Testa se os headers CORS estão configurados corretamente"""
        try:
            # Testa OPTIONS request (preflight)
            response = requests.options(
                f"{self.FRONTEND_URL}/api/v1/auth/login", timeout=self.TIMEOUT_TEST
            )

            cors_headers = {
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers",
            }

            present_headers = set(response.headers.keys()) & cors_headers

            print(f"✅ CORS headers presentes: {present_headers}")

            if present_headers:
                return True
            else:
                print("⚠️  Nenhum header CORS encontrado")
                return False

        except Exception as e:
            print(f"❌ Erro no teste CORS: {e}")
            return False

    def test_proxy_configuration(self):
        """Verifica se o proxy está configurado para o backend correto"""
        # Tenta acessar o backend através do proxy
        try:
            response = requests.get(
                f"{self.FRONTEND_URL}/api/v1/health", timeout=self.TIMEOUT_TEST
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Proxy funcionando corretamente")
                    return True

            print(
                f"❌ Proxy não está redirecionando corretamente: {response.status_code}"
            )
            return False

        except requests.exceptions.Timeout:
            print("❌ Proxy timeout - configuração incorreta")
            return False
        except Exception as e:
            print(f"❌ Erro no proxy: {e}")
            return False

    def test_network_connectivity(self):
        """Testa conectividade básica de rede"""
        results = {}

        # Testa backend direto
        try:
            response = requests.get(f"{self.BACKEND_URL}/api/v1/health", timeout=2)
            results["backend_direct"] = response.status_code == 200
        except:
            results["backend_direct"] = False

        # Testa frontend
        try:
            response = requests.get(f"{self.FRONTEND_URL}", timeout=2)
            results["frontend"] = response.status_code == 200
        except:
            results["frontend"] = False

        # Testa proxy
        try:
            response = requests.get(f"{self.FRONTEND_URL}/api/v1/health", timeout=2)
            results["proxy"] = response.status_code == 200
        except:
            results["proxy"] = False

        print("📊 Status da conectividade:")
        for service, status in results.items():
            print(f"  {service}: {'✅' if status else '❌'}")

        return results

    @pytest.mark.parametrize(
        "endpoint", ["/api/v1/auth/login", "/api/v1/health", "/api/v1/companies/"]
    )
    def test_multiple_endpoints_via_proxy(self, endpoint: str):
        """Testa múltiplos endpoints via proxy"""
        try:
            if endpoint == "/api/v1/auth/login":
                response = requests.post(
                    f"{self.FRONTEND_URL}{endpoint}",
                    data={"username": "test", "password": "test"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=self.TIMEOUT_TEST,
                )
            else:
                response = requests.get(
                    f"{self.FRONTEND_URL}{endpoint}", timeout=self.TIMEOUT_TEST
                )

            assert response.status_code in [200, 401, 422, 500]

        except requests.exceptions.Timeout:
            pytest.fail(f"Timeout no endpoint {endpoint} via proxy")
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Connection error no endpoint {endpoint} via proxy")


if __name__ == "__main__":
    # Executar diagnóstico completo
    test = TestLoginTimeoutIssue()

    print("🔬 DIAGNÓSTICO COMPLETO - Problema de Timeout no Login")
    print("=" * 60)

    # 1. Conectividade básica
    print("\n1. Testando conectividade básica...")
    connectivity = test.test_network_connectivity()

    # 2. Backend direto
    print("\n2. Testando backend diretamente...")
    backend_ok = test.test_backend_login_direct()

    # 3. CORS
    print("\n3. Testando configuração CORS...")
    cors_ok = test.test_cors_headers()

    # 4. Proxy
    print("\n4. Testando configuração do proxy...")
    proxy_ok = test.test_proxy_configuration()

    # 5. Cenário exato do erro
    print("\n5. Reproduzindo cenário exato do erro...")
    try:
        test.test_exact_login_scenario()
        login_ok = True
    except:
        login_ok = False

    print("\n" + "=" * 60)
    print("📋 RESUMO DO DIAGNÓSTICO:")
    print(f"   Backend direto: {'✅' if connectivity['backend_direct'] else '❌'}")
    print(f"   Frontend: {'✅' if connectivity['frontend'] else '❌'}")
    print(f"   Proxy: {'✅' if connectivity['proxy'] else '❌'}")
    print(f"   CORS: {'✅' if cors_ok else '❌'}")
    print(f"   Login via proxy: {'✅' if login_ok else '❌'}")

    if not connectivity["proxy"]:
        print("\n🎯 PROBLEMA IDENTIFICADO:")
        print("   O proxy do Vite não está funcionando corretamente.")
        print("   Verificar vite.config.ts - target deve ser localhost:8000")

    if not login_ok:
        print("\n🚨 ERRO CONFIRMADO:")
        print("   Timeout de 10s no login reproduzido com sucesso.")
        print("   Correção necessária na configuração do proxy.")
