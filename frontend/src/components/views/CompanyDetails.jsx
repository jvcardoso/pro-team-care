import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { companiesService, establishmentsService } from "../../services/api";
import Card from "../ui/Card";
import Button from "../ui/Button";
import EntityDetailsLayout from "./EntityDetailsLayout";
import CompanyBasicInfo from "../entities/CompanyBasicInfo";
import ReceitaFederalInfo from "../metadata/ReceitaFederalInfo";
import {
  PhoneDisplayCard,
  EmailDisplayCard,
  AddressDisplayCard,
} from "../contacts";
import {
  getStatusBadge,
  getStatusLabel,
  getPhoneTypeLabel,
  getEmailTypeLabel,
  getAddressTypeLabel,
  formatPhone,
  formatZipCode,
} from "../../utils/statusUtils";
import { notify } from "../../utils/notifications.jsx";
import CompanyBillingCard from "../billing/CompanyBillingCard";
import SubscriptionManagementModal from "../billing/SubscriptionManagementModal";
import CreateInvoiceModal from "../billing/CreateInvoiceModal";
import {
  ArrowLeft,
  Edit,
  Trash2,
  Building,
  Users,
  User,
  Briefcase,
  CreditCard,
  Plus,
} from "lucide-react";
import BillingInfoCard from "../billing/BillingInfoCard";
import { clientsService } from "../../services/clientsService";
import DataTableTemplate from "../shared/DataTable/DataTableTemplate";
import { useDataTable } from "../../hooks/useDataTable";
import { createCompanyClientsConfig } from "../../config/tables/companyClients.config";
import CompanyActivationTab from "../companies/CompanyActivationTab";

