"""
Teste de conectividade entre Frontend e Backend
===========================================

Este teste verifica a conectividade entre o frontend React e o backend FastAPI,
reproduzindo o erro de timeout relatado no login.

Problema identificado:
- Frontend roda na porta 3000 (Vite)
- Backend roda na porta 8000 (FastAPI)
- Proxy do Vite configurado incorretamente (aponta para IP remoto)
- Resultado: Timeout de 10s no login
"""

import pytest
import requests
import time
from typing import Dict, Any


class TestFrontendBackendConnectivity:
    """Testes de conectividade frontend-backend"""

    FRONTEND_URL = "http://localhost:3000"
    BACKEND_URL = "http://localhost:8000"
    TIMEOUT = 5  # segundos

    def test_backend_health_direct(self):
        """Testa se o backend responde diretamente"""
        response = requests.get(f"{self.BACKEND_URL}/api/v1/health", timeout=self.TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_frontend_proxy_health(self):
        """Testa se o proxy do frontend funciona para health check"""
        response = requests.get(f"{self.FRONTEND_URL}/api/v1/health", timeout=self.TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_frontend_proxy_login_timeout(self):
        """Reproduz o erro de timeout no login via proxy"""
        # Simula a requisição que o frontend faz
        payload = {"username": "test@example.com", "password": "test123"}

        start_time = time.time()
        try:
            response = requests.post(
                f"{self.FRONTEND_URL}/api/v1/auth/login",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10  # Mesmo timeout do frontend
            )
            elapsed = time.time() - start_time
            print(f"Request completed in {elapsed:.2f}s")
            # Se chegou aqui, o proxy está funcionando
            assert response.status_code in [200, 401, 422]  # Sucesso ou erro esperado

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            pytest.fail(
                f"Frontend proxy timeout após {elapsed:.2f}s. "
                f"Problema: Proxy do Vite não está redirecionando corretamente para o backend. "
                f"Verificar configuração em vite.config.ts"
            )

        except requests.exceptions.ConnectionError:
            pytest.fail(
                "Frontend proxy não consegue conectar ao backend. "
                "Verificar se o backend está rodando e se o proxy está configurado corretamente."
            )

    def test_backend_login_endpoint_direct(self):
        """Testa o endpoint de login diretamente no backend"""
        payload = {"username": "test@example.com", "password": "test123"}

        response = requests.post(
            f"{self.BACKEND_URL}/api/v1/auth/login",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=self.TIMEOUT
        )

        # Pode retornar erro de autenticação, mas não deve dar timeout
        assert response.status_code in [200, 401, 422, 500]
        # Se for 500, pode indicar problema no banco ou configuração

    def test_vite_config_proxy_target(self):
        """Testa se o target do proxy do Vite está acessível"""
        # O proxy está configurado para 192.168.11.62:8000
        # Mas o backend está rodando em localhost:8000
        remote_target = "http://192.168.11.62:8000"

        try:
            response = requests.get(f"{remote_target}/api/v1/health", timeout=self.TIMEOUT)
            assert response.status_code == 200
            print("✅ Proxy target remoto está acessível")
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            pytest.fail(
                f"Proxy do Vite aponta para {remote_target} mas não está acessível. "
                "O backend está rodando localmente em localhost:8000. "
                "Corrigir vite.config.ts para apontar para o backend local."
            )

    @pytest.mark.parametrize("endpoint", [
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/companies/",
    ])
    def test_frontend_proxy_endpoints(self, endpoint: str):
        """Testa múltiplos endpoints via proxy do frontend"""
        try:
            if endpoint == "/api/v1/auth/login":
                # Para login, usar método POST com dados
                response = requests.post(
                    f"{self.FRONTEND_URL}{endpoint}",
                    data={"username": "test", "password": "test"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=self.TIMEOUT
                )
            else:
                response = requests.get(f"{self.FRONTEND_URL}{endpoint}", timeout=self.TIMEOUT)

            assert response.status_code in [200, 401, 422, 500]

        except requests.exceptions.Timeout:
            pytest.fail(f"Timeout no endpoint {endpoint} via proxy do frontend")
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Connection error no endpoint {endpoint} via proxy do frontend")


if __name__ == "__main__":
    # Executar testes manualmente para debug
    test = TestFrontendBackendConnectivity()

    print("🔍 Testando conectividade frontend-backend...")
    print()

    try:
        print("1. Testando backend direto...")
        test.test_backend_health_direct()
        print("✅ Backend direto OK")
    except Exception as e:
        print(f"❌ Backend direto falhou: {e}")

    try:
        print("2. Testando proxy do frontend...")
        test.test_frontend_proxy_health()
        print("✅ Proxy do frontend OK")
    except Exception as e:
        print(f"❌ Proxy do frontend falhou: {e}")

    try:
        print("3. Testando login via proxy...")
        test.test_frontend_proxy_login_timeout()
        print("✅ Login via proxy OK")
    except Exception as e:
        print(f"❌ Login via proxy falhou: {e}")

    print()
    print("📋 Diagnóstico:")
    print("- Backend está rodando em localhost:8000")
    print("- Frontend está rodando em localhost:3000")
    print("- Proxy do Vite aponta para 192.168.11.62:8000 (remoto)")
    print("- Problema: Proxy não consegue alcançar o backend local")
    print()
    print("🔧 Solução sugerida:")
    print("Alterar vite.config.ts para apontar para localhost:8000 ou 192.168.11.83:8000")