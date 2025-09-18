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

interface EstablishmentData {
  id: number;
  code: string;
  company_name?: string;
  company_tax_id?: string;
  person?: {
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

interface ClientDataCopyModalProps {
  isOpen: boolean;
  establishment: EstablishmentData | null;
  onConfirm: (shouldCopy: boolean) => void;
  onCancel: () => void;
}

const ClientDataCopyModal: React.FC<ClientDataCopyModalProps> = ({
  isOpen,
  establishment,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen || !establishment) return null;

  const hasPhones = establishment.phones && establishment.phones.length > 0;
  const hasEmails = establishment.emails && establishment.emails.length > 0;
  const hasAddresses =
    establishment.addresses && establishment.addresses.length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-background border border-border rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Copy className="h-5 w-5" />
            Dados do Estabelecimento
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
              Estabelecimento selecionado
            </h3>
            <p className="text-muted-foreground">
              Você selecionou o estabelecimento{" "}
              <strong>{establishment.person?.name || "Estabelecimento"}</strong>
              . Deseja copiar automaticamente os dados do estabelecimento para o
              formulário do cliente?
            </p>
          </div>

          {/* Dados que podem ser copiados */}
          <Card className="bg-muted/50">
            <div className="space-y-4">
              <h4 className="font-medium text-foreground flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                Dados que podem ser copiados:
              </h4>

              <div className="space-y-3">
                {/* Nome e Código */}
                <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                  <Building className="h-4 w-4 text-primary" />
                  <div>
                    <p className="font-medium text-foreground">
                      {establishment.person?.name || "Estabelecimento"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Código: {establishment.code}
                    </p>
                    {establishment.company_name && (
                      <p className="text-sm text-muted-foreground">
                        Empresa: {establishment.company_name}
                      </p>
                    )}
                  </div>
                </div>

                {/* Telefones */}
                {hasPhones && (
                  <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                    <Phone className="h-4 w-4 text-blue-600" />
                    <div>
                      <p className="font-medium text-foreground">
                        {establishment.phones!.length} telefone
                        {establishment.phones!.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {establishment
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
                        {establishment.emails!.length} e-mail
                        {establishment.emails!.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {establishment
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
                        {establishment.addresses!.length} endereço
                        {establishment.addresses!.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {establishment
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
                {establishment.person?.description && (
                  <div className="flex items-center gap-3 p-3 bg-background rounded-md">
                    <Building className="h-4 w-4 text-purple-600" />
                    <div>
                      <p className="font-medium text-foreground">Descrição</p>
                      <p className="text-sm text-muted-foreground">
                        {establishment.person.description}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Aviso */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Nota:</strong> Para clientes, é mais comum não copiar os
              dados do estabelecimento. Você pode preencher os dados específicos
              do cliente manualmente.
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
              onClick={() => onConfirm(false)} // NÃO COPIAR (padrão para clientes)
            >
              Não Copiar
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

export default ClientDataCopyModal;
