# 📋 GUIA: Como Consultar Histórico de Auditoria de Vidas

**Última atualização:** 03/10/2025
**Autor:** Sistema Pro Team Care
**Sprint:** Sprint 3 - Sistema de Auditoria Automática

---

## 🎯 OBJETIVO

Este documento mostra **todas as formas de consultar o histórico de auditoria** das vidas de contratos, incluindo queries SQL diretas, API endpoints, e métodos do frontend.

---

## 📊 OPÇÕES DE CONSULTA

### 1️⃣ SQL DIRETO - Tabela de Histórico

**Tabela:** `master.contract_lives_history`

**Query básica:**
```sql
SELECT *
FROM master.contract_lives_history
ORDER BY changed_at DESC;
```

**Colunas disponíveis:**
- `id` - ID do registro de auditoria
- `contract_life_id` - ID da vida auditada
- `action` - Tipo de ação: 'created', 'updated', 'substituted', 'cancelled'
- `changed_fields` - JSONB com array de campos alterados
- `old_values` - JSONB com valores antigos
- `new_values` - JSONB com valores novos
- `changed_by` - ID do usuário que fez a mudança
- `changed_at` - Timestamp da mudança
- `metadata` - JSONB com metadados adicionais

---

### 2️⃣ SQL - View Enriquecida (RECOMENDADO)

**View:** `master.v_contract_lives_history_enriched`

Esta view faz JOINs automáticos e retorna informações completas.

**Query básica:**
```sql
SELECT *
FROM master.v_contract_lives_history_enriched
ORDER BY changed_at DESC
LIMIT 50;
```

**Colunas adicionais (além das da tabela base):**
- `person_id` - ID da pessoa
- `person_name` - Nome da pessoa
- `contract_id` - ID do contrato
- `contract_number` - Número do contrato
- `changed_by_email` - Email do usuário que fez a mudança
- `changed_by_name` - Nome do usuário que fez a mudança

---

## 📝 EXEMPLOS DE CONSULTAS SQL

### Exemplo 1: Histórico de uma vida específica

```sql
SELECT
    action,
    changed_fields,
    old_values,
    new_values,
    changed_by_name,
    changed_at
FROM master.v_contract_lives_history_enriched
WHERE contract_life_id = 1
ORDER BY changed_at DESC;
```

**Resultado esperado:**
```
 action      | changed_fields                        | changed_by_name | changed_at
-------------+---------------------------------------+-----------------+---------------------
 substituted | ["status", "end_date", ...]           | Admin User      | 2025-10-03 14:30:00
 updated     | ["substitution_reason"]               | Admin User      | 2025-10-02 10:15:00
 created     | null                                  | Admin User      | 2025-01-15 08:00:00
```

---

### Exemplo 2: Histórico de todas as vidas de um contrato

```sql
SELECT
    person_name,
    action,
    changed_at,
    changed_by_name
FROM master.v_contract_lives_history_enriched
WHERE contract_id = 1
ORDER BY changed_at DESC;
```

---

### Exemplo 3: Mudanças feitas por um usuário específico

```sql
SELECT
    person_name,
    contract_number,
    action,
    changed_at
FROM master.v_contract_lives_history_enriched
WHERE changed_by = 5  -- ID do usuário
ORDER BY changed_at DESC;
```

---

### Exemplo 4: Apenas substituições

```sql
SELECT
    person_name,
    contract_number,
    old_values->>'status' AS status_anterior,
    new_values->>'status' AS status_novo,
    new_values->>'substitution_reason' AS motivo,
    changed_at
FROM master.v_contract_lives_history_enriched
WHERE action = 'substituted'
ORDER BY changed_at DESC;
```

---

### Exemplo 5: Mudanças nas últimas 24 horas

```sql
SELECT
    person_name,
    action,
    changed_fields,
    changed_at
FROM master.v_contract_lives_history_enriched
WHERE changed_at >= NOW() - INTERVAL '24 hours'
ORDER BY changed_at DESC;
```

---

### Exemplo 6: Timeline completa de uma pessoa em todos os contratos

```sql
SELECT
    contract_number,
    action,
    changed_fields,
    changed_at
FROM master.v_contract_lives_history_enriched
WHERE person_name ILIKE '%João Silva%'
ORDER BY changed_at DESC;
```

---

### Exemplo 7: Buscar mudanças em campo específico

