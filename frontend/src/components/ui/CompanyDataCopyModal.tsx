import React from "react";
import Button from "./Button";
import Card from "./Card";
import {
  Building,
  Copy,
  X,
  CheckCircle,
  Phone,
  Mail,
  MapPin,
} from "lucide-react";

interface CompanyData {
  id: number;
  name: string;
  tax_id: string;
  people?: {
    name: string;
    tax_id: string;
    description?: string;
  };
  phones?: Array<{
    country_code: string;
    number: string;
    type: string;
    is_principal: boolean;
  }>;
  emails?: Array<{
    email_address: string;
    type: string;
    is_principal: boolean;
  }>;
  addresses?: Array<{
    street: string;
    number?: string;
    city: string;
    state: string;
    zip_code: string;
    type: string;
    is_principal: boolean;
  }>;
}

interface CompanyDataCopyModalProps {
  isOpen: boolean;
  company: CompanyData | null;
  onConfirm: (shouldCopy: boolean) => void;
  onCancel: () => void;
}

const CompanyDataCopyModal: React.FC<CompanyDataCopyModalProps> = ({
  isOpen,
  company,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen || !company) return null;

  const hasPhones = company.phones && company.phones.length > 0;
  const hasEmails = company.emails && company.emails.length > 0;
  const hasAddresses = company.addresses && company.addresses.length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-background border border-border rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Copy className="h-5 w-5" />
            Copiar Dados da Empresa
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onCancel}
            icon={<X className="h-4 w-4" />}
            aria-label="Fechar modal"
          />
        </div>

        {/* Content */}
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-full mx-auto mb-4">
              <Building className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              Copiar dados da empresa?
            </h3>
            <p className="text-muted-foreground">
              Você selecionou a empresa{" "}
              <strong>
                {company.people?.name || company.name || "Empresa"}
              </strong>
              . Deseja copiar automaticamente os dados da empresa para o
              formulário do estabelecimento?
            </p>
          </div>

          {/* Dados que serão copiados */}
          <Card className="bg-muted/50">
            <div className="space-y-4">
              <h4 className="font-medium text-foreground flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                Dados que serão copiados:
              </h4>

              <div className="space-y-3">
                {/* Nome e CNPJ */}
                <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                  <Building className="h-4 w-4 text-primary" />
                  <div>
                    <p className="font-medium text-foreground">
                      {company.people?.name || company.name || "Empresa"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      CNPJ: {company.people?.tax_id || company.tax_id}
                    </p>
                  </div>
                </div>

                {/* Telefones */}
                {hasPhones && (
                  <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                    <Phone className="h-4 w-4 text-blue-600" />
                    <div>
                      <p className="font-medium text-foreground">
                        {company.phones!.length} telefone
                        {company.phones!.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {company
                          .phones!.map(
                            (phone) => `(${phone.country_code}) ${phone.number}`
                          )
                          .join(", ")}
                      </p>
                    </div>
                  </div>
                )}

                {/* Emails */}
                {hasEmails && (
                  <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                    <Mail className="h-4 w-4 text-green-600" />
                    <div>
                      <p className="font-medium text-foreground">
                        {company.emails!.length} e-mail
                        {company.emails!.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {company
                          .emails!.map((email) => email.email_address)
                          .join(", ")}
                      </p>
                    </div>
                  </div>
                )}

                {/* Endereços */}
                {hasAddresses && (
                  <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                    <MapPin className="h-4 w-4 text-orange-600" />
                    <div>
                      <p className="font-medium text-foreground">
                        {company.addresses!.length} endereço
                        {company.addresses!.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {company
                          .addresses!.map(
                            (addr) =>
                              `${addr.street}, ${addr.city} - ${addr.state}`
                          )
                          .join("; ")}
                      </p>
                    </div>
                  </div>
                )}

                {/* Descrição */}
                {company.people?.description && (
                  <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                    <Building className="h-4 w-4 text-purple-600" />
                    <div>
                      <p className="font-medium text-foreground">Descrição</p>
                      <p className="text-sm text-muted-foreground">
                        {company.people.description}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Aviso */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              <strong>Atenção:</strong> Esta ação irá sobrescrever os dados
              atuais do formulário do estabelecimento. Os dados existentes serão
              perdidos.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 flex items-center justify-between gap-3 p-6 border-t border-border">
          <Button variant="secondary" outline onClick={onCancel}>
            Cancelar
          </Button>
          <div className="flex gap-3">
            <Button
              variant="secondary"
              outline
              onClick={() => onConfirm(false)} // Apenas selecionar, sem copiar
            >
              Apenas Selecionar
            </Button>
            <Button
              onClick={() => onConfirm(true)} // Copiar dados
              icon={<Copy className="h-4 w-4" />}
              className="bg-primary hover:bg-primary/90"
            >
              Copiar Dados
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyDataCopyModal;
