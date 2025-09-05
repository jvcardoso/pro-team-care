# Guia de Implementação - Sistema de Menus Dinâmicos

**Data:** 2025-09-04  
**Versão:** 1.0  
**Status:** Estrutura Pronta - Implementação Simplificada

## 🎯 OBJETIVO

Implementar sistema de menus dinâmicos que carrega automaticamente do banco de dados, baseado nas permissões do usuário e contexto atual (sistema/empresa/estabelecimento).

## 📊 ANÁLISE DA BASE EXISTENTE

### ✅ ESTRUTURA COMPLETA JÁ DISPONÍVEL
- **Tabela `menus`:** 27 menus cadastrados em hierarquia de 3 níveis
- **Sistema de permissões:** 64 permissões granulares ativas
- **Views otimizadas:** `vw_menu_hierarchy` para consultas recursivas
- **Controle de contexto:** Multi-tenancy implementado
- **Usuários root:** 4 super administradores identificados

### 🔍 EXEMPLO DE DADOS ATUAIS

```sql
-- Menus Principais (Level 0)
1. Dashboard (dashboard.view)
2. Home Care (homecare.access) 
3. Administração (admin.access)
4. Templates & Exemplos (dev only)

-- Submenus Home Care (Level 1)  
- Pacientes (patients.view)
- Consultas (appointments.view) 
- Profissionais (professionals.view)

-- Submenus Administração (Level 1)
- Usuários (users.view)
- Perfis e Permissões (admin.roles.view)
- Empresas (companies.view)
- Auditoria (audit.view.logs)
```

## 🏗️ ESTRUTURA DE IMPLEMENTAÇÃO

### FASE 1: API Backend (PRIORIDADE ALTA)

#### 1.1 Repository Pattern

```python
# app/domain/repositories/menu_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class MenuRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_menus(
        self, 
        user_id: int, 
        context_type: str = "establishment", 
        context_id: Optional[int] = None
    ) -> List[dict]:
        """
        Busca menus permitidos para usuário baseado em suas permissões
        e contexto atual (system/company/establishment).
        """
        
        # Query complexa usando a view vw_menu_hierarchy
        query = text("""
            WITH user_permissions AS (
                SELECT DISTINCT p.name as permission_name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN role_permissions rp ON ur.role_id = rp.role_id  
                JOIN permissions p ON rp.permission_id = p.id
                WHERE u.id = :user_id 
                AND ur.status = 'active'
                AND p.is_active = true
                AND (
                    (ur.context_type = :context_type AND ur.context_id = :context_id)
                    OR (u.is_system_admin = true)
                )
            ),
            filtered_menus AS (
                SELECT m.*
                FROM vw_menu_hierarchy m
                WHERE m.is_active = true 
                AND m.is_visible = true
                AND m.visible_in_menu = true
                AND (
                    -- Menu sem permissão específica (público)
                    m.permission_name IS NULL
                    OR 
                    -- Usuário tem a permissão necessária
                    EXISTS (
                        SELECT 1 FROM user_permissions up 
                        WHERE up.permission_name = m.permission_name
                    )
                    OR
                    -- Super admin vê tudo (exceto dev_only em produção)
                    (
                        EXISTS (
                            SELECT 1 FROM users u 
                            WHERE u.id = :user_id AND u.is_system_admin = true
                        )
                        AND (m.dev_only = false OR :show_dev_menus = true)
                    )
                )
                -- Filtros de contexto de empresa/estabelecimento
                AND (
                    (m.company_specific = false AND m.establishment_specific = false)
                    OR 
                    (m.company_specific = true AND :context_type IN ('company', 'establishment'))
                    OR
                    (m.establishment_specific = true AND :context_type = 'establishment')
                )
            )
            SELECT 
                id,
                parent_id,
                name,
                slug,
                url,
                route_name,
                route_params,
                icon,
                color,
                level,
                sort_order,
                badge_text,
                badge_color,
                full_path_name,
                id_path,
                type,
                target
            FROM filtered_menus
            ORDER BY level, sort_order, name
        """)
        
        # Determinar se deve mostrar menus de desenvolvimento
        show_dev = context_type == "system" and context_id == 1
        
        result = await self.db.execute(query, {
            "user_id": user_id,
            "context_type": context_type, 
            "context_id": context_id,
            "show_dev_menus": show_dev
        })
        
        return [dict(row) for row in result.fetchall()]
    
    async def get_menu_tree(self, flat_menus: List[dict]) -> List[dict]:
        """Converte lista plana de menus em árvore hierárquica."""
        
        # Mapear menus por ID para acesso rápido
        menu_map = {menu['id']: menu for menu in flat_menus}
        
        # Inicializar children para todos os menus
        for menu in menu_map.values():
            menu['children'] = []
        
        # Construir hierarquia
        root_menus = []
        
        for menu in flat_menus:
            if menu['parent_id'] is None:
                # Menu raiz
                root_menus.append(menu)
            elif menu['parent_id'] in menu_map:
                # Adicionar como filho do parent
                parent = menu_map[menu['parent_id']]
                parent['children'].append(menu)
        
        return root_menus
```

