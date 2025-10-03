/**
 * Company Details Component
 * Mostra os detalhes completos de uma empresa específica
 */

import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import {
  Building,
  Phone,
  Mail,
  MapPin,
  Calendar,
  ArrowLeft,
  Edit,
  Trash2,
  User,
  Globe,
  Plus,
} from "lucide-react";
import { Company } from "../../types/company.types";
import Card from "../ui/Card";
import Button from "../ui/Button";
import EntityDetailsLayout from "./EntityDetailsLayout";
import { establishmentsService } from "../../services/api";
import { notify } from "../../utils/notifications.jsx";

const CompanyDetailsNew: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [company, setCompany] = useState<Company | null>(null);
  const [establishments, setEstablishments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("informacoes");

  // Verificar aba da URL
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (
      tabParam &&
      [
        "informacoes",
        "estabelecimentos",
        "clientes",
        "profissionais",
        "pacientes",
        "usuarios",
        "lgpd",
      ].includes(tabParam)
    ) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  useEffect(() => {
    const fetchCompany = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        const { companiesService } = await import("../../services/api");
        const companyData = await companiesService.getCompany(parseInt(id));
        setCompany(companyData);
      } catch (err: any) {
        setError(err.message || "Erro ao carregar empresa");
      } finally {
        setLoading(false);
      }
    };

    fetchCompany();
  }, [id]);

  useEffect(() => {
    if (activeTab === "estabelecimentos" && id) {
      loadEstablishments();
    }
  }, [activeTab, id]);

  const loadEstablishments = async () => {
    try {
      const response = await establishmentsService.getEstablishmentsByCompany(
        parseInt(id)
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

  const handleBack = () => {
    navigate("/admin/empresas");
  };

  const handleEdit = () => {
    navigate(`/admin/empresas?companyId=${id}&action=edit`);
  };

  const handleDelete = async () => {
    if (!company) return;

    const executeDelete = async () => {
      try {
        const { companiesService } = await import("../../services/api");
        await companiesService.deleteCompany(parseInt(id));
        notify.success("Empresa excluída com sucesso!");
        navigate("/admin/empresas");
      } catch (err) {
        notify.error("Erro ao excluir empresa");
        console.error(err);
      }
    };

    notify.confirmDelete(
      "Excluir Empresa",
      `Tem certeza que deseja excluir a empresa "${company.name}"?\n\nEsta ação não pode ser desfeita.`,
      executeDelete
    );
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded dark:bg-gray-700 w-96 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-64 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-24 bg-gray-200 rounded dark:bg-gray-700"
              ></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded dark:bg-red-900/20 dark:border-red-900 dark:text-red-400">
          <h3 className="font-semibold">Erro ao carregar empresa</h3>
          <p>{error}</p>
        </div>
        <button
          onClick={handleBack}
          className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-blue-100 rounded-lg hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Voltar para lista
        </button>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full mb-4">
            <Building className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Empresa não encontrada
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            A empresa com ID {id} não foi encontrada.
          </p>
          <button
            onClick={handleBack}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-blue-100 rounded-lg hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar para lista
          </button>
        </div>
      </div>
    );
  }

  const statusBadge = (
    <span
      className={`px-2 py-1 text-xs rounded whitespace-nowrap ${
        company.status === "active"
          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
          : company.status === "inactive"
          ? "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300"
          : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
      }`}
    >
      {company.status === "active"
        ? "Ativo"
        : company.status === "inactive"
        ? "Inativo"
        : "Suspenso"}
    </span>
  );

  const metrics = [
    {
      icon: <Building className="h-5 w-5 text-blue-600" />,
      label: "Estabelecimentos",
      value: establishments.length.toString(),
    },
    {
      icon: <User className="h-5 w-5 text-green-600" />,
      label: "Clientes",
      value: "Em breve",
    },
    {
      icon: <User className="h-5 w-5 text-purple-600" />,
      label: "Profissionais",
      value: "Em breve",
    },
    {
      icon: <User className="h-5 w-5 text-orange-600" />,
      label: "Pacientes",
      value: "Em breve",
    },
  ];

  const tabs = [
    { key: "informacoes", label: "Informações", shortLabel: "Info" },
    { key: "estabelecimentos", label: "Estabelecimentos", shortLabel: "Estab." },
    { key: "clientes", label: "Clientes", shortLabel: "Client." },
    { key: "profissionais", label: "Profissionais", shortLabel: "Profis." },
    { key: "pacientes", label: "Pacientes", shortLabel: "Pacient." },
    { key: "usuarios", label: "Usuários", shortLabel: "Users" },
    { key: "lgpd", label: "LGPD" },
  ];

  const actionButtons = [
    {
      label: "Editar",
      onClick: handleEdit,
      icon: <Edit className="h-4 w-4" />,
    },
    {
      label: "Excluir",
      onClick: handleDelete,
      variant: "danger" as const,
      outline: true,
      icon: <Trash2 className="h-4 w-4" />,
    },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case "informacoes":
        return (
          <div className="space-y-6">
            <Card title="Informações Básicas">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">
                      ID
                    </label>
                    <p className="text-foreground font-mono">#{company.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">
                      CNPJ
                    </label>
                    <p className="text-foreground font-mono">
                      {company.tax_id}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">
                      Criado em
                    </label>
                    <p className="text-foreground">
                      {new Date(company.created_at).toLocaleString("pt-BR")}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">
                      Atualizado em
                    </label>
                    <p className="text-foreground">
                      {new Date(
                        company.updated_at || company.created_at
                      ).toLocaleString("pt-BR")}
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Contatos */}
            <Card title="Contatos">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center">
                    <Phone className="w-5 h-5 mr-3 text-blue-600" />
                    <span className="text-foreground">Telefones</span>
                  </div>
                  <span className="text-2xl font-bold text-blue-600">
                    {company.phones_count || 0}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center">
                    <Mail className="w-5 h-5 mr-3 text-green-600" />
                    <span className="text-foreground">Emails</span>
                  </div>
                  <span className="text-2xl font-bold text-green-600">
                    {company.emails_count || 0}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center">
                    <MapPin className="w-5 h-5 mr-3 text-purple-600" />
                    <span className="text-foreground">Endereços</span>
                  </div>
                  <span className="text-2xl font-bold text-purple-600">
                    {company.addresses_count || 0}
                  </span>
                </div>
              </div>
            </Card>
          </div>
        );

      case "estabelecimentos":
        return (
          <div className="space-y-6">
            {/* Header com botão Novo Estabelecimento */}
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
                onClick={() => {
                  navigate(
                    `/admin/estabelecimentos?companyId=${id}&action=create`
                  );
                }}
                icon={<Plus className="h-4 w-4" />}
                className="w-full sm:w-auto whitespace-nowrap"
              >
                <span className="hidden sm:inline">Novo Estabelecimento</span>
                <span className="sm:hidden">+ Estabelecimento</span>
              </Button>
            </div>

            {/* Lista de Estabelecimentos */}
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
                  onClick={() => {
                    navigate(
                      `/admin/estabelecimentos?companyId=${id}&action=create`
                    );
                  }}
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
                            {establishment.person?.tax_id && (
                              <p className="text-sm text-muted-foreground break-all">
                                CNPJ: {establishment.person.tax_id}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2">
                        <div className="flex flex-wrap gap-2">
                          <span
                            className={`px-2 py-1 text-xs rounded whitespace-nowrap ${
                              establishment.is_active
                                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
                                : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            }`}
                          >
                            {establishment.is_active ? "Ativo" : "Inativo"}
                          </span>
                          {establishment.is_principal && (
                            <span className="px-2 py-1 text-xs bg-primary/10 text-primary rounded whitespace-nowrap">
                              Principal
                            </span>
                          )}
                        </div>
                        <Button
                          size="sm"
                          variant="secondary"
                          outline
                          onClick={() => {
                            navigate(
                              `/admin/estabelecimentos/${establishment.id}?tab=informacoes`
                            );
                          }}
                          className="w-full sm:w-auto whitespace-nowrap"
                        >
                          Ver Detalhes
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        );

      case "clientes":
        return (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">Clientes</h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os clientes desta empresa
            </p>
          </div>
        );

      case "profissionais":
        return (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Profissionais
            </h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os profissionais desta empresa
            </p>
          </div>
        );

      case "pacientes":
        return (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Pacientes
            </h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os pacientes desta empresa
            </p>
          </div>
        );

      case "usuarios":
        return (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">Usuários</h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie os usuários desta empresa
            </p>
          </div>
        );

      case "lgpd":
        return (
          <div className="text-center py-12">
            <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">LGPD</h3>
            <p className="text-muted-foreground">
              Em breve: Gerencie as configurações de privacidade e LGPD
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <EntityDetailsLayout
      title={company.name}
      subtitle={company.trade_name && company.trade_name !== company.name ? company.trade_name : undefined}
      icon={<Building className="h-6 w-6" />}
      statusBadge={statusBadge}
      backButton={{ onClick: handleBack }}
      actionButtons={actionButtons}
      metrics={metrics}
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      loading={loading}
      error={error}
    >
      {renderTabContent()}
    </EntityDetailsLayout>
  );
};

export default CompanyDetailsNew;
