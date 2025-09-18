import React from "react";
import ErrorDemo from "../components/error/ErrorDemo";

const ErrorTestPage = () => {
  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Sistema de Tratamento de Erros
          </h1>
          <p className="text-gray-600">
            Esta página demonstra como o sistema trata diferentes tipos de erro
            HTTP com mensagens user-friendly e ações apropriadas.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg">
          <ErrorDemo />
        </div>

        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">
            Recursos Implementados:
          </h2>
          <ul className="space-y-2 text-sm text-gray-700">
            <li>
              ✅ <strong>Erro 403 (Acesso Negado):</strong> Página dedicada com
              instruções claras
            </li>
            <li>
              ✅ <strong>Erro 404 (Não Encontrado):</strong> Mensagem específica
              de recurso não encontrado
            </li>
            <li>
              ✅ <strong>Erro 500 (Servidor):</strong> Indicação de erro interno
              com tentativa novamente
            </li>
            <li>
              ✅ <strong>Erro 401 (Não Autorizado):</strong> Redirecionamento
              automático para login
            </li>
            <li>
              ✅ <strong>Erro 429 (Rate Limit):</strong> Instrução para aguardar
              antes de tentar novamente
            </li>
            <li>
              ✅ <strong>Interceptador Global:</strong> Tratamento automático em
              toda a aplicação
            </li>
            <li>
              ✅ <strong>Hook Reutilizável:</strong> Facilita implementação em
              novos componentes
            </li>
            <li>
              ✅ <strong>Componente Dedicado:</strong> Interface consistente
              para erros de acesso
            </li>
          </ul>
        </div>

        <div className="mt-6 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            💡 Melhores Práticas Implementadas:
          </h3>
          <ul className="space-y-1 text-sm text-blue-800">
            <li>• Mensagens claras e acionáveis para o usuário</li>
            <li>• Códigos de erro visíveis apenas quando necessário</li>
            <li>
              • Botões de ação contextual (Voltar, Tentar Novamente, Ir para
              Início)
            </li>
            <li>• Design consistente com o restante da aplicação</li>
            <li>• Logging detalhado para debug sem exposição ao usuário</li>
            <li>• Tratamento específico por tipo de erro HTTP</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ErrorTestPage;
