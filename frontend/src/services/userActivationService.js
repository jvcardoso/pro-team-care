import api from "./api";

/**
 * Serviço para operações de ativação e convite de usuários
 */
export const userActivationService = {
  /**
   * Convidar gestor para uma empresa
   * @param {string} email - Email do gestor
   * @param {number} companyId - ID da empresa
   * @returns {Promise<Object>} Dados do usuário criado
   */
  inviteCompanyManager: async (email, companyId) => {
    const response = await api.post(
      "/api/v1/user-activation/invite-company-manager",
      {
        email,
        company_id: companyId,
      }
    );
    return response.data;
  },

  /**
   * Convidar gestor para um estabelecimento
   * @param {string} email - Email do gestor
   * @param {number} establishmentId - ID do estabelecimento
   * @returns {Promise<Object>} Dados do usuário criado
   */
  inviteEstablishmentManager: async (email, establishmentId) => {
    const response = await api.post(
      "/api/v1/user-activation/invite-establishment-manager",
      {
        email,
        establishment_id: establishmentId,
      }
    );
    return response.data;
  },

  /**
   * Ativar conta de usuário
   * @param {string} activationToken - Token de ativação
   * @param {string} password - Nova senha
   * @returns {Promise<Object>} Dados do usuário ativado
   */
  activateUser: async (activationToken, password) => {
    const response = await api.post("/api/v1/user-activation/activate", {
      activation_token: activationToken,
      password,
    });
    return response.data;
  },

  /**
   * Reenviar email de ativação
   * @param {number} userId - ID do usuário
   * @returns {Promise<Object>} Resultado do envio
   */
  resendActivationEmail: async (userId) => {
    const response = await api.post(
      "/api/v1/user-activation/resend-activation",
      {
        user_id: userId,
      }
    );
    return response.data;
  },

  /**
   * Validar token de ativação
   * @param {string} token - Token de ativação
   * @returns {Promise<Object>} Informações do token
   */
  validateActivationToken: async (token) => {
    const response = await api.get(
      `/api/v1/user-activation/validate-token/${token}`
    );
    return response.data;
  },
};

export default userActivationService;