#### 1.2 Endpoint da API

```python  
# app/presentation/api/v1/menus.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.domain.repositories.menu_repository import MenuRepository
from app.infrastructure.auth import get_current_user
from app.domain.models.user import User

router = APIRouter(prefix="/menus", tags=["menus"])

@router.get("/user/{user_id}")
async def get_user_dynamic_menus(
    user_id: int,
    context_type: str = "establishment",
    context_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna menus dinâmicos permitidos para o usuário no contexto atual.
    
    **Parâmetros:**
    - `user_id`: ID do usuário
    - `context_type`: Tipo de contexto (system/company/establishment)  
    - `context_id`: ID do contexto específico
    
    **Retorna:**
    ```json
    {
        "user_id": 2,
        "context": {
            "type": "establishment", 
            "id": 1,
            "name": "Clínica São João"
        },
        "menus": [
            {
                "id": 1,
                "name": "Dashboard",
                "slug": "dashboard",
                "url": "/admin/dashboard",
                "icon": "LayoutDashboard",
                "children": []
            }
        ]
    }
    ```
    """
    
    # Validar se usuário pode acessar menus de outro usuário
    if current_user.id != user_id and not current_user.is_system_admin:
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado: não é possível acessar menus de outro usuário"
        )
    
    try:
        # Buscar menus do usuário
        menu_repo = MenuRepository(db)
        flat_menus = await menu_repo.get_user_menus(
            user_id=user_id,
            context_type=context_type,
            context_id=context_id
        )
        
        # Converter para árvore hierárquica
        menu_tree = await menu_repo.get_menu_tree(flat_menus)
        
        # Buscar informações do contexto (opcional)
        context_info = await _get_context_info(db, context_type, context_id)
        
        return {
            "user_id": user_id,
            "context": context_info,
            "total_menus": len(flat_menus),
            "menus": menu_tree
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar menus: {str(e)}"
        )

async def _get_context_info(db: AsyncSession, context_type: str, context_id: int):
    """Helper para buscar informações do contexto atual."""
    
    if context_type == "system":
        return {"type": "system", "id": context_id, "name": "Sistema Global"}
    
    elif context_type == "company":
        result = await db.execute(
            text("SELECT id, social_name FROM companies WHERE id = :id"),
            {"id": context_id}
        )
        company = result.fetchone()
        if company:
            return {"type": "company", "id": company[0], "name": company[1]}
    
    elif context_type == "establishment":
        result = await db.execute(
            text("SELECT id, trade_name FROM establishments WHERE id = :id"), 
            {"id": context_id}
        )
        establishment = result.fetchone()
        if establishment:
            return {"type": "establishment", "id": establishment[0], "name": establishment[1]}
    
    return {"type": context_type, "id": context_id, "name": f"{context_type.title()} {context_id}"}
```

