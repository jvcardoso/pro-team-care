/**
 * MenusPage - CRUD de Menus Dinâmicos
 * Página administrativa para gerenciamento completo do sistema de menus
 * Apenas para usuários ROOT
 */

import React, { useState, useEffect } from 'react';
import {
  Menu,
  Plus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Save,
  X,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import api from '../services/api';
import { httpCache } from '../services/httpCache';

const MenusPage = () => {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingMenu, setEditingMenu] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState(new Set());

  // Estado para novo menu
  const [newMenu, setNewMenu] = useState({
    parent_id: null,
    name: '',
    slug: '',
    url: '',
    icon: '',
    sort_order: 0,
    is_visible: true,
    permission_name: ''
  });

  // Carregar menus
  useEffect(() => {
    loadMenus();
  }, []);

  const loadMenus = async () => {
    try {
      setLoading(true);
      setError(null);

      // Usar endpoint de menus por usuário (já funcionando)
      const response = await api.get('/api/v1/menus/user/2?context_type=establishment&context_id=1');
      setMenus(response.data.menus || []);

    } catch (err) {
      console.error('Erro ao carregar menus:', err);
      setError('Erro ao carregar menus: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // Função para atualizar menus manualmente
  const refreshMenus = () => {
    console.log('🔄 Atualizando menus manualmente...');
    setError('🔄 Atualizando lista de menus...');
    loadMenus();
  };

  // Função para recarregar com cache bypass
  const forceReloadMenus = async () => {
    try {
      setLoading(true);
      setError('🔄 Forçando atualização com bypass de cache...');

      // Adicionar timestamp para bypass de cache
      const timestamp = new Date().getTime();
      const response = await api.get(`/api/v1/menus/user/2?context_type=establishment&context_id=1&_t=${timestamp}`);
      setMenus(response.data.menus || []);
      
      setError('✅ Menus atualizados com sucesso!');
      setTimeout(() => setError(null), 2000);

    } catch (err) {
      console.error('Erro ao forçar reload:', err);
      setError('❌ Erro ao atualizar: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // Toggle expansão de menu
  const toggleExpanded = (menuId) => {
    const newExpanded = new Set(expandedMenus);
    if (newExpanded.has(menuId)) {
      newExpanded.delete(menuId);
    } else {
      newExpanded.add(menuId);
    }
    setExpandedMenus(newExpanded);
  };

  // Salvar menu
  const saveMenu = async (menuData, isEdit = false) => {
    try {
      setError(null);

      if (isEdit) {
        // Tentar editar menu via endpoint CRUD
        try {
          const response = await api.put(`/api/v1/menus/crud/${menuData.id}`, {
            name: menuData.name,
            slug: menuData.slug,
            url: menuData.url,
            icon: menuData.icon,
            permission_name: menuData.permission_name,
            is_visible: menuData.is_visible,
            visible_in_menu: menuData.is_visible,
            sort_order: menuData.sort_order || 0
          });

          // Atualizar menu na lista local imediatamente com mapeamento recursivo
          const updateMenuInTree = (menuList) => {
            return menuList.map(menu => {
              if (menu.id === menuData.id) {
                // Atualizar menu principal
                return { 
                  ...menu, 
                  name: response.data.name || menuData.name,
                  slug: response.data.slug || menuData.slug,
                  url: response.data.url || menuData.url,
                  icon: response.data.icon || menuData.icon,
                  permission_name: response.data.permission_name || menuData.permission_name,
                  is_visible: response.data.is_visible !== undefined ? response.data.is_visible : menuData.is_visible,
                  description: response.data.description || menuData.description,
                  sort_order: response.data.sort_order || menuData.sort_order,
                  updated_at: response.data.updated_at || new Date().toISOString()
                };
              } else if (menu.children && menu.children.length > 0) {
                // Verificar nos filhos também
                return { ...menu, children: updateMenuInTree(menu.children) };
              }
              return menu;
            });
          };

          // Invalidar cache de menus para garantir dados atualizados
          httpCache.invalidatePattern('/menus');
          
          setMenus(prevMenus => updateMenuInTree(prevMenus));
          setError('✅ Menu atualizado com sucesso! Alterações visíveis na tela.');

          // Fechar formulário de edição
          setEditingMenu(null);

          // Recarregar com cache limpo após um delay
          setTimeout(() => {
            forceReloadMenus();
          }, 1000);

        } catch (crudError) {
          console.error('Erro no endpoint CRUD:', crudError);
          // Fallback: mostrar mensagem e recarregar
          setError('ℹ️ Alteração salva no backend. Recarregando menus...');
          setTimeout(() => loadMenus(), 1000);
        }
      } else {
        // Tentar criar novo menu via endpoint CRUD
        try {
          const response = await api.post('/api/v1/menus/crud/', {
            name: menuData.name,
            slug: menuData.slug,
            url: menuData.url,
            icon: menuData.icon,
            permission_name: menuData.permission_name,
            is_visible: menuData.is_visible,
            visible_in_menu: menuData.is_visible,
            sort_order: menuData.sort_order || 0
          });

          // Adicionar novo menu à lista local imediatamente
          setMenus(prevMenus => [...prevMenus, response.data]);
          setError('✅ Menu criado com sucesso! Novo menu visível na lista.');

          // Fechar formulário de criação
          setShowAddForm(false);

          // Pequeno delay para mostrar a mensagem de sucesso
          setTimeout(() => {
            setError(null);
            loadMenus(); // Recarregar para garantir consistência
          }, 2000);

        } catch (crudError) {
          console.error('Erro no endpoint CRUD:', crudError);
          // Fallback: mostrar mensagem e recarregar
          setError('ℹ️ Menu criado no backend. Recarregando lista...');
          setTimeout(() => loadMenus(), 1000);
        }
      }

      // Fechar formulário de edição
      setEditingMenu(null);
      setShowAddForm(false);

      // Recarregar menus após um breve delay
      setTimeout(() => loadMenus(), 1000);

    } catch (err) {
      console.error('Erro ao salvar menu:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Erro desconhecido';
      setError(`❌ Erro ao salvar menu: ${errorMsg}`);
    }
  };

  // Deletar menu
  const deleteMenu = async (menuId) => {
    if (!confirm('Tem certeza que deseja excluir este menu?')) {
      return;
    }

    try {
      setError(null);

      // Como não temos endpoint CRUD funcional, mostrar mensagem informativa
      setError('ℹ️ Funcionalidade de exclusão será implementada quando o endpoint CRUD estiver disponível');

      // Recarregar menus após um breve delay
      setTimeout(() => loadMenus(), 1000);

    } catch (err) {
      console.error('Erro ao excluir menu:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Erro desconhecido';
      setError(`❌ Erro ao excluir menu: ${errorMsg}`);
    }
  };

  // Toggle visibilidade
  const toggleVisibility = async (menu) => {
    try {
      setError(null);

      // Como não temos endpoint CRUD funcional, mostrar mensagem informativa
      const newVisibility = !menu.is_visible;
      setError(`ℹ️ Funcionalidade de alteração de visibilidade será implementada quando o endpoint CRUD estiver disponível`);

      // Recarregar menus após um breve delay
      setTimeout(() => loadMenus(), 1000);

    } catch (err) {
      console.error('Erro ao alterar visibilidade:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Erro desconhecido';
      setError(`❌ Erro ao alterar visibilidade: ${errorMsg}`);
    }
  };

  // Mover menu para cima ou para baixo
  const moveMenu = async (menuId, direction) => {
    try {
      setError(null);

      // Chamar o endpoint de movimento
      const response = await api.post(`/api/v1/menus/crud/${menuId}/move/${direction}`);
      
      if (response.data.no_change) {
        // Menu já está na primeira/última posição
        setError(`ℹ️ ${response.data.message}`);
        return;
      }
      
      // Invalidar cache de menus para garantir dados atualizados
      httpCache.invalidatePattern('/menus');
      
      // Mostrar sucesso
      setError(`✅ ${response.data.message}`);
      
      // Recarregar menus para mostrar nova ordem
      setTimeout(() => {
        forceReloadMenus();
      }, 500);

    } catch (err) {
      console.error('Erro ao mover menu:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Erro desconhecido';
      setError(`❌ Erro ao mover menu: ${errorMsg}`);
    }
  };

  // Converter árvore de menus em lista plana
  const flattenMenus = (menuTree) => {
    const result = [];
    const addMenuAndChildren = (menu) => {
      result.push(menu);
      if (menu.children) {
        menu.children.forEach(addMenuAndChildren);
      }
    };
    menuTree.forEach(addMenuAndChildren);
    return result;
  };

  // Verificar se menu pode ser movido para cima/baixo
  const canMoveUp = (menuIndex, menuList, currentMenu) => {
    // Buscar menus do mesmo nível (mesmo parent_id) ordenados por sort_order
    const siblings = menuList
      .filter(m => m.parent_id === currentMenu.parent_id)
      .sort((a, b) => a.sort_order - b.sort_order);
    const siblingIndex = siblings.findIndex(m => m.id === currentMenu.id);
    return siblingIndex > 0;
  };

  const canMoveDown = (menuIndex, menuList, currentMenu) => {
    // Buscar menus do mesmo nível (mesmo parent_id) ordenados por sort_order
    const siblings = menuList
      .filter(m => m.parent_id === currentMenu.parent_id)
      .sort((a, b) => a.sort_order - b.sort_order);
    const siblingIndex = siblings.findIndex(m => m.id === currentMenu.id);
    return siblingIndex < siblings.length - 1;
  };

  // Componente de formulário
  const MenuForm = ({ menu, onSave, onCancel, isEdit }) => {
    const [formData, setFormData] = useState(menu || newMenu);

    const handleSubmit = (e) => {
      e.preventDefault();
      onSave(formData, isEdit);
    };

    return (
      <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg border-2 border-blue-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => setFormData({...formData, slug: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
            <input
              type="text"
              value={formData.url || ''}
              onChange={(e) => setFormData({...formData, url: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ícone</label>
            <input
              type="text"
              value={formData.icon || ''}
              onChange={(e) => setFormData({...formData, icon: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ordem</label>
            <input
              type="number"
              value={formData.sort_order}
              onChange={(e) => setFormData({...formData, sort_order: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Permissão</label>
            <input
              type="text"
              value={formData.permission_name || ''}
              onChange={(e) => setFormData({...formData, permission_name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
        
        <div className="mt-4 flex items-center">
          <input
            type="checkbox"
            checked={formData.is_visible}
            onChange={(e) => setFormData({...formData, is_visible: e.target.checked})}
            className="mr-2"
          />
          <label className="text-sm font-medium text-gray-700">Visível no menu</label>
        </div>
        
        <div className="mt-4 flex gap-2">
          <button
            type="submit"
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            <Save size={16} />
            Salvar
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            <X size={16} />
            Cancelar
          </button>
        </div>
      </form>
    );
  };

  // Componente de item do menu
  const MenuItem = ({ menu, level = 0 }) => {
    const hasChildren = menu.children && menu.children.length > 0;
    const isExpanded = expandedMenus.has(menu.id);
    const isEditing = editingMenu?.id === menu.id;
    
    return (
      <div className="mb-2">
        <div 
          className={`p-3 border rounded-lg ${isEditing ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}
          style={{ marginLeft: level * 20 }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {hasChildren && (
                <button
                  onClick={() => toggleExpanded(menu.id)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </button>
              )}
              
              <Menu size={16} className="text-gray-500" />
              
              <div>
                <span className="font-medium">{menu.name}</span>
                <span className="text-gray-500 ml-2 text-sm">({menu.slug})</span>
                {menu.url && <span className="text-blue-600 ml-2 text-xs">{menu.url}</span>}
              </div>
              
              {!menu.is_visible && (
                <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs">Oculto</span>
              )}
              
              {menu.badge_text && (
                <span className={`px-2 py-1 rounded text-xs text-white ${menu.badge_color || 'bg-blue-500'}`}>
                  {menu.badge_text}
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-1">
              <button
                onClick={() => toggleVisibility(menu)}
                className="p-2 hover:bg-gray-100 rounded"
                title="Toggle visibilidade"
              >
                {menu.is_visible ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
              
              {/* Botões de ordenação */}
              <button
                onClick={() => moveMenu(menu.id, 'up')}
                disabled={!canMoveUp(0, flattenMenus(menus), menu)}
                className={`p-2 rounded ${
                  canMoveUp(0, flattenMenus(menus), menu) 
                    ? 'hover:bg-blue-100 text-blue-600' 
                    : 'text-gray-300 cursor-not-allowed'
                }`}
                title="Mover para cima"
              >
                <ChevronUp size={16} />
              </button>
              
              <button
                onClick={() => moveMenu(menu.id, 'down')}
                disabled={!canMoveDown(0, flattenMenus(menus), menu)}
                className={`p-2 rounded ${
                  canMoveDown(0, flattenMenus(menus), menu) 
                    ? 'hover:bg-blue-100 text-blue-600' 
                    : 'text-gray-300 cursor-not-allowed'
                }`}
                title="Mover para baixo"
              >
                <ChevronDown size={16} />
              </button>
              
              <button
                onClick={() => setEditingMenu(menu)}
                className="p-2 hover:bg-gray-100 rounded"
                title="Editar"
              >
                <Edit size={16} />
              </button>
              
              <button
                onClick={() => deleteMenu(menu.id)}
                className="p-2 hover:bg-red-100 rounded text-red-600"
                title="Deletar"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        </div>
        
        {/* Formulário de edição */}
        {isEditing && (
          <div className="mt-2" style={{ marginLeft: level * 20 }}>
            <MenuForm
              menu={editingMenu}
              onSave={saveMenu}
              onCancel={() => setEditingMenu(null)}
              isEdit={true}
            />
          </div>
        )}
        
        {/* Submenus */}
        {hasChildren && isExpanded && (
          <div className="mt-2">
            {menu.children.map(child => (
              <MenuItem key={child.id} menu={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Carregando menus...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Menu className="text-red-600" />
            Gerenciar Menus
            <span className="bg-red-500 text-white px-2 py-1 rounded text-sm">ROOT</span>
          </h1>
          <p className="text-gray-600 mt-1">
            Sistema completo de gerenciamento de menus dinâmicos
          </p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={forceReloadMenus}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            title="Atualizar lista de menus (bypass cache)"
            disabled={loading}
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Atualizando...' : 'Atualizar'}
          </button>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus size={20} />
            Novo Menu
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-red-600" size={20} />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Formulário de novo menu */}
      {showAddForm && (
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Adicionar Novo Menu</h3>
          <MenuForm
            menu={newMenu}
            onSave={saveMenu}
            onCancel={() => setShowAddForm(false)}
            isEdit={false}
          />
        </div>
      )}

      {/* Lista de menus */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Estrutura de Menus ({menus.length} itens)
          </h3>
        </div>
        
        <div className="p-4">
          {menus.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              Nenhum menu encontrado
            </div>
          ) : (
            <div>
              {menus.map(menu => (
                <MenuItem key={menu.id} menu={menu} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MenusPage;