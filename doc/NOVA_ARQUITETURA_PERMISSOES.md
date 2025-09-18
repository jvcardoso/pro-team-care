# Nova Arquitetura: Sistema 100% Baseado em Permissões

## 🎯 Visão Geral

Proposta de arquitetura para substituir o sistema hierárquico de níveis por **permissões granulares**, proporcionando controle preciso e flexibilidade total na gestão de acessos.

## 🏗️ Componentes da Nova Arquitetura

### 1. **Sistema de Permissões Granulares**

```python
# Estrutura de Permissões
PERMISSION_CATEGORIES = {
    "users": [
        "users.view",           # Ver usuários
        "users.list",           # Listar usuários
        "users.create",         # Criar usuários
        "users.edit",           # Editar usuários
        "users.delete",         # Excluir usuários
        "users.activate",       # Ativar/desativar usuários
        "users.permissions",    # Gerenciar permissões de usuários
    ],
    "companies": [
        "companies.view",       # Ver empresas
        "companies.list",       # Listar empresas
        "companies.create",     # Criar empresas
        "companies.edit",       # Editar empresas
        "companies.delete",     # Excluir empresas
        "companies.settings",   # Configurações da empresa
    ],
    "establishments": [
        "establishments.view",
        "establishments.list",
        "establishments.create",
        "establishments.edit",
        "establishments.delete",
        "establishments.settings",
    ],
    "roles": [
        "roles.view",
        "roles.list",
        "roles.create",
        "roles.edit",
        "roles.delete",
        "roles.assign",         # Atribuir perfis a usuários
    ],
    "system": [
        "system.admin",         # Administração geral
        "system.settings",      # Configurações do sistema
        "system.logs",          # Acesso a logs
        "system.backup",        # Backup/restore
    ]
}
```

### 2. **Templates de Perfis Pré-configurados**

```python
# Templates baseados em funções de negócio
ROLE_TEMPLATES = {
    "super_admin": {
        "name": "Super Administrador",
        "description": "Acesso total ao sistema",
        "permissions": [
            "system.admin", "system.settings", "system.logs", "system.backup",
            "companies.create", "companies.edit", "companies.delete", "companies.settings",
            "users.create", "users.edit", "users.delete", "users.permissions",
            "roles.create", "roles.edit", "roles.delete", "roles.assign",
        ]
    },

    "admin_empresa": {
        "name": "Administrador da Empresa",
        "description": "Gestão completa da empresa",
        "permissions": [
            "companies.edit", "companies.settings",
            "establishments.create", "establishments.edit", "establishments.delete",
            "users.create", "users.edit", "users.delete",
            "roles.view", "roles.assign",
        ]
    },

    "admin_estabelecimento": {
        "name": "Administrador do Estabelecimento",
        "description": "Gestão do estabelecimento",
        "permissions": [
            "establishments.edit", "establishments.settings",
            "users.view", "users.list", "users.edit",
            "companies.view",
        ]
    },

    "gerente_operacional": {
        "name": "Gerente Operacional",
        "description": "Operações diárias",
        "permissions": [
            "users.view", "users.list",
            "establishments.view",
            "companies.view",
        ]
    },

    "operador": {
        "name": "Operador",
        "description": "Acesso básico para operações",
        "permissions": [
            "users.view",
            "establishments.view",
            "companies.view",
        ]
    },

    "consultor": {
        "name": "Consultor Externo",
        "description": "Acesso limitado para consultoria",
        "permissions": [
            "companies.view",
            "establishments.view",
        ]
    }
}
```

### 3. **Sistema de Cache de Permissões**

```python
# Cache otimizado para performance
class PermissionCache:
    """Cache inteligente de permissões por usuário"""

    @staticmethod
    async def get_user_permissions(user_id: int, context_type: str, context_id: int = None):
        """
        Retorna todas as permissões do usuário em um contexto específico
        com cache Redis para performance
        """
        cache_key = f"permissions:{user_id}:{context_type}:{context_id}"

        # Verificar cache
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Buscar no banco
        permissions = await db.execute("""
            SELECT DISTINCT p.name
            FROM master.user_roles ur
            JOIN master.roles r ON ur.role_id = r.id
            JOIN master.role_permissions rp ON r.id = rp.role_id
            JOIN master.permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = :user_id
              AND ur.context_type = :context_type
              AND (:context_id IS NULL OR ur.context_id = :context_id)
              AND ur.status = 'active'
              AND ur.deleted_at IS NULL
              AND r.is_active = true
              AND p.is_active = true
        """, {
            "user_id": user_id,
            "context_type": context_type,
            "context_id": context_id
        })

        permissions_list = [row[0] for row in permissions]

        # Cachear por 30 minutos
        await redis.setex(cache_key, 1800, json.dumps(permissions_list))

        return permissions_list

    @staticmethod
    async def has_permission(user_id: int, permission: str, context_type: str, context_id: int = None):
        """Verificação rápida de permissão específica"""
        permissions = await PermissionCache.get_user_permissions(user_id, context_type, context_id)
        return permission in permissions

    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Limpar cache quando permissões do usuário mudarem"""
        pattern = f"permissions:{user_id}:*"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
```