```sql
SELECT
    person_name,
    old_values->>'start_date' AS data_inicio_antiga,
    new_values->>'start_date' AS data_inicio_nova,
    changed_at,
    changed_by_name
FROM master.v_contract_lives_history_enriched
WHERE changed_fields @> '["start_date"]'::jsonb  -- Busca JSONB
ORDER BY changed_at DESC;
```

---

## 🌐 API ENDPOINT

### Endpoint de Histórico

**URL:** `GET /api/v1/contracts/{contract_id}/lives/{life_id}/history`

**Autenticação:** Bearer Token (JWT)

**Permissão necessária:** `contracts.view`

**Exemplo de requisição:**
```bash
curl -X GET "http://192.168.11.83:8000/api/v1/contracts/1/lives/1/history" \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

**Response (JSON):**
```json
{
  "contract_life_id": 1,
  "person_name": "João Silva",
  "total_events": 3,
  "events": [
    {
      "id": 15,
      "action": "substituted",
      "changed_fields": ["status", "end_date", "substitution_reason"],
      "old_values": {
        "status": "active",
        "end_date": null,
        "substitution_reason": null
      },
      "new_values": {
        "status": "substituted",
        "end_date": "2025-10-03",
        "substitution_reason": "Substituído por Maria Santos"
      },
      "changed_by": 5,
      "changed_by_name": "Admin User",
      "changed_at": "2025-10-03T14:30:00"
    },
    {
      "id": 12,
      "action": "updated",
      "changed_fields": ["substitution_reason"],
      "old_values": {
        "substitution_reason": null
      },
      "new_values": {
        "substitution_reason": "Mudança de endereço"
      },
      "changed_by": 5,
      "changed_by_name": "Admin User",
      "changed_at": "2025-10-02T10:15:00"
    },
    {
      "id": 8,
      "action": "created",
      "changed_fields": null,
      "old_values": null,
      "new_values": {
        "id": 1,
        "contract_id": 1,
        "person_id": 141,
        "person_name": "João Silva",
        "start_date": "2025-01-15",
        "relationship_type": "FUNCIONARIO",
        "status": "active"
      },
      "changed_by": 5,
      "changed_by_name": "Admin User",
      "changed_at": "2025-01-15T08:00:00"
    }
  ]
}
```

**Possíveis erros:**
- `404 Not Found` - Vida não encontrada
- `400 Bad Request` - Vida não pertence ao contrato especificado
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Sem permissão `contracts.view`

---

## 💻 FRONTEND - TypeScript/React

### Service Layer

**Arquivo:** `frontend/src/services/contractsService.ts`

**Método disponível:**
```typescript
async getContractLifeHistory(
  contractId: number,
  lifeId: number
): Promise<ContractLifeHistory>
```

**Exemplo de uso em componente:**
```typescript
import { contractsService } from '@/services/contractsService';

const MyComponent = () => {
  const [history, setHistory] = useState<ContractLifeHistory | null>(null);

  const loadHistory = async (contractId: number, lifeId: number) => {
    try {
      const data = await contractsService.getContractLifeHistory(contractId, lifeId);
      setHistory(data);
      console.log(`Total de eventos: ${data.total_events}`);
      console.log(`Pessoa: ${data.person_name}`);

      data.events.forEach(event => {
        console.log(`${event.action} em ${event.changed_at} por ${event.changed_by_name}`);
      });
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    }
  };

  return (
    <button onClick={() => loadHistory(1, 1)}>
      Ver Histórico
    </button>
  );
};
```

---

### Tipos TypeScript

**Arquivo:** `frontend/src/types/contract-lives.types.ts`

**Interfaces disponíveis:**
```typescript
export interface ContractLifeHistoryEvent {
  id: number;
  action: 'created' | 'updated' | 'substituted' | 'cancelled';
  changed_fields: string[] | null;
  old_values: Record<string, any> | null;
  new_values: Record<string, any> | null;
  changed_by: number;
  changed_by_name: string;
  changed_at: string;
}

export interface ContractLifeHistory {
  contract_life_id: number;
  person_name: string;
  total_events: number;
  events: ContractLifeHistoryEvent[];
}
```

---

## 🖥️ ACESSAR PELA INTERFACE

### Menu de Navegação

1. **Acessar gestão de vidas:**
   - URL: http://192.168.11.83:3000/admin/vidas
   - Menu: "Gestão de Vidas" (após implementação)
   - Atalho: `Ctrl+Alt+X` → digite `hc0050` ou `vidas`

2. **Visualizar histórico de uma vida:**
   - Acesse a lista de vidas
   - Clique no botão "Ver Histórico" (ícone de relógio)
   - Modal exibirá timeline completa

---

## 📈 CASES DE USO

### Case 1: Auditoria de Conformidade
**Situação:** Auditor precisa verificar todas as mudanças em vidas nos últimos 30 dias

**Query:**
```sql
SELECT
    contract_number,
    person_name,
    action,
    changed_fields,
    changed_by_name,
    changed_at
