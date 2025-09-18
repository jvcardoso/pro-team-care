# 🔒 SEGURANÇA SIMPLIFICADA - NÃO ALTERAR!

## ⚠️ AVISO IMPORTANTE
Este projeto foi **INTENCIONALMENTE SIMPLIFICADO** para desenvolvimento ágil.
**NÃO REATIVE** a segurança enterprise complexa!

## ❌ O QUE FOI REMOVIDO (E POR QUÊ):

### 1. CSP (Content Security Policy) Complexo
- **Problema**: Bloqueava frontend/APIs
- **Removido**: CSP restritivo
- **Mantido**: Headers básicos apenas

### 2. Rate Limiting Avançado
- **Problema**: Redis dependency, complexidade
- **Removido**: Storage inteligente Redis/Memory
- **Mantido**: Memory apenas, só no login

### 3. CORS Restritivo
- **Problema**: Bloqueava desenvolvimento local
- **Removido**: Origins específicos, headers limitados
- **Mantido**: CORS aberto (`allow_origins=["*"]`)

### 4. Middlewares Pesados
- **Problema**: Performance ruim, debugging difícil
- **Removido**: TrustedHost, Monitoring, HSTS
- **Mantido**: Security headers básicos

## ✅ CONFIGURAÇÃO ATUAL (NÃO ALTERAR):

```python
# CORS - SIMPLES E FUNCIONAL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ NÃO MUDAR - necessário para desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HEADERS - APENAS O ESSENCIAL
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Menos restritivo

# RATE LIMITING - MEMÓRIA APENAS
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # ⚠️ NÃO MUDAR - sem Redis dependency
)
```

## 🚫 NUNCA REATIVAR:

1. `Strict-Transport-Security` headers
2. `Content-Security-Policy` complexo
3. `TrustedHostMiddleware`
4. Rate limiting com Redis
5. CORS com origins específicos
6. Monitoring middleware pesado

## ✅ SE PRECISAR DE SEGURANÇA EM PRODUÇÃO:

Crie um **arquivo separado** `security_production.py` - NÃO modifique os arquivos atuais!

---
**Data**: 2025-09-10
**Motivo**: Desenvolvimento travado por segurança excessiva
**Decisão**: Manter simples SEMPRE
