# 🚀 Pro Team Care - Sistema de Gestão Home Care

[![CI/CD Pipeline](https://github.com/your-org/pro-team-care/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/pro-team-care/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)](https://github.com/your-org/pro-team-care)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://reactjs.org/)

Sistema completo para gerenciamento de empresas de Home Care, desenvolvido com **arquitetura enterprise** baseada em Clean Architecture. Oferece controle total sobre pacientes, profissionais, agendamentos e operações de cuidados domiciliares com foco em conformidade regulatória e segurança de dados.

## 🎯 **Visão Geral**

O **Pro Team Care** é uma solução enterprise para empresas de **Home Care**, construída com as melhores práticas de desenvolvimento:

- 🏗️ **Clean Architecture** (Arquitetura Hexagonal)
- 🔐 **Segurança Enterprise** (JWT, CORS, CSP, Rate Limiting)
- 📊 **Observabilidade Completa** (Logs estruturados, métricas, health checks)
- 🚀 **Performance Otimizada** (Redis cache, connection pooling)
- 🧪 **Qualidade Garantida** (Testes automatizados, CI/CD, pre-commit hooks)
- 📱 **Frontend Moderno** (React 18 + Tailwind CSS + Vite)

## 🚀 **Início Rápido**

### Pré-requisitos
- **Python 3.11+**
- **PostgreSQL** (banco remoto já configurado)
- **Node.js 18+** (opcional, para desenvolvimento frontend)
- **Redis** (opcional, para cache avançado)

### 🚀 **Inicialização Rápida (Recomendado)**

```bash
# Opção 1: Backend + Frontend (completo)
./start_simple.sh

# Opção 2: Apenas backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Opção 3: Parar todos os serviços
./stop_servers.sh
```

### 📦 **Instalação Manual**

```bash
# 1. Instalar dependências Python
pip install -r requirements.txt

# 2. Instalar pre-commit hooks (recomendado)
./scripts/install-hooks.sh

# 3. Executar migrações do banco
alembic upgrade head

# 4. Executar aplicação
uvicorn app.main:app --reload
```

## 📚 **Documentação da API**

- **🌐 Swagger UI**: http://localhost:8000/docs
- **📖 ReDoc**: http://localhost:8000/redoc
- **🔗 OpenAPI JSON**: http://localhost:8000/openapi.json
- **💓 Health Check**: http://localhost:8000/api/v1/health

## 🏗️ **Arquitetura Enterprise**

### 🎯 **Clean Architecture (Arquitetura Hexagonal)**

O sistema é construído seguindo os princípios de **Clean Architecture**, garantindo:

- **🔄 Independência de Frameworks**: Lógica de negócio isolada
- **🧪 Testabilidade**: Camadas bem definidas facilitam testes
- **🔧 Manutenibilidade**: Mudanças não afetam outras camadas
- **📈 Escalabilidade**: Fácil adição de novos recursos

#### **Estrutura de Camadas:**

```
📁 app/
├── 🎯 domain/           # Regras de negócio puras
│   ├── entities/        # Modelos de dados (SQLAlchemy)
│   ├── models/          # Schemas Pydantic
│   └── repositories/    # Interfaces de repositório
├── ⚙️ application/      # Casos de uso da aplicação
│   └── use_cases/       # Lógica de aplicação
├── 🔧 infrastructure/   # Camada de infraestrutura
│   ├── database.py      # Conexão PostgreSQL
│   ├── auth.py          # JWT Authentication
│   ├── cache/           # Redis Cache
│   ├── security_middleware.py
│   └── rate_limiting.py
└── 🌐 presentation/     # Camada de apresentação
    └── api/v1/          # APIs REST (FastAPI)
```

## 🏥 **Funcionalidades do Sistema**

### 📋 **Módulos Principais:**

#### **👥 Gestão de Usuários**
- Autenticação JWT com bcrypt
- Controle de permissões por roles
- Sistema de recuperação de senha
- Logs de auditoria

#### **🏠 Gestão de Pacientes**
- Cadastro completo de pacientes
- Histórico médico e tratamentos
- Controle de medicamentos
- Alertas e lembretes

#### **📅 Agendamento e Visitas**
- Sistema de agendamento inteligente
- Controle de visitas domiciliares
- Roteirização otimizada
- Notificações automáticas

#### **📊 Monitoramento e Analytics**
- Dashboards em tempo real
- Relatórios de performance
- Métricas de qualidade
- Indicadores de compliance

#### **🔐 Segurança e Compliance**
- Criptografia de dados sensíveis
- Logs de auditoria completos
- Conformidade LGPD
- Rate limiting inteligente
- Content Security Policy (CSP)

### 🗄️ **Banco de Dados**

**PostgreSQL Remoto Configurado:**
- **Host:** 192.168.11.62:5432
- **Database:** pro_team_care_11
- **Schema:** master
- **Conexão:** AsyncPG (alta performance)

**Características:**
- ✅ 47+ tabelas já estruturadas
- ✅ Índices otimizados
- ✅ Constraints e triggers
- ✅ Particionamento de tabelas
- ✅ Funções armazenadas
- ✅ Views para consultas complexas

## 🔐 **Sistema de Autenticação**

### JWT Authentication Enterprise
- **Algoritmo:** HS256 com chave de 256 bits
- **Expiração:** 30 minutos (configurável)
- **Refresh Tokens:** Suporte completo
- **Rate Limiting:** 5 tentativas/min por IP

### Teste de Autenticação:
```bash
# Login via API
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@example.com&password=password"

# Resposta esperada:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## 🛡️ **Segurança Enterprise**

### **Mecanismos Implementados:**
- ✅ **JWT Authentication** com bcrypt hashing
- ✅ **CORS Configurado** (origins específicas)
- ✅ **Content Security Policy** (CSP duplo)
- ✅ **Rate Limiting** inteligente (Redis)
- ✅ **Security Headers** completos
- ✅ **Input Validation** rigorosa (Pydantic)
- ✅ **SQL Injection Protection** (SQLAlchemy)
- ✅ **XSS Protection** (CSP + sanitização)
- ✅ **CSRF Protection** (SameSite cookies)

### **Headers de Segurança:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

## 📊 **Monitoramento e Observabilidade**

### **Logs Estruturados:**
- ✅ **Formato JSON** para análise
- ✅ **Níveis configuráveis** (DEBUG, INFO, WARNING, ERROR)
- ✅ **Context enrichment** automático
- ✅ **Performance tracking** por operação

### **Health Checks:**
```bash
# Health check completo
GET /api/v1/health

# Resposta:
{
  "status": "healthy",
  "service": "Pro Team Care API",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "uptime": "2h 30m"
}
```

### **Métricas Prometheus:**
- ✅ **Response times** por endpoint
- ✅ **Error rates** por serviço
- ✅ **Database connections** ativas
- ✅ **Cache hit/miss ratios**
- ✅ **Memory usage** e performance

## 🧪 **Testes e Qualidade**

### **Estrutura de Testes:**
```bash
# Executar todos os testes
pytest

# Com cobertura detalhada
pytest --cov=app --cov-report=html --cov-report=term-missing

# Testes específicos
pytest tests/test_auth.py -v
pytest tests/test_health.py -v

# Testes de performance
pytest --durations=10
```

### **Cobertura de Testes:**
- ✅ **Backend:** 80%+ cobertura
- ✅ **Frontend:** Testes configurados
- ✅ **Integração:** Testes end-to-end
- ✅ **Performance:** Benchmarks automatizados

### **Qualidade de Código:**
```bash
# Formatação automática
black app/ frontend/src/

# Verificação de linting
flake8 app/

# Type checking
mypy app/ --ignore-missing-imports

# Import sorting
isort app/
```

## 🚀 **Scripts de Gerenciamento**

### **Inicialização Rápida:**
```bash
# Backend + Frontend (recomendado)
./start_simple.sh

# Apenas backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Parar todos os serviços
./stop_servers.sh
```

### **Banco de Dados:**
```bash
# Executar migrações
alembic upgrade head

# Criar nova migração
alembic revision --autogenerate -m "nova feature"

# Ver status das migrações
alembic current
```

### **Pre-commit Hooks:**
```bash
# Instalar hooks de qualidade
./scripts/install-hooks.sh

# Executar hooks manualmente
pre-commit run --all-files
```

## 🔄 **Configuração do Banco de Dados**

### **PostgreSQL Remoto:**
- **Host:** 192.168.11.62:5432
- **Database:** pro_team_care_11
- **Schema:** master
- **Driver:** AsyncPG (alta performance)
- **Pool:** 20 conexões + pre-ping

### **Características Avançadas:**
- ✅ **47+ tabelas** já estruturadas
- ✅ **Índices otimizados** para performance
- ✅ **Constraints e triggers** de integridade
- ✅ **Particionamento** de tabelas grandes
- ✅ **Funções armazenadas** para lógica complexa
- ✅ **Views otimizadas** para consultas
- ✅ **Auditoria automática** (LGPD compliant)

## 🚀 **CI/CD Pipeline**

### **GitHub Actions Automatizado:**
[![CI/CD Pipeline](https://github.com/your-org/pro-team-care/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/pro-team-care/actions/workflows/ci.yml)

#### **Jobs Executados:**
1. **🧪 Test Backend** (PostgreSQL + Redis)
   - Testes unitários e integração
   - Cobertura de código (80%+)
   - Linting e type checking

2. **🎨 Test Frontend** (Node.js 18)
   - Build e testes React
   - Linting e formatação
   - Upload de artefatos

3. **🔐 Security Scan**
   - Bandit (Python security)
   - Dependency scanning

4. **📊 Quality Check**
   - Black (formatação)
   - isort (imports)
   - flake8 (linting)
   - mypy (tipagem)

5. **🚀 Deploy** (branch main)
   - Build otimizado
   - Deploy automatizado

### **Pre-commit Hooks:**
```bash
# Instalação automática
./scripts/install-hooks.sh

# Hooks configurados:
✅ Python formatting (black)
✅ Import sorting (isort)
✅ Linting (flake8)
✅ Security scanning (bandit)
✅ Frontend linting (eslint)
✅ Conventional commits
✅ Secrets detection
```

## 📝 **Desenvolvimento**

### **Configuração do Ambiente:**
```bash
# 1. Instalar dependências
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Configurar pre-commit
./scripts/install-hooks.sh

# 3. Executar migrações
alembic upgrade head

# 4. Configurar variáveis de ambiente
cp .env.example .env  # Ajustar configurações
```

### **Comandos Essenciais:**
```bash
# Desenvolvimento
uvicorn app.main:app --reload                    # Backend
cd frontend && npm run dev                      # Frontend

# Qualidade de código
black app/                                      # Formatação
flake8 app/                                     # Linting
mypy app/                                       # Type checking
pytest --cov=app                               # Testes

# Banco de dados
alembic revision --autogenerate -m "feature"    # Nova migração
alembic upgrade head                           # Aplicar migrações

# Docker (futuro)
docker-compose up                              # Ambiente completo
docker-compose -f docker-compose.test.yml up   # Testes
```

### **Estrutura de Branches:**
```
main        # Produção (sempre estável)
develop     # Desenvolvimento principal
feature/*   # Novas funcionalidades
hotfix/*    # Correções urgentes
release/*   # Preparação para release
```

## 🤝 **Contribuição**

### **Fluxo de Desenvolvimento:**
1. **Fork** o projeto
2. **Clone** sua fork: `git clone https://github.com/YOUR-USERNAME/pro-team-care.git`
3. **Crie uma branch**: `git checkout -b feature/nova-funcionalidade`
4. **Instale dependências**: `pip install -r requirements.txt`
5. **Configure pre-commit**: `./scripts/install-hooks.sh`
6. **Desenvolva** sua feature seguindo os padrões
7. **Execute testes**: `pytest --cov=app`
8. **Commit**: `git commit -m "feat: descrição da funcionalidade"`
9. **Push**: `git push origin feature/nova-funcionalidade`
10. **Pull Request** com descrição detalhada

### **Padrões de Código:**
- ✅ **Black** para formatação Python
- ✅ **Conventional Commits** para mensagens
- ✅ **Type hints** obrigatórios
- ✅ **Docstrings** em funções públicas
- ✅ **Testes** para novas funcionalidades
- ✅ **Cobertura** mínima de 80%

## 🏥 **Setor de Aplicação**

### **Público-Alvo:**
- 🏥 **Clínicas de Home Care**
- 👩‍⚕️ **Cooperativas de profissionais de saúde**
- 🏢 **Empresas de assistência domiciliar**
- 🩺 **Serviços de enfermagem especializada**
- 💊 **Gestão de cuidados paliativos**
- 👴 **Atendimento geriátrico domiciliar**
- 🏠 **Serviços de cuidados continuados**

### **Benefícios para o Setor:**
- 📊 **Redução de custos** com gestão automatizada
- ⏱️ **Otimização de rotas** e agendamentos
- 📱 **Mobilidade** com acesso remoto
- 🔐 **Compliance** com regulamentações de saúde
- 📈 **Analytics** para tomada de decisão
- 🤖 **Automação** de processos repetitivos

## 🚀 **Stack Tecnológica Completa**

### **Backend (Python/FastAPI):**
- ✅ **FastAPI 0.104+** - Framework web assíncrono
- ✅ **PostgreSQL + AsyncPG** - Banco de dados de alta performance
- ✅ **SQLAlchemy 2.0** - ORM moderno com tipagem forte
- ✅ **Pydantic 2.5+** - Validação e serialização de dados
- ✅ **JWT Authentication** - Segurança enterprise com bcrypt
- ✅ **Redis** - Cache e sessões de alta performance
- ✅ **Alembic** - Migrations de banco automatizadas

### **Frontend (React/TypeScript):**
- ✅ **React 18.2+** - Interface moderna e responsiva
- ✅ **Tailwind CSS 3.2+** - Design system profissional
- ✅ **Vite 4.1+** - Build system ultra-rápido
- ✅ **Axios 1.3+** - Cliente HTTP robusto
- ✅ **React Router 6.8+** - Roteamento SPA
- ✅ **React Query 3.39+** - Gerenciamento de estado server

### **DevOps & Qualidade:**
- ✅ **Pytest 7.4+** - Framework de testes completo
- ✅ **GitHub Actions** - CI/CD automatizado
- ✅ **Pre-commit Hooks** - Qualidade de código automática
- ✅ **Black + isort** - Formatação e organização de código
- ✅ **Flake8 + mypy** - Linting e type checking
- ✅ **Bandit** - Segurança de código Python
- ⚠️ **Docker** - Containerização (planejado)

### **Monitoramento & Observabilidade:**
- ✅ **Structlog** - Logs estruturados em JSON
- ✅ **Prometheus** - Métricas de sistema
- ✅ **Health Checks** - Monitoramento de saúde
- ✅ **Rate Limiting** - Controle de carga inteligente

## 📄 **Licença**

Este projeto é propriedade da **Pro Team Care** - Sistema de Gestão para Home Care.

---

## 🎯 **Próximos Passos**

### **Imediatos (1-2 semanas):**
- [ ] Implementar Docker e docker-compose
- [ ] Expandir estrutura frontend (componentes, rotas)
- [ ] Adicionar mais testes de integração
- [ ] Configurar monitoring avançado

### **Médio Prazo (1-3 meses):**
- [ ] Sistema de notificações push
- [ ] Relatórios avançados e dashboards
- [ ] API mobile para profissionais
- [ ] Integração com sistemas de saúde

### **Longo Prazo (3-6 meses):**
- [ ] Inteligência artificial para otimização de rotas
- [ ] Telemedicina integrada
- [ ] Marketplace de profissionais
- [ ] Sistema multi-tenant completo

---

**💡 Desenvolvido com foco nas necessidades específicas do setor de cuidados domiciliares, garantindo conformidade com regulamentações de saúde (LGPD, normas sanitárias) e máxima segurança de dados.**