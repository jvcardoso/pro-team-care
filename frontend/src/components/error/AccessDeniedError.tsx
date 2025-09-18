import React from "react";
import { AlertTriangle, Lock, Home, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Button from "../ui/Button";
import Card from "../ui/Card";

interface AccessDeniedErrorProps {
  title?: string;
  message?: string;
  resource?: string;
  action?: string;
  showBackButton?: boolean;
  showHomeButton?: boolean;
  onRetry?: () => void;
}

const AccessDeniedError: React.FC<AccessDeniedErrorProps> = ({
  title = "Acesso Negado",
  message,
  resource = "este recurso",
  action = "visualizar",
  showBackButton = true,
  showHomeButton = true,
  onRetry,
}) => {
  const navigate = useNavigate();

  const defaultMessage = `Você não possui permissão para ${action} ${resource}. Entre em contato com o administrador do sistema para solicitar acesso.`;

  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate("/admin");
    }
  };

  const handleGoHome = () => {
    navigate("/admin");
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <Card className="max-w-lg w-full text-center p-8">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <Lock className="w-8 h-8 text-red-600" />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-4">{title}</h1>

        <div className="flex items-center justify-center mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-500 mr-2" />
          <span className="text-sm font-medium text-amber-700">
            Erro 403 - Forbidden
          </span>
        </div>

        <p className="text-gray-600 mb-8 leading-relaxed">
          {message || defaultMessage}
        </p>

        <div className="space-y-3">
          {onRetry && (
            <Button onClick={onRetry} className="w-full" variant="outline">
              Tentar Novamente
            </Button>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            {showBackButton && (
              <Button
                onClick={handleGoBack}
                variant="outline"
                className="flex-1"
                icon={<ArrowLeft className="w-4 h-4" />}
              >
                Voltar
              </Button>
            )}

            {showHomeButton && (
              <Button
                onClick={handleGoHome}
                className="flex-1"
                icon={<Home className="w-4 h-4" />}
              >
                Ir para Início
              </Button>
            )}
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Se você acredita que deveria ter acesso a este recurso, entre em
            contato com o administrador do sistema.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default AccessDeniedError;
