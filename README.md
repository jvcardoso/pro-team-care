# Pro Team Care - Sistema de Gestão Home Care

Sistema completo para gerenciamento de empresas de Home Care, desenvolvido com FastAPI (backend) e React (frontend). Oferece controle total sobre pacientes, profissionais, agendamentos e operações de cuidados domiciliares.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.11+
- PostgreSQL (banco remoto já configurado)

### Instalação

1. Clone o repositório:
```bash
cd /home/juliano/Projetos/pro_team_care_16
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (arquivo `.env` já criado)

4. Execute a aplicação:
```bash
uvicorn app.main:app --reload
```

A API estará disponível em: http://localhost:8000

## 📚 Documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🏥 **Sobre o Sistema**

O **Pro Team Care** é uma solução completa para empresas de **Home Care**, oferecendo:

### 📋 **Funcionalidades Principais:**
- **👥 Gestão de Profissionais** - Cadastro e controle de equipe médica/enfermagem
- **🏠 Gestão de Pacientes** - Prontuários, histórico médico e cuidados
- **📅 Agendamento** - Controle de visitas e procedimentos domiciliares
- **💰 Faturamento** - Gestão financeira e cobrança de serviços
- **📊 Relatórios** - Analytics e indicadores de performance
- **🔐 Compliance** - Adequação à LGPD e normas de saúde
- **📱 Multi-tenant** - Suporte a múltiplos estabelecimentos

### 🏗️ **Arquitetura Enterprise**

Baseado em **Clean Architecture (Arquitetura Hexagonal)**:

- **🎯 Domain Layer** (`app/domain/`): Regras de negócio do setor de saúde
- **⚙️ Application Layer** (`app/application/`): Casos de uso específicos de Home Care
- **🔧 Infrastructure Layer** (`app/infrastructure/`): Integrações (banco, APIs externas)
- **🌐 Presentation Layer** (`app/presentation/`): APIs REST e interfaces

## 🔐 Autenticação

A API utiliza JWT para autenticação. Para testar:

```bash
# Login (credenciais mock)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@example.com&password=password"
```

## 🧪 Testes

Execute os testes:
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar testes
pytest

# Com cobertura
pytest --cov=app
```

## 🚀 **INICIALIZAÇÃO RÁPIDA (RECOMENDADO)**

```bash
# Opção 1: Script simples (mais compatível)
./start_simple.sh

# Opção 2: Script completo  
./start_full_stack.sh

# Opção 3: Parar serviços
./stop_servers.sh
```

## 🛡️ Segurança

- JWT Authentication
- CORS configurado
- Headers de segurança
- Validação rigorosa de entrada

## 📊 Monitoramento

- Logs estruturados em JSON
- Health checks automatizados
- Métricas de performance

## 🔄 Banco de Dados

Conectado ao PostgreSQL remoto com:
- Host: 192.168.11.62:5432
- Database: pro_team_care_11
- Schema: master

## 📝 Desenvolvimento

### Comandos úteis

```bash
# Formatar código
black .

# Verificar linting
flake8

# Executar testes com cobertura
pytest --cov=app
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 🏥 **Setor de Aplicação**

**Voltado especificamente para empresas de Home Care:**
- 🏥 Clínicas de cuidados domiciliares
- 👩‍⚕️ Cooperativas de profissionais de saúde  
- 🏢 Empresas de assistência domiciliar
- 🩺 Serviços de enfermagem em domicílio
- 💊 Gestão de cuidados paliativos
- 👴 Atendimento a idosos em casa

## 🚀 **Stack Tecnológica**

### **Backend:**
- **FastAPI** - Framework web moderno e rápido
- **PostgreSQL** - Banco de dados robusto
- **SQLAlchemy 2.0** - ORM com tipagem forte
- **JWT Authentication** - Segurança enterprise
- **Pydantic** - Validação de dados rigorosa

### **Frontend:**
- **React 18** - Interface moderna e responsiva  
- **Tailwind CSS** - Design system profissional
- **Vite** - Build system otimizado
- **Axios** - Cliente HTTP configurado

### **DevOps & Qualidade:**
- **Docker** - Containerização (preparado)
- **Pytest** - Testes automatizados
- **Alembic** - Migrations de banco
- **Estrutura CI/CD** - Pipeline preparado

## 📄 Licença

Este projeto é propriedade da **Pro Team Care** - Sistema de Gestão para Home Care.

---

**💡 Desenvolvido com foco nas necessidades específicas do setor de cuidados domiciliares, garantindo conformidade com regulamentações de saúde e proteção de dados.**