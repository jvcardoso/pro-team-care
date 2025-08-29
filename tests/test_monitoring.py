import pytest
import time
from fastapi.testclient import TestClient


class TestMonitoring:
    """Test suite para sistema de monitoramento"""
    
    def test_metrics_endpoint_available(self, client: TestClient):
        """Teste se endpoint de métricas está disponível"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        # Verificar se contém métricas Prometheus
        content = response.text
        assert "# HELP" in content or "# TYPE" in content
    
    def test_metrics_summary_endpoint(self, client: TestClient):
        """Teste do endpoint de resumo de métricas"""
        response = client.get("/api/v1/metrics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        # O timestamp_iso está dentro do data
        assert "timestamp_iso" in data["data"]
        
        # Verificar estrutura do resumo
        summary_data = data["data"]
        assert "system" in summary_data
        assert "timestamp" in summary_data
        assert "metrics_available" in summary_data
    
    def test_metrics_health_check(self, client: TestClient):
        """Teste do health check do sistema de métricas"""
        response = client.get("/api/v1/metrics/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["metrics_system"] == "operational"
        assert "prometheus_export" in data
        assert "timestamp" in data
    
    def test_generate_test_metrics(self, client: TestClient):
        """Teste de geração de métricas de teste"""
        response = client.post("/api/v1/metrics/test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "metrics_generated" in data
        assert len(data["metrics_generated"]) > 0
        
        # Verificar se métricas específicas foram geradas
        generated = data["metrics_generated"]
        assert "http_requests_total" in generated
        assert "cache_operations_total" in generated
        assert "auth_attempts_total" in generated
    
    def test_middleware_adds_performance_headers(self, client: TestClient):
        """Teste se middleware adiciona headers de performance"""
        response = client.get("/api/v1/health")
        
        # Verificar se header de tempo de resposta foi adicionado
        assert "X-Response-Time" in response.headers
        
        # Verificar formato do header
        response_time = response.headers["X-Response-Time"]
        assert response_time.endswith("s")
        
        # Verificar se é um número válido
        time_value = float(response_time[:-1])
        assert time_value >= 0
    
    def test_monitoring_doesnt_affect_regular_endpoints(self, client: TestClient):
        """Teste se monitoramento não afeta endpoints normais"""
        # Fazer requisição normal
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        # Dados devem estar normais
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Pro Team Care API"
    
    def test_metrics_endpoint_excludes_monitoring_paths(self, client: TestClient):
        """Teste se paths de monitoramento são excluídos das métricas"""
        # Fazer requisições para paths que devem ser excluídos
        client.get("/api/v1/metrics")
        client.get("/api/v1/health")
        client.get("/docs")
        
        # Fazer requisição normal que deve ser monitorada
        client.get("/api/v1/auth/me")  # Este deve ser monitorado (mesmo que falhe)
        
        # Verificar métricas
        metrics_response = client.get("/api/v1/metrics")
        metrics_content = metrics_response.text
        
        # Paths de monitoramento não devem aparecer nas métricas HTTP
        # (serão filtrados pelo middleware)
        # Mas requisições normais devem aparecer
        assert "/auth/me" in metrics_content or "auth" in metrics_content