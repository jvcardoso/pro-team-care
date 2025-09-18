import React from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { PageErrorBoundary } from "../error";
import { ClientDetailed, ClientStatus, PersonType } from "../../types";
import { formatTaxId } from "../../utils/formatters";
import {
  User,
  CreditCard,
  Building2,
  Phone,
  Mail,
  MapPin,
  Calendar,
  FileText,
  Edit,
  ArrowLeft,
  Globe,
  Hash,
} from "lucide-react";

interface ClientDetailsProps {
  client: ClientDetailed;
  onEdit?: () => void;
  onBack?: () => void;
}

const ClientDetails: React.FC<ClientDetailsProps> = ({
  client,
  onEdit,
  onBack,
}) => {
  return (
    <PageErrorBoundary pageName="ClientDetails">
      <ClientDetailsContent client={client} onEdit={onEdit} onBack={onBack} />
    </PageErrorBoundary>
  );
};

const ClientDetailsContent: React.FC<ClientDetailsProps> = ({
  client,
  onEdit,
  onBack,
}) => {
  const formatPhone = (phone: string, areaCode?: string): string => {
    const clean = phone.replace(/\D/g, "");
    if (areaCode) {
      if (clean.length === 9) {
        return `(${areaCode}) ${clean.replace(/(\d{5})(\d{4})/, "$1-$2")}`;
      } else if (clean.length === 8) {
        return `(${areaCode}) ${clean.replace(/(\d{4})(\d{4})/, "$1-$2")}`;
      }
    } else if (clean.length === 11) {
      return clean.replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
    } else if (clean.length === 10) {
      return clean.replace(/(\d{2})(\d{4})(\d{4})/, "($1) $2-$3");
    }
    return phone;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const getPersonTypeLabel = (type: PersonType): string => {
    return type === PersonType.PF ? "Pessoa Física" : "Pessoa Jurídica";
  };

  const getClientStatusLabel = (status: ClientStatus): string => {
    const labels = {
      [ClientStatus.ACTIVE]: "Ativo",
      [ClientStatus.INACTIVE]: "Inativo",
      [ClientStatus.ON_HOLD]: "Em Espera",
      [ClientStatus.ARCHIVED]: "Arquivado",
    };
    return labels[status] || status;
  };

  const getClientStatusColor = (status: ClientStatus): string => {
    const colors = {
      [ClientStatus.ACTIVE]: "bg-green-100 text-green-800",
      [ClientStatus.INACTIVE]: "bg-gray-100 text-gray-800",
      [ClientStatus.ON_HOLD]: "bg-yellow-100 text-yellow-800",
      [ClientStatus.ARCHIVED]: "bg-red-100 text-red-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            {onBack && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                icon={<ArrowLeft className="h-4 w-4" />}
              />
            )}
            <h1 className="text-2xl font-bold text-foreground">
              Detalhes do Cliente
            </h1>
          </div>
          <p className="text-muted-foreground">
            Informações completas do cliente {client.name}
          </p>
        </div>
        {onEdit && (
          <Button onClick={onEdit} icon={<Edit className="h-4 w-4" />}>
            Editar Cliente
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dados Básicos */}
        <Card title="Informações Básicas" icon={<User className="h-5 w-5" />}>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-foreground">
                {client.name}
              </h3>
              {client.person.trade_name && (
                <p className="text-sm text-muted-foreground">
                  Nome fantasia: {client.person.trade_name}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">
                  Documento
                </label>
                <p className="font-mono text-foreground">
                  {formatTaxId(client.tax_id)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {getPersonTypeLabel(client.person_type)}
                </p>
              </div>

              {client.client_code && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Código do Cliente
                  </label>
                  <p className="text-foreground">{client.client_code}</p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-muted-foreground">
                  Status
                </label>
                <div>
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getClientStatusColor(
                      client.status
                    )}`}
                  >
                    {getClientStatusLabel(client.status)}
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-muted-foreground">
                  Criado em
                </label>
                <p className="text-foreground">
                  {formatDate(client.created_at)}
                </p>
              </div>
            </div>

            {/* Dados específicos por tipo */}
            {client.person_type === PersonType.PF && (
              <div className="border-t pt-4">
                <h4 className="font-medium text-foreground mb-2">
                  Dados Pessoais
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {client.person.birth_date && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Data de Nascimento
                      </label>
                      <p className="text-foreground">
                        {formatDate(client.person.birth_date)}
                      </p>
                    </div>
                  )}
                  {client.person.gender && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Gênero
                      </label>
                      <p className="text-foreground">{client.person.gender}</p>
                    </div>
                  )}
                  {client.person.marital_status && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Estado Civil
                      </label>
                      <p className="text-foreground">
                        {client.person.marital_status}
                      </p>
                    </div>
                  )}
                  {client.person.occupation && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Profissão
                      </label>
                      <p className="text-foreground">
                        {client.person.occupation}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {client.person_type === PersonType.PJ && (
              <div className="border-t pt-4">
                <h4 className="font-medium text-foreground mb-2">
                  Dados Empresariais
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {client.person.incorporation_date && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Data de Constituição
                      </label>
                      <p className="text-foreground">
                        {formatDate(client.person.incorporation_date)}
                      </p>
                    </div>
                  )}
                  {client.person.tax_regime && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Regime Tributário
                      </label>
                      <p className="text-foreground">
                        {client.person.tax_regime}
                      </p>
                    </div>
                  )}
                  {client.person.legal_nature && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Natureza Jurídica
                      </label>
                      <p className="text-foreground">
                        {client.person.legal_nature}
                      </p>
                    </div>
                  )}
                  {client.person.website && (
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">
                        Website
                      </label>
                      <a
                        href={client.person.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                      >
                        <Globe className="h-4 w-4" />
                        {client.person.website}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Estabelecimento */}
        <Card title="Estabelecimento" icon={<Building2 className="h-5 w-5" />}>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-foreground">
                {client.establishment_name}
              </h3>
              <p className="text-sm text-muted-foreground">
                Código: {client.establishment_code}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Empresa
              </label>
              <p className="text-foreground">{client.company_name}</p>
              <p className="text-sm text-muted-foreground">
                ID da Empresa: {client.company_id}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Contatos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Telefones */}
        <Card title="Telefones" icon={<Phone className="h-5 w-5" />}>
          <div className="space-y-3">
            {client.phones.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Nenhum telefone cadastrado
              </p>
            ) : (
              client.phones.map((phone, index) => (
                <div
                  key={index}
                  className="border-b last:border-b-0 pb-3 last:pb-0"
                >
                  <p className="font-medium">
                    {formatPhone(phone.number, phone.area_code)}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {phone.type}
                    </span>
                    {phone.is_principal && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Principal
                      </span>
                    )}
                    {phone.is_whatsapp && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        WhatsApp
                      </span>
                    )}
                  </div>
                  {phone.description && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {phone.description}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>

        {/* E-mails */}
        <Card title="E-mails" icon={<Mail className="h-5 w-5" />}>
          <div className="space-y-3">
            {client.emails.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Nenhum e-mail cadastrado
              </p>
            ) : (
              client.emails.map((email, index) => (
                <div
                  key={index}
                  className="border-b last:border-b-0 pb-3 last:pb-0"
                >
                  <p className="font-medium break-all">{email.email_address}</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {email.type}
                    </span>
                    {email.is_principal && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Principal
                      </span>
                    )}
                    {email.is_verified && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Verificado
                      </span>
                    )}
                  </div>
                  {email.description && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {email.description}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Endereços */}
        <Card title="Endereços" icon={<MapPin className="h-5 w-5" />}>
          <div className="space-y-3">
            {client.addresses.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Nenhum endereço cadastrado
              </p>
            ) : (
              client.addresses.map((address, index) => (
                <div
                  key={index}
                  className="border-b last:border-b-0 pb-3 last:pb-0"
                >
                  <div className="space-y-1">
                    <p className="font-medium">
                      {address.street}
                      {address.number && `, ${address.number}`}
                    </p>
                    {address.complement && (
                      <p className="text-sm text-muted-foreground">
                        {address.complement}
                      </p>
                    )}
                    <p className="text-sm">
                      {address.neighborhood}, {address.city} - {address.state}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      CEP: {address.zip_code}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {address.type}
                    </span>
                    {address.is_principal && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Principal
                      </span>
                    )}
                  </div>
                  {address.description && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {address.description}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Observações */}
      {client.person.description && (
        <Card title="Observações" icon={<FileText className="h-5 w-5" />}>
          <p className="text-foreground whitespace-pre-wrap">
            {client.person.description}
          </p>
        </Card>
      )}
    </div>
  );
};

export default ClientDetails;
