import React, { useState, useEffect } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Textarea from "../ui/Textarea";
import Card from "../ui/Card";
import { rolesService } from "../../services/rolesService";

export const RoleForm = ({ initialData, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: "",
    display_name: "",
    description: "",
    level: 40,
    context_type: "establishment",
    is_active: true,
    permission_ids: [],
  });

  const [permissions, setPermissions] = useState({});
  const [selectedPermissions, setSelectedPermissions] = useState(new Set());
  const [contextTypes, setContextTypes] = useState([]);
  const [roleLevels, setRoleLevels] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFormData();
  }, []);

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || "",
        display_name: initialData.display_name || "",
        description: initialData.description || "",
        level: initialData.level || 40,
        context_type: initialData.context_type || "establishment",
        is_active:
          initialData.is_active !== undefined ? initialData.is_active : true,
        permission_ids: [],
      });

      // Load role permissions if editing
      if (initialData.id) {
        loadRolePermissions(initialData.id);
      }
    }
  }, [initialData]);

  const loadFormData = async () => {
    try {
      setLoadingData(true);
      const [permissionsData, contextTypesData, levelsData] = await Promise.all(
        [
          rolesService.getPermissionsGrouped(),
          rolesService.getContextTypes(),
          rolesService.getRoleLevels(),
        ]
      );

      setPermissions(permissionsData);
      setContextTypes(contextTypesData);
      setRoleLevels(levelsData);
    } catch (err) {
      setError("Erro ao carregar dados do formulário: " + err.message);
    } finally {
      setLoadingData(false);
    }
  };

  const loadRolePermissions = async (roleId) => {
    try {
      const rolePermissions = await rolesService.getRolePermissions(roleId);
      const permissionIds = new Set(rolePermissions.map((p) => p.id));
      setSelectedPermissions(permissionIds);
      setFormData((prev) => ({
        ...prev,
        permission_ids: Array.from(permissionIds),
      }));
    } catch (err) {
      console.error("Erro ao carregar permissões do perfil:", err);
    }
  };

  const handleInputChange = (field, value) => {
    // Sanitize name field to only allow valid characters
    if (field === "name") {
      value = value.toLowerCase().replace(/[^a-z0-9_]/g, "");
    }

    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  };

  const handlePermissionToggle = (permissionId) => {
    const newSelected = new Set(selectedPermissions);

    if (newSelected.has(permissionId)) {
      newSelected.delete(permissionId);
    } else {
      newSelected.add(permissionId);
    }

    setSelectedPermissions(newSelected);
    setFormData((prev) => ({
      ...prev,
      permission_ids: Array.from(newSelected),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validations
      if (!formData.name.trim()) {
        throw new Error("Nome técnico é obrigatório");
      }
      if (!formData.display_name.trim()) {
        throw new Error("Nome de exibição é obrigatório");
      }
      if (!/^[a-zA-Z0-9_]+$/.test(formData.name)) {
        throw new Error(
          "Nome técnico deve conter apenas letras, números e underscore"
        );
      }
      if (formData.name.length < 3) {
        throw new Error("Nome técnico deve ter pelo menos 3 caracteres");
      }
      if (formData.display_name.length < 3) {
        throw new Error("Nome de exibição deve ter pelo menos 3 caracteres");
      }
      if (formData.level < 10 || formData.level > 100) {
        throw new Error("Nível deve estar entre 10 e 100");
      }
      if (
        !["system", "company", "establishment"].includes(formData.context_type)
      ) {
        throw new Error("Contexto inválido");
      }
      if (formData.description && formData.description.length > 500) {
        throw new Error("Descrição deve ter no máximo 500 caracteres");
      }

      await onSubmit(formData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getContextTypeLabel = (type) => {
    const labels = {
      system: "Sistema",
      company: "Empresa",
      establishment: "Estabelecimento",
    };
    return labels[type] || type;
  };

  if (loadingData) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Carregando formulário...</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
        role="banner"
      >
        <div className="min-w-0">
          <h1
            id="form-title"
            className="text-2xl font-bold text-foreground"
            tabIndex={-1}
          >
            {initialData ? "Editar Perfil" : "Novo Perfil"}
          </h1>
          <p className="text-muted-foreground" id="form-description">
            {initialData
              ? "Atualize as informações do perfil"
              : "Cadastre um novo perfil no sistema"}
          </p>
        </div>
      </header>

      <form
        onSubmit={handleSubmit}
        className="space-y-6"
        aria-labelledby="form-title"
        aria-describedby="form-description"
        noValidate
      >
        {error && (
          <div
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            role="alert"
            aria-live="polite"
            id="form-error"
          >
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Informações Básicas
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome Técnico *
              </label>
              <Input
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                placeholder="Ex: gerente_clinico"
                required
              />
              <p className="mt-1 text-xs sm:text-sm text-gray-500">
                Nome único usado internamente (apenas letras, números e
                underscore)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome de Exibição *
              </label>
              <Input
                value={formData.display_name}
                onChange={(e) =>
                  handleInputChange("display_name", e.target.value)
                }
                placeholder="Ex: Gerente Clínico"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contexto *
              </label>
              <select
                value={formData.context_type}
                onChange={(e) =>
                  handleInputChange("context_type", e.target.value)
                }
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {contextTypes.map((type) => (
                  <option key={type} value={type}>
                    {getContextTypeLabel(type)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nível Hierárquico *
              </label>
              <div className="space-y-2">
                <Input
                  type="number"
                  min="10"
                  max="100"
                  value={formData.level}
                  onChange={(e) =>
                    handleInputChange("level", parseInt(e.target.value))
                  }
                  required
                />
                <select
                  value={formData.level}
                  onChange={(e) =>
                    handleInputChange("level", parseInt(e.target.value))
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {Object.entries(roleLevels).map(([level, description]) => (
                    <option key={level} value={level}>
                      {level} - {description}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descrição
              </label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  handleInputChange("description", e.target.value)
                }
                placeholder="Descrição detalhada do perfil e suas responsabilidades"
                rows={3}
                className="text-sm"
                maxLength={500}
              />
              <div className="text-right">
                <span
                  className={`text-xs ${
                    formData.description.length > 450
                      ? "text-red-500"
                      : "text-gray-500"
                  }`}
                >
                  {formData.description.length}/500 caracteres
                </span>
              </div>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) =>
                    handleInputChange("is_active", e.target.checked)
                  }
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <span className="ml-2 text-sm text-gray-700">Perfil ativo</span>
              </label>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Permissões</h3>

          <div className="space-y-4">
            {Object.entries(permissions).map(([module, modulePermissions]) => (
              <div
                key={module}
                className="border border-gray-200 rounded-md p-4"
              >
                <h4 className="font-medium text-gray-900 mb-3 capitalize text-base">
                  {module}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {modulePermissions.map((permission) => (
                    <label
                      key={permission.id}
                      className="flex items-start space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPermissions.has(permission.id)}
                        onChange={() => handlePermissionToggle(permission.id)}
                        className="mt-0.5 rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring focus:ring-blue-200 focus:ring-opacity-50 flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 line-clamp-1">
                          {permission.display_name}
                        </div>
                        <div className="text-xs text-gray-500 truncate">
                          {permission.action} • {permission.resource}
                        </div>
                        {permission.description && (
                          <div className="text-xs text-gray-400 mt-1 line-clamp-1">
                            {permission.description}
                          </div>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>{selectedPermissions.size}</strong> permissões
              selecionadas
            </p>
          </div>
        </Card>

        <div
          className="flex gap-3 justify-end"
          role="group"
          aria-label="Ações do formulário"
        >
          <Button
            type="button"
            variant="secondary"
            outline
            onClick={onCancel}
            disabled={loading}
            className="flex-1 sm:flex-none"
            aria-label="Cancelar edição e fechar formulário"
          >
            <span className="hidden sm:inline">Cancelar</span>
            <span className="sm:hidden">Cancelar</span>
          </Button>
          <Button
            type="submit"
            loading={loading}
            disabled={loading}
            className="flex-1 sm:flex-none"
            aria-label={
              loading
                ? "Salvando perfil, aguarde..."
                : initialData
                ? "Salvar alterações do perfil"
                : "Salvar novo perfil"
            }
          >
            <span className="hidden sm:inline">
              {loading
                ? "Salvando..."
                : initialData
                ? "Atualizar Perfil"
                : "Criar Perfil"}
            </span>
            <span className="sm:hidden">
              {loading ? "Salvando..." : "Salvar"}
            </span>
          </Button>
        </div>
      </form>
    </div>
  );
};