#### 1.3 Registrar Rota

```python
# app/presentation/api/v1/api.py  
from .menus import router as menus_router

# Adicionar ao app
app.include_router(menus_router, prefix="/api/v1")
```

### FASE 2: Frontend Dinâmico (PRIORIDADE ALTA)

#### 2.1 Hook Personalizado

```javascript
// frontend/src/hooks/useDynamicMenus.jsx
import { useState, useEffect } from 'react';
import { useUser } from './useUser';
import { useUserContext } from './useUserContext';
import api from '../services/api';

export const useDynamicMenus = () => {
    const [menus, setMenus] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    const { user } = useUser();
    const { currentContext } = useUserContext();
    
    const fetchMenus = async () => {
        if (!user?.id || !currentContext) {
            setLoading(false);
            return;
        }
        
        try {
            setLoading(true);
            setError(null);
            
            const response = await api.get(`/menus/user/${user.id}`, {
                params: {
                    context_type: currentContext.type,
                    context_id: currentContext.id
                }
            });
            
            setMenus(response.data.menus || []);
            
        } catch (err) {
            console.error('Erro ao carregar menus dinâmicos:', err);
            setError('Falha ao carregar menus. Tente novamente.');
            
            // Fallback para menus estáticos em caso de erro
            setMenus(getStaticFallbackMenus());
            
        } finally {
            setLoading(false);
        }
    };
    
    // Recarregar menus quando usuário ou contexto mudarem
    useEffect(() => {
        fetchMenus();
    }, [user?.id, currentContext?.type, currentContext?.id]);
    
    // Função para recarregar manualmente
    const refreshMenus = () => {
        fetchMenus();
    };
    
    return {
        menus,
        loading,
        error,
        refreshMenus
    };
};

// Menus de fallback em caso de erro na API
const getStaticFallbackMenus = () => [
    {
        id: 1,
        name: 'Dashboard',
        slug: 'dashboard',
        url: '/admin/dashboard',
        icon: 'LayoutDashboard',
        children: []
    },
    {
        id: 999,
        name: 'Erro de Conexão',
        slug: 'error',
        url: '#',
        icon: 'AlertCircle',
        children: []
    }
];
```

#### 2.2 Componente de Sidebar Dinâmica

```javascript
// frontend/src/components/navigation/DynamicSidebar.jsx
import React from 'react';
import { useDynamicMenus } from '../../hooks/useDynamicMenus';
import { MenuItem } from './MenuItem';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { Alert } from '../ui/Alert';

export const DynamicSidebar = ({ className = "" }) => {
    const { menus, loading, error, refreshMenus } = useDynamicMenus();
    
    if (loading) {
        return (
            <div className={`${className} flex items-center justify-center p-4`}>
                <LoadingSpinner />
                <span className="ml-2 text-sm text-gray-600">Carregando menus...</span>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className={`${className} p-4`}>
                <Alert type="error" title="Erro ao carregar menus">
                    {error}
                    <button 
                        onClick={refreshMenus}
                        className="ml-2 text-sm underline"
                    >
                        Tentar novamente
                    </button>
                </Alert>
            </div>
        );
    }
    
    return (
        <nav className={`${className} space-y-1`}>
            {menus.map((menu) => (
                <MenuItem 
                    key={menu.id} 
                    menu={menu} 
                    level={0}
                />
            ))}
            
            {menus.length === 0 && (
                <div className="p-4 text-center text-gray-500">
                    <p>Nenhum menu disponível</p>
                    <button 
                        onClick={refreshMenus}
                        className="mt-2 text-sm text-blue-600 hover:underline"
                    >
                        Recarregar
                    </button>
                </div>
            )}
        </nav>
    );
};
```

#### 2.3 Componente de Item de Menu