FROM master.v_contract_lives_history_enriched
WHERE changed_at >= NOW() - INTERVAL '30 days'
ORDER BY changed_at DESC;
```

---

### Case 2: Rastreamento de Substituições
**Situação:** Gestor quer ver todas as substituições realizadas

**Query:**
```sql
SELECT
    person_name,
    contract_number,
    new_values->>'substitution_reason' AS motivo,
    new_values->>'end_date' AS data_fim,
    changed_by_name AS responsavel,
    changed_at AS quando
FROM master.v_contract_lives_history_enriched
WHERE action = 'substituted'
ORDER BY changed_at DESC;
```

---

### Case 3: Debugging de Problema
**Situação:** Suporte precisa entender o que aconteceu com uma vida específica

**Query:**
```sql
SELECT
    action AS acao,
    to_char(changed_at, 'DD/MM/YYYY HH24:MI:SS') AS quando,
    changed_by_name AS quem,
    changed_fields AS campos_alterados,
    old_values AS valores_antigos,
    new_values AS valores_novos
FROM master.v_contract_lives_history_enriched
WHERE contract_life_id = 1
ORDER BY changed_at ASC;  -- Ordem cronológica
```

---

### Case 4: Relatório de Atividade de Usuário
**Situação:** Supervisor quer ver o que um usuário específico fez no sistema

**Query:**
```sql
SELECT
    to_char(changed_at, 'DD/MM/YYYY') AS data,
    COUNT(*) AS total_mudancas,
    COUNT(DISTINCT contract_life_id) AS vidas_afetadas,
    COUNT(*) FILTER (WHERE action = 'created') AS criadas,
    COUNT(*) FILTER (WHERE action = 'updated') AS atualizadas,
    COUNT(*) FILTER (WHERE action = 'substituted') AS substituidas,
    COUNT(*) FILTER (WHERE action = 'cancelled') AS canceladas
FROM master.v_contract_lives_history_enriched
WHERE changed_by_email = 'admin@proteamcare.com'
GROUP BY to_char(changed_at, 'DD/MM/YYYY')
ORDER BY to_char(changed_at, 'DD/MM/YYYY') DESC;
```

---

## 🔒 PERMISSÕES NECESSÁRIAS

### Backend (API)
- **Endpoint de histórico:** Requer permissão `contracts.view`
- **Acesso direto ao banco:** Requer acesso ao schema `master`

### Frontend
- **Modal de timeline:** Usuário logado com permissão `contracts.view`

---

## 📊 PERFORMANCE

### Índices criados para otimização:

1. `idx_contract_lives_history_life_id` - Busca por vida
2. `idx_contract_lives_history_changed_by` - Busca por usuário
3. `idx_contract_lives_history_changed_at` - Busca por data
4. `idx_contract_lives_history_action` - Busca por tipo de ação
5. `idx_contract_lives_history_timeline` - Timeline de uma vida (composto)
6. `idx_contract_lives_history_changed_fields_gin` - Busca em campos alterados (GIN)

**Dica:** Use os índices nas cláusulas WHERE para queries rápidas.

---

## 🎓 BOAS PRÁTICAS

### ✅ Recomendado:
- Use a **view enriquecida** para consultas com informações de contexto
- Sempre filtre por **data** em consultas de longo período
- Use **LIMIT** em queries exploratórias
- Aproveite os **índices** filtrando por `contract_life_id`, `changed_by`, `changed_at`, ou `action`

### ❌ Evite:
- SELECT * sem WHERE em ambientes de produção
- Queries sem LIMIT em tabelas grandes
- Buscar campos JSON sem usar operadores otimizados (`@>`, `->`, `->>`)

---

## 📞 SUPORTE

**Dúvidas?** Consulte a documentação completa:
- Sprint 3: `doc/SPRINT3_AUDITORIA_CONCLUIDA.md`
- Migration: `migrations/018_contract_lives_audit_history.sql`

**Problemas?** Verifique:
1. Permissões de usuário (`contracts.view`)
2. Conexão com banco de dados
3. Logs da aplicação backend

---

**Documento criado em:** 03/10/2025
**Versão:** 1.0
**Status:** ✅ Pronto para uso
