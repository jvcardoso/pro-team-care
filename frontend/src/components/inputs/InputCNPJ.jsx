import React, { useState, useEffect } from "react";
import { Building2, Search, Loader2 } from "lucide-react";
import BaseInputField from "./BaseInputField";
import { cnpjConfig } from "../../utils/inputHelpers.tsx";
import { removeNonNumeric } from "../../utils/validators";
import { consultarCNPJ } from "../../services/cnpjService";

const InputCNPJ = ({
  label = "CNPJ",
  value = "",
  onChange,
  onCompanyFound,
  onEnrichmentStart,
  onEnrichmentEnd,
  showConsultButton = true,
  autoConsult = false,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isEnriching, setIsEnriching] = useState(false);
  const [companyData, setCompanyData] = useState(null);
  const [currentValue, setCurrentValue] = useState(value || "");
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState("");

  // Função para finalizar enriquecimento
  const finishEnrichment = () => {
    setIsEnriching(false);
    if (onEnrichmentEnd) {
      onEnrichmentEnd();
    }
  };

  // Sincronizar currentValue com o valor das props
  useEffect(() => {
    if (value !== undefined && value !== currentValue) {
      setCurrentValue(value);
    }
  }, [value, currentValue]);

  // Auto-consulta quando CNPJ estiver válido
  useEffect(() => {
    if (
      autoConsult &&
      currentValue &&
      currentValue.length === 14 &&
      !isLoading
    ) {
      const timeoutId = setTimeout(() => {
        consultCompany(currentValue);
      }, 500);
      return () => clearTimeout(timeoutId);
    }
  }, [autoConsult, currentValue, isLoading]);

  const consultCompany = async (cnpj) => {
    if (!cnpj || cnpj.length !== 14) return;

    setIsLoading(true);

    try {
      const result = await consultarCNPJ(cnpj);

      setCompanyData(result);
      setValidationMessage("");
      setIsValid(true);

      // Notificar início do enriquecimento se houver callback
      if (onEnrichmentStart) {
        setIsEnriching(true);
        onEnrichmentStart();
      }

      // Callback para o componente pai com dados da empresa
      if (onCompanyFound) {
        onCompanyFound(result);
      }

      // Notificar fim do enriquecimento (será chamado pelo componente pai)
      // O componente pai deve chamar onEnrichmentEnd quando terminar
    } catch (error) {
      console.error("Erro ao consultar CNPJ:", error);

      // Mesmo com erro na consulta, se o CNPJ for válido, criar dados básicos
      if (cnpj.length === 14 && /^\d+$/.test(cnpj)) {
        console.log(
          "CNPJ válido mas não encontrado na Receita Federal - criando dados básicos"
        );

        const basicCompanyData = {
          people: {
            person_type: "PJ",
            name: "",
            trade_name: "",
            tax_id: cnpj,
            incorporation_date: "",
            tax_regime: "simples_nacional",
            legal_nature: "",
            status: "active",
            description: "",
          },
          company: {
            settings: {},
            metadata: {},
            display_order: 0,
          },
          phones: [
            {
              country_code: "55",
              number: "",
              type: "commercial",
              is_principal: true,
              is_whatsapp: false,
            },
          ],
          emails: [
            {
              email_address: "",
              type: "work",
              is_principal: true,
            },
          ],
          addresses: [
            {
              street: "",
              number: "",
              details: "",
              neighborhood: "",
              city: "",
              state: "",
              zip_code: "",
              country: "BR",
              type: "commercial",
              is_principal: true,
            },
          ],
        };

        setCompanyData(basicCompanyData);
        setValidationMessage(
          "CNPJ válido, mas dados não encontrados na Receita Federal"
        );
        setIsValid(true);

        // Chamar callback mesmo com dados básicos
        if (onCompanyFound) {
          onCompanyFound(basicCompanyData);
        }

        // Notificar início do enriquecimento
        if (onEnrichmentStart) {
          setIsEnriching(true);
          onEnrichmentStart();
        }
      } else {
        setValidationMessage(error.message || "Erro ao consultar CNPJ");
        setIsValid(false);
        setCompanyData(null);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBaseInputChange = (event) => {
    setCurrentValue(event.rawValue);

    if (onChange) {
      onChange(event);
    }
  };

  const handleConsult = () => {
    if (currentValue && currentValue.length === 14) {
      consultCompany(currentValue);
    }
  };

  const canConsult = currentValue && currentValue.length === 14 && !isLoading;

  // Ícone customizado baseado no estado
  const getRightIcon = () => {
    if (isLoading) {
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
    }
    if (isEnriching) {
      return (
        <div className="flex items-center space-x-1">
          <Loader2 className="h-4 w-4 text-purple-500 animate-spin" />
          <span className="text-xs text-purple-600 hidden sm:inline">
            Completando...
          </span>
        </div>
      );
    }
    if (companyData && currentValue && currentValue.length === 14) {
      return <Building2 className="h-4 w-4 text-green-500" />;
    }
    return null;
  };

  return (
    <div className="space-y-1">
      <div className="flex gap-3 items-start">
        <div className="flex-1 min-h-[60px]">
          <BaseInputField
            label={label}
            value={value}
            onChange={handleBaseInputChange}
            formatterConfig={cnpjConfig.formatter}
            validatorConfig={cnpjConfig.validator}
            leftIcon={cnpjConfig.icon}
            rightIcon={getRightIcon()}
            placeholder={cnpjConfig.placeholder}
            inputMode={cnpjConfig.inputMode}
            autoComplete={cnpjConfig.autoComplete}
            successMessage={cnpjConfig.successMessage}
            progressMessage={cnpjConfig.progressMessage}
            showProgressIndicator
            {...props}
          />
        </div>

        {/* Botão Consultar */}
        {showConsultButton && (
          <div className="flex items-start pt-[22px]">
            <button
              type="button"
              onClick={handleConsult}
              disabled={!canConsult || props.disabled}
              className={`px-4 py-2 border rounded-md font-medium transition-colors flex items-center gap-2 h-10 flex-shrink-0 ${
                canConsult && !props.disabled
                  ? "border-border bg-secondary text-secondary-foreground hover:bg-secondary/80"
                  : "border-border bg-muted text-muted-foreground cursor-not-allowed"
              }`}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">Consultar</span>
              <span className="sm:hidden">Buscar</span>
            </button>
          </div>
        )}
      </div>

      {/* Dados da empresa encontrada */}
      {companyData && (
        <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded border">
          <div className="flex items-start gap-2">
            <Building2 className="h-4 w-4 mt-0.5 text-green-600" />
            <div className="flex-1">
              <p className="font-medium text-foreground">
                {companyData.people.name}
              </p>
              {companyData.people.trade_name &&
                companyData.people.trade_name !== companyData.people.name && (
                  <p className="text-xs opacity-75">
                    Nome Fantasia: {companyData.people.trade_name}
                  </p>
                )}
              <div className="mt-1 space-y-1">
                <p>
                  Status:{" "}
                  <span className="capitalize">
                    {companyData.people.status}
                  </span>
                </p>
                {companyData.people.metadata?.situacao && (
                  <p>Situação: {companyData.people.metadata.situacao}</p>
                )}
                {companyData.people.metadata?.porte && (
                  <p>Porte: {companyData.people.metadata.porte}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mensagem de ajuda customizada */}
      {!companyData && currentValue && currentValue.length === 14 && (
        <p className="text-xs text-muted-foreground">
          CNPJ válido • Clique em "Consultar" para buscar dados da empresa
        </p>
      )}
    </div>
  );
};

export default InputCNPJ;
