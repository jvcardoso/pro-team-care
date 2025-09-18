import React from "react";
import {
  Bell,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  HelpCircle,
  Trash2,
} from "lucide-react";
import { notify } from "../utils/notifications";

const NotificationDemo = () => {
  const handleSuccessToast = () => {
    notify.success("Operação realizada com sucesso!");
  };

  const handleErrorToast = () => {
    notify.error("Erro ao processar a solicitação. Tente novamente.");
  };

  const handleInfoToast = () => {
    notify.info("Esta é uma mensagem informativa para o usuário.");
  };

  const handleWarningToast = () => {
    notify.warning("Atenção! Verifique os dados antes de continuar.");
  };

  const handleConfirmModal = () => {
    notify.confirm(
      "Confirmar Operação",
      "Tem certeza que deseja continuar com esta operação? Esta ação pode afetar outros dados no sistema.",
      () => {
        notify.success("Operação confirmada e executada!");
      },
      () => {
        notify.info("Operação cancelada pelo usuário.");
      }
    );
  };

  const handleDeleteConfirm = () => {
    notify.confirmDelete(
      "Excluir Registro",
      "Você está prestes a excluir este registro permanentemente. Todos os dados associados serão perdidos.",
      () => {
        notify.success("Registro excluído com sucesso!");
      },
      () => {
        notify.info("Exclusão cancelada.");
      }
    );
  };

  const demoCards = [
    {
      title: "Toast de Sucesso",
      description: "Notificação para operações bem-sucedidas",
      icon: <CheckCircle className="h-6 w-6 text-green-500" />,
      color: "border-green-200 bg-green-50",
      buttonColor: "bg-green-600 hover:bg-green-700",
      action: handleSuccessToast,
      code: `notify.success("Operação realizada com sucesso!");`,
    },
    {
      title: "Toast de Erro",
      description: "Notificação para erros e falhas",
      icon: <XCircle className="h-6 w-6 text-red-500" />,
      color: "border-red-200 bg-red-50",
      buttonColor: "bg-red-600 hover:bg-red-700",
      action: handleErrorToast,
      code: `notify.error("Erro ao processar a solicitação.");`,
    },
    {
      title: "Toast de Informação",
      description: "Mensagens informativas para o usuário",
      icon: <Info className="h-6 w-6 text-blue-500" />,
      color: "border-blue-200 bg-blue-50",
      buttonColor: "bg-blue-600 hover:bg-blue-700",
      action: handleInfoToast,
      code: `notify.info("Esta é uma mensagem informativa.");`,
    },
    {
      title: "Toast de Aviso",
      description: "Avisos e alertas importantes",
      icon: <AlertTriangle className="h-6 w-6 text-yellow-500" />,
      color: "border-yellow-200 bg-yellow-50",
      buttonColor: "bg-yellow-600 hover:bg-yellow-700",
      action: handleWarningToast,
      code: `notify.warning("Atenção! Verifique os dados.");`,
    },
    {
      title: "Modal de Confirmação",
      description: "Modal elegante para confirmações",
      icon: <HelpCircle className="h-6 w-6 text-amber-500" />,
      color: "border-amber-200 bg-amber-50",
      buttonColor: "bg-amber-600 hover:bg-amber-700",
      action: handleConfirmModal,
      code: `notify.confirm("Título", "Mensagem", onConfirm, onCancel);`,
    },
    {
      title: "Confirmação de Exclusão",
      description: "Modal crítico para operações destrutivas",
      icon: <Trash2 className="h-6 w-6 text-red-600" />,
      color: "border-red-300 bg-red-100",
      buttonColor: "bg-red-700 hover:bg-red-800",
      action: handleDeleteConfirm,
      code: `notify.confirmDelete("Título", "Mensagem", onConfirm, onCancel);`,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
            <Bell className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Templates & Exemplos - Notificações
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-1">
              Demonstração de todos os tipos de notificações e modais
              disponíveis no sistema
            </p>
          </div>
        </div>
      </div>

      {/* Notification Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {demoCards.map((card, index) => (
          <div
            key={index}
            className={`bg-white dark:bg-gray-800 rounded-lg border-2 ${card.color} dark:border-gray-600 p-6 hover:shadow-md transition-shadow`}
          >
            <div className="flex items-center space-x-3 mb-4">
              {card.icon}
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {card.title}
              </h3>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              {card.description}
            </p>

            <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3 mb-4">
              <code className="text-xs text-gray-800 dark:text-gray-200 font-mono">
                {card.code}
              </code>
            </div>

            <button
              onClick={card.action}
              className={`w-full px-4 py-2 text-white text-sm font-medium rounded-md transition-colors ${card.buttonColor}`}
            >
              Testar {card.title}
            </button>
          </div>
        ))}
      </div>

      {/* Usage Examples */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Exemplos de Uso Avançado
        </h2>

        <div className="space-y-6">
          {/* Example 1 */}
          <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              1. Confirmação com CNPJ Existente (Exemplo Real)
            </h3>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
              <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-x-auto">
                {`notify.confirm(
  "CNPJ já cadastrado",
  \`O CNPJ \${cnpj} já está relacionado à empresa "\${companyName}".

Deseja reutilizar os mesmos dados dessa empresa para criar o estabelecimento?\`,
  () => {
    // Confirmar - usar dados existentes
    saveWithExistingPerson(data, existingCompany);
  },
  () => {
    // Cancelar - não criar estabelecimento
    notify.info("Criação de estabelecimento cancelada.");
  }
);`}
              </pre>
            </div>
          </div>

          {/* Example 2 */}
          <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              2. Notificações com Duração Personalizada
            </h3>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
              <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-x-auto">
                {`// Notificação que fica na tela por 10 segundos
notify.success("Dados salvos!", { duration: 10000 });

// Notificação que não desaparece automaticamente
notify.error("Erro crítico!", { duration: Infinity });`}
              </pre>
            </div>
          </div>

          {/* Example 3 */}
          <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
              3. Substituindo window.confirm() e window.alert()
            </h3>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
              <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-x-auto">
                {`// ❌ Evitar - Não tem estilo
const result = window.confirm("Tem certeza?");

// ✅ Usar - Com estilo profissional
notify.confirm(
  "Confirmar Ação",
  "Tem certeza que deseja continuar?",
  () => { /* ação confirmada */ },
  () => { /* ação cancelada */ }
);`}
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          💡 <strong>Dica:</strong> Todas as notificações suportam modo escuro
          automaticamente e são responsivas para dispositivos móveis.
        </p>
      </div>
    </div>
  );
};

export default NotificationDemo;
