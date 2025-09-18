# Guia Rápido - Sistema de Permissões Granulares

## TL;DR - Para Desenvolvedores

### Como Proteger um Endpoint
```python
from app.presentation.decorators.hybrid_permissions import require_permission_or_level

@router.post("/meu-endpoint")
@require_permission_or_level(permission="minha.permissao", context_type="establishment")
async def meu_endpoint(current_user: User = Depends(get_current_user)):
    pass
```

### Contextos Disponíveis
- `system` - Permissões globais
- `company` - Limitado à empresa do usuário
- `establishment` - Limitado ao estabelecimento do usuário

### Permissões Comuns
```python
# Clientes
permission="clients.create"
permission="clients.view"
permission="clients.edit"
permission="clients.delete"

# Empresas
permission="companies.create"
permission="companies.view"
permission="companies.edit"

# Sistema
permission="system.admin"
permission="dashboard.admin"

# Notificações
permission="notifications.view"
permission="notifications.create"
```

### Administração Rápida

#### Atribuir Role a Usuário
```bash
curl -X POST "http://localhost:8000/api/v1/permissions-admin/assign-role" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "role_key": "admin_estabelecimento",
    "context_type": "establishment",
    "context_id": 1
  }'
```

#### Ver Permissões de um Usuário
```bash
curl "http://localhost:8000/api/v1/permissions-admin/user/1/permissions" \
  -H "Authorization: Bearer SEU_TOKEN"
```

#### Migrar Usuário Individual
```bash
curl -X POST "http://localhost:8000/api/v1/permissions-admin/migrate-user/1" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Roles Disponíveis
- `super_admin` - Acesso total
- `admin_empresa` - Admin de empresa
- `admin_estabelecimento` - Admin de estabelecimento
- `usuario_normal` - Usuário básico
- `convidado` - Acesso mínimo

### Troubleshooting Rápido

#### Erro 403 - Permission Denied
1. Verificar se usuário tem role atribuída
2. Verificar se contexto está correto
3. Invalidar cache: `POST /api/v1/permissions-admin/invalidate-cache`

#### Usuário Sem Permissões
1. Migrar usuário: `POST /api/v1/permissions-admin/migrate-user/{id}`
2. Ou atribuir role manualmente

#### Performance Issues
1. Cache Redis deve estar funcionando
2. Verificar logs de cache hits/misses
3. TTL do cache: 5 minutos

---

**Sistema 100% Operacional** ✅
**Sem Dependências de Levels** ✅
**43 Endpoints Protegidos** ✅
