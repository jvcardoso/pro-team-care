# Análise Técnica: DevOps e Infraestrutura

- **ID da Tarefa:** PTC-006
- **Projeto:** Pro Team Care - Sistema de Gestão Home Care
- **Autor:** Arquiteto de Soluções Sênior
- **Data:** 01/09/2025
- **Versão:** 1.0
- **Status:** Aprovado para Desenvolvimento

## 📋 Resumo Executivo

Esta análise técnica examina o pipeline CI/CD, estratégias de deployment, containerização, monitoramento em produção, backup/recovery e configurações de infraestrutura para garantir alta disponibilidade e confiabilidade.

## 🎯 Objetivos da Análise

1. **Avaliar** pipeline CI/CD atual e melhorias necessárias
2. **Analisar** estratégias de deployment e rollback
3. **Verificar** containerização e orquestração
4. **Examinar** monitoramento, logging e alertas
5. **Identificar** necessidades de backup e disaster recovery

## 🔍 Metodologia dos 5 Porquês

### **Por que precisamos auditar DevOps e infraestrutura?**
**R:** Para garantir deployments seguros, rollbacks rápidos e alta disponibilidade do sistema em produção.

### **Por que DevOps é crítico em sistemas healthcare?**
**R:** Porque downtime pode interromper atendimento a pacientes e deployments mal sucedidos podem comprometer dados críticos.

### **Por que automatização é essencial?**
**R:** Porque processos manuais são propensos a erros e não escalam com o crescimento do sistema.

### **Por que monitoramento proativo é fundamental?**
**R:** Porque detectar problemas antes que afetem usuários é mais barato e seguro que reagir a incidentes.

### **Por que implementar infraestrutura como código agora?**
**R:** Porque ambientes reproduzíveis e versionados reduzem bugs específicos de ambiente e facilitam disaster recovery.

## 📊 Análise da Implementação Atual

### **✅ Pontos Fortes Identificados**

1. **Pipeline CI/CD Estruturado**
   ```yaml
   # .github/workflows/ci.yml - Pipeline bem organizado
   jobs:
     test-backend:    # ✅ Testes backend com PostgreSQL
     test-frontend:   # ✅ Testes frontend com Node.js
     security-scan:   # ✅ Security scan com bandit
     quality-check:   # ✅ Quality gates (black, flake8, mypy)
   ```

2. **Scripts de Automação**
   ```bash
   # start_simple.sh - Script robusto com:
   # ✅ Verificação de sistema
   # ✅ Health checks automáticos
   # ✅ Cleanup de processos
   # ✅ Tratamento de erros
   ```

3. **Configuração Flexível**
   ```python
   # settings.py - Environment-specific config
   env_files = [f".env.{env}", ".env"]  # ✅ Multi-environment
   ```

4. **Database Migration Strategy**
   ```yaml
   # CI pipeline inclui Alembic migrations
   - name: Run database migrations
     run: alembic upgrade head  # ✅ Automated migrations
   ```

### **🚨 Problemas Críticos Identificados**

1. **Falta de Containerização**
   - **Localização:** Ausência de Docker/Kubernetes
   - **Problema:** Deploy manual sem padronização de ambiente
   - **Impacto:** Alto - dificuldade de escalabilidade e reprodutibilidade

2. **Monitoramento Insuficiente**
   - **Localização:** Sem APM (Application Performance Monitoring)
   - **Problema:** Visibilidade limitada do sistema em produção
   - **Impacto:** Alto - dificuldade de diagnóstico de problemas

3. **Ausência de Backup Strategy**
   - **Localização:** Sem estratégia de backup documentada
   - **Problema:** Risco de perda de dados críticos
   - **Impacto:** Crítico - violação de compliance em healthcare

4. **Deployment Manual**
   - **Localização:** Pipeline CI não inclui auto-deploy
   - **Problema:** Process error-prone e lento
   - **Impacto:** Médio - impacta velocidade de entrega

## 🎯 Especificações Técnicas para Correção

### **1. Containerização Completa**

**Arquivos a Criar:**
```
Dockerfile                              # Backend container
frontend/Dockerfile                     # Frontend container  
docker-compose.yml                      # Desenvolvimento local
docker-compose.prod.yml                 # Produção
.dockerignore                           # Otimização de build
kubernetes/                             # K8s manifests (opcional)
```