const CompanyDetails = ({
  companyId,
  onEdit,
  onBack,
  onDelete,
  initialTab = "informacoes",
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [company, setCompany] = useState(null);
  const [establishments, setEstablishments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(initialTab);
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  const [billingDataKey, setBillingDataKey] = useState(0);
  const [companyStats, setCompanyStats] = useState({
    establishments_count: 0,
    clients_count: 0,
    professionals_count: 0,
  });
  const [clients, setClients] = useState([]);
  const [loadingClients, setLoadingClients] = useState(false);

  // Hook para tabela de clientes
  const clientsDataTableProps = useDataTable({
    config: createCompanyClientsConfig({
      onView: (client) =>
        navigate(`/admin/clientes/${client.id}?tab=informacoes`),
    }),
    initialData: clients,
  });

  // Verificar parâmetro de aba na URL
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (
      tabParam &&
      [
        "informacoes",
        "ativacao",
        "estabelecimentos",
        "clientes",
        "profissionais",
        "pacientes",
        "usuarios",
        "faturamento",
        "lgpd",
      ].includes(tabParam)
    ) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  useEffect(() => {
    if (companyId) {
      loadCompany();
      loadCompanyStats();
    }
  }, [companyId]);

  useEffect(() => {
    if (activeTab === "estabelecimentos" && companyId) {
      loadEstablishments();
    }
  }, [activeTab, companyId]);

  useEffect(() => {
    if (activeTab === "clientes" && companyId) {
      loadClients();
    }
  }, [activeTab, companyId]);

  const loadCompany = async () => {
    try {
      setLoading(true);
      const data = await companiesService.getCompany(companyId);

      if (process.env.NODE_ENV === "development") {
        console.log("CompanyDetails - Estrutura de metadados verificada");
      }

      setCompany(data);

      // Salvar nome da empresa no localStorage para breadcrumb
      if (data?.people?.name) {
        localStorage.setItem(`company_name_${companyId}`, data.people.name);
      }

      setError(null);
    } catch (err) {
      setError("Erro ao carregar empresa");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCompanyStats = async () => {
    try {
      const stats = await companiesService.getCompanyStats(companyId);
      setCompanyStats(stats);
    } catch (err) {
      console.error("Erro ao carregar estatísticas:", err);
    }
  };

  const loadEstablishments = async () => {
    try {
      const response = await establishmentsService.getEstablishmentsByCompany(
        companyId
      );
      const establishmentsData = response?.establishments || response || [];
      setEstablishments(
        Array.isArray(establishmentsData) ? establishmentsData : []
      );
    } catch (err) {
      console.error("Erro ao carregar estabelecimentos:", err);
      setEstablishments([]);
    }
  };

  const loadClients = async () => {
    try {
      setLoadingClients(true);
      const response = await clientsService.getAll({
        page: 1,
        size: 100,
      });
      setClients(response?.clients || []);
    } catch (err) {
      console.error("Erro ao carregar clientes:", err);
      setClients([]);
    } finally {
      setLoadingClients(false);
    }
  };

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    navigate(`/admin/empresas/${companyId}?tab=${newTab}`, { replace: true });
  };

  const handleDelete = async () => {
    const executeDelete = async () => {
      try {
        await companiesService.deleteCompany(companyId);
        notify.success("Empresa excluída com sucesso!");
        onDelete?.();
      } catch (err) {
        notify.error("Erro ao excluir empresa");
        console.error(err);
      }
    };

    notify.confirmDelete(
      "Excluir Empresa",
      `Tem certeza que deseja excluir a empresa "${
        company?.people?.name || "esta empresa"
      }"?`,
      executeDelete
    );
  };

  // Definição de tabs
  const tabs = [
    { key: "informacoes", label: "Informações", shortLabel: "Info" },
    { key: "ativacao", label: "Ativação", shortLabel: "Ativa\u00e7\u00e3o" },
    {
      key: "estabelecimentos",
      label: "Estabelecimentos",
      shortLabel: "Estab.",
    },
    { key: "clientes", label: "Clientes", shortLabel: "Client." },
    { key: "profissionais", label: "Profissionais", shortLabel: "Profis." },
    { key: "pacientes", label: "Pacientes", shortLabel: "Pacient." },
    { key: "usuarios", label: "Usuários", shortLabel: "Users" },
    { key: "faturamento", label: "Faturamento", shortLabel: "Cobrança" },
    { key: "lgpd", label: "LGPD", shortLabel: "LGPD" },
  ];

  // Action buttons
  const actionButtons = [
    {
      label: "Editar",
      onClick: () => onEdit?.(companyId),
      variant: "primary",
      icon: <Edit className="h-4 w-4" />,
    },
    {
      label: "Excluir",
      onClick: handleDelete,
      variant: "danger",
      outline: true,
      icon: <Trash2 className="h-4 w-4" />,
    },
  ];

  // Métricas para cards horizontais
  const metrics = company
    ? [
        {
          icon: <Building className="h-6 w-6" />,
          label: "Estabelecimentos",
          value: companyStats.establishments_count,
          color:
            "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
          onClick: () => handleTabChange("estabelecimentos"),
        },
        {
          icon: <Users className="h-6 w-6" />,
          label: "Clientes",
          value: companyStats.clients_count,
          color:
            "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
          onClick: () => handleTabChange("clientes"),
        },
        {
          icon: <Briefcase className="h-6 w-6" />,
          label: "Profissionais",
          value: companyStats.professionals_count,
          color:
            "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400",
          onClick: () => handleTabChange("profissionais"),
        },
      ]
    : [];

  // Status badge
  const statusBadge = company && (
    <span className={getStatusBadge(company.people.status)}>
      {getStatusLabel(company.people.status)}
    </span>
  );

  return (
    <>
      <EntityDetailsLayout
        title={company?.people?.name || "Carregando..."}
        subtitle={
          company?.people?.trade_name &&
          company.people.trade_name !== company.people.name
            ? company.people.trade_name
            : undefined
        }
        icon={<Building className="h-6 w-6" />}
        statusBadge={statusBadge}
        backButton={{
          onClick: () => navigate("/admin/empresas"),
          label: "Voltar",
        }}
        actionButtons={actionButtons}
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={handleTabChange}
        metrics={metrics}
        loading={loading}
        error={error}
        onRetry={loadCompany}
      >
        {/* Tab: Informações */}
        {activeTab === "informacoes" && company && (
          <div className="space-y-6">
            <CompanyBasicInfo company={company} />

            <PhoneDisplayCard
              phones={company.phones || []}
              formatPhone={formatPhone}
              getPhoneTypeLabel={getPhoneTypeLabel}
            />

            <EmailDisplayCard
              emails={company.emails || []}
              getEmailTypeLabel={getEmailTypeLabel}
            />

            <AddressDisplayCard
              addresses={company.addresses || []}
              getAddressTypeLabel={getAddressTypeLabel}
              formatZipCode={formatZipCode}
            />

            <ReceitaFederalInfo
              metadata={
                company.company?.metadata ||
                company.people?.metadata ||
                company.metadata ||
                {}
              }
            />

            {/* Card de Faturamento */}
            <BillingInfoCard companyId={company.id} />

            {/* Informações do Sistema */}
            <Card title="Informações do Sistema">
              <div className="space-y-4 text-sm">
                <div>
                  <label className="block text-muted-foreground mb-1">
                    ID da Empresa
                  </label>
                  <p className="text-foreground font-mono">#{company.id}</p>
                </div>
                <div>
                  <label className="block text-muted-foreground mb-1">
                    Criado em
                  </label>
                  <p className="text-foreground">
                    {new Date(company.created_at).toLocaleString("pt-BR")}
                  </p>
                </div>
                <div>
                  <label className="block text-muted-foreground mb-1">
                    Atualizado em
                  </label>
                  <p className="text-foreground">
                    {new Date(company.updated_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tab: Ativação */}
        {activeTab === "ativacao" && company && (
          <CompanyActivationTab
            companyId={company.id}
            companyName={company.people?.name || `Empresa ${company.id}`}
          />
        )}

        {/* Tab: Estabelecimentos */}
        {activeTab === "estabelecimentos" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-medium text-foreground">
                  Estabelecimentos da Empresa
                </h3>
                <p className="text-muted-foreground">
                  Gerencie os estabelecimentos vinculados a esta empresa
                </p>
              </div>
              <Button
                onClick={() =>
                  navigate(
                    `/admin/estabelecimentos?companyId=${companyId}&action=create`
                  )
                }
                icon={<Plus className="h-4 w-4" />}
                className="w-full sm:w-auto whitespace-nowrap"
              >
                <span className="hidden sm:inline">Novo Estabelecimento</span>
                <span className="sm:hidden">+ Estabelecimento</span>
              </Button>
            </div>

            {establishments.length === 0 ? (
              <div className="text-center py-12">
                <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">
                  Nenhum estabelecimento encontrado
                </h3>
                <p className="text-muted-foreground mb-6">
                  Esta empresa ainda não possui estabelecimentos cadastrados
                </p>
                <Button
                  onClick={() =>
                    navigate(
                      `/admin/estabelecimentos?companyId=${companyId}&action=create`
                    )
                  }
                  icon={<Plus className="h-4 w-4" />}
                >
                  Criar Primeiro Estabelecimento
                </Button>
              </div>
            ) : (
              <div className="grid gap-4">
                {establishments.map((establishment) => (
                  <Card key={establishment.id} className="p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <Building className="h-5 w-5 text-primary flex-shrink-0" />
                          <div className="min-w-0 flex-1">
                            <h4 className="font-medium text-foreground break-words">
                              {establishment.person?.name || establishment.code}
                            </h4>
                            <p className="text-sm text-muted-foreground">
                              Código: {establishment.code}
                            </p>
                          </div>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="secondary"
                        outline
                        onClick={() =>
                          navigate(
                            `/admin/estabelecimentos/${establishment.id}?tab=informacoes`
                          )
                        }
                      >
                        Ver Detalhes
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab: Clientes */}
        {activeTab === "clientes" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-foreground">
                Clientes da Empresa
              </h3>
              <p className="text-muted-foreground">
                Lista de todos os clientes da empresa em todos os
                estabelecimentos
              </p>
            </div>

            {loadingClients ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <span className="ml-3 text-muted-foreground">
                  Carregando clientes...
                </span>
              </div>
            ) : (
              <DataTableTemplate
                config={createCompanyClientsConfig({
                  onView: (client) =>
                    navigate(`/admin/clientes/${client.id}?tab=informacoes`),
                })}
                tableData={clientsDataTableProps}
              />
            )}
          </div>
        )}

        {/* Tab: Profissionais */}
        {activeTab === "profissionais" && (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Profissionais
            </h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os profissionais desta empresa
            </p>
          </div>
        )}

        {/* Tab: Pacientes */}
        {activeTab === "pacientes" && (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Pacientes
            </h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os pacientes desta empresa
            </p>
          </div>
        )}

        {/* Tab: Usuários */}
        {activeTab === "usuarios" && (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Usuários
            </h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os usuários desta empresa
            </p>
          </div>
        )}

        {/* Tab: Faturamento */}
        {activeTab === "faturamento" && company && (
          <div className="space-y-6">
            <CompanyBillingCard
              key={billingDataKey}
              company={{
                id: company.id,
                name:
                  company.name ||
                  company.people?.name ||
                  `Empresa ${company.id}`,
                tax_id: company.people?.tax_id,
              }}
              onCreateSubscription={() => {
                setSelectedSubscription(null);
                setShowSubscriptionModal(true);
              }}
              onManageSubscription={(subscription) => {
                setSelectedSubscription(subscription);
                setShowSubscriptionModal(true);
              }}
              onCreateInvoice={(companyId, subscription) => {
                setSelectedSubscription(subscription);
                setShowInvoiceModal(true);
              }}
            />
          </div>
        )}

        {/* Tab: LGPD */}
        {activeTab === "lgpd" && (
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-foreground mb-2">LGPD</h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie as configurações de privacidade e LGPD
            </p>
          </div>
        )}
      </EntityDetailsLayout>

      {/* Modais */}
      {company && (
        <>
          <SubscriptionManagementModal
            isOpen={showSubscriptionModal}
            onClose={() => setShowSubscriptionModal(false)}
            company={{
              id: company.id,
              name: company.people?.name || `Empresa ${company.id}`,
              tax_id: company.people?.tax_id,
            }}
            subscription={selectedSubscription}
            onSuccess={() => {
              setShowSubscriptionModal(false);
              setSelectedSubscription(null);
              setBillingDataKey((prev) => prev + 1);
              loadCompany();
            }}
          />

          <CreateInvoiceModal
            isOpen={showInvoiceModal}
            onClose={() => setShowInvoiceModal(false)}
            companyId={company.id}
            companyName={company.people?.name || `Empresa ${company.id}`}
            subscription={selectedSubscription}
            onSuccess={() => {
              setShowInvoiceModal(false);
              setSelectedSubscription(null);
              setBillingDataKey((prev) => prev + 1);
              loadCompany();
            }}
          />
        </>
      )}
    </>
  );
};

export default CompanyDetails;
