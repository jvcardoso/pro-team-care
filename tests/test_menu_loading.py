"""
Teste para carregamento de menus laterais - Pro Team Care
Gera relatório de testes automatizados para o sistema de menus dinâmicos
"""

import pytest
import requests
import json
from datetime import datetime


class MenuLoadingTester:
    """Tester para sistema de carregamento de menus"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test_result(self, test_name, status, details=None, error=None):
        """Registra resultado do teste"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error": str(error) if error else None
        }
        self.test_results.append(result)
        print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")

    def test_backend_health(self):
        """Testa se o backend está saudável"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "Backend Health Check",
                    "PASS",
                    f"Status: {data.get('status')}, Service: {data.get('service')}"
                )
                return True
            else:
                self.log_test_result("Backend Health Check", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Backend Health Check", "ERROR", error=e)
            return False

    def test_debug_menus_endpoint(self):
        """Testa endpoint de debug de menus (público)"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/debug/menus-public")
            if response.status_code == 200:
                data = response.json()
                menu_count = len(data.get('tree', []))
                self.log_test_result(
                    "Debug Menus Endpoint",
                    "PASS",
                    f"Menus retornados: {menu_count}, Status: {data.get('status')}"
                )
                return True
            else:
                self.log_test_result("Debug Menus Endpoint", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Debug Menus Endpoint", "ERROR", error=e)
            return False

    def test_main_menus_endpoint_unauthenticated(self):
        """Testa endpoint principal sem autenticação (deve falhar)"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/menus/crud/tree")
            if response.status_code == 401:
                self.log_test_result(
                    "Main Menus Endpoint (Unauthenticated)",
                    "PASS",
                    "Corretamente rejeitou acesso não autorizado"
                )
                return True
            else:
                self.log_test_result(
                    "Main Menus Endpoint (Unauthenticated)",
                    "FAIL",
                    f"Status inesperado: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test_result("Main Menus Endpoint (Unauthenticated)", "ERROR", error=e)
            return False

    def test_frontend_menu_hook_simulation(self):
        """Simula o comportamento do hook useDynamicMenus"""
        try:
            # Simular falta de token
            has_token = False  # Simulando cenário do erro reportado

            if not has_token:
                self.log_test_result(
                    "Frontend Hook - Token Check",
                    "FAIL",
                    "Token de acesso não encontrado (cenário do erro reportado)"
                )
                return False

            # Se tivesse token, testaria o endpoint
            response = self.session.get(f"{self.base_url}/api/v1/menus/crud/tree")
            if response.status_code == 200:
                self.log_test_result("Frontend Hook - Authenticated Request", "PASS")
                return True
            else:
                self.log_test_result("Frontend Hook - Authenticated Request", "FAIL")
                return False

        except Exception as e:
            self.log_test_result("Frontend Hook Simulation", "ERROR", error=e)
            return False

    def test_menu_structure_validation(self):
        """Valida estrutura dos menus retornados"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/debug/menus-public")
            if response.status_code == 200:
                data = response.json()
                tree = data.get('tree', [])

                # Validar estrutura básica
                required_fields = ['id', 'name', 'url', 'children']
                valid_structure = True

                for menu in tree:
                    for field in required_fields:
                        if field not in menu:
                            valid_structure = False
                            break
                    if not valid_structure:
                        break

                if valid_structure:
                    self.log_test_result(
                        "Menu Structure Validation",
                        "PASS",
                        f"Estrutura válida para {len(tree)} menus"
                    )
                    return True
                else:
                    self.log_test_result("Menu Structure Validation", "FAIL", "Campos obrigatórios faltando")
                    return False
            else:
                self.log_test_result("Menu Structure Validation", "SKIP", "Endpoint não disponível")
                return False
        except Exception as e:
            self.log_test_result("Menu Structure Validation", "ERROR", error=e)
            return False

    def generate_report(self):
        """Gera relatório completo dos testes"""
        report = {
            "test_suite": "Menu Loading Tests",
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed": len([r for r in self.test_results if r['status'] == 'PASS']),
            "failed": len([r for r in self.test_results if r['status'] == 'FAIL']),
            "errors": len([r for r in self.test_results if r['status'] == 'ERROR']),
            "results": self.test_results
        }

        return report

    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando testes de carregamento de menus...")
        print("=" * 50)

        self.test_backend_health()
        self.test_debug_menus_endpoint()
        self.test_main_menus_endpoint_unauthenticated()
        self.test_frontend_menu_hook_simulation()
        self.test_menu_structure_validation()

        print("=" * 50)
        report = self.generate_report()

        # Salvar relatório
        with open('menu_loading_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 Relatório salvo em: menu_loading_test_report.json")
        print(f"✅ Passaram: {report['passed']}")
        print(f"❌ Falharam: {report['failed']}")
        print(f"🔧 Erros: {report['errors']}")

        return report


def main():
    """Função principal para executar os testes"""
    tester = MenuLoadingTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    main()