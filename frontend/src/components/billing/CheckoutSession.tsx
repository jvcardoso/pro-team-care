import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Alert, AlertDescription } from "../ui/alert";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import {
  Loader2,
  ExternalLink,
  QrCode,
  CreditCard,
  Banknote,
  Smartphone,
  Copy,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import {
  CheckoutSessionResponse,
  CheckoutState,
} from "../../types/pagbank.types";

interface CheckoutSessionProps {
  invoiceId: number;
  invoiceNumber?: string;
  totalAmount?: number;
  contractNumber?: string;
  customerName?: string;
  onCheckoutCreate?: (response: CheckoutSessionResponse) => void;
  onPaymentComplete?: () => void;
  autoCreate?: boolean;
}

const CheckoutSession: React.FC<CheckoutSessionProps> = ({
  invoiceId,
  invoiceNumber,
  totalAmount,
  contractNumber,
  customerName,
  onCheckoutCreate,
  onPaymentComplete,
  autoCreate = false,
}) => {
  const [checkoutState, setCheckoutState] = useState<CheckoutState>({
    loading: false,
  });
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (autoCreate && invoiceId) {
      handleCreateCheckout();
    }
  }, [autoCreate, invoiceId]);

  const handleCreateCheckout = async () => {
    setCheckoutState({ loading: true });

    try {
      // This would call the actual API
      // const response = await billingService.createCheckoutSession({ invoice_id: invoiceId });

      // Mock response for now
      const mockResponse: CheckoutSessionResponse = {
        success: true,
        invoice_id: invoiceId,
        checkout_url: `https://sandbox.pagseguro.uol.com.br/checkout/${Date.now()}`,
        session_id: "SESS_" + Date.now(),
        expires_at: new Date(
          Date.now() + 7 * 24 * 60 * 60 * 1000
        ).toISOString(),
        qr_code:
          "00020126360014BR.GOV.BCB.PIX0114+55119999999995204000053039865802BR5925Empresa Exemplo Ltda6009SAO PAULO61080540900062070503***63043D3D",
        transaction_id: Math.floor(Math.random() * 1000000),
      };

      setCheckoutState({
        loading: false,
        checkoutUrl: mockResponse.checkout_url,
        sessionId: mockResponse.session_id,
        expiresAt: mockResponse.expires_at,
        qrCode: mockResponse.qr_code,
      });

      onCheckoutCreate?.(mockResponse);
    } catch (err: any) {
      setCheckoutState({
        loading: false,
        error: err.message || "Erro ao criar sessão de checkout",
      });
    }
  };

  const handleCopyQRCode = async () => {
    if (!checkoutState.qrCode) return;

    try {
      await navigator.clipboard.writeText(checkoutState.qrCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy QR code:", err);
    }
  };

  const handleOpenCheckout = () => {
    if (checkoutState.checkoutUrl) {
      window.open(checkoutState.checkoutUrl, "_blank", "noopener,noreferrer");
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date().getTime();
    const expiry = new Date(expiresAt).getTime();
    const diff = expiry - now;

    if (diff <= 0) return "Expirado";

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  // Loading state
  if (checkoutState.loading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Criando sessão de pagamento...
          </h3>
          <p className="text-gray-600 text-center">
            Aguarde enquanto preparamos as opções de pagamento
          </p>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (checkoutState.error) {
    return (
      <Card>
        <CardContent className="py-6">
          <Alert className="border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-700">
              {checkoutState.error}
            </AlertDescription>
          </Alert>
          <div className="flex justify-center mt-4">
            <Button onClick={handleCreateCheckout} variant="outline">
              Tentar Novamente
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Initial state - no checkout created yet
  if (!checkoutState.checkoutUrl) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-blue-600" />
            Pagamento Manual
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Invoice Info */}
          {(invoiceNumber || totalAmount || contractNumber) && (
            <div className="space-y-2 p-4 bg-gray-50 rounded-lg">
              {invoiceNumber && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Fatura:</span>
                  <span className="font-medium">{invoiceNumber}</span>
                </div>
              )}
              {contractNumber && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Contrato:</span>
                  <span className="font-medium">{contractNumber}</span>
                </div>
              )}
              {customerName && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Cliente:</span>
                  <span className="font-medium">{customerName}</span>
                </div>
              )}
              {totalAmount && (
                <div className="flex justify-between text-lg">
                  <span className="text-gray-600">Valor:</span>
                  <span className="font-bold text-green-600">
                    {formatCurrency(totalAmount)}
                  </span>
                </div>
              )}
            </div>
          )}

          <div className="text-center space-y-4">
            <p className="text-gray-600">
              Clique para criar uma sessão de pagamento segura com múltiplas
              opções:
            </p>

            <div className="flex items-center justify-center gap-6 py-4">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Smartphone className="h-4 w-4 text-blue-600" />
                PIX
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Banknote className="h-4 w-4 text-orange-600" />
                Boleto
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CreditCard className="h-4 w-4 text-green-600" />
                Cartão
              </div>
            </div>

            <Button
              onClick={handleCreateCheckout}
              size="lg"
              className="w-full max-w-sm"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Criar Link de Pagamento
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Checkout created state
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            Sessão de Pagamento Criada
          </CardTitle>
          {checkoutState.expiresAt && (
            <Badge variant="outline" className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {getTimeRemaining(checkoutState.expiresAt)}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Success Message */}
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700">
            Link de pagamento criado com sucesso! O cliente pode escolher entre
            PIX, Boleto ou Cartão.
          </AlertDescription>
        </Alert>

        {/* Payment Link */}
        <div className="space-y-3">
          <Label className="text-sm font-medium text-gray-700">
            Link de Pagamento
          </Label>
          <div className="flex items-center gap-2">
            <Button
              onClick={handleOpenCheckout}
              className="flex-1 justify-start"
              variant="outline"
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Abrir Página de Pagamento
            </Button>
          </div>
          <p className="text-xs text-gray-500">
            O link abre em uma nova aba com a página segura do PagBank
          </p>
        </div>

        {/* QR Code PIX */}
        {checkoutState.qrCode && (
          <>
            <Separator />
            <div className="space-y-3">
              <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <QrCode className="h-4 w-4" />
                Código PIX (QR Code)
              </Label>
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <code className="flex-1 text-xs text-gray-600 break-all bg-white p-2 rounded border">
                    {checkoutState.qrCode}
                  </code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyQRCode}
                    className="shrink-0"
                  >
                    {copied ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-gray-500">
                  Copie este código para colar no app do banco ou escaneie o QR
                  Code na página de pagamento
                </p>
              </div>
            </div>
          </>
        )}

        {/* Session Details */}
        <Separator />
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">ID da Sessão:</span>
            <p className="font-mono text-xs">{checkoutState.sessionId}</p>
          </div>
          {checkoutState.expiresAt && (
            <div>
              <span className="text-gray-500">Expira em:</span>
              <p className="font-medium">
                {formatDate(checkoutState.expiresAt)}
              </p>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="font-medium text-blue-900 mb-2">
            Instruções para o Cliente
          </h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Acesse o link de pagamento para ver todas as opções</li>
            <li>• Para PIX: use o QR Code ou copie o código acima</li>
            <li>• Para Boleto: será gerado automaticamente na página</li>
            <li>• Para Cartão: preencha os dados na página segura</li>
            <li>• O pagamento é processado em tempo real</li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-4 border-t">
          <Button onClick={handleOpenCheckout} className="flex-1">
            <ExternalLink className="mr-2 h-4 w-4" />
            Abrir Pagamento
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              // Refresh or check payment status
              onPaymentComplete?.();
            }}
          >
            Verificar Status
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default CheckoutSession;
