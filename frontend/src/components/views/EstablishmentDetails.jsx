import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { establishmentsService } from "../../services/api";
import Card from "../ui/Card";
import Button from "../ui/Button";
import {
  getStatusBadge,
  getStatusLabel,
  getPhoneTypeLabel,
  getEmailTypeLabel,
  getAddressTypeLabel,
  formatPhone,
  formatZipCode,
} from "../../utils/statusUtils";
import { formatTaxId } from "../../utils/formatters";
import { notify } from "../../utils/notifications.jsx";
import {
  ArrowLeft,
  Edit,
  Trash2,
  Building,
  User,
  Users,
  Calendar,
  Settings,
  MapPin,
  Phone,
  Mail,
  Clock,
  MessageCircle,
  Send,
  Navigation,
  ExternalLink,
  Activity,
  Shield,
  Briefcase,
} from "lucide-react";

const EstablishmentDetails = ({
  establishmentId,
  onEdit,
  onBack,
  onDelete,
}) => {
  const navigate = useNavigate();
  const [establishment, setEstablishment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("informacoes");

  const loadEstablishment = useCallback(async () => {
    try {
      setLoading(true);
      const data = await establishmentsService.getEstablishment(
        establishmentId
      );

      setEstablishment(data);
    } catch {
      setError("Erro ao carregar estabelecimento");
    } finally {
      setLoading(false);
    }
  }, [establishmentId]);

  useEffect(() => {
    if (establishmentId) {
      loadEstablishment();
    }
  }, [establishmentId, loadEstablishment]);

  const handleAddUser = () => {
    // Navegar para página de usuários com parâmetros para pré-selecionar o estabelecimento
    navigate(
      `/admin/usuarios?establishmentId=${establishmentId}&action=create`
    );
  };

  const handleDelete = async () => {
    const executeDelete = async () => {
      try {
        await establishmentsService.deleteEstablishment(establishmentId);
        notify.success("Estabelecimento excluído com sucesso!");
        onDelete?.();
      } catch {
        notify.error("Erro ao excluir estabelecimento");
      }
    };

    notify.confirmDelete(
      "Excluir Estabelecimento",
      `Tem certeza que deseja excluir o estabelecimento "${
        establishment?.person?.name ||
        establishment?.code ||
        "este estabelecimento"
      }"?`,
      executeDelete
    );
  };

  const openWhatsApp = (phone) => {
    const number = phone.number.replace(/\D/g, "");
    const url = `https://wa.me/${phone.country_code}${number}`;
    window.open(url, "_blank");
  };

  const openEmail = (email) => {
    const url = `mailto:${email.email_address}`;
    window.open(url, "_blank");
  };

  const openGoogleMaps = (address) => {
    const query = encodeURIComponent(
      `${address.street}, ${address.number}, ${address.city}, ${address.state}, ${address.zip_code}, ${address.country}`
    );
    const url = `https://www.google.com/maps/search/?api=1&query=${query}`;
    window.open(url, "_blank");
  };

  const openWaze = (address) => {
    const query = encodeURIComponent(
      `${address.street}, ${address.number}, ${address.city}, ${address.state}`
    );
    const url = `https://waze.com/ul?q=${query}`;
    window.open(url, "_blank");
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">
            Carregando dados do estabelecimento...
          </p>
        </div>
      </div>
    );
  }

  if (error || !establishment) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">
            {error || "Estabelecimento não encontrado"}
          </p>
          <Button onClick={onBack} icon={<ArrowLeft className="h-4 w-4" />}>
            Voltar
          </Button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "informacoes", label: "Informações" },
    { id: "usuarios", label: "Usuários" },
    { id: "configuracoes", label: "Configurações" },
    { id: "equipe", label: "Equipe" },
  ];

  const typeLabels = {
    matriz: "Matriz",
    filial: "Filial",
    unidade: "Unidade",
    posto: "Posto",
  };

  const categoryLabels = {
    clinica: "Clínica",
    hospital: "Hospital",
    laboratorio: "Laboratório",
    farmacia: "Farmácia",
    consultorio: "Consultório",
    upa: "UPA",
    ubs: "UBS",
    outro: "Outro",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            outline
            onClick={onBack}
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {establishment.person?.name || establishment.code}
            </h1>
            <p className="text-muted-foreground">
              {establishment.code} •{" "}
              {typeLabels[establishment.type] || establishment.type}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="primary"
            onClick={() => onEdit?.(establishmentId)}
            icon={<Edit className="h-4 w-4" />}
          >
            Editar
          </Button>
          <Button
            variant="danger"
            outline
            onClick={handleDelete}
            icon={<Trash2 className="h-4 w-4" />}
          >
            Excluir
          </Button>
        </div>
      </div>

      {/* Status Card */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Building className="h-8 w-8 text-blue-600 dark:text-blue-300" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {establishment.person?.name || "Estabelecimento"}
              </h2>
              <p className="text-muted-foreground flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                {categoryLabels[establishment.category] ||
                  establishment.category}
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex gap-2">
              <span
                className={getStatusBadge(
                  establishment.is_active ? "active" : "inactive"
                )}
              >
                {getStatusLabel(
                  establishment.is_active ? "active" : "inactive"
                )}
              </span>
              {establishment.is_principal && (
                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                  Principal
                </span>
              )}
            </div>
            {establishment.created_at && (
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Criado em{" "}
                {new Date(establishment.created_at).toLocaleDateString("pt-BR")}
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="overflow-x-auto">
          <div className="flex space-x-4 sm:space-x-8 min-w-max">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "informacoes" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Informações Principais */}
          <div className="lg:col-span-2 space-y-6">
            {/* Dados Básicos */}
            <Card title="Dados do Estabelecimento">
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Nome
                    </div>
                    <p className="text-foreground font-medium">
                      {establishment.person?.name || "Não informado"}
                    </p>
                  </div>
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Código
                    </div>
                    <p className="text-foreground font-mono text-sm">
                      {establishment.code}
                    </p>
                  </div>
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      CNPJ
                    </div>
                    <p className="text-foreground font-mono text-sm">
                      {establishment.person?.tax_id
                        ? formatTaxId(establishment.person.tax_id)
                        : "Não informado"}
                    </p>
                  </div>
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Status
                    </div>
                    <span
                      className={getStatusBadge(
                        establishment.is_active ? "active" : "inactive"
                      )}
                    >
                      {getStatusLabel(
                        establishment.is_active ? "active" : "inactive"
                      )}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Tipo
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                      {typeLabels[establishment.type] || establishment.type}
                    </span>
                  </div>
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Categoria
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 capitalize">
                      {categoryLabels[establishment.category] ||
                        establishment.category}
                    </span>
                  </div>
                </div>

                {establishment.person?.description && (
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Observações
                    </div>
                    <p className="text-foreground text-sm">
                      {establishment.person.description}
                    </p>
                  </div>
                )}
              </div>
            </Card>

            {/* Telefones */}
            {establishment.phones && establishment.phones.length > 0 && (
              <Card title="Telefones">
                <div className="space-y-4">
                  {establishment.phones.map((phone, index) => (
                    <div
                      key={phone.id || index}
                      className="p-3 bg-muted/30 rounded-lg"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <Phone className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-foreground">
                            {formatPhone(phone)}
                          </p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{getPhoneTypeLabel(phone.type)}</span>
                            {phone.is_principal && (
                              <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                                Principal
                              </span>
                            )}
                            {phone.is_whatsapp && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                                WhatsApp
                              </span>
                            )}
                          </div>

                          {phone.is_whatsapp && (
                            <div className="mt-3">
                              <button
                                onClick={() => openWhatsApp(phone)}
                                className="flex items-center justify-center gap-2 w-full p-3 bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:hover:bg-green-900/50 text-green-700 dark:text-green-300 rounded-lg transition-colors"
                              >
                                <MessageCircle className="h-5 w-5" />
                                <span className="text-sm font-medium">
                                  Abrir no WhatsApp
                                </span>
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* E-mails */}
            {establishment.emails && establishment.emails.length > 0 && (
              <Card title="E-mails">
                <div className="space-y-4">
                  {establishment.emails.map((email, index) => (
                    <div
                      key={email.id || index}
                      className="p-3 bg-muted/30 rounded-lg"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                          <Mail className="h-4 w-4 text-green-600 dark:text-green-300" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-foreground break-all">
                            {email.email_address}
                          </p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{getEmailTypeLabel(email.type)}</span>
                            {email.is_principal && (
                              <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                                Principal
                              </span>
                            )}
                          </div>

                          <div className="mt-3">
                            <button
                              onClick={() => openEmail(email)}
                              className="flex items-center justify-center gap-2 w-full p-3 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-lg transition-colors"
                            >
                              <Send className="h-5 w-5" />
                              <span className="text-sm font-medium">
                                Enviar Email
                              </span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Endereços */}
            {establishment.addresses && establishment.addresses.length > 0 && (
              <Card title="Endereços">
                <div className="space-y-4">
                  {establishment.addresses.map((address, index) => (
                    <div
                      key={address.id || index}
                      className="p-4 bg-muted/30 rounded-lg"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                          <MapPin className="h-4 w-4 text-orange-600 dark:text-orange-300" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-foreground">
                              {getAddressTypeLabel(address.type)}
                            </span>
                            {address.is_principal && (
                              <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                                Principal
                              </span>
                            )}
                          </div>
                          <p className="text-foreground">
                            {address.street}
                            {address.number && `, ${address.number}`}
                            {address.details && ` - ${address.details}`}
                          </p>
                          <p className="text-foreground">
                            {address.neighborhood}, {address.city} -{" "}
                            {address.state}
                          </p>
                          <p className="text-muted-foreground">
                            CEP: {formatZipCode(address.zip_code)}
                            {address.country &&
                              address.country !== "Brasil" &&
                              ` - ${address.country}`}
                          </p>

                          <div className="mt-3">
                            <div className="grid grid-cols-2 gap-2">
                              <button
                                onClick={() => openGoogleMaps(address)}
                                className="flex items-center justify-center gap-2 p-3 bg-red-100 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-700 dark:text-red-300 rounded-lg transition-colors"
                              >
                                <Navigation className="h-5 w-5" />
                                <span className="text-sm font-medium">
                                  Maps
                                </span>
                              </button>
                              <button
                                onClick={() => openWaze(address)}
                                className="flex items-center justify-center gap-2 p-3 bg-purple-100 hover:bg-purple-200 dark:bg-purple-900/30 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300 rounded-lg transition-colors"
                              >
                                <ExternalLink className="h-5 w-5" />
                                <span className="text-sm font-medium">
                                  Waze
                                </span>
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Informações da Empresa */}
            <Card title="Empresa">
              <div className="space-y-4">
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Nome
                  </div>
                  <p className="text-foreground font-medium">
                    {establishment.company_name || "Não informado"}
                  </p>
                </div>

                {establishment.company_tax_id && (
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      CNPJ
                    </div>
                    <p className="text-foreground font-mono text-sm">
                      {formatTaxId(establishment.company_tax_id)}
                    </p>
                  </div>
                )}

                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    ID da Empresa
                  </div>
                  <p className="text-foreground font-mono text-sm">
                    {establishment.company_id}
                  </p>
                </div>
              </div>
            </Card>

            {/* Resumo */}
            <Card title="Resumo">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Usuários</span>
                  <span className="font-medium text-foreground">
                    {establishment.user_count || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Profissionais</span>
                  <span className="font-medium text-foreground">
                    {establishment.professional_count || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Clientes</span>
                  <span className="font-medium text-foreground">
                    {establishment.client_count || 0}
                  </span>
                </div>
              </div>
            </Card>

            {/* Detalhes Técnicos */}
            <Card title="Detalhes">
              <div className="space-y-4">
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    ID do Estabelecimento
                  </div>
                  <p className="text-foreground font-mono text-sm">
                    {establishment.id}
                  </p>
                </div>

                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Data de Criação
                  </div>
                  <p className="text-foreground text-sm">
                    {establishment.created_at
                      ? new Date(establishment.created_at).toLocaleDateString(
                          "pt-BR"
                        )
                      : "Não informado"}
                  </p>
                </div>

                {establishment.updated_at && (
                  <div>
                    <div className="block text-sm font-medium text-muted-foreground mb-1">
                      Última Atualização
                    </div>
                    <p className="text-foreground text-sm">
                      {new Date(establishment.updated_at).toLocaleDateString(
                        "pt-BR"
                      )}
                    </p>
                  </div>
                )}

                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Ordem de Exibição
                  </div>
                  <p className="text-foreground text-sm">
                    {establishment.display_order || 0}
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {activeTab === "usuarios" && (
        <Card
          title="Usuários do Estabelecimento"
          icon={<Users className="h-5 w-5" />}
        >
          <div className="space-y-6">
            {/* Resumo de Usuários */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Total
                    </p>
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {establishment.user_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                    <Activity className="h-6 w-6 text-green-600 dark:text-green-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Ativos
                    </p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {establishment.active_user_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <Shield className="h-6 w-6 text-purple-600 dark:text-purple-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Administradores
                    </p>
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {establishment.admin_user_count || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Lista de Usuários */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-foreground">
                  Usuários Cadastrados
                </h3>
                <Button size="sm" variant="primary" onClick={handleAddUser}>
                  <User className="h-4 w-4 mr-2" />
                  Adicionar Usuário
                </Button>
              </div>

              {establishment.users && establishment.users.length > 0 ? (
                <div className="space-y-3">
                  {establishment.users.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <User className="h-5 w-5 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {user.person_name || user.email}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {user.email} •{" "}
                            {user.role_display_name || user.role_name}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.is_active
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                          }`}
                        >
                          {user.is_active ? "Ativo" : "Inativo"}
                        </span>
                        {user.is_system_admin && (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                            Admin
                          </span>
                        )}
                        <Button size="sm" variant="secondary" outline>
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-muted/30 rounded-lg">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground/50" />
                  <h3 className="mt-4 text-lg font-medium text-foreground">
                    Nenhum usuário encontrado
                  </h3>
                  <p className="mt-2 text-muted-foreground">
                    Este estabelecimento ainda não possui usuários cadastrados.
                  </p>
                  <Button
                    className="mt-4"
                    variant="primary"
                    onClick={handleAddUser}
                  >
                    <User className="h-4 w-4 mr-2" />
                    Adicionar Primeiro Usuário
                  </Button>
                </div>
              )}
            </div>

            {/* Permissões e Acessos */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Controle de Acesso
              </h3>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-foreground mb-2">
                      Perfis Disponíveis
                    </h4>
                    <div className="space-y-2">
                      {["Administrador", "Gestor", "Operador", "Consulta"].map(
                        (role, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between"
                          >
                            <span className="text-sm text-muted-foreground">
                              {role}
                            </span>
                            <span className="text-sm font-medium text-foreground">
                              {Math.floor(Math.random() * 5)}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground mb-2">
                      Últimos Acessos
                    </h4>
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">
                        Sistema em desenvolvimento...
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {activeTab === "configuracoes" && (
        <Card
          title="Configurações do Estabelecimento"
          icon={<Settings className="h-5 w-5" />}
        >
          <div className="space-y-6">
            {/* Configurações Gerais */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Configurações Gerais
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card title="Status e Visibilidade">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Status do estabelecimento
                      </span>
                      <span
                        className={getStatusBadge(
                          establishment.is_active ? "active" : "inactive"
                        )}
                      >
                        {getStatusLabel(
                          establishment.is_active ? "active" : "inactive"
                        )}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Estabelecimento principal
                      </span>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          establishment.is_principal
                            ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                            : "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400"
                        }`}
                      >
                        {establishment.is_principal ? "Sim" : "Não"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Ordem de exibição
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.display_order || 0}
                      </span>
                    </div>
                  </div>
                </Card>

                <Card title="Informações de Contato">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Telefones cadastrados
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.phones?.length || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        E-mails cadastrados
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.emails?.length || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Endereços cadastrados
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.addresses?.length || 0}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>

            {/* Configurações Avançadas */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Configurações Avançadas
              </h3>
              <div className="bg-muted/30 p-6 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-foreground mb-3 flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Segurança
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Autenticação 2FA
                        </span>
                        <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded">
                          Não configurado
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Backup automático
                        </span>
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                          Ativo
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-3 flex items-center gap-2">
                      <Briefcase className="h-4 w-4" />
                      Operacional
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Horário de funcionamento
                        </span>
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                          08:00 - 18:00
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Agendamento online
                        </span>
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                          Habilitado
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-border">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-4">
                      Configurações detalhadas e personalizações específicas do
                      estabelecimento serão implementadas em futuras
                      atualizações.
                    </p>
                    <Button variant="primary" size="sm">
                      <Settings className="h-4 w-4 mr-2" />
                      Configurar Estabelecimento
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Histórico de Alterações */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Histórico
              </h3>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                        <Clock className="h-4 w-4 text-green-600 dark:text-green-300" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          Estabelecimento criado
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {establishment.created_at
                            ? new Date(
                                establishment.created_at
                              ).toLocaleDateString("pt-BR")
                            : "Data não informada"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {establishment.updated_at && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <Edit className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            Última modificação
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(
                              establishment.updated_at
                            ).toLocaleDateString("pt-BR")}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {activeTab === "equipe" && (
        <Card
          title="Equipe do Estabelecimento"
          icon={<User className="h-5 w-5" />}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <User className="h-8 w-8 text-blue-600" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">
                      Usuários
                    </p>
                    <p className="text-2xl font-bold text-blue-600">
                      {establishment.user_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <User className="h-8 w-8 text-green-600" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">
                      Profissionais
                    </p>
                    <p className="text-2xl font-bold text-green-600">
                      {establishment.professional_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center">
                  <User className="h-8 w-8 text-purple-600" />
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">
                      Clientes
                    </p>
                    <p className="text-2xl font-bold text-purple-600">
                      {establishment.client_count || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center py-8">
              <p className="text-sm text-gray-500">
                Detalhes da equipe do estabelecimento ainda não foram
                implementados.
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default EstablishmentDetails;
