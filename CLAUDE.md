# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Full Stack (Recomendado)
```bash
# Iniciar backend + frontend (rede local)
./start_full_stack.sh

# Parar todos os serviços
./stop_servers.sh
```

### Backend Apenas
```bash
# Executar em modo desenvolvimento
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Usar script personalizado
./start_server.sh development
./start_server.sh production
```

### Frontend
```bash
# Desenvolvimento (dentro da pasta frontend/)
cd frontend
npm install
npm run dev

# Build para produção
npm run build
npm run serve
```

### Testing
```bash
# Executar testes
pytest

# Executar testes com cobertura
pytest --cov=app

# Executar teste específico
pytest tests/test_main.py
```

### Code Quality
```bash
# Formatar código
black .

# Verificar linting
flake8
```

### Database
```bash
# Testar conectividade (via script)
./start_server.sh development  # Inclui teste de conectividade
```

## Architecture

### Clean Architecture Structure
O projeto segue arquitetura hexagonal (Clean Architecture) com separação clara de responsabilidades:

- **Domain Layer** (`app/domain/`): Entidades de negócio puras (User models)
- **Application Layer** (`app/application/`): Casos de uso (ainda não implementado)
- **Infrastructure Layer** (`app/infrastructure/`): Implementações externas (database, auth)
- **Presentation Layer** (`app/presentation/`): APIs REST (FastAPI routes)

### Database Configuration
- PostgreSQL remoto: `192.168.11.62:5432`
- Database: `pro_team_care_11`
- Schema: `master`
- Conexão assíncrona via SQLAlchemy + asyncpg

### Authentication
- JWT-based authentication implementado
- Mock authentication atual (admin@example.com / password)
- Token expiry: 30 minutos (configurável)

### Key Components
- **FastAPI app**: `app/main.py` - Configuração principal, middlewares, rotas
- **Settings**: `config/settings.py` - Configurações centralizadas via Pydantic
- **Database**: `app/infrastructure/database.py` - Engine assíncrono SQLAlchemy
- **Auth**: `app/infrastructure/auth.py` - JWT utilities
- **Models**: `app/domain/models/user.py` - Pydantic models para User

### Logging
- Structured logging via structlog
- Output em JSON format
- Configurado em `app/main.py`

## URLs de Acesso

### Rede Local (192.168.11.62)
- **Backend API**: http://192.168.11.62:8000
- **Frontend App**: http://192.168.11.62:3000
- **API Docs**: http://192.168.11.62:8000/docs
- **Health Check**: http://192.168.11.62:8000/api/v1/health

### Localhost
- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:3000

## Development Notes

### Current State - PRODUÇÃO READY!
- ✅ API completa funcional com autenticação real
- ✅ Integração com banco PostgreSQL existente
- ✅ Estrutura frontend React + Tailwind preparada
- ✅ Scripts full-stack para rede local
- ✅ Segurança enterprise implementada
- ✅ Health checks e monitoring robustos

### Database Structure
- Utiliza banco PostgreSQL remoto existente (192.168.11.62:5432)
- Schema `master` com 46 tabelas já estruturadas
- Tabela `users` mapeada corretamente
- Relacionamentos com `people`, `establishments`, `roles`

### Environment Variables
Configuradas em `.env` (com secrets seguros):
- Database credentials (PostgreSQL remoto)
- JWT secret key (256-bit)
- CORS origins (rede local)
- Allowed hosts (específicos)

### Security Features
- ✅ JWT Authentication com hash bcrypt
- ✅ Rate limiting (5/min login, 3/min register)
- ✅ CORS restritivo (não wildcard)
- ✅ Security headers completos
- ✅ Input validation rigorosa
- ✅ Error handling padronizado