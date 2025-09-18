import React, { useState, useEffect } from "react";
import { usersService } from "../../services/api";
import { rolesService } from "../../services/rolesService";
import { PageErrorBoundary } from "../error";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { notify } from "../../utils/notifications.jsx";
import {
  validateTaxId,
  detectPersonTypeFromTaxId,
  formatCPF,
  formatCNPJ,
  removeNonNumeric,
} from "../../utils/validators";
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
    roles: [],
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

      // Carregar roles do usuário
      let userRoles = [];
      try {
        const rolesResponse = await rolesService.getUserRoles(userId);
        userRoles = rolesResponse; // Já vem como array de IDs
      } catch (err) {
        console.warn("Endpoint de user roles ainda não implementado:", err);
        // Por enquanto, deixar vazio - usuário pode selecionar manualmente
        userRoles = [];
      }

      // Formatar tax_id se existir
      const rawTaxId = user.person_tax_id || "";
      let formattedTaxId = rawTaxId;
      if (rawTaxId) {
        const numbers = removeNonNumeric(rawTaxId);
        if (numbers.length === 11) {
          formattedTaxId = formatCPF(numbers);
        } else if (numbers.length === 14) {
          formattedTaxId = formatCNPJ(numbers);
        }
      }

      // Backend retorna dados com prefixos user_ e person_
      setFormData({
        email_address: user.user_email || "",
        password: "", // Senha sempre vazia no modo edição
        confirm_password: "",
        person: {
          name: user.person_name || "",
          tax_id: formattedTaxId,
          birth_date: user.person_birth_date || null,
          gender: user.person_gender || null,
          status: user.person_status || "active",
          person_type: user.person_type || "PF",
          description: user.person_description || "",
        },
        is_active:
          user.user_is_active !== undefined ? user.user_is_active : true,
        preferences: user.user_preferences || {},
        notification_settings: user.user_notification_settings || {},
        roles: userRoles,
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
      const response = await rolesService.listRoles();
      // Backend retorna { roles: [...], total: ... }
      const roles = response.roles || response || [];
      setAvailableRoles(roles);
      console.log("Roles carregados:", roles);
    } catch (err) {
      console.error("Error loading roles:", err);
      // Fallback baseado nos roles reais do banco
      setAvailableRoles([
        {
          id: 22,
          name: "admin_empresa_customizado",
          description:
            "Administrador da Empresa (Customizado) - pode gerenciar estabelecimentos, usuários e configurações da empresa",
        },
        {
          id: 6,
          name: "super_admin",
          description:
            "Acesso total ao sistema, incluindo gerenciamento de empresas e configurações globais",
        },
        {
          id: 7,
          name: "admin_empresa",
          description:
            "Gerencia toda a empresa, estabelecimentos e usuários da empresa",
        },
        {
          id: 8,
          name: "admin_estabelecimento",
          description: "Gerencia um estabelecimento específico e seus dados",
        },
        {
          id: 9,
          name: "operador",
          description: "Acesso operacional para cadastros e consultas básicas",
        },
      ]);
    }
  };

  const handleChange = (field, value) => {
    if (field.includes(".")) {
      const [parent, child] = field.split(".");
      setFormData((prev) => {
        const newData = {
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: value,
          },
        };

        // Auto-detectar tipo de pessoa e formatar quando tax_id muda
        if (field === "person.tax_id" && value) {
          const numbers = removeNonNumeric(value);
          let formattedValue = value;

          // Aplicar formatação baseado no tamanho
          if (numbers.length === 11) {
            formattedValue = formatCPF(numbers);
          } else if (numbers.length === 14) {
            formattedValue = formatCNPJ(numbers);
          }

          // Atualizar valor formatado
          newData[parent][child] = formattedValue;

          // Auto-detectar tipo de pessoa
          const detection = detectPersonTypeFromTaxId(numbers);
          if (detection.personType) {
            newData[parent].person_type = detection.personType;
          }
        }

        return newData;
      });
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
        ? [...(prev.roles || []), roleId]
        : (prev.roles || []).filter((id) => id !== roleId),
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
      throw new Error("CPF/CNPJ é obrigatório");
    }

    // Validação de CPF/CNPJ usando função existente
    if (!validateTaxId(formData.person.tax_id)) {
      const detection = detectPersonTypeFromTaxId(formData.person.tax_id);
      if (detection.documentType) {
        throw new Error(`${detection.documentType} inválido`);
      } else {
        throw new Error(
          "CPF/CNPJ inválido - deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)"
        );
      }
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

      // Backend espera campos diferentes para user vs person
      const userData = {
        email: formData.email_address.trim(), // Backend espera 'email', não 'email_address'
        is_active: formData.is_active,
        // Não incluir dados de person aqui - eles são atualizados separadamente
      };

      console.log("📤 Dados sendo enviados para o backend:", userData);

      // Incluir senha apenas se fornecida
      if (formData.password.trim()) {
        userData.password = formData.password.trim();
      }

      if (isEditing) {
        await usersService.updateUser(userId, userData);

        // Atualizar roles do usuário
        try {
          const roleIds = (formData.roles || []).map((role) =>
            typeof role === "object" ? role.id : role
          );
          await rolesService.updateUserRoles(userId, roleIds);
          console.log("Roles selecionados para o usuário:", roleIds);
          notify.info(`Roles selecionados: ${roleIds.length} funções`);
        } catch (roleErr) {
          console.warn("Erro ao atualizar roles:", roleErr);
          notify.warning("Usuário atualizado, mas houve problema com os roles");
        }

        notify.success("Usuário atualizado com sucesso!");

        // Recarregar dados do usuário após salvamento bem-sucedido
        if (isEditing) {
          // Invalidar cache para garantir dados atualizados
          try {
            const { httpCache } = await import("../../config/http");
            if (httpCache && httpCache.invalidatePattern) {
              httpCache.invalidatePattern(`/api/v1/users/${userId}`);
            }
          } catch (e) {
            console.warn("Erro ao invalidar cache:", e);
          }
          await loadUser();
        }
      } else {
        const newUser = await usersService.createUser(userData);

        // Associar roles ao novo usuário
        if (formData.roles && formData.roles.length > 0) {
          try {
            const roleIds = formData.roles.map((role) =>
              typeof role === "object" ? role.id : role
            );
            await rolesService.updateUserRoles(
              newUser.user_id || newUser.id,
              roleIds
            );
            console.log("Roles selecionados para o novo usuário:", roleIds);
            notify.info(`Roles selecionados: ${roleIds.length} funções`);
          } catch (roleErr) {
            console.warn("Erro ao associar roles:", roleErr);
            notify.warning("Usuário criado, mas houve problema com os roles");
          }
        }

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
            {isEditing ? "Editar Usuário" : "Novo Usuário"}
          </h1>
          <p className="text-muted-foreground" id="form-description">
            {isEditing
              ? "Atualize as informações do usuário"
              : "Preencha os dados para criar um novo usuário"}
          </p>
        </div>
        <div
          className="flex gap-3 shrink-0"
          role="group"
          aria-label="Ações do formulário"
        >
          <Button
            type="button"
            variant="secondary"
            outline
            onClick={onCancel}
            icon={<X className="h-4 w-4" />}
            className="flex-1 sm:flex-none"
            aria-label="Cancelar edição e fechar formulário"
          >
            <span className="hidden sm:inline">Cancelar</span>
            <span className="sm:hidden">Cancelar</span>
          </Button>
          <Button
            type="submit"
            form="user-form"
            disabled={loading}
            icon={<Save className="h-4 w-4" />}
            className="flex-1 sm:flex-none"
            aria-label={
              loading
                ? "Salvando usuário, aguarde..."
                : isEditing
                ? "Salvar alterações do usuário"
                : "Salvar novo usuário"
            }
          >
            <span className="hidden sm:inline">
              {loading ? "Salvando..." : "Salvar"}
            </span>
            <span className="sm:hidden">
              {loading ? "Salvando..." : "Salvar"}
            </span>
          </Button>
        </div>
      </header>

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

      <form
        id="user-form"
        onSubmit={handleSubmit}
        className="space-y-6"
        aria-labelledby="form-title"
        aria-describedby="form-description"
        noValidate
      >
        {/* Dados Básicos */}
        <Card title="Dados Básicos">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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

            <div className="space-y-2">
              <Input
                label="CPF/CNPJ"
                value={formData.person.tax_id}
                onChange={(e) => handleChange("person.tax_id", e.target.value)}
                placeholder="Ex: 000.000.000-00 ou 00.000.000/0000-00"
                required
              />
              {formData.person.tax_id && (
                <div className="text-xs text-muted-foreground">
                  {(() => {
                    const detection = detectPersonTypeFromTaxId(
                      formData.person.tax_id
                    );
                    if (detection.isValid) {
                      return (
                        <span className="text-green-600 dark:text-green-400">
                          ✓ {detection.documentType} válido -{" "}
                          {detection.personType === "PF"
                            ? "Pessoa Física"
                            : "Pessoa Jurídica"}
                        </span>
                      );
                    } else if (detection.documentType) {
                      return (
                        <span className="text-red-600 dark:text-red-400">
                          ✗ {detection.documentType} inválido
                        </span>
                      );
                    } else {
                      const numbers = removeNonNumeric(formData.person.tax_id);
                      if (numbers.length > 0) {
                        return (
                          <span className="text-gray-500">
                            {numbers.length}/11 (CPF) ou {numbers.length}/14
                            (CNPJ) dígitos
                          </span>
                        );
                      } else {
                        return (
                          <span className="text-gray-500">
                            Digite o CPF ou CNPJ - formatação automática
                          </span>
                        );
                      }
                    }
                  })()}
                </div>
              )}
            </div>

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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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

        {/* Funções/Roles */}
        <Card title="Funções" icon={<Shield className="h-5 w-5" />}>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Selecione as funções que o usuário terá no sistema.
            </p>

            {availableRoles.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {availableRoles.map((role) => (
                  <div
                    key={role.id}
                    className="flex items-start space-x-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <input
                      type="checkbox"
                      id={`role-${role.id}`}
                      checked={(formData.roles || []).includes(role.id)}
                      onChange={(e) =>
                        handleRoleChange(role.id, e.target.checked)
                      }
                      className="mt-1 h-4 w-4 text-primary border-border rounded focus:ring-2 focus:ring-ring"
                    />
                    <div className="flex-1 min-w-0">
                      <label
                        htmlFor={`role-${role.id}`}
                        className="block text-sm font-medium text-foreground cursor-pointer"
                      >
                        {role.name}
                      </label>
                      {role.description && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {role.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Carregando funções disponíveis...
              </p>
            )}

            {(formData.roles || []).length > 0 && (
              <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                <p className="text-sm font-medium text-foreground mb-2">
                  Funções selecionadas: {(formData.roles || []).length}
                </p>
                <div className="flex flex-wrap gap-2">
                  {(formData.roles || []).map((roleId) => {
                    const role = availableRoles.find((r) => r.id === roleId);
                    return role ? (
                      <span
                        key={roleId}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary"
                      >
                        {role.name}
                      </span>
                    ) : null;
                  })}
                </div>
              </div>
            )}
          </div>
        </Card>
      </form>
    </div>
  );
};

export default UserForm;
