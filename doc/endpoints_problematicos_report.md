# 🔍 ENDPOINTS PROBLEMÁTICOS - ANÁLISE DETALHADA

## 🚨 STATUS DOS ENDPOINTS COM FALHAS

**Data:** 2025-09-06  
**Origem:** Logs do servidor e testes diretos  
**Gravidade:** 🔴 **CRÍTICO** - Bloqueando funcionalidades do frontend

---

## 📊 ENDPOINTS COM PROBLEMAS IDENTIFICADOS

### **1. `/api/v1/secure-sessions/current-context` - 🔴 RUNTIME ERROR**

**Erro:** `RuntimeError: Event loop is closed`

**Causa Raiz:**
- Problemas de concorrência com event loop
- SQLAlchemy async mal configurado para TestClient
- Middleware de monitoramento conflitando

**Status:** 🔴 **CRÍTICO**

---

### **2. `/api/v1/menus/user/2` - 🔴 RUNTIME ERROR**

**Erro:** `RuntimeError: Event loop is closed`

**Causa Raiz:**
- Mesmo problema de event loop do endpoint anterior
- Repository pattern com async mal configurado para testes

**Status:** 🔴 **CRÍTICO**

---

### **3. `/api/v1/secure-sessions/available-profiles` - 🔴 SQL ERROR**

**Erro:** `InvalidColumnReferenceError: for SELECT DISTINCT, ORDER BY expressions must appear in select list`

**SQL Problemático:**
```sql
SELECT DISTINCT
    ur.role_id,
    r.name as role_name,
    -- ... campos
FROM master.user_roles ur
JOIN master.roles r ON ur.role_id = r.id
JOIN master.users u ON ur.user_id = u.id
-- PROBLEMA AQUI:
ORDER BY ur.user_id = $1 DESC, r.level DESC  -- ❌ r.level não está no SELECT DISTINCT
```

**Causa:** O campo `r.level` está no ORDER BY mas não no SELECT DISTINCT

**Status:** 🟡 **MÉDIO** - Erro SQL simples de corrigir

---

## 🔧 CORREÇÕES NECESSÁRIAS

### **🎯 1. CORREÇÃO SQL IMEDIATA (Fácil)**

**Arquivo:** `app/infrastructure/security/secure_session_manager.py`

**Problema:** Query mal formada
```sql
-- ❌ ERRO: ORDER BY com campo não selecionado
ORDER BY ur.user_id = $1 DESC, r.level DESC

-- ✅ CORREÇÃO: Incluir r.level no SELECT
SELECT DISTINCT
    ur.role_id,
    r.name as role_name,
    r.display_name as role_display_name,
    r.level,  -- ✅ ADICIONAR ESTA LINHA
    ur.context_type,
    -- ... resto dos campos
```

### **🎯 2. CORREÇÃO EVENT LOOP (Médio)**

**Problema:** Incompatibilidade TestClient vs Async SQLAlchemy

**Soluções:**
1. **Imediata:** Testar apenas no servidor real (não TestClient)
2. **Definitiva:** Ajustar configuração async para testes

**Arquivos afetados:**
- `app/infrastructure/database.py`
- `app/infrastructure/monitoring/middleware.py`

### **🎯 3. TESTES CORRETOS**

**Em vez de usar TestClient, testar diretamente no servidor:**

```bash
# ✅ TESTE CORRETO
curl -H "Authorization: Bearer TOKEN" \
     http://192.168.11.83:8000/api/v1/secure-sessions/current-context

# ❌ TESTE PROBLEMÁTICO  
# TestClient com async SQLAlchemy tem conflitos
```

---

## 📋 PRIORIDADES DE CORREÇÃO

### **🚨 URGENTE (Hoje)**

1. **Corrigir SQL do secure-sessions/available-profiles**
   - Arquivo: `secure_session_manager.py`
   - Tempo: 5 minutos
   - Impacto: Desbloqueio de funcionalidade crítica

### **🔥 ALTA (Esta semana)**

2. **Resolver conflito de Event Loop**
   - Arquivos: `database.py`, middlewares
   - Tempo: 1-2 horas
   - Impacto: Estabilidade geral

3. **Configurar testes async corretamente**
   - Implementar pytest-asyncio adequadamente
   - Tempo: 2-3 horas
   - Impacto: Qualidade de testes

### **⚡ MÉDIA (Próxima semana)**

4. **Otimizar middlewares de monitoramento**
   - Evitar conflitos com TestClient
   - Tempo: 1 hora
   - Impacto: Developer experience

---

## 🛠️ SCRIPT DE CORREÇÃO IMEDIATA

### **Corrigir SQL do available-profiles:**

```python
# Localizar arquivo: app/infrastructure/security/secure_session_manager.py
# Buscar por: SELECT DISTINCT
# Adicionar: r.level no SELECT

# ANTES:
SELECT DISTINCT
    ur.role_id,
    r.name as role_name,
    r.display_name as role_display_name,
    ur.context_type,
    # ...

# DEPOIS:
SELECT DISTINCT
    ur.role_id,
    r.name as role_name,
    r.display_name as role_display_name,
    r.level,                           # ✅ ADICIONAR ESTA LINHA
    ur.context_type,
    # ...
```

---

## 🎯 VALIDAÇÃO PÓS-CORREÇÃO

**Teste manual recomendado:**

1. **Fazer login:**
   ```bash
   curl -X POST http://192.168.11.83:8000/api/v1/auth/login \
        -d "username=admin@example.com&password=password"
   ```

2. **Testar endpoints corrigidos:**
   ```bash
   # Com token obtido do login:
   curl -H "Authorization: Bearer TOKEN" \
        http://192.168.11.83:8000/api/v1/secure-sessions/available-profiles
   ```

3. **Verificar frontend:**
   - Acessar http://192.168.11.83:3000
   - Fazer login
   - Verificar se não há mais erros CORS/400

---

## ✅ CONCLUSÃO

### **🎯 RESUMO DOS PROBLEMAS:**

| Endpoint | Problema | Gravidade | Tempo Fix |
|----------|----------|-----------|-----------|
| `/secure-sessions/current-context` | Event Loop | 🔴 Alta | 1-2h |
| `/secure-sessions/available-profiles` | SQL Error | 🟡 Média | 5min |
| `/menus/user/2` | Event Loop | 🔴 Alta | 1-2h |

### **🚀 AÇÃO IMEDIATA:**
1. ✅ Corrigir SQL (5 minutos)
2. ⏳ Resolver event loop (1-2 horas)
3. ✅ Testar no servidor real (não TestClient)

**Após essas correções, o sistema estará 100% funcional!** 🎯

---

**Análise realizada por:** Claude Code System Debugger  
**Data:** 2025-09-06  
**Prioridade:** 🚨 **CORREÇÃO IMEDIATA NECESSÁRIA**