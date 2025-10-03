# 📚 Documentação do Sistema - Pro Team Care

Bem-vindo à documentação técnica completa do Pro Team Care!

## 🚀 Início Rápido

**Novo no projeto?** Comece por aqui:

1. 📖 Leia o [`INDICE_VISUAL.md`](INDICE_VISUAL.md) para uma visão rápida de todos os diagramas
2. 🗺️ Abra o [`visao_geral_modulos.drawio`](visao_geral_modulos.drawio) para ver todos os módulos do sistema
3. 🏗️ Depois, veja [`arquitetura_sistema.drawio`](arquitetura_sistema.drawio) para entender a arquitetura

**Procurando algo específico?** Use o [`INDICE_VISUAL.md`](INDICE_VISUAL.md) como guia de navegação.

---

## 📂 Estrutura do Diretório

```
doc/
├── README.md ............................ Este arquivo (porta de entrada)
├── INDICE_VISUAL.md ..................... Índice de navegação rápida ⭐
├── DIAGRAMAS_README.md .................. Documentação detalhada de cada diagrama
├── SUMARIO_DIAGRAMAS.txt ................ Sumário em formato texto
│
├── visao_geral_modulos.drawio ........... 🆕 Visão panorâmica (COMECE AQUI!)
├── arquitetura_sistema.drawio ........... Arquitetura Clean Architecture
├── mapa_frontend.drawio ................. Estrutura do frontend React
├── fluxo_home_care.drawio ............... Fluxo de negócio Home Care
│
├── erd_core.drawio ...................... ERD: Autenticação e Permissões
├── erd_multi-tenant.drawio .............. ERD: Multi-tenant
├── erd_cadastros.drawio ................. ERD: Cadastros Base
├── erd_home_care_contratos.drawio ....... ERD: Contratos e Serviços
└── erd_financeiro_contratos.drawio ...... ERD: Faturamento
```

---

## 🎯 Guias de Uso por Perfil

### 👨‍💻 Desenvolvedor Backend
**Você precisa entender:**
1. Arquitetura: `arquitetura_sistema.drawio` (camadas, responsabilidades)
2. Modelo de Dados: Todos os ERDs (`erd_*.drawio`)
3. Fluxo de Negócio: `fluxo_home_care.drawio`

**Dica:** Mantenha o `visao_geral_modulos.drawio` aberto enquanto trabalha para entender as dependências entre módulos.

---

### 👩‍💻 Desenvolvedor Frontend
**Você precisa entender:**
1. Mapa de Navegação: `mapa_frontend.drawio` (rotas, componentes)
2. Arquitetura Geral: `arquitetura_sistema.drawio` (onde o frontend se encaixa)
3. APIs Disponíveis: `arquitetura_sistema.drawio` (endpoints)

**Dica:** O `mapa_frontend.drawio` mostra todos os componentes, hooks e services disponíveis para reutilização.

---

### 🏗️ Arquiteto de Software
**Você precisa revisar:**
1. Visão Geral: `visao_geral_modulos.drawio`
2. Arquitetura: `arquitetura_sistema.drawio`
3. Modelo de Dados Completo: Todos os 5 ERDs
4. Fluxos Críticos: `fluxo_home_care.drawio`

**Dica:** Use [`DIAGRAMAS_README.md`](DIAGRAMAS_README.md) para entender as decisões arquiteturais.

---

### 📊 Product Owner / Gestor
**Você precisa ver:**
1. Módulos do Sistema: `visao_geral_modulos.drawio` (o que existe)
2. Fluxo de Negócio: `fluxo_home_care.drawio` (como funciona)
3. Funcionalidades: `mapa_frontend.drawio` (páginas disponíveis)

**Dica:** Os diagramas mostram o que já está implementado, não o roadmap futuro.

---

## 📊 Resumo do Sistema

### Tecnologias Principais
- **Backend:** Python 3.12 + FastAPI (Clean Architecture)
- **Frontend:** React 18 + TypeScript + TailwindCSS
- **Banco de Dados:** PostgreSQL 14+ (schema `master`)
- **Autenticação:** JWT + Permissões Granulares
- **Integrações:** PagBank, Redis Cache

