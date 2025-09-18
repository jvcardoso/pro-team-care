import React from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import { Home, ArrowLeft, Search } from "lucide-react";

const NotFoundPage = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate("/admin");
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="h-screen flex items-center justify-center bg-background">
      <div className="text-center max-w-md mx-auto px-6">
        {/* 404 Icon */}
        <div className="mb-8">
          <div className="text-6xl md:text-8xl font-bold text-primary-600 mb-4">
            404
          </div>
          <div className="mx-auto w-24 h-1 bg-primary-600 rounded-full"></div>
        </div>

        {/* Message */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-foreground mb-4">
            Página não encontrada
          </h1>
          <p className="text-muted-foreground text-lg mb-2">
            A página que você está procurando não existe ou foi movida.
          </p>
          <p className="text-muted-foreground">
            Verifique o endereço ou navegue para uma das opções abaixo.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
          <Button
            onClick={handleGoHome}
            icon={<Home className="h-4 w-4" />}
            className="w-full sm:w-auto"
          >
            Ir para Dashboard
          </Button>
          <Button
            variant="outline"
            onClick={handleGoBack}
            icon={<ArrowLeft className="h-4 w-4" />}
            className="w-full sm:w-auto"
          >
            Voltar
          </Button>
        </div>

        {/* Help Text */}
        <div className="mt-8 pt-8 border-t border-border">
          <p className="text-sm text-muted-foreground">
            Se você acredita que isso é um erro, entre em contato com o suporte
            técnico.
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
