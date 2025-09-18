import axios from "axios";

/**
 * Configura interceptador global para tratamento de erros HTTP
 * Este interceptador padroniza o tratamento de erros em toda a aplicação
 */
export const setupErrorInterceptor = () => {
  // Response interceptor para tratar erros
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      // Enriquecer o erro com informações padronizadas
      const enrichedError = {
        ...error,
        statusCode: error?.response?.status || null,
        isAccessDenied: error?.response?.status === 403,
        isNotFound: error?.response?.status === 404,
        isServerError: error?.response?.status >= 500,
        isClientError:
          error?.response?.status >= 400 && error?.response?.status < 500,
        userMessage: getUserFriendlyMessage(error?.response?.status),
        originalMessage: error.message,
        timestamp: new Date().toISOString(),
      };

      // Log do erro para debug
      console.group(`🚫 HTTP Error ${error?.response?.status || "Unknown"}`);
      console.error("Original Error:", error);
      console.error("Enriched Error:", enrichedError);
      console.groupEnd();

      // Tratamentos específicos por tipo de erro
      switch (error?.response?.status) {
        case 401:
          // Redirecionar para login se não autenticado
          if (window.location.pathname !== "/login") {
            console.info("Redirecionando para login devido a erro 401");
            window.location.href = "/login";
          }
          break;

        case 403:
          // Não redirecionar - deixar o componente tratar
          console.warn("Acesso negado - usuário sem permissão");
          break;

        case 429:
          // Rate limiting - mostrar mensagem específica
          console.warn("Rate limit excedido");
          break;

        case 500:
        case 502:
        case 503:
        case 504:
          // Erro de servidor - pode tentar novamente
          console.error("Erro de servidor detectado");
          break;
      }

      return Promise.reject(enrichedError);
    }
  );
};

/**
 * Gera mensagem amigável baseada no código de status HTTP
 */
const getUserFriendlyMessage = (statusCode) => {
  const messages = {
    400: "Solicitação inválida. Verifique os dados enviados.",
    401: "Sua sessão expirou. Faça login novamente.",
    403: "Você não possui permissão para acessar este recurso.",
    404: "O recurso solicitado não foi encontrado.",
    422: "Dados inválidos. Verifique as informações e tente novamente.",
    429: "Muitas tentativas. Aguarde alguns minutos e tente novamente.",
    500: "Erro interno do servidor. Nossa equipe foi notificada.",
    502: "Serviço temporariamente indisponível. Tente novamente em alguns minutos.",
    503: "Serviço temporariamente indisponível. Tente novamente em alguns minutos.",
    504: "Tempo limite esgotado. Tente novamente em alguns minutos.",
  };

  return messages[statusCode] || "Ocorreu um erro inesperado. Tente novamente.";
};

/**
 * Hook para usar em componentes que precisam de tratamento de erro específico
 */
export const useGlobalErrorHandler = () => {
  const handleError = (error) => {
    // Se o erro já foi enriquecido pelo interceptor, usar as informações
    if (error.statusCode) {
      return {
        statusCode: error.statusCode,
        isAccessDenied: error.isAccessDenied,
        isNotFound: error.isNotFound,
        isServerError: error.isServerError,
        userMessage: error.userMessage,
        canRetry: error.isServerError || error.statusCode === 429,
      };
    }

    // Fallback para erros não interceptados
    return {
      statusCode: null,
      isAccessDenied: false,
      isNotFound: false,
      isServerError: false,
      userMessage: "Ocorreu um erro inesperado. Tente novamente.",
      canRetry: true,
    };
  };

  return { handleError };
};