**Backend Dockerfile (Multi-stage):**
```dockerfile
# Dockerfile
# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION

# Copy dependency files
WORKDIR /app
COPY pyproject.toml poetry.lock* requirements.txt ./

# Install Python dependencies
RUN if [ -f "pyproject.toml" ]; then \
        poetry config virtualenvs.create false && \
        poetry install --only=main --no-root; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Production stage
FROM python:3.11-slim as production

# Install system dependencies for production
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set ownership and permissions
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
# frontend/Dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose para Produção:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: pro-team-care-backend
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    volumes:
      - /app/logs:/app/logs
    networks:
      - app-network
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    container_name: pro-team-care-frontend
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - app-network
    depends_on:
      - backend

  postgres:
    image: postgres:16-alpine
    container_name: pro-team-care-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_DATABASE}
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME} -d ${DB_DATABASE}"]
      interval: 30s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: pro-team-care-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 3s
      retries: 5

  nginx:
    image: nginx:alpine
    container_name: pro-team-care-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    networks:
      - app-network
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  app-network:
    driver: bridge
```

### **2. Pipeline CI/CD Avançado**

**Workflow de Deploy Completo:**
```yaml
# .github/workflows/deploy.yml
name: Production Deploy

on:
  push:
    branches: [main]
  release:
    types: [published]

env:
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    outputs:
      backend-image: ${{ steps.meta-backend.outputs.tags }}
      frontend-image: ${{ steps.meta-frontend.outputs.tags }}
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.DOCKER_REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata for backend
      id: meta-backend
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}/backend
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push backend
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta-backend.outputs.tags }}
        labels: ${{ steps.meta-backend.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        target: production
    
    - name: Extract metadata for frontend
      id: meta-frontend
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}/frontend
        tags: |
          type=ref,event=branch
          type=ref,event=pr  
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push frontend
      uses: docker/build-push-action@v5
      with:
        context: ./frontend
        push: true
        tags: ${{ steps.meta-frontend.outputs.tags }}
        labels: ${{ steps.meta-frontend.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: [build-and-push]
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Setup SSH
      uses: webfactory/ssh-agent@v0.8.0
      with:
        ssh-private-key: ${{ secrets.DEPLOY_SSH_KEY }}
    
    - name: Deploy to production
      run: |
        ssh -o StrictHostKeyChecking=no ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }} << 'EOF'
          cd /opt/pro-team-care
          
          # Backup current deployment
          docker-compose -f docker-compose.prod.yml down --timeout 60
          
          # Pull latest images
          docker pull ${{ needs.build-and-push.outputs.backend-image }}
          docker pull ${{ needs.build-and-push.outputs.frontend-image }}
          
          # Update docker-compose with new image tags
          sed -i 's|image: .*backend.*|image: ${{ needs.build-and-push.outputs.backend-image }}|g' docker-compose.prod.yml
          sed -i 's|image: .*frontend.*|image: ${{ needs.build-and-push.outputs.frontend-image }}|g' docker-compose.prod.yml
          
          # Run database migrations
          docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
          
          # Deploy new version
          docker-compose -f docker-compose.prod.yml up -d
          
          # Health check
          sleep 30
          curl -f http://localhost/api/v1/health || exit 1
          
          echo "✅ Deployment successful"
        EOF
    
    - name: Notify deployment
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: |
          🚀 Production deployment ${{ job.status }}
          Commit: ${{ github.sha }}
          Author: ${{ github.actor }}
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### **3. Monitoramento e Observabilidade**

**Prometheus + Grafana Stack:**
```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring

  loki:
    image: grafana/loki:2.9.0
    container_name: loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - ./loki/loki-config.yml:/etc/loki/loki-config.yml
      - loki_data:/loki
    command: -config.file=/etc/loki/loki-config.yml
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:2.9.0
    container_name: promtail
    restart: unless-stopped
    volumes:
      - ./promtail/promtail-config.yml:/etc/promtail/promtail-config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/promtail-config.yml
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  loki_data:

networks:
  monitoring:
    driver: bridge
```

### **4. Backup e Disaster Recovery**

**Script de Backup Automatizado:**
```bash
#!/bin/bash
# scripts/backup.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/backups/pro-team-care"
S3_BUCKET="pro-team-care-backups"
RETENTION_DAYS=30
DB_CONTAINER="pro-team-care-postgres"
REDIS_CONTAINER="pro-team-care-redis"

# Create backup directory
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

echo "🔄 Starting backup: $BACKUP_NAME"

# Database backup
echo "📊 Backing up PostgreSQL..."
docker exec "$DB_CONTAINER" pg_dump -U postgres pro_team_care_11 | gzip > "${BACKUP_NAME}_postgres.sql.gz"

# Redis backup
echo "🔴 Backing up Redis..."
docker exec "$REDIS_CONTAINER" redis-cli --rdb /data/dump.rdb
docker cp "$REDIS_CONTAINER:/data/dump.rdb" "${BACKUP_NAME}_redis.rdb"

# Application files backup
echo "📁 Backing up application files..."
tar -czf "${BACKUP_NAME}_files.tar.gz" \
    /opt/pro-team-care/.env* \
    /opt/pro-team-care/docker-compose*.yml \
    /opt/pro-team-care/nginx/ \
    /opt/pro-team-care/logs/ \
    --exclude='*.log'

