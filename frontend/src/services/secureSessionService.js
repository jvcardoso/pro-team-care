/**
 * Serviço para gerenciar sessões seguras e personificação
 */
import { api } from "./api";

class SecureSessionService {
  constructor() {
    this.baseUrl = "/api/v1/secure-sessions";
    this.currentContext = null;
    this.availableProfiles = [];
    this.listeners = [];
  }

  // Event listener system for context changes
  addListener(callback) {
    this.listeners.push(callback);
  }

  removeListener(callback) {
    this.listeners = this.listeners.filter((l) => l !== callback);
  }

  notifyListeners() {
    this.listeners.forEach((callback) => callback(this.currentContext));
  }

  /**
   * Obter perfis disponíveis para troca
   */
  async getAvailableProfiles() {
    try {
      const response = await api.get(`${this.baseUrl}/available-profiles`);
      this.availableProfiles = response.data.profiles || [];
      return response.data;
    } catch (error) {
      // Tratamento gracioso para erros de autenticação
      if (error.response?.status === 401) {
        console.info(
          "Usuário não autenticado para perfis - usando perfil padrão"
        );
        this.availableProfiles = [];
        return { profiles: [], total_profiles: 0, user_is_root: false };
      }

      // Endpoint não implementado - falhar
      if (error.response?.status === 404) {
        throw new Error("Endpoint de perfis não implementado no backend");
      }

      console.error("Erro ao obter perfis disponíveis:", error);
      throw error;
    }
  }

  /**
   * Trocar perfil/contexto
   */
  async switchProfile(switchData) {
    try {
      const response = await api.post(
        `${this.baseUrl}/switch-profile`,
        switchData
      );

      if (response.data.success) {
        // Atualizar contexto atual
        await this.getCurrentContext();
        this.notifyListeners();
      }

      return response.data;
    } catch (error) {
      console.error("Erro ao trocar perfil:", error);
      throw error;
    }
  }

  /**
   * Personificar um usuário (ROOT apenas)
   */
  async impersonateUser(userId, reason) {
    try {
      const response = await this.switchProfile({
        impersonated_user_id: userId,
        reason: reason || "Personificação administrativa",
      });
      return response;
    } catch (error) {
      console.error("Erro ao personificar usuário:", error);
      throw error;
    }
  }

  /**
   * Trocar contexto (empresa/estabelecimento)
   */
  async switchContext(contextType, contextId, reason) {
    try {
      const response = await this.switchProfile({
        context_type: contextType,
        context_id: contextId,
        reason: reason || "Troca de contexto",
      });
      return response;
    } catch (error) {
      console.error("Erro ao trocar contexto:", error);
      throw error;
    }
  }

  /**
   * Obter contexto atual da sessão
   */
  async getCurrentContext() {
    try {
      const response = await api.get(`${this.baseUrl}/current-context`);

      // Verificar se a sessão é válida na resposta
      if (response.data && response.data.session_valid === false) {
        console.info("Sessão segura não ativa - funcionando em modo padrão");
        this.currentContext = null;
        return null;
      }

      this.currentContext = response.data;
      return response.data;
    } catch (error) {
      // Se der erro 401, usuário não tem sessão segura ativa
      if (error.response?.status === 401) {
        console.info("Sessão segura não ativa - funcionando em modo padrão");
        this.currentContext = null;
        return null;
      }

      // Endpoint não implementado - falhar
      if (error.response?.status === 404) {
        throw new Error("Endpoint de contexto não implementado no backend");
      }

      console.error("Erro ao obter contexto atual:", error);
      throw error;
    }
  }

  /**
   * Terminar sessão segura
   */
  async terminateSession() {
    try {
      const response = await api.post(`${this.baseUrl}/terminate`);
      this.currentContext = null;
      this.notifyListeners();
      return response.data;
    } catch (error) {
      console.error("Erro ao terminar sessão:", error);
      throw error;
    }
  }

  /**
   * Listar sessões ativas (ROOT apenas)
   */
  async getActiveSessions() {
    try {
      const response = await api.get(`${this.baseUrl}/active-sessions`);
      return response.data;
    } catch (error) {
      console.error("Erro ao listar sessões ativas:", error);
      throw error;
    }
  }

  /**
   * Verificar se usuário está personificando
   */
  isImpersonating() {
    return this.currentContext?.is_impersonating || false;
  }

  /**
   * Verificar se usuário é ROOT
   */
  isRoot() {
    return this.currentContext?.is_root || false;
  }

  /**
   * Obter usuário efetivo (personificado ou real)
   */
  getEffectiveUser() {
    if (!this.currentContext) return null;

    return {
      id: this.currentContext.effective_user_id,
      email: this.currentContext.effective_user_email,
      isImpersonating: this.currentContext.is_impersonating,
    };
  }

  /**
   * Obter usuário real (quem está logado)
   */
  getRealUser() {
    if (!this.currentContext) return null;

    return {
      id: this.currentContext.user_id,
      email: this.currentContext.user_email,
    };
  }

  /**
   * Obter contexto ativo
   */
  getActiveContext() {
    if (!this.currentContext) return null;

    return {
      type: this.currentContext.active_context?.type,
      id: this.currentContext.active_context?.id,
      role: {
        id: this.currentContext.active_role?.id,
        name: this.currentContext.active_role?.name,
        displayName: this.currentContext.active_role?.display_name,
      },
    };
  }

  /**
   * Inicializar serviço (carregar contexto se existir)
   */
  async initialize() {
    try {
      console.info("🔐 Inicializando serviço de sessão segura...");
      await this.getCurrentContext();

      if (this.currentContext) {
        console.info("✅ Contexto de sessão encontrado, carregando perfis...");
        await this.getAvailableProfiles();
      } else {
        console.info(
          "ℹ️ Nenhum contexto de sessão ativa - sistema funcionando em modo padrão"
        );
      }

      console.info("✅ Serviço de sessão segura inicializado com sucesso");
    } catch (error) {
      // Tratamento gracioso - não falhar a aplicação inteira
      console.warn(
        "⚠️ Erro na inicialização do serviço de sessão segura:",
        error.message
      );
      console.info("🔄 Continuando sem funcionalidades de sessão segura");

      // Garantir estado consistente
      this.currentContext = null;
      this.availableProfiles = [];
    }
  }
}

// Instância singleton
const secureSessionService = new SecureSessionService();

export default secureSessionService;