```javascript
// frontend/src/components/navigation/MenuItem.jsx
import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Icon } from '../ui/Icon';
import { Badge } from '../ui/Badge';

export const MenuItem = ({ menu, level = 0 }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const location = useLocation();
    
    const hasChildren = menu.children && menu.children.length > 0;
    const isActive = location.pathname === menu.url;
    const indentClass = level > 0 ? `ml-${level * 4}` : '';
    
    const handleToggle = (e) => {
        if (hasChildren) {
            e.preventDefault();
            setIsExpanded(!isExpanded);
        }
    };
    
    const MenuContent = () => (
        <>
            <div className="flex items-center">
                {menu.icon && (
                    <Icon 
                        name={menu.icon} 
                        size={18}
                        color={menu.color || 'currentColor'}
                    />
                )}
                
                <span className="ml-3 flex-1">{menu.name}</span>
                
                {menu.badge_text && (
                    <Badge 
                        text={menu.badge_text}
                        color={menu.badge_color}
                        size="sm"
                    />
                )}
                
                {hasChildren && (
                    <div className="ml-2">
                        {isExpanded ? (
                            <ChevronDown size={16} />
                        ) : (
                            <ChevronRight size={16} />
                        )}
                    </div>
                )}
            </div>
        </>
    );
    
    const itemClasses = `
        ${indentClass}
        flex items-center px-3 py-2 text-sm rounded-lg
        transition-colors duration-200
        ${isActive 
            ? 'bg-blue-100 text-blue-700 font-medium' 
            : 'text-gray-700 hover:bg-gray-100'
        }
        ${hasChildren ? 'cursor-pointer' : ''}
    `;
    
    return (
        <div>
            {menu.url && menu.url !== '#' ? (
                <Link 
                    to={menu.url}
                    target={menu.target || '_self'}
                    className={itemClasses}
                    onClick={handleToggle}
                >
                    <MenuContent />
                </Link>
            ) : (
                <div 
                    className={itemClasses}
                    onClick={handleToggle}
                >
                    <MenuContent />
                </div>
            )}
            
            {hasChildren && isExpanded && (
                <div className="mt-1">
                    {menu.children.map((child) => (
                        <MenuItem 
                            key={child.id}
                            menu={child}
                            level={level + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};
```

#### 2.4 Integração no Layout Principal

```javascript
// frontend/src/components/layout/AdminLayout.tsx - ATUALIZAR
import { DynamicSidebar } from '../navigation/DynamicSidebar';

export const AdminLayout = ({ children }) => {
    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <div className="w-64 bg-white shadow-sm">
                <div className="p-4">
                    <h1 className="text-xl font-semibold text-gray-800">
                        Pro Team Care
                    </h1>
                </div>
                
                {/* Substituir Sidebar estática por DynamicSidebar */}
                <DynamicSidebar className="px-4 pb-4" />
            </div>
            
            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                {children}
            </div>
        </div>
    );
};
```

### FASE 3: Cache e Otimização (PRIORIDADE MÉDIA)

#### 3.1 Cache Redis (Opcional)

```python
# app/infrastructure/cache/menu_cache.py
import json
from typing import List, Optional
import redis.asyncio as redis
from app.core.config import settings

class MenuCache:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
        self.ttl = 900  # 15 minutos
    
    def _get_cache_key(self, user_id: int, context_type: str, context_id: Optional[int]) -> str:
        return f"menus:user:{user_id}:ctx:{context_type}:{context_id}"
    
    async def get_user_menus(
        self, 
        user_id: int, 
        context_type: str, 
        context_id: Optional[int]
    ) -> Optional[List[dict]]:
        """Busca menus do cache."""
        key = self._get_cache_key(user_id, context_type, context_id)
        
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Falha silenciosa, buscar do banco
        
        return None
    
    async def set_user_menus(
        self,
        user_id: int,
        context_type: str, 
        context_id: Optional[int],
        menus: List[dict]
    ):
        """Salva menus no cache."""
        key = self._get_cache_key(user_id, context_type, context_id)
        
        try:
            await self.redis.setex(
                key, 
                self.ttl, 
                json.dumps(menus, default=str)
            )
        except Exception:
            pass  # Falha silenciosa
    
    async def invalidate_user_cache(self, user_id: int):
        """Invalida cache de um usuário específico."""
        pattern = f"menus:user:{user_id}:*"
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception:
            pass
```

