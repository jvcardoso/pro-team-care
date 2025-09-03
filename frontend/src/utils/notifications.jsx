import React from "react";
import toast from "react-hot-toast";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
  Trash2,
  HelpCircle,
} from "lucide-react";

export const notify = {
  // Toast de Sucesso
  success: (message, options = {}) => {
    return toast.custom(
      (t) => (
        <div
          className={`${
            t.visible ? "animate-enter" : "animate-leave"
          } max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
        >
          <div className="flex-1 w-0 p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Sucesso
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-300">
                  {message}
                </p>
              </div>
            </div>
          </div>
          <div className="flex border-l border-gray-200 dark:border-gray-600">
            <button
              onClick={() => toast.dismiss(t.id)}
              className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-green-600 hover:text-green-500 focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-green-400"
            >
              OK
            </button>
          </div>
        </div>
      ),
      { duration: 4000, ...options }
    );
  },

  // Toast de Erro
  error: (message, options = {}) => {
    return toast.custom(
      (t) => (
        <div
          className={`${
            t.visible ? "animate-enter" : "animate-leave"
          } max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
        >
          <div className="flex-1 w-0 p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Erro
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-300">
                  {message}
                </p>
              </div>
            </div>
          </div>
          <div className="flex border-l border-gray-200 dark:border-gray-600">
            <button
              onClick={() => toast.dismiss(t.id)}
              className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-red-600 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 dark:text-red-400"
            >
              Fechar
            </button>
          </div>
        </div>
      ),
      { duration: 6000, ...options }
    );
  },

  // Toast de Informação
  info: (message, options = {}) => {
    return toast.custom(
      (t) => (
        <div
          className={`${
            t.visible ? "animate-enter" : "animate-leave"
          } max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
        >
          <div className="flex-1 w-0 p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <Info className="h-8 w-8 text-blue-500" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Informação
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-300">
                  {message}
                </p>
              </div>
            </div>
          </div>
          <div className="flex border-l border-gray-200 dark:border-gray-600">
            <button
              onClick={() => toast.dismiss(t.id)}
              className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-blue-400"
            >
              Entendi
            </button>
          </div>
        </div>
      ),
      { duration: 5000, ...options }
    );
  },

  // Toast de Aviso
  warning: (message, options = {}) => {
    return toast.custom(
      (t) => (
        <div
          className={`${
            t.visible ? "animate-enter" : "animate-leave"
          } max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5`}
        >
          <div className="flex-1 w-0 p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <AlertCircle className="h-8 w-8 text-yellow-500" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Atenção
                </p>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-300">
                  {message}
                </p>
              </div>
            </div>
          </div>
          <div className="flex border-l border-gray-200 dark:border-gray-600">
            <button
              onClick={() => toast.dismiss(t.id)}
              className="w-full border border-transparent rounded-none rounded-r-lg p-4 flex items-center justify-center text-sm font-medium text-yellow-600 hover:text-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-500 dark:text-yellow-400"
            >
              OK
            </button>
          </div>
        </div>
      ),
      { duration: 5000, ...options }
    );
  },

  // Modal de Confirmação Elegante
  confirm: (title, message, onConfirm, onCancel = () => {}, options = {}) => {
    return toast.custom(
      (t) => (
        <div
          className={`${
            t.visible ? "animate-enter" : "animate-leave"
          } max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5`}
        >
          <div className="p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <HelpCircle className="h-8 w-8 text-amber-500" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {title}
                </p>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-300">
                  {message}
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-3 justify-end">
              <button
                onClick={() => {
                  onCancel();
                  toast.dismiss(t.id);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-300 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  onConfirm();
                  toast.dismiss(t.id);
                }}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      ),
      { duration: Infinity, ...options }
    );
  },

  // Modal de Confirmação de Exclusão (mais crítico)
  confirmDelete: (
    title,
    message,
    onConfirm,
    onCancel = () => {},
    options = {}
  ) => {
    return toast.custom(
      (t) => (
        <div
          className={`${
            t.visible ? "animate-enter" : "animate-leave"
          } max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5`}
        >
          <div className="p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 pt-0.5">
                <Trash2 className="h-8 w-8 text-red-500" />
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {title}
                </p>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-300">
                  {message}
                </p>
                <p className="mt-1 text-xs text-red-600 dark:text-red-400 font-medium">
                  Esta ação não pode ser desfeita.
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-3 justify-end">
              <button
                onClick={() => {
                  onCancel();
                  toast.dismiss(t.id);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-300 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  onConfirm();
                  toast.dismiss(t.id);
                }}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Excluir
              </button>
            </div>
          </div>
        </div>
      ),
      { duration: Infinity, ...options }
    );
  },
};

// Funções de conveniência para manter compatibilidade
export const showSuccess = notify.success;
export const showError = notify.error;
export const showInfo = notify.info;
export const showWarning = notify.warning;
export const showConfirm = notify.confirm;
export const showDeleteConfirm = notify.confirmDelete;
