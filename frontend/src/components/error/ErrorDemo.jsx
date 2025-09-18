import React from "react";
import AccessDeniedError from "./AccessDeniedError";
import useErrorHandler from "../../hooks/useErrorHandler";

const ErrorDemo = () => {
  const { handleError, isAccessDenied, hasError, userMessage, statusCode } =
    useErrorHandler();

  const simulate403Error = () => {
    const error = {
      response: {
        status: 403,
      },
      message: "Request failed with status code 403",
    };
    handleError(error);
  };

  const simulate500Error = () => {
    const error = {
      response: {
        status: 500,
      },
      message: "Request failed with status code 500",
    };
    handleError(error);
  };

  const simulate404Error = () => {
    const error = {
      response: {
        status: 404,
      },
      message: "Request failed with status code 404",
    };
    handleError(error);
  };

  if (hasError) {
    if (isAccessDenied) {
      return (
        <AccessDeniedError
          title="Acesso Negado aos Perfis"
          message="Você não possui permissão para visualizar os perfis do sistema. Entre em contato com o administrador para solicitar acesso a esta funcionalidade."
          resource="perfis do sistema"
          action="visualizar"
          onRetry={() => window.location.reload()}
        />
      );
    } else {
      return (
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Erro Simulado
          </h3>
          <p className="text-red-600 mb-4">{userMessage}</p>
          <p className="text-sm text-gray-500 mb-4">Código: {statusCode}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded"
          >
            Recarregar
          </button>
        </div>
      );
    }
  }

  return (
    <div className="p-8 space-y-4">
      <h2 className="text-xl font-bold">Demo de Tratamento de Erros</h2>
      <div className="space-x-4">
        <button
          onClick={simulate403Error}
          className="px-4 py-2 bg-red-600 text-white rounded"
        >
          Simular Erro 403 (Acesso Negado)
        </button>
        <button
          onClick={simulate500Error}
          className="px-4 py-2 bg-orange-600 text-white rounded"
        >
          Simular Erro 500 (Servidor)
        </button>
        <button
          onClick={simulate404Error}
          className="px-4 py-2 bg-gray-600 text-white rounded"
        >
          Simular Erro 404 (Não Encontrado)
        </button>
      </div>
    </div>
  );
};

export default ErrorDemo;
