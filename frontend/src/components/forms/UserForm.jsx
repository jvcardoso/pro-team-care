import React, { useState, useEffect } from "react";
import { usersService } from "../../services/api";
import { PageErrorBoundary } from "../error";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { notify } from "../../utils/notifications.jsx";
import { Save, X, User, Mail, Key, Shield } from "lucide-react";

const UserForm = ({ userId, onSave, onCancel }) => {
  return (
    <PageErrorBoundary pageName="UserForm">
      <UserFormContent userId={userId} onSave={onSave} onCancel={onCancel} />
    </PageErrorBoundary>
  );
};

const UserFormContent = ({ userId, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    email_address: "",
    password: "",
    confirm_password: "",
    person: {
      name: "",
      tax_id: "",
      birth_date: null,
      gender: null,
      status: "active",
      person_type: "PF",
      description: "",
    },
    is_active: true,
    preferences: {},
    notification_settings: {},
  });

  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(!!userId);
  const [error, setError] = useState(null);
  const [availableRoles, setAvailableRoles] = useState([]);

  const isEditing = !!userId;

  useEffect(() => {
    if (userId) {
      loadUser();
    }
    loadAvailableRoles();
  }, [userId]);

  const loadUser = async () => {
    try {
      setLoadingData(true);
      const user = await usersService.getUser(userId);
      setFormData({
        email_address: user.email_address || "",
        password: "", // Senha sempre vazia no modo edição
        confirm_password: "",
        person: {
          name: user.person?.name || "",
          tax_id: user.person?.tax_id || "",
          birth_date: user.person?.birth_date || null,
          gender: user.person?.gender || null,
          status: user.person?.status || "active",
          person_type: user.person?.person_type || "PF",
          description: user.person?.description || "",
        },
        is_active: user.is_active !== undefined ? user.is_active : true,
        preferences: user.preferences || {},
        notification_settings: user.notification_settings || {},
      });
    } catch (err) {
      setError(`Erro ao carregar usuário: ${err.message}`);
      console.error("Error loading user:", err);
    } finally {
      setLoadingData(false);
    }
  };

  const loadAvailableRoles = async () => {
    try {
      // TODO: Implementar endpoint para listar roles disponíveis
      // const roles = await rolesService.getRoles();
      // setAvailableRoles(roles);

      // Mock temporário
      setAvailableRoles([
        { id: 1, name: "Admin", description: "Administrador do sistema" },
        { id: 2, name: "User", description: "Usuário padrão" },
        { id: 3, name: "Manager", description: "Gerente" },
      ]);
    } catch (err) {
      console.error("Error loading roles:", err);
    }
  };

  const handleChange = (field, value) => {
    if (field.includes(".")) {
      const [parent, child] = field.split(".");
      setFormData((prev) => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const handleRoleChange = (roleId, checked) => {
    setFormData((prev) => ({
      ...prev,
      roles: checked
        ? [...prev.roles, roleId]
        : prev.roles.filter((id) => id !== roleId),
    }));
  };

  const validateForm = () => {
    if (!formData.email_address.trim()) {
      throw new Error("Email é obrigatório");
    }

    if (!formData.person.name.trim()) {
      throw new Error("Nome é obrigatório");
    }

    if (!formData.person.tax_id.trim()) {
      throw new Error("CPF é obrigatório");
    }

    // Validação de CPF básica
    const cpf = formData.person.tax_id.replace(/\D/g, "");
    if (cpf.length !== 11) {
      throw new Error("CPF deve ter 11 dígitos");
    }

    if (cpf === cpf[0].repeat(11)) {
      throw new Error("CPF não pode ser uma sequência de dígitos iguais");
    }

    if (!isEditing && !formData.password.trim()) {
      throw new Error("Senha é obrigatória para novos usuários");
    }

    if (formData.password && formData.password !== formData.confirm_password) {
      throw new Error("Senhas não coincidem");
    }

    if (formData.password && formData.password.length < 8) {
      throw new Error("Senha deve ter pelo menos 8 caracteres");
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email_address)) {
      throw new Error("Email inválido");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);

      validateForm();

      const userData = {
        email_address: formData.email_address.trim(),
        person: {
          name: formData.person.name.trim(),
          tax_id: formData.person.tax_id.trim(),
          birth_date: formData.person.birth_date || null,
          gender: formData.person.gender || null,
          status: formData.person.status,
          person_type: formData.person.person_type,
          description: formData.person.description?.trim() || null,
        },
        is_active: formData.is_active,
        preferences: formData.preferences || {},
        notification_settings: formData.notification_settings || {},
      };

      // Incluir senha apenas se fornecida
      if (formData.password.trim()) {
        userData.password = formData.password.trim();
      }

      if (isEditing) {
        await usersService.updateUser(userId, userData);
        notify.success("Usuário atualizado com sucesso!");
      } else {
        await usersService.createUser(userData);
        notify.success("Usuário criado com sucesso!");
      }

      if (onSave) onSave();
    } catch (err) {
      let errorMessage = err.message || "Erro ao salvar usuário";

      // Tratar erros específicos do backend
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Erros de validação do Pydantic
          const validationErrors = err.response.data.detail
            .map((e) => e.msg)
            .join(", ");
          errorMessage = validationErrors;
        } else if (typeof err.response.data.detail === "string") {
          errorMessage = err.response.data.detail;
        }

        // Mensagens específicas para erros comuns
        if (
          errorMessage.includes(
            "duplicate key value violates unique constraint"
          )
        ) {
          if (errorMessage.includes("people_tax_id_unique")) {
            errorMessage = "Este CPF já está cadastrado no sistema";
          } else if (errorMessage.includes("users_email_address_unique")) {
            errorMessage = "Este email já está cadastrado no sistema";
          }
        }
      }

      setError(errorMessage);
      notify.error(errorMessage);
      console.error("Error saving user:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">
            Carregando dados do usuário...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {isEditing ? "Editar Usuário" : "Novo Usuário"}
          </h1>
          <p className="text-muted-foreground">
            {isEditing
              ? "Atualize as informações do usuário"
              : "Preencha os dados para criar um novo usuário"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="secondary"
            outline
            onClick={onCancel}
            icon={<X className="h-4 w-4" />}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            form="user-form"
            disabled={loading}
            icon={<Save className="h-4 w-4" />}
          >
            {loading ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </div>

      {error && (
        <Card>
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{error}</p>
          </div>
        </Card>
      )}

      <form id="user-form" onSubmit={handleSubmit} className="space-y-6">
        {/* Dados Básicos */}
        <Card title="Dados Básicos">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nome Completo"
              value={formData.person.name}
              onChange={(e) => handleChange("person.name", e.target.value)}
              placeholder="Digite o nome completo"
              required
              icon={<User className="h-4 w-4" />}
            />

            <Input
              label="Email"
              type="email"
              value={formData.email_address}
              onChange={(e) => handleChange("email_address", e.target.value)}
              placeholder="Digite o email"
              required
              icon={<Mail className="h-4 w-4" />}
            />

            <Input
              label="CPF"
              value={formData.person.tax_id}
              onChange={(e) => handleChange("person.tax_id", e.target.value)}
              placeholder="Digite o CPF (apenas números)"
              required
            />

            <Input
              label="Data de Nascimento"
              type="date"
              value={formData.person.birth_date || ""}
              onChange={(e) =>
                handleChange("person.birth_date", e.target.value || null)
              }
              placeholder="Selecione a data de nascimento"
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gênero
              </label>
              <select
                value={formData.person.gender || ""}
                onChange={(e) =>
                  handleChange("person.gender", e.target.value || null)
                }
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
              >
                <option value="">Selecione...</option>
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
                <option value="O">Outro</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status do Usuário
              </label>
              <select
                value={formData.is_active}
                onChange={(e) =>
                  handleChange("is_active", e.target.value === "true")
                }
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
              >
                <option value="true">Ativo</option>
                <option value="false">Inativo</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Senha */}
        <Card title="Senha">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label={
                isEditing ? "Nova Senha (deixe vazio para manter)" : "Senha"
              }
              type="password"
              value={formData.password}
              onChange={(e) => handleChange("password", e.target.value)}
              placeholder={isEditing ? "Digite a nova senha" : "Digite a senha"}
              required={!isEditing}
              icon={<Key className="h-4 w-4" />}
            />

            <Input
              label="Confirmar Senha"
              type="password"
              value={formData.confirm_password}
              onChange={(e) => handleChange("confirm_password", e.target.value)}
              placeholder="Confirme a senha"
              required={!!formData.password}
              icon={<Key className="h-4 w-4" />}
            />
          </div>
          <Input
            label="Observações"
            value={formData.person.description || ""}
            onChange={(e) => handleChange("person.description", e.target.value)}
            placeholder="Observações sobre o usuário (opcional)"
          />
        </Card>

        {/* Funções/Roles - Temporariamente desabilitado */}
        <Card title="Funções" icon={<Shield className="h-5 w-5" />}>
          <div className="space-y-3">
            <p className="text-muted-foreground">
              Sistema de funções será implementado em breve.
            </p>
          </div>
        </Card>
      </form>
    </div>
  );
};

export default UserForm;
