/**
 * MenusPage - CRUD de Menus Dinâmicos
 * Página administrativa para gerenciamento completo do sistema de menus
 * Apenas para usuários ROOT
 */

import React, { useState, useEffect } from "react";
import PermissionProtectedRoute from "../components/auth/PermissionProtectedRoute";
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
  RefreshCw,
} from "lucide-react";
import { menusService } from "../services/api";
import { notify } from "../utils/notifications";

const MenusPage = () => {
  return (
    <PermissionProtectedRoute
      requireRoot={true}
      fallbackMessage="O gerenciamento de menus é restrito a administradores do sistema. Entre em contato com o suporte se precisar de acesso."
    >
      <MenusPageContent />
    </PermissionProtectedRoute>
  );
};

const MenusPageContent = () => {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingMenu, setEditingMenu] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState(new Set());

  // Estado para novo menu
  const [newMenu, setNewMenu] = useState({
    parent_id: null,
    name: "",
    slug: "",
    url: "",
    icon: "",
    sort_order: 0,
    is_visible: true,
    permission_name: "",
  });

  // Carregar menus
  useEffect(() => {
    loadMenus();
  }, []);

  const loadMenus = async () => {
    try {
      setLoading(true);
      setError(null);

      // Obter usuário atual do localStorage para usar ID correto
      const userData = localStorage.getItem("user");
      let userId = 9; // Fallback para admin

      if (userData) {
        try {
          const user = JSON.parse(userData);
          userId = user.id || 9;
        } catch (e) {
          console.warn("Erro ao parsear dados do usuário:", e);
        }
      }

      // Usar serviço de menus para obter menus do usuário
      const response = await menusService.getUserMenus(userId, "establishment");
      setMenus(response.menus || []);
    } catch (err) {
      console.error("Erro ao carregar menus:", err);
      setError(
        "Erro ao carregar menus: " + (err.response?.data?.detail || err.message)
      );
    } finally {
      setLoading(false);
    }
  };

  // Função para atualizar menus manualmente
  const refreshMenus = () => {
    console.log("🔄 Atualizando menus manualmente...");
    setError("🔄 Atualizando lista de menus...");
    loadMenus();
  };

  // Função para recarregar com cache bypass
  const forceReloadMenus = async () => {
    try {
      setLoading(true);
      setError("🔄 Forçando atualização...");

      await loadMenus();

      setError("✅ Menus atualizados com sucesso!");
      setTimeout(() => setError(null), 2000);
    } catch (err) {
      console.error("Erro ao forçar reload:", err);
      setError(
        "❌ Erro ao atualizar: " + (err.response?.data?.detail || err.message)
      );
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
        // Atualizar menu existente
        await menusService.updateMenu(menuData.id, {
          name: menuData.name,
          slug: menuData.slug,
          url: menuData.url,
          icon: menuData.icon,
          permission_name: menuData.permission_name,
          is_visible: menuData.is_visible,
          visible_in_menu: menuData.is_visible,
          sort_order: menuData.sort_order || 0,
        });

        notify.success("Menu atualizado com sucesso!");
        setEditingMenu(null);
      } else {
        // Criar novo menu
        await menusService.createMenu({
          parent_id: menuData.parent_id,
          name: menuData.name,
          slug: menuData.slug,
          url: menuData.url,
          icon: menuData.icon,
          permission_name: menuData.permission_name,
          is_visible: menuData.is_visible,
          visible_in_menu: menuData.is_visible,
          sort_order: menuData.sort_order || 0,
        });

        notify.success("Menu criado com sucesso!");
        setShowAddForm(false);
        setNewMenu({
          parent_id: null,
          name: "",
          slug: "",
          url: "",
          icon: "",
          sort_order: 0,
          is_visible: true,
          permission_name: "",
        });
      }

      // Recarregar menus
      await loadMenus();
    } catch (err) {
      console.error("Erro ao salvar menu:", err);
      const errorMsg =
        err.response?.data?.detail || err.message || "Erro desconhecido";
      notify.error(`Erro ao salvar menu: ${errorMsg}`);
    }
  };

  // Deletar menu
  const deleteMenu = async (menuId) => {
    const menu =
      menus.find((m) => m.id === menuId) ||
      flattenMenus(menus).find((m) => m.id === menuId);
    const menuName = menu?.name || "este menu";

    const executeDelete = async () => {
      try {
        setError(null);

        await menusService.deleteMenu(menuId);
        notify.success("Menu excluído com sucesso!");

        // Recarregar menus
        await loadMenus();
      } catch (err) {
        console.error("Erro ao excluir menu:", err);
        const errorMsg =
          err.response?.data?.detail || err.message || "Erro desconhecido";
        notify.error(`Erro ao excluir menu: ${errorMsg}`);
      }
    };

    notify.confirmDelete(
      "Excluir Menu",
      `Tem certeza que deseja excluir o menu "${menuName}"?`,
      executeDelete
    );
  };

  // Toggle visibilidade
  const toggleVisibility = async (menu) => {
    try {
      setError(null);

      const newVisibility = !menu.is_visible;
      await menusService.toggleMenuVisibility(menu.id, newVisibility);

      notify.success(
        `Menu ${newVisibility ? "ativado" : "desativado"} com sucesso!`
      );

      // Recarregar menus
      await loadMenus();
    } catch (err) {
      console.error("Erro ao alterar visibilidade:", err);
      const errorMsg =
        err.response?.data?.detail || err.message || "Erro desconhecido";
      notify.error(`Erro ao alterar visibilidade: ${errorMsg}`);
    }
  };

  // Mover menu para cima ou para baixo
  const moveMenu = async (menuId, direction) => {
    try {
      setError(null);

      const response = await menusService.moveMenu(menuId, direction);

      if (response.no_change) {
        notify.warning(response.message);
        return;
      }

      notify.success(response.message);

      // Recarregar menus para mostrar nova ordem
      await loadMenus();
    } catch (err) {
      console.error("Erro ao mover menu:", err);
      const errorMsg =
        err.response?.data?.detail || err.message || "Erro desconhecido";
      notify.error(`Erro ao mover menu: ${errorMsg}`);
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
      .filter((m) => m.parent_id === currentMenu.parent_id)
      .sort((a, b) => a.sort_order - b.sort_order);
    const siblingIndex = siblings.findIndex((m) => m.id === currentMenu.id);
    return siblingIndex > 0;
  };

  const canMoveDown = (menuIndex, menuList, currentMenu) => {
    // Buscar menus do mesmo nível (mesmo parent_id) ordenados por sort_order
    const siblings = menuList
      .filter((m) => m.parent_id === currentMenu.parent_id)
      .sort((a, b) => a.sort_order - b.sort_order);
    const siblingIndex = siblings.findIndex((m) => m.id === currentMenu.id);
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
      <form
        onSubmit={handleSubmit}
        className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg border-2 border-blue-200 dark:border-blue-800"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nome
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Slug
            </label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) =>
                setFormData({ ...formData, slug: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL
            </label>
            <input
              type="text"
              value={formData.url || ""}
              onChange={(e) =>
                setFormData({ ...formData, url: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Ícone
            </label>
            <input
              type="text"
              value={formData.icon || ""}
              onChange={(e) =>
                setFormData({ ...formData, icon: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Ordem
            </label>
            <input
              type="number"
              value={formData.sort_order}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  sort_order: parseInt(e.target.value),
                })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Permissão
            </label>
            <input
              type="text"
              value={formData.permission_name || ""}
              onChange={(e) =>
                setFormData({ ...formData, permission_name: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
        </div>

        <div className="mt-4 flex items-center">
          <input
            type="checkbox"
            checked={formData.is_visible}
            onChange={(e) =>
              setFormData({ ...formData, is_visible: e.target.checked })
            }
            className="mr-2"
          />
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Visível no menu
          </label>
        </div>

        <div className="mt-4 flex flex-col sm:flex-row gap-2">
          <button
            type="submit"
            className="flex items-center justify-center gap-2 px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded hover:bg-green-700 dark:hover:bg-green-600 text-sm"
          >
            <Save size={16} />
            Salvar
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded hover:bg-gray-700 dark:hover:bg-gray-600 text-sm"
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
          className={`p-2 sm:p-3 border rounded-lg ${
            isEditing
              ? "border-blue-500 dark:border-blue-600 bg-blue-50 dark:bg-blue-900/30"
              : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
          }`}
          style={{ marginLeft: level * (level > 0 ? 15 : 0) }}
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {hasChildren && (
                <button
                  onClick={() => toggleExpanded(menu.id)}
                  className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  {isExpanded ? (
                    <ChevronDown size={16} />
                  ) : (
                    <ChevronRight size={16} />
                  )}
                </button>
              )}

              <Menu size={16} className="text-gray-500 dark:text-gray-400" />

              <div className="min-w-0 flex-1">
                <div className="font-medium truncate text-gray-900 dark:text-white">
                  {menu.name}
                </div>
                <div className="text-gray-500 dark:text-gray-400 text-sm truncate">
                  ({menu.slug})
                  {menu.url && (
                    <span className="text-blue-600 dark:text-blue-400 ml-2">
                      {menu.url}
                    </span>
                  )}
                </div>
              </div>

              {!menu.is_visible && (
                <span className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 px-2 py-1 rounded text-xs">
                  Oculto
                </span>
              )}

              {menu.badge_text && (
                <span
                  className={`px-2 py-1 rounded text-xs text-white ${
                    menu.badge_color || "bg-blue-500 dark:bg-blue-600"
                  }`}
                >
                  {menu.badge_text}
                </span>
              )}
            </div>

            <div className="flex items-center gap-1 flex-shrink-0">
              {/* Mobile: Botões essenciais */}
              <div className="flex sm:hidden gap-1">
                <button
                  onClick={() => toggleVisibility(menu)}
                  className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  title="Toggle visibilidade"
                >
                  {menu.is_visible ? <Eye size={14} /> : <EyeOff size={14} />}
                </button>
                <button
                  onClick={() => setEditingMenu(menu)}
                  className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  title="Editar"
                >
                  <Edit size={14} />
                </button>
                <button
                  onClick={() => deleteMenu(menu.id)}
                  className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-600 dark:text-red-500"
                  title="Deletar"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {/* Desktop: Todos os botões */}
              <div className="hidden sm:flex gap-1">
                <button
                  onClick={() => toggleVisibility(menu)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  title="Toggle visibilidade"
                >
                  {menu.is_visible ? <Eye size={16} /> : <EyeOff size={16} />}
                </button>

                {/* Botões de ordenação */}
                <button
                  onClick={() => moveMenu(menu.id, "up")}
                  disabled={!canMoveUp(0, flattenMenus(menus), menu)}
                  className={`p-2 rounded ${
                    canMoveUp(0, flattenMenus(menus), menu)
                      ? "hover:bg-blue-100 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                      : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
                  }`}
                  title="Mover para cima"
                >
                  <ChevronUp size={16} />
                </button>

                <button
                  onClick={() => moveMenu(menu.id, "down")}
                  disabled={!canMoveDown(0, flattenMenus(menus), menu)}
                  className={`p-2 rounded ${
                    canMoveDown(0, flattenMenus(menus), menu)
                      ? "hover:bg-blue-100 dark:hover:bg-blue-900/30 text-blue-600 dark:text-blue-400"
                      : "text-gray-300 dark:text-gray-600 cursor-not-allowed"
                  }`}
                  title="Mover para baixo"
                >
                  <ChevronDown size={16} />
                </button>

                <button
                  onClick={() => setEditingMenu(menu)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  title="Editar"
                >
                  <Edit size={16} />
                </button>

                <button
                  onClick={() => deleteMenu(menu.id)}
                  className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-600 dark:text-red-500"
                  title="Deletar"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Formulário de edição */}
        {isEditing && (
          <div className="mt-2" style={{ marginLeft: level * 15 }}>
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
            {menu.children.map((child) => (
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
          <div className="text-gray-500 dark:text-gray-400">
            Carregando menus...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6">
      {/* Header Mobile-First */}
      <div className="mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2 flex-wrap">
              <Menu className="text-red-600 dark:text-red-500" />
              <span>Gerenciar Menus</span>
              <span className="bg-red-500 dark:bg-red-600 text-white px-2 py-1 rounded text-xs sm:text-sm">
                ROOT
              </span>
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">
              Sistema completo de gerenciamento de menus dinâmicos
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={forceReloadMenus}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 text-sm"
              title="Atualizar lista de menus (bypass cache)"
              disabled={loading}
            >
              <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
              <span className="hidden sm:inline">
                {loading ? "Atualizando..." : "Atualizar"}
              </span>
              <span className="sm:hidden">↻</span>
            </button>

            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 text-sm"
            >
              <Plus size={18} />
              <span className="hidden sm:inline">Novo Menu</span>
              <span className="sm:hidden">Novo</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertTriangle
              className="text-red-600 dark:text-red-500"
              size={20}
            />
            <span className="text-red-800 dark:text-red-300">{error}</span>
          </div>
        </div>
      )}

      {/* Formulário de novo menu */}
      {showAddForm && (
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-3">
            Adicionar Novo Menu
          </h3>
          <MenuForm
            menu={newMenu}
            onSave={saveMenu}
            onCancel={() => setShowAddForm(false)}
            isEdit={false}
          />
        </div>
      )}

      {/* Lista de menus */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Estrutura de Menus ({menus.length} itens)
          </h3>
        </div>

        <div className="p-4">
          {menus.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              Nenhum menu encontrado
            </div>
          ) : (
            <div>
              {menus.map((menu) => (
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
