import { useState, useCallback } from "react";

export interface ErrorState {
  hasError: boolean;
  error: Error | null;
  statusCode: number | null;
  isAccessDenied: boolean;
  isNotFound: boolean;
  isServerError: boolean;
  userMessage: string;
  canRetry: boolean;
}

const useErrorHandler = () => {
  const [errorState, setErrorState] = useState<ErrorState>({
    hasError: false,
    error: null,
    statusCode: null,
    isAccessDenied: false,
    isNotFound: false,
    isServerError: false,
    userMessage: "",
    canRetry: false,
  });

  const handleError = useCallback((error: any) => {
    console.error("Error caught by handler:", error);

    let statusCode: number | null = null;
    let userMessage = "Ocorreu um erro inesperado. Tente novamente.";

    // Extract status code from different error formats
    if (error?.response?.status) {
      statusCode = error.response.status;
    } else if (error?.status) {
      statusCode = error.status;
    } else if (error?.message?.includes("status code")) {
      const match = error.message.match(/status code (\d+)/);
      if (match) {
        statusCode = parseInt(match[1]);
      }
    }

    // Generate user-friendly messages based on status code
    switch (statusCode) {
      case 401:
        userMessage = "Sua sessão expirou. Faça login novamente.";
        break;
      case 403:
        userMessage = "Você não possui permissão para acessar este recurso.";
        break;
      case 404:
        userMessage = "O recurso solicitado não foi encontrado.";
        break;
      case 422:
        userMessage =
          "Dados inválidos. Verifique as informações e tente novamente.";
        break;
      case 429:
        userMessage =
          "Muitas tentativas. Aguarde alguns minutos e tente novamente.";
        break;
      case 500:
        userMessage = "Erro interno do servidor. Nossa equipe foi notificada.";
        break;
      case 502:
      case 503:
      case 504:
        userMessage =
          "Serviço temporariamente indisponível. Tente novamente em alguns minutos.";
        break;
      default:
        if (statusCode && statusCode >= 400 && statusCode < 500) {
          userMessage =
            "Erro na solicitação. Verifique os dados e tente novamente.";
        } else if (statusCode && statusCode >= 500) {
          userMessage = "Erro no servidor. Nossa equipe foi notificada.";
        }
        break;
    }

    const canRetry =
      statusCode === 429 || (statusCode ? statusCode >= 500 : true);

    const newErrorState: ErrorState = {
      hasError: true,
      error:
        error instanceof Error
          ? error
          : new Error(error?.message || "Unknown error"),
      statusCode,
      isAccessDenied: statusCode === 403,
      isNotFound: statusCode === 404,
      isServerError: statusCode ? statusCode >= 500 : false,
      userMessage,
      canRetry,
    };

    setErrorState(newErrorState);
    return newErrorState;
  }, []);

  const clearError = useCallback(() => {
    setErrorState({
      hasError: false,
      error: null,
      statusCode: null,
      isAccessDenied: false,
      isNotFound: false,
      isServerError: false,
      userMessage: "",
      canRetry: false,
    });
  }, []);

  const retry = useCallback(() => {
    clearError();
  }, [clearError]);

  return {
    errorState,
    handleError,
    clearError,
    retry,
    // Convenience getters
    hasError: errorState.hasError,
    isAccessDenied: errorState.isAccessDenied,
    isNotFound: errorState.isNotFound,
    isServerError: errorState.isServerError,
    userMessage: errorState.userMessage,
    statusCode: errorState.statusCode,
    canRetry: errorState.canRetry,
  };
};

export default useErrorHandler;
