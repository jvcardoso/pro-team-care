import React, { useState } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { X, Key, Eye, EyeOff } from "lucide-react";
import { notify } from "../../utils/notifications";
import { usersService } from "../../services/api";

const ChangePasswordModal = ({ isOpen, onClose, user }) => {
  const [formData, setFormData] = useState({
    newPassword: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validações usando o mesmo padrão do projeto
    if (!formData.newPassword || !formData.confirmPassword) {
      notify.warning("Todos os campos são obrigatórios para alterar a senha");
      return;
    }

    if (formData.newPassword.length < 6) {
      notify.warning(
        "A senha deve ter pelo menos 6 caracteres para garantir a segurança"
      );
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      notify.error("As senhas não coincidem. Verifique e tente novamente.");
      return;
    }

    setLoading(true);
    try {
      await usersService.changePassword(user.user_id, {
        new_password: formData.newPassword,
      });

      notify.success(
        `Senha alterada com sucesso para ${
          user?.person_name || user?.user_email
        }!`
      );
      onClose();
      setFormData({ newPassword: "", confirmPassword: "" });
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Erro desconhecido";
      notify.error(`Falha ao alterar senha: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({ newPassword: "", confirmPassword: "" });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-enter">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-full max-w-md ring-1 ring-black ring-opacity-5 pointer-events-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0 p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Key className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Alterar Senha
            </h3>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            disabled={loading}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              <p className="font-medium text-gray-900 dark:text-white mb-1">
                {user?.person_name || user?.user_email}
              </p>
              <p className="text-gray-600 dark:text-gray-400 font-mono text-xs">
                {user?.user_email}
              </p>
            </div>
          </div>

          {/* Nova Senha */}
          <div className="relative">
            <Input
              label="Nova Senha"
              type={showPassword ? "text" : "password"}
              name="newPassword"
              value={formData.newPassword}
              onChange={handleInputChange}
              placeholder="Digite a nova senha"
              required
              minLength={6}
            />
            <button
              type="button"
              className="absolute right-3 top-8 text-gray-400 hover:text-gray-600"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          {/* Confirmar Senha */}
          <div className="relative">
            <Input
              label="Confirmar Nova Senha"
              type={showConfirmPassword ? "text" : "password"}
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              placeholder="Digite novamente a nova senha"
              required
              minLength={6}
            />
            <button
              type="button"
              className="absolute right-3 top-8 text-gray-400 hover:text-gray-600"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
            <div className="text-xs text-yellow-800 dark:text-yellow-200">
              <p className="flex items-center mb-1">
                <span className="w-1 h-1 bg-yellow-500 rounded-full mr-2"></span>
                A senha deve ter pelo menos 6 caracteres
              </p>
              <p className="flex items-center">
                <span className="w-1 h-1 bg-yellow-500 rounded-full mr-2"></span>
                Use uma combinação de letras, números e símbolos
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
            <Button
              type="button"
              variant="secondary"
              outline
              onClick={handleClose}
              className="flex-1"
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={loading}
              className="flex-1"
              disabled={loading}
            >
              {loading ? "Alterando..." : "Alterar Senha"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangePasswordModal;