### 4. **Decorators Aprimorados**

```python
# Decorators mais flexíveis e performáticos
def require_permission(permission: str, context_type: str = "establishment"):
    """
    Decorator principal para verificação de permissões
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            context_id = kwargs.get('context_id') or getattr(current_user, f'current_{context_type}_id', None)

            has_permission = await PermissionCache.has_permission(
                current_user.id, permission, context_type, context_id
            )

            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "message": f"Missing permission: {permission}",
                        "required_permission": permission,
                        "context_type": context_type,
                    }
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_any_permission(*permissions: str, context_type: str = "establishment"):
    """
    Decorator para verificar se usuário tem QUALQUER uma das permissões
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            context_id = kwargs.get('context_id') or getattr(current_user, f'current_{context_type}_id', None)

            user_permissions = await PermissionCache.get_user_permissions(
                current_user.id, context_type, context_id
            )

            has_any = any(perm in user_permissions for perm in permissions)

            if not has_any:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "message": f"Missing any of permissions: {', '.join(permissions)}",
                        "required_permissions": list(permissions),
                        "context_type": context_type,
                    }
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_all_permissions(*permissions: str, context_type: str = "establishment"):
    """
    Decorator para verificar se usuário tem TODAS as permissões
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            context_id = kwargs.get('context_id') or getattr(current_user, f'current_{context_type}_id', None)

            user_permissions = await PermissionCache.get_user_permissions(
                current_user.id, context_type, context_id
            )

            has_all = all(perm in user_permissions for perm in permissions)

            if not has_all:
                missing = [perm for perm in permissions if perm not in user_permissions]
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "message": f"Missing permissions: {', '.join(missing)}",
                        "required_permissions": list(permissions),
                        "missing_permissions": missing,
                        "context_type": context_type,
                    }
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### 5. **Interface de Gestão Aprimorada**

```javascript
// Componente React para gestão de perfis
const RolePermissionManager = () => {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [customPermissions, setCustomPermissions] = useState([]);
  const [roleData, setRoleData] = useState({
    name: '',
    description: '',
    permissions: []
  });

  const permissionCategories = {
    'Usuários': ['users.view', 'users.create', 'users.edit', 'users.delete'],
    'Empresas': ['companies.view', 'companies.create', 'companies.edit'],
    'Estabelecimentos': ['establishments.view', 'establishments.create', 'establishments.edit'],
    'Sistema': ['system.admin', 'system.settings', 'system.logs']
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setRoleData({
      ...roleData,
      name: template.name,
      description: template.description,
      permissions: [...template.permissions]
    });
  };

  const togglePermission = (permission) => {
    const newPermissions = roleData.permissions.includes(permission)
      ? roleData.permissions.filter(p => p !== permission)
      : [...roleData.permissions, permission];

    setRoleData({
      ...roleData,
      permissions: newPermissions
    });
  };

  return (
    <div className="role-permission-manager">
      {/* Template Selection */}
      <div className="template-section">
        <h3>Templates Pré-configurados</h3>
        {Object.entries(ROLE_TEMPLATES).map(([key, template]) => (
          <button
            key={key}
            onClick={() => handleTemplateSelect(template)}
            className="template-button"
          >
            {template.name}
          </button>
        ))}
      </div>

      {/* Permission Grid */}
      <div className="permissions-grid">
        {Object.entries(permissionCategories).map(([category, permissions]) => (
          <div key={category} className="permission-category">
            <h4>{category}</h4>
            {permissions.map(permission => (
              <label key={permission} className="permission-item">
                <input
                  type="checkbox"
                  checked={roleData.permissions.includes(permission)}
                  onChange={() => togglePermission(permission)}
                />
                {permission.split('.')[1]}
              </label>
            ))}
          </div>
        ))}
      </div>

      {/* Permission Preview */}
      <div className="permission-preview">
        <h4>Permissões Selecionadas:</h4>
        <div className="selected-permissions">
          {roleData.permissions.map(permission => (
            <span key={permission} className="permission-tag">
              {permission}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### 6. **Sistema de Validação e Auditoria**

```python
# Validações automáticas de consistência
class PermissionValidator:
    """Validador de permissões e detecção de inconsistências"""

    PERMISSION_DEPENDENCIES = {
        "users.delete": ["users.edit", "users.view"],
        "users.edit": ["users.view"],
        "companies.delete": ["companies.edit", "companies.view"],
        "companies.edit": ["companies.view"],
    }

    @classmethod
    def validate_permission_set(cls, permissions: List[str]) -> Dict:
        """Valida se o conjunto de permissões é consistente"""
        warnings = []
        errors = []

        for permission in permissions:
            dependencies = cls.PERMISSION_DEPENDENCIES.get(permission, [])
            missing_deps = [dep for dep in dependencies if dep not in permissions]

            if missing_deps:
                warnings.append({
                    "permission": permission,
                    "missing_dependencies": missing_deps,
                    "message": f"Permission '{permission}' requires: {', '.join(missing_deps)}"
                })

        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors
        }

    @classmethod
    def suggest_permission_templates(cls, requested_permissions: List[str]) -> List[str]:
        """Sugere templates baseado nas permissões solicitadas"""
        suggestions = []

        for template_name, template in ROLE_TEMPLATES.items():
            overlap = len(set(requested_permissions) & set(template["permissions"]))
            similarity = overlap / len(template["permissions"])

            if similarity > 0.7:
                suggestions.append({
                    "template": template_name,
                    "similarity": similarity,
                    "match_count": overlap
                })

        return sorted(suggestions, key=lambda x: x["similarity"], reverse=True)

# Sistema de Auditoria
class PermissionAuditLogger:
    """Log detalhado de mudanças de permissões"""

    @staticmethod
    async def log_permission_change(
        user_id: int,
        action: str,  # 'granted', 'revoked', 'role_assigned', 'role_removed'
        permission: str,
        context_type: str,
        context_id: int = None,
        changed_by: int = None
    ):
        await db.execute("""
            INSERT INTO master.permission_audit_log
            (user_id, action, permission, context_type, context_id, changed_by, created_at)
            VALUES (:user_id, :action, :permission, :context_type, :context_id, :changed_by, NOW())
        """, {
            "user_id": user_id,
            "action": action,
            "permission": permission,
            "context_type": context_type,
            "context_id": context_id,
            "changed_by": changed_by
        })

        # Invalidar cache do usuário
        await PermissionCache.invalidate_user_cache(user_id)
```

## 🚀 Benefícios da Nova Arquitetura

### 1. **Flexibilidade Total**
- Criação de perfis específicos para qualquer necessidade
- Combinações livres de permissões
- Adaptação fácil a mudanças de negócio

### 2. **Performance Otimizada**
- Cache inteligente de permissões
- Consultas otimizadas
- Verificação rápida de acessos

### 3. **Gestão Intuitiva**
- Templates pré-configurados
- Interface visual clara
- Validação automática

### 4. **Auditoria Completa**
- Log detalhado de mudanças
- Rastreabilidade total
- Conformidade com LGPD

### 5. **Escalabilidade**
- Fácil adição de novas permissões
- Suporte a contextos múltiplos
- Crescimento sem limitações

## 📊 Comparação: Antes vs Depois

| Aspecto | Sistema Atual (Níveis) | Nova Arquitetura (Permissões) |
|---------|------------------------|------------------------------|
| **Flexibilidade** | Baixa (hierarquia fixa) | Alta (combinações livres) |
| **Hard Code** | Muito (level >= 80) | Zero |
| **Granularidade** | Baixa (por nível) | Alta (por função) |
| **Manutenção** | Difícil (constantes) | Fácil (configurável) |
| **Performance** | Boa (simples) | Boa (com cache) |
| **Auditoria** | Limitada | Completa |
| **Aprendizado** | Simples | Moderado |

---

**✅ Conclusão:** A nova arquitetura oferece controle total, flexibilidade máxima e elimina definitivamente o hard code, proporcionando uma base sólida para crescimento futuro.