# Create manifest
echo "📋 Creating backup manifest..."
cat > "${BACKUP_NAME}_manifest.json" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$TIMESTAMP",
  "files": {
    "postgres": "${BACKUP_NAME}_postgres.sql.gz",
    "redis": "${BACKUP_NAME}_redis.rdb", 
    "files": "${BACKUP_NAME}_files.tar.gz"
  },
  "checksums": {
    "postgres": "$(md5sum ${BACKUP_NAME}_postgres.sql.gz | cut -d' ' -f1)",
    "redis": "$(md5sum ${BACKUP_NAME}_redis.rdb | cut -d' ' -f1)",
    "files": "$(md5sum ${BACKUP_NAME}_files.tar.gz | cut -d' ' -f1)"
  }
}
EOF

# Upload to S3 (if configured)
if command -v aws >/dev/null 2>&1 && [ -n "${S3_BUCKET:-}" ]; then
    echo "☁️  Uploading to S3..."
    aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/$(date +%Y/%m)/" \
        --exclude "*" --include "${BACKUP_NAME}*"
fi

# Cleanup old backups
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "backup_*" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed: $BACKUP_NAME"

# Health check notification
curl -X POST "${HEALTHCHECK_URL:-}" \
    -H "Content-Type: application/json" \
    -d "{\"status\": \"success\", \"backup\": \"$BACKUP_NAME\"}" \
    2>/dev/null || true
```

## 🧪 Casos de Teste Necessários

### **Testes de Infraestrutura**
```python
# tests/infrastructure/test_deployment.py
import pytest
import requests
import docker
import time

def test_docker_containers_health():
    """Testar saúde dos containers Docker"""
    client = docker.from_env()
    
    containers = [
        'pro-team-care-backend',
        'pro-team-care-frontend', 
        'pro-team-care-postgres',
        'pro-team-care-redis'
    ]
    
    for container_name in containers:
        container = client.containers.get(container_name)
        assert container.status == 'running'
        
        # Check health status if available
        if container.attrs['Config'].get('Healthcheck'):
            health = container.attrs['State']['Health']['Status']
            assert health == 'healthy'

def test_deployment_rollback():
    """Testar processo de rollback"""
    # Simular deployment com falha
    # Verificar se rollback funciona automaticamente
    pass

def test_backup_and_restore():
    """Testar processo de backup e restore"""
    # Executar backup
    # Simular perda de dados
    # Executar restore
    # Verificar integridade dos dados
    pass

@pytest.mark.integration
def test_monitoring_endpoints():
    """Testar endpoints de monitoramento"""
    endpoints = [
        'http://localhost:9090/metrics',  # Prometheus
        'http://localhost:3001/api/health',  # Grafana  
        'http://localhost/api/v1/health'  # Application
    ]
    
    for endpoint in endpoints:
        response = requests.get(endpoint, timeout=10)
        assert response.status_code == 200
```

## 🚨 Riscos e Mitigações

### **Risco Crítico: Downtime Durante Deploy**
- **Mitigação:** Blue-green deployment strategy
- **Estratégia:** Zero-downtime deployments com health checks

### **Risco Alto: Perda de Dados**
- **Mitigação:** Backups automáticos e replicação
- **Estratégia:** RPO < 1 hora, RTO < 30 minutos

### **Risco Médio: Monitoramento Inadequado**
- **Mitigação:** APM completo e alertas proativos
- **Estratégia:** SLA/SLO definition e monitoring

## 📈 Métricas de Sucesso

1. **Deployment Success Rate:** > 98%
2. **Mean Time to Recovery (MTTR):** < 30 minutes
3. **System Uptime:** > 99.9%
4. **Backup Success Rate:** 100%
5. **Alert Response Time:** < 5 minutes

## 🛠️ Cronograma de Implementação

### **Sprint 1 (1 semana)**
- Containerização completa (Docker)
- Pipeline CI/CD com auto-deploy
- Scripts de backup básicos

### **Sprint 2 (1 semana)**
- Stack de monitoramento (Prometheus/Grafana)
- Health checks e alertas
- Testes de infraestrutura

### **Sprint 3 (1 semana)**
- Disaster recovery procedures
- Load testing e capacity planning
- Documentation e runbooks

## ✅ Critérios de Aceitação

1. ✅ Aplicação containerizada e rodando em Docker
2. ✅ Pipeline CI/CD com deploy automático
3. ✅ Monitoramento completo implementado
4. ✅ Backups automáticos funcionando
5. ✅ Rollback strategy testada
6. ✅ Uptime > 99.9% em ambiente de produção

---
**Próxima Análise:** Redundância e Otimização (Fase 7)