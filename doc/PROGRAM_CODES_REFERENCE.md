# 📋 Referência de Códigos de Programas - Pro Team Care

## 🎯 Visão Geral

Sistema de códigos curtos estilo **Datasul** para navegação rápida via **Ctrl+Alt+X** ou **Ctrl+K**.

Permite acesso instantâneo a qualquer tela do sistema digitando:
- **Código direto**: `em0001` → Abre Cadastro de Empresas
- **Nome/busca**: `empresa` → Lista resultados relacionados

---

## 📖 Índice

1. [Estrutura de Códigos](#estrutura-de-códigos)
2. [Módulos e Siglas](#módulos-e-siglas)
3. [Tipos de Programas](#tipos-de-programas)
4. [Referência Completa](#referência-completa-de-códigos)
5. [Como Usar](#como-usar)
6. [Criando Novos Códigos](#criando-novos-códigos)
7. [Regras e Padrões](#regras-e-padrões)

---

## 🏗️ Estrutura de Códigos

### Formato Padrão: `[SIGLA][TIPO][SEQ]`

```
em0001
││││││
││││└└─ Sequencial (01-99)
││└└─── Tipo de programa (00-99)
└└───── Módulo (2 letras)
```

**Características:**
- Total: 6 caracteres
- Case: **lowercase obrigatório** (em0001, não EM0001)
- Único no sistema
- Memorável e intuitivo

---

## 📦 Módulos e Siglas

### Cadastros Base

| Sigla | Módulo | Descrição | Exemplo |
|-------|--------|-----------|---------|
| **EM** | Empresas | Cadastro de empresas/companhias | `em0001` |
| **ES** | Estabelecimentos | Filiais, unidades, lojas | `es0001` |
| **US** | Usuários | Gestão de usuários do sistema | `us0001` |
| **PE** | Perfis | Perfis de acesso e permissões | `pe0001` |
| **PS** | Pessoas | Cadastro de pessoas físicas | `ps0001` |

### Home Care / Negócio

| Sigla | Módulo | Descrição | Exemplo |
|-------|--------|-----------|---------|
| **CL** | Clientes | Clientes/Pacientes home care | `cl0001` |
| **PR** | Profissionais | Profissionais de saúde | `pr0001` |
| **CT** | Contratos | Contratos home care | `ct0001` |
| **AM** | Autorizações Médicas | Autorizações e solicitações | `am0001` |
| **LM** | Controle de Limites | Limites e vidas contratuais | `lm0001` |
| **CS** | Catálogo de Serviços | Serviços e procedimentos | `cs0001` |
| **EX** | Execução de Serviços | Agendamentos e execuções | `ex0001` |

### Financeiro

| Sigla | Módulo | Descrição | Exemplo |
|-------|--------|-----------|---------|
| **FS** | Faturamento SaaS | Cobrança de assinaturas | `fs0001` |
| **FB** | Faturamento B2B | Faturamento contratos | `fb0001` |
| **PA** | Planos de Assinatura | Subscription plans | `pa0001` |
| **NF** | Notas Fiscais | Emissão de NF | `nf0001` |
| **CR** | Contas a Receber | Gestão de recebíveis | `cr0001` |

### Gerencial

| Sigla | Módulo | Descrição | Exemplo |
|-------|--------|-----------|---------|
| **DS** | Dashboard | Dashboards e KPIs | `ds0001` |
| **RE** | Relatórios | Relatórios diversos | `re0001` |
| **GR** | Gráficos | Análises gráficas | `gr0001` |

### Administração

| Sigla | Módulo | Descrição | Exemplo |
|-------|--------|-----------|---------|
| **CF** | Configurações | Configurações do sistema | `cf0001` |
| **MN** | Menus | Gestão de menus | `mn0001` |
| **NT** | Notificações | Central de notificações | `nt0001` |
| **AU** | Auditoria | Logs e auditoria | `au0001` |
| **IT** | Integrações | APIs e integrações | `it0001` |

### Utilitários

| Sigla | Módulo | Descrição | Exemplo |
|-------|--------|-----------|---------|
| **GE** | Geolocalização | Geocoding e mapas | `ge0001` |
| **CN** | Consulta CNPJ | Validação CNPJ | `cn0001` |
| **IM** | Importação | Importação de dados | `im0001` |
| **EP** | Exportação | Exportação de dados | `ep0001` |

---

## 🎨 Tipos de Programas

| Numeração | Tipo | Descrição | Exemplos |
|-----------|------|-----------|----------|
| **00-09** | Cadastros Principais | Manutenção cadastral básica | `em0001`, `cl0001` |
| **10-19** | Cadastros Relacionados | Cadastros secundários | `em0011` (endereços) |
| **20-29** | Consultas Simples | Consultas e filtros básicos | `em0020`, `cl0020` |
| **30-39** | Consultas Complexas | Consultas com relacionamentos | `em0030` (multi-estabelecimento) |
| **40-49** | Listagens | Listagens e exportações | `em0040` |
| **50-69** | Relatórios | Relatórios impressos/PDF | `re0050`, `re0051` |
| **70-79** | Processos/Tarefas | Processos batch, jobs | `em0070` (ativação) |
| **80-89** | Dashboards/Gráficos | Painéis gerenciais | `ds0080`, `ct0080` |
| **90-99** | Utilitários/Especiais | Importações, migrações | `em0090` |

---

## 📚 Referência Completa de Códigos

### 🏢 Cadastros Base (EM, ES, US, PE)

| Código | Nome | Rota | Descrição |
|--------|------|------|-----------|
| `em0001` | Cadastro de Empresas | `/admin/empresas` | Manutenção cadastral de empresas |
| `em0011` | Detalhes da Empresa | `/admin/empresas/:id` | Visualização detalhada |
| `em0020` | Consulta de Empresas | `/admin/empresas` | Consulta e filtros |
| `em0070` | Ativação de Empresa | `/admin/company-activation` | Processo de ativação |
| | | | |
| `es0001` | Cadastro de Estabelecimentos | `/admin/estabelecimentos` | Manutenção de estabelecimentos |
| `es0011` | Detalhes do Estabelecimento | `/admin/estabelecimentos/:id` | Visualização detalhada |
| `es0020` | Consulta de Estabelecimentos | `/admin/estabelecimentos` | Consulta e filtros |
| | | | |
| `us0001` | Cadastro de Usuários | `/admin/usuarios` | Manutenção de usuários |
| `us0011` | Detalhes do Usuário | `/admin/usuarios/:id` | Perfil do usuário |
| `us0020` | Consulta de Usuários | `/admin/usuarios` | Consulta e filtros |
| `us0070` | Ativação de Usuário | `/admin/user-activation` | Processo de ativação |
| | | | |
| `pe0001` | Cadastro de Perfis | `/admin/perfis` | Gestão de perfis e permissões |
| `pe0020` | Consulta de Perfis | `/admin/perfis` | Consulta de perfis |

### 👥 Home Care (CL, PR, CT, AM, LM, CS)

| Código | Nome | Rota | Descrição |
|--------|------|------|-----------|
| `cl0001` | Cadastro de Clientes | `/admin/clientes` | Manutenção de clientes/pacientes |
| `cl0011` | Detalhes do Cliente | `/admin/clientes/:id` | Ficha completa |
| `cl0020` | Consulta de Clientes | `/admin/clientes` | Consulta e filtros |
| | | | |
| `pr0001` | Cadastro de Profissionais | `/admin/profissionais` | Manutenção de profissionais |
| `pr0020` | Consulta de Profissionais | `/admin/profissionais` | Consulta e filtros |
| | | | |
| `ct0001` | Cadastro de Contratos | `/admin/contratos` | Manutenção de contratos |
| `ct0011` | Detalhes do Contrato | `/admin/contratos/:id` | Visualização completa |
| `ct0012` | Gestão de Vidas | `/admin/contratos/:id/vidas` | Controle de vidas |
| `ct0020` | Consulta de Contratos | `/admin/contratos` | Consulta e filtros |
| `ct0080` | Dashboard Contratos | `/admin/contract-dashboard` | Painel gerencial |
| | | | |
| `am0001` | Autorizações Médicas | `/admin/autorizacoes` | Gestão de autorizações |
| `am0020` | Consulta de Autorizações | `/admin/autorizacoes` | Consulta e filtros |
| | | | |
| `lm0001` | Controle de Limites | `/admin/limites` | Gestão de limites |
| `lm0020` | Consulta de Limites | `/admin/limites` | Consulta por contrato |
| | | | |
| `cs0001` | Catálogo de Serviços | `/admin/servicos` | Manutenção de serviços |
| `cs0020` | Consulta de Serviços | `/admin/servicos` | Consulta disponíveis |

### 💰 Financeiro (FS, FB, PA)

| Código | Nome | Rota | Descrição |
|--------|------|------|-----------|
| `fs0001` | Faturamento SaaS | `/admin/saas-billing` | Cobrança de assinaturas |
| `fs0020` | Consulta Faturas SaaS | `/admin/saas-billing/invoices` | Consulta de faturas |
| `fs0080` | Dashboard Financeiro | `/admin/billing-dashboard` | Painel financeiro |
| | | | |
| `fb0001` | Faturamento B2B | `/admin/b2b-billing` | Faturamento contratos |
| `fb0020` | Consulta Faturas B2B | `/admin/b2b-billing/invoices` | Consulta faturas B2B |
| | | | |
| `pa0001` | Planos de Assinatura | `/admin/subscription-plans` | Manutenção de planos |
| `pa0020` | Consulta de Planos | `/admin/subscription-plans` | Consulta planos |

### 📊 Gerencial (DS, RE)

| Código | Nome | Rota | Descrição |
|--------|------|------|-----------|
| `ds0001` | Dashboard Principal | `/admin/dashboard` | Painel principal |
| `ds0002` | Dashboard Contratos | `/admin/contract-dashboard` | Painel contratos |
| `ds0003` | Dashboard Financeiro | `/admin/billing-dashboard` | Painel financeiro |
| | | | |
| `re0001` | Central de Relatórios | `/admin/relatorios` | Acesso a relatórios |
| `re0050` | Relatório de Empresas | `/admin/relatorios/empresas` | Relatório detalhado |
| `re0051` | Relatório de Contratos | `/admin/relatorios/contratos` | Relatório detalhado |
| `re0052` | Relatório Financeiro | `/admin/relatorios/faturamento` | Relatório receitas |

### ⚙️ Administração (CF, MN, NT, AU)

| Código | Nome | Rota | Descrição |
|--------|------|------|-----------|
| `cf0001` | Configurações Sistema | `/admin/configuracoes` | Configurações gerais |
| `cf0010` | Configurações Email | `/admin/configuracoes/email` | Config SMTP |
| `cf0011` | Configurações Integração | `/admin/configuracoes/integracao` | Config APIs |
| | | | |
| `mn0001` | Gestão de Menus | `/admin/menus` | Manutenção menus |
| `mn0020` | Consulta de Menus | `/admin/menus` | Consulta menus |
| | | | |
| `nt0001` | Central de Notificações | `/admin/notificacoes` | Gestão notificações |
| `nt0020` | Consulta de Notificações | `/admin/notificacoes` | Histórico avisos |
| | | | |
| `au0001` | Logs de Auditoria | `/admin/auditoria` | Visualização logs |
| `au0020` | Consulta de Auditoria | `/admin/auditoria` | Busca em logs |

---

## 🚀 Como Usar

### 1. Navegação por Código (Rápida)

**Para usuários experientes que já conhecem os códigos:**

```
1. Pressione: Ctrl+Alt+X (ou Ctrl+K)
2. Digite o código: em0001
3. Pressione: Enter
4. ✅ Abre diretamente Cadastro de Empresas
```

⏱️ **Tempo:** ~3 segundos
🎯 **Melhor para:** Telas frequentes, usuários veteranos

---

### 2. Navegação por Nome (Intuitiva)

**Para usuários novos ou telas menos frequentes:**

```
1. Pressione: Ctrl+Alt+X (ou Ctrl+K)
2. Digite texto: empresa
3. Veja resultados filtrados
4. Navegue com ↑↓
5. Pressione: Enter
6. ✅ Abre tela selecionada
```

⏱️ **Tempo:** ~5-7 segundos
🎯 **Melhor para:** Descobrir funcionalidades, usuários novos

---

### 3. Busca Parcial

```
Digite: "cad" → Mostra todos cadastros
Digite: "cons" → Mostra todas consultas
Digite: "dash" → Mostra todos dashboards
```

---

### 4. Atalhos de Teclado

| Tecla | Ação |
|-------|------|
| `Ctrl+Alt+X` | Abrir command palette (padrão Datasul) |
| `Ctrl+K` | Abrir command palette (padrão web moderno) |
| `↑` `↓` | Navegar entre resultados |
| `Enter` | Selecionar e abrir |
| `Esc` | Fechar |

---

## 🛠️ Criando Novos Códigos

### Passo a Passo

#### 1. Identificar o Módulo

Escolha a sigla de 2 letras apropriada:

```
Nova tela de Relatório de Faturamento
→ Módulo: RE (Relatórios)
```

#### 2. Identificar o Tipo

Baseado na função (00-99):

```
É um relatório impresso
→ Tipo: 50-69 (Relatórios)
→ Escolher: 52
```

#### 3. Gerar Código

Combinar sigla + tipo + sequencial:

```
RE + 05 + 2
= re0052
```

#### 4. Validar Unicidade

```sql
SELECT * FROM master.program_codes WHERE shortcode = 're0052';
-- Deve retornar vazio
```

#### 5. Registrar no Banco

```sql
INSERT INTO master.program_codes (
    shortcode,
    module_code,
    program_type,
    label,
    description,
    route,
    icon,
    search_tokens
) VALUES (
    're0052',
    'RE',
    '05',
    'Relatório Financeiro',
    'Relatório detalhado de faturamento e receitas',
    '/admin/relatorios/faturamento',
    'FileText',
    ARRAY['relatório', 'financeiro', 'receita', 'faturamento']
);
```

#### 6. Documentar

Adicionar linha neste README na seção apropriada.

---

## 📏 Regras e Padrões

### ✅ Regras Obrigatórias

1. **Lowercase sempre**: `em0001` ✅ | `EM0001` ❌
2. **6 caracteres exatos**: `em0001` ✅ | `em001` ❌
3. **Código único**: Verificar duplicatas antes de criar
4. **Search tokens relevantes**: Incluir sinônimos e termos comuns
5. **Documentar**: Atualizar este README

### 🎯 Boas Práticas

1. **Agrupamento lógico**
   - Códigos relacionados devem ter tipos próximos
   - Ex: `em0001` (cadastro), `em0011` (detalhes), `em0020` (consulta)

2. **Search tokens completos**
   - Incluir: nome oficial, sinônimos, termos em inglês
   - Ex: `['empresa', 'company', 'cadastro empresa', 'firmas']`

3. **Aliases para compatibilidade**
   - Registrar códigos antigos em aliases
   - Equivalentes Datasul se houver
   ```json
   {
     "old_code": "cad001",
     "datasul_eq": "EST001"
   }
   ```

4. **Descrições claras**
   - Description deve explicar função completa
   - Evitar ambiguidade

### ⚠️ Restrições

❌ **Não fazer:**
- Reutilizar códigos desativados sem justificativa
- Pular numeração sem motivo (ex: 00, 01, 05)
- Criar códigos sem search_tokens
- Esquecer de atualizar documentação
- Usar caracteres especiais ou maiúsculas

---

## 🔧 Manutenção

### Desativar Código

```sql
UPDATE master.program_codes
SET is_active = FALSE
WHERE shortcode = 'xx9999';
```

⚠️ **Não deletar!** Histórico de uso deve ser mantido.

### Atualizar Rota

```sql
UPDATE master.program_codes
SET route = '/nova/rota',
    updated_at = CURRENT_TIMESTAMP
WHERE shortcode = 'xx9999';
```

### Adicionar Aliases

```sql
UPDATE master.program_codes
SET aliases = aliases || '{"new_alias": "old_code"}'::jsonb
WHERE shortcode = 'xx9999';
```

---

## 📊 Estatísticas

### Consultar Mais Usados

```sql
SELECT shortcode, label, usage_count, last_used_at
FROM master.program_codes
WHERE is_active = TRUE
ORDER BY usage_count DESC
LIMIT 10;
```

### Consultar por Módulo

```sql
SELECT module_code, COUNT(*) as total
FROM master.program_codes
WHERE is_active = TRUE
GROUP BY module_code
ORDER BY total DESC;
```

### Códigos Nunca Usados

```sql
SELECT shortcode, label, created_at
FROM master.program_codes
WHERE usage_count = 0
AND is_active = TRUE
ORDER BY created_at DESC;
```

---

## 🎓 Dicas de Uso

### Para Novos Usuários

1. **Explore**: Digite termos genéricos como "cadastro", "consulta"
2. **Aprenda gradualmente**: Memorize códigos das telas mais usadas
3. **Use Ctrl+K**: Mais familiar para usuários modernos

### Para Usuários Experientes

1. **Decore top 10**: Códigos das telas diárias
2. **Use Ctrl+Alt+X**: Mais rápido (padrão Datasul)
3. **Códigos diretos**: Evite busca quando souber o código exato

### Para Administradores

1. **Monitore analytics**: Identifique telas subutilizadas
2. **Adicione aliases**: Para erros comuns de digitação
3. **Treine usuários**: Documente códigos principais

---

## 🔗 Referências

### Inspirações
- **Datasul/TOTVS**: Sistema de códigos de programas original
- **VS Code**: Command Palette (Ctrl+Shift+P)
- **Slack**: Quick Switcher (Ctrl+K)
- **Linear**: Command Menu

### Tecnologias
- **PostgreSQL pg_trgm**: Busca fuzzy por similaridade
- **GIN Index**: Performance em arrays e texto
- **React**: Interface responsiva
- **FastAPI**: API assíncrona de alta performance

---

## 📞 Suporte

**Problemas comuns:**

- Código não encontrado → Verificar se está cadastrado
- Muitos resultados → Ser mais específico na busca
- Sem permissão → Verificar perfil do usuário

**Contato:**
- 📧 dev@proteamcare.com
- 📚 Documentação completa: `/doc/PROGRAM_CODES_REFERENCE.md`

---

**Última atualização:** 2025-10-02
**Versão:** 1.0.0
**Total de códigos:** 52 ativos