### Números do Sistema
- **Módulos:** 11 módulos de negócio
- **Tabelas:** 45 tabelas no banco de dados
- **Endpoints API:** 200+ endpoints REST
- **Páginas Frontend:** 27 páginas
- **Componentes:** 50+ componentes reutilizáveis
- **Permissões:** 215 permissões em 19 perfis de acesso

---

## 🛠️ Ferramentas Necessárias

Para visualizar os diagramas, você precisa de uma destas opções:

### Opção 1: Draw.io Desktop (Recomendado)
```bash
# Download: https://github.com/jgraph/drawio-desktop/releases
# Instalação Ubuntu/Debian:
sudo dpkg -i drawio-amd64-*.deb

# Uso:
drawio doc/visao_geral_modulos.drawio
```

### Opção 2: Draw.io Online
1. Acesse: https://app.diagrams.net/
2. File → Open → Selecione o arquivo `.drawio`
3. **Não requer instalação**

### Opção 3: VS Code Extension
```bash
# Instalar extensão
code --install-extension hediet.vscode-drawio

# Depois, abra os arquivos .drawio diretamente no VS Code
```

---

## 📖 Documentação Adicional

Além dos diagramas, consulte também:

- **[`CLAUDE.md`](../CLAUDE.md)** - Instruções para Claude Code (AI assistant)
- **[`ENTITY_DETAILS_LAYOUT_PATTERN.md`](../frontend/ENTITY_DETAILS_LAYOUT_PATTERN.md)** - Padrão de layout frontend
- **[`app/infrastructure/orm/models.py`](../app/infrastructure/orm/models.py)** - Definição completa das tabelas
- **[`alembic/versions/`](../alembic/versions/)** - Migrações do banco de dados

---

## 🔄 Atualização dos Diagramas

### Quando Atualizar?

Os diagramas devem ser atualizados quando:

- ✅ **Nova tabela criada** → Atualizar ERD correspondente
- ✅ **Nova página/componente** → Atualizar `mapa_frontend.drawio`
- ✅ **Nova camada/módulo** → Atualizar `arquitetura_sistema.drawio`
- ✅ **Mudança de fluxo** → Atualizar `fluxo_home_care.drawio`

### Como Atualizar?

1. Abra o arquivo `.drawio` no Draw.io
2. Edite visualmente conforme necessário
3. Salve o arquivo (Ctrl+S)
4. Faça commit no git:
   ```bash
   git add doc/*.drawio
   git commit -m "docs: Atualizar diagrama X (motivo)"
   git push
   ```

---

## ❓ FAQ - Perguntas Frequentes

### P: Por que os ERDs estão divididos em vários arquivos?
**R:** O sistema tem 45 tabelas. Um único diagrama seria ilegível. A divisão por módulo facilita manutenção e navegação.

### P: Os diagramas refletem o estado atual do código?
**R:** Sim! Foram gerados analisando o código-fonte real em 2025-01-01. Mas precisam ser atualizados conforme o sistema evolui.

### P: Posso editar os diagramas?
**R:** Sim! Use Draw.io para abrir e editar. Depois faça commit das mudanças.

### P: Onde está o diagrama de deployment/infraestrutura?
**R:** Ainda não foi criado. Está na lista de "Próximos Passos" do [`DIAGRAMAS_README.md`](DIAGRAMAS_README.md).

### P: Como vejo os relacionamentos entre tabelas de módulos diferentes?
**R:** Consulte o arquivo [`app/infrastructure/orm/models.py`](../app/infrastructure/orm/models.py) que contém todas as foreign keys definidas.

---

## 🤝 Contribuindo

Encontrou uma inconsistência entre o diagrama e o código?

1. Abra uma issue descrevendo o problema
2. Ou melhor: atualize o diagrama e abra um PR! 🎉

---

## 📞 Suporte

Dúvidas sobre a documentação? Entre em contato com a equipe de arquitetura.

---

## 📝 Changelog

- **2025-01-01** - Criação inicial de todos os diagramas
  - 9 diagramas Draw.io gerados
  - 2 documentos de índice criados
  - Cobertura: 11 módulos, 45 tabelas, 200+ endpoints

---

<div align="center">

**🎨 Gerado automaticamente por Claude Code**

Pro Team Care © 2025

[📚 Ver Índice Completo](INDICE_VISUAL.md) | [📖 Documentação Detalhada](DIAGRAMAS_README.md) | [📊 Sumário](SUMARIO_DIAGRAMAS.txt)

</div>
