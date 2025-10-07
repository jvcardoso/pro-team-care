import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Alert, AlertDescription } from "../ui/alert";
import { Separator } from "../ui/separator";
import {
  Loader2,
  CreditCard,
  Shield,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import {
  RecurrentBillingSetupRequest,
  RecurrentBillingSetupResponse,
  CreditCardFormData,
  AddressData,
} from "../../types/pagbank.types";

interface RecurrentBillingSetupProps {
  contractId: number;
  clientData?: {
    name: string;
    email: string;
    tax_id: string;
    phone: string;
    address?: Partial<AddressData>;
  };
  onSetupComplete?: (response: RecurrentBillingSetupResponse) => void;
  onCancel?: () => void;
  loading?: boolean;
}

const RecurrentBillingSetup: React.FC<RecurrentBillingSetupProps> = ({
  contractId,
  clientData,
  onSetupComplete,
  onCancel,
  loading = false,
}) => {
  const [formData, setFormData] = useState<CreditCardFormData>({
    cardNumber: "",
    expiryMonth: "",
    expiryYear: "",
    cvv: "",
    holderName: clientData?.name || "",
  });

  const [addressData, setAddressData] = useState<AddressData>({
    street: clientData?.address?.street || "",
    number: clientData?.address?.number || "",
    details: clientData?.address?.details || "",
    neighborhood: clientData?.address?.neighborhood || "",
    city: clientData?.address?.city || "",
    state: clientData?.address?.state || "",
    zip_code: clientData?.address?.zip_code || "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>("");
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  const handleInputChange = (
    field: keyof CreditCardFormData,
    value: string
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const handleAddressChange = (field: keyof AddressData, value: string) => {
    setAddressData((prev) => ({ ...prev, [field]: value }));
    if (validationErrors[field]) {
      setValidationErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || "";
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(" ");
    } else {
      return v;
    }
  };

  const formatZipCode = (value: string) => {
    const v = value.replace(/\D/g, "");
    return v.replace(/(\d{5})(\d{3})/, "$1-$2");
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    // Card validation
    if (!formData.cardNumber.replace(/\s/g, "")) {
      errors.cardNumber = "Número do cartão é obrigatório";
    } else if (formData.cardNumber.replace(/\s/g, "").length < 13) {
      errors.cardNumber = "Número do cartão inválido";
    }

    if (!formData.expiryMonth) {
      errors.expiryMonth = "Mês é obrigatório";
    } else if (!/^(0[1-9]|1[0-2])$/.test(formData.expiryMonth)) {
      errors.expiryMonth = "Mês inválido";
    }

    if (!formData.expiryYear) {
      errors.expiryYear = "Ano é obrigatório";
    } else if (!/^\d{4}$/.test(formData.expiryYear)) {
      errors.expiryYear = "Ano inválido";
    }

    if (!formData.cvv) {
      errors.cvv = "CVV é obrigatório";
    } else if (!/^\d{3,4}$/.test(formData.cvv)) {
      errors.cvv = "CVV inválido";
    }

    if (!formData.holderName.trim()) {
      errors.holderName = "Nome do portador é obrigatório";
    }

    // Address validation
    if (!addressData.street.trim()) {
      errors.street = "Rua é obrigatória";
    }
    if (!addressData.number.trim()) {
      errors.number = "Número é obrigatório";
    }
    if (!addressData.neighborhood.trim()) {
      errors.neighborhood = "Bairro é obrigatório";
    }
    if (!addressData.city.trim()) {
      errors.city = "Cidade é obrigatória";
    }
    if (!addressData.state.trim()) {
      errors.state = "Estado é obrigatório";
    }
    if (!addressData.zip_code.trim()) {
      errors.zip_code = "CEP é obrigatório";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    if (!clientData) {
      setError("Dados do cliente não informados");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      // Parse phone number
      const phoneClean = clientData.phone.replace(/\D/g, "");
      const phoneArea = phoneClean.slice(0, 2);
      const phoneNumber = phoneClean.slice(2);

      const setupRequest: RecurrentBillingSetupRequest = {
        contract_id: contractId,
        client_data: {
          client_id: 0, // Will be filled by backend
          name: clientData.name,
          email: clientData.email,
          tax_id: clientData.tax_id,
          phone_area: phoneArea,
          phone_number: phoneNumber,
          address: addressData,
          card_data: {
            card_number: formData.cardNumber.replace(/\s/g, ""),
            card_expiry_month: formData.expiryMonth,
            card_expiry_year: formData.expiryYear,
            card_cvv: formData.cvv,
            card_holder_name: formData.holderName,
          },
        },
      };

      // This would call the actual API
      // const response = await billingService.setupRecurrentBilling(setupRequest);

      // Mock response for now
      const mockResponse: RecurrentBillingSetupResponse = {
        success: true,
        contract_id: contractId,
        billing_method: "recurrent",
        pagbank_subscription_id: "SUB_" + Date.now(),
        pagbank_customer_id: "CUST_" + Date.now(),
        next_billing_date: new Date(
          Date.now() + 30 * 24 * 60 * 60 * 1000
        ).toISOString(),
        message: "Cobrança recorrente configurada com sucesso!",
      };

      onSetupComplete?.(mockResponse);
    } catch (err: any) {
      setError(err.message || "Erro ao configurar cobrança recorrente");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-blue-600" />
          Configurar Cobrança Recorrente
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Security Alert */}
          <Alert className="border-blue-200 bg-blue-50">
            <Shield className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-700">
              Seus dados de cartão são processados de forma segura pelo PagBank.
              Não armazenamos informações sensíveis em nossos servidores.
            </AlertDescription>
          </Alert>

          {/* Card Information */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Informações do Cartão</h3>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label htmlFor="cardNumber">Número do Cartão *</Label>
                <Input
                  id="cardNumber"
                  type="text"
                  placeholder="0000 0000 0000 0000"
                  value={formData.cardNumber}
                  onChange={(e) =>
                    handleInputChange(
                      "cardNumber",
                      formatCardNumber(e.target.value)
                    )
                  }
                  maxLength={19}
                  className={
                    validationErrors.cardNumber ? "border-red-500" : ""
                  }
                  disabled={isSubmitting}
                />
                {validationErrors.cardNumber && (
                  <p className="text-sm text-red-500 mt-1">
                    {validationErrors.cardNumber}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="expiryMonth">Mês *</Label>
                  <Input
                    id="expiryMonth"
                    type="text"
                    placeholder="MM"
                    value={formData.expiryMonth}
                    onChange={(e) =>
                      handleInputChange(
                        "expiryMonth",
                        e.target.value.replace(/\D/g, "").slice(0, 2)
                      )
                    }
                    maxLength={2}
                    className={
                      validationErrors.expiryMonth ? "border-red-500" : ""
                    }
                    disabled={isSubmitting}
                  />
                  {validationErrors.expiryMonth && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.expiryMonth}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="expiryYear">Ano *</Label>
                  <Input
                    id="expiryYear"
                    type="text"
                    placeholder="YYYY"
                    value={formData.expiryYear}
                    onChange={(e) =>
                      handleInputChange(
                        "expiryYear",
                        e.target.value.replace(/\D/g, "").slice(0, 4)
                      )
                    }
                    maxLength={4}
                    className={
                      validationErrors.expiryYear ? "border-red-500" : ""
                    }
                    disabled={isSubmitting}
                  />
                  {validationErrors.expiryYear && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.expiryYear}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="cvv">CVV *</Label>
                  <Input
                    id="cvv"
                    type="text"
                    placeholder="123"
                    value={formData.cvv}
                    onChange={(e) =>
                      handleInputChange(
                        "cvv",
                        e.target.value.replace(/\D/g, "").slice(0, 4)
                      )
                    }
                    maxLength={4}
                    className={validationErrors.cvv ? "border-red-500" : ""}
                    disabled={isSubmitting}
                  />
                  {validationErrors.cvv && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.cvv}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="holderName">Nome do Portador *</Label>
                <Input
                  id="holderName"
                  type="text"
                  placeholder="Nome conforme impresso no cartão"
                  value={formData.holderName}
                  onChange={(e) =>
                    handleInputChange("holderName", e.target.value)
                  }
                  className={
                    validationErrors.holderName ? "border-red-500" : ""
                  }
                  disabled={isSubmitting}
                />
                {validationErrors.holderName && (
                  <p className="text-sm text-red-500 mt-1">
                    {validationErrors.holderName}
                  </p>
                )}
              </div>
            </div>
          </div>

          <Separator />

          {/* Address Information */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Endereço de Cobrança</h3>

            <div className="grid grid-cols-1 gap-4">
              <div className="grid grid-cols-4 gap-4">
                <div className="col-span-3">
                  <Label htmlFor="street">Rua *</Label>
                  <Input
                    id="street"
                    type="text"
                    value={addressData.street}
                    onChange={(e) =>
                      handleAddressChange("street", e.target.value)
                    }
                    className={validationErrors.street ? "border-red-500" : ""}
                    disabled={isSubmitting}
                  />
                  {validationErrors.street && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.street}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="number">Número *</Label>
                  <Input
                    id="number"
                    type="text"
                    value={addressData.number}
                    onChange={(e) =>
                      handleAddressChange("number", e.target.value)
                    }
                    className={validationErrors.number ? "border-red-500" : ""}
                    disabled={isSubmitting}
                  />
                  {validationErrors.number && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.number}
                    </p>
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="details">Complemento</Label>
                <Input
                  id="details"
                  type="text"
                  placeholder="Apartamento, casa, etc."
                  value={addressData.details}
                  onChange={(e) =>
                    handleAddressChange("details", e.target.value)
                  }
                  disabled={isSubmitting}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="neighborhood">Bairro *</Label>
                  <Input
                    id="neighborhood"
                    type="text"
                    value={addressData.neighborhood}
                    onChange={(e) =>
                      handleAddressChange("neighborhood", e.target.value)
                    }
                    className={
                      validationErrors.neighborhood ? "border-red-500" : ""
                    }
                    disabled={isSubmitting}
                  />
                  {validationErrors.neighborhood && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.neighborhood}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="city">Cidade *</Label>
                  <Input
                    id="city"
                    type="text"
                    value={addressData.city}
                    onChange={(e) =>
                      handleAddressChange("city", e.target.value)
                    }
                    className={validationErrors.city ? "border-red-500" : ""}
                    disabled={isSubmitting}
                  />
                  {validationErrors.city && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.city}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="state">Estado *</Label>
                  <Input
                    id="state"
                    type="text"
                    placeholder="SP"
                    value={addressData.state}
                    onChange={(e) =>
                      handleAddressChange(
                        "state",
                        e.target.value.toUpperCase().slice(0, 2)
                      )
                    }
                    maxLength={2}
                    className={validationErrors.state ? "border-red-500" : ""}
                    disabled={isSubmitting}
                  />
                  {validationErrors.state && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.state}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="zip_code">CEP *</Label>
                  <Input
                    id="zip_code"
                    type="text"
                    placeholder="00000-000"
                    value={addressData.zip_code}
                    onChange={(e) =>
                      handleAddressChange(
                        "zip_code",
                        formatZipCode(e.target.value)
                      )
                    }
                    maxLength={9}
                    className={
                      validationErrors.zip_code ? "border-red-500" : ""
                    }
                    disabled={isSubmitting}
                  />
                  {validationErrors.zip_code && (
                    <p className="text-sm text-red-500 mt-1">
                      {validationErrors.zip_code}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-700">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || loading}
              className="min-w-[120px]"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Configurando...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Configurar
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default RecurrentBillingSetup;
