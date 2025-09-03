import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Button from "../ui/Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  level?: "app" | "page" | "form" | "component";
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report to error tracking service in production
    if (process.env.NODE_ENV === "production") {
      // TODO: Integrate with error tracking service (Sentry, LogRocket, etc.)
      console.error("Production error logged:", {
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        level: this.props.level || "component",
      });
    }
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleGoHome = () => {
    window.location.href = "/";
  };

  private renderErrorUI() {
    const { level = "component", fallback } = this.props;
    const { error, errorInfo } = this.state;

    // Use custom fallback if provided
    if (fallback) {
      return fallback;
    }

    // Different UI based on error level
    switch (level) {
      case "app":
        return (
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Oops! Algo deu errado
              </h1>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                A aplicação encontrou um erro inesperado. Nossa equipe foi
                notificada.
              </p>
              <div className="space-y-3">
                <Button onClick={this.handleRetry} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Tentar Novamente
                </Button>
                <Button
                  variant="secondary"
                  onClick={this.handleGoHome}
                  className="w-full"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Voltar ao Início
                </Button>
              </div>
              {process.env.NODE_ENV === "development" && error && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400">
                    Detalhes do erro (desenvolvimento)
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-auto">
                    {error.message}
                    {error.stack}
                  </pre>
                </details>
              )}
            </div>
          </div>
        );

      case "page":
        return (
          <div className="flex items-center justify-center p-8">
            <div className="max-w-sm w-full bg-white dark:bg-gray-800 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
              <div className="w-12 h-12 mx-auto mb-4 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Erro na página
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                Não foi possível carregar esta seção.
              </p>
              <Button size="sm" onClick={this.handleRetry}>
                <RefreshCw className="w-4 h-4 mr-1" />
                Recarregar
              </Button>
            </div>
          </div>
        );

      case "form":
        return (
          <div className="border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Erro no formulário
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  Ocorreu um erro ao processar o formulário. Tente novamente.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={this.handleRetry}
                  className="mt-2"
                >
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Tentar Novamente
                </Button>
              </div>
            </div>
          </div>
        );

      default: // component level
        return (
          <div className="border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10 rounded p-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
              <span className="text-sm text-red-700 dark:text-red-300">
                Erro no componente
              </span>
              <button
                onClick={this.handleRetry}
                className="text-xs text-red-600 dark:text-red-400 underline ml-2"
              >
                Recarregar
              </button>
            </div>
          </div>
        );
    }
  }

  public render() {
    if (this.state.hasError) {
      return this.renderErrorUI();
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