## 🚀 PLANO DE EXECUÇÃO

### Cronograma Estimado: 2-3 dias

#### DIA 1: Backend API
- [ ] Criar `MenuRepository` com query otimizada
- [ ] Implementar endpoint `/menus/user/{user_id}`  
- [ ] Testar API com usuários reais do sistema
- [ ] Validar performance das queries

#### DIA 2: Frontend Dinâmico
- [ ] Implementar hook `useDynamicMenus`
- [ ] Criar componente `DynamicSidebar`
- [ ] Implementar componente `MenuItem` recursivo
- [ ] Integrar no `AdminLayout`

#### DIA 3: Testes e Refinamentos  
- [ ] Testar mudança de contexto (empresa/estabelecimento)
- [ ] Validar permissões por usuário
- [ ] Implementar fallbacks para erros
- [ ] Ajustes de UI/UX

### Tarefas Opcionais (Futuro)
- [ ] Cache Redis para performance
- [ ] Breadcrumbs dinâmicos
- [ ] Favoritos de menu por usuário
- [ ] Menus contextuais (ações rápidas)

## 🔧 CONFIGURAÇÕES NECESSÁRIAS

### Variáveis de Ambiente
```bash
# .env
REDIS_URL=redis://localhost:6379/0  # Opcional para cache
```

### Dependências Python
```bash
# Já instaladas no projeto atual
- sqlalchemy[asyncio]
- fastapi
- asyncpg
```

### Dependências Frontend  
```bash
# frontend/package.json - Já instaladas
- react
- react-router-dom  
- lucide-react (ícones)
```

## ✅ VALIDAÇÃO E TESTES

### Casos de Teste Principais

1. **Super Admin:** Deve ver todos os menus (incluindo dev_only)
2. **Admin Empresa:** Deve ver menus do contexto empresa + estabelecimento
3. **Admin Estabelecimento:** Deve ver apenas menus do estabelecimento
4. **Operador:** Deve ver apenas menus operacionais
5. **Mudança de contexto:** Menus devem atualizar automaticamente

### Queries de Teste

```sql
-- Testar menu hierarchy para usuário específico  
SELECT * FROM vw_menu_hierarchy 
WHERE permission_name IN (
    SELECT p.name FROM users u
    JOIN user_roles ur ON u.id = ur.user_id
    JOIN role_permissions rp ON ur.role_id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id  
    WHERE u.id = 2 AND ur.status = 'active'
) OR permission_name IS NULL
ORDER BY level, sort_order;

-- Validar permissões de usuário por contexto
SELECT u.email_address, r.name as role, p.name as permission, ur.context_type, ur.context_id
FROM users u
JOIN user_roles ur ON u.id = ur.user_id  
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.id = 2 AND ur.status = 'active'
ORDER BY ur.context_type, p.module, p.action;
```

## 🎉 CONCLUSÃO

A estrutura para menus dinâmicos **já está completamente implementada no banco de dados**. A implementação se resume a:

1. **API Backend:** 1 repository + 1 endpoint
2. **Frontend:** 2 hooks + 2 componentes  
3. **Integração:** Substituir sidebar estática

**Vantagens da implementação:**
- ✅ **Zero breaking changes** na estrutura atual
- ✅ **Performance otimizada** com views especializadas
- ✅ **Segurança enterprise** com validação dupla  
- ✅ **Multi-tenancy completo** já funcional
- ✅ **Escalabilidade** para novos módulos via cadastro

**A base sólida já existe - apenas conectar frontend ao backend!**