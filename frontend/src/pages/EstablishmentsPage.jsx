import React, { useState, useEffect } from "react";
import { useSearchParams, useParams, useNavigate } from "react-router-dom";
import { establishmentsService, companiesService } from "../services/api";
import { PageErrorBoundary } from "../components/error";
import { DataTableTemplate } from "../components/shared/DataTable/DataTableTemplate";
import { useDataTable } from "../hooks/useDataTable";
import { createEstablishmentsConfig } from "../config/tables/establishments.config";
import EstablishmentForm from "../components/forms/EstablishmentForm";
import EstablishmentDetails from "../components/views/EstablishmentDetails";
import { notify } from "../utils/notifications.jsx";

const EstablishmentsPage = () => {
  return (
    <PageErrorBoundary pageName="Estabelecimentos">
      <EstablishmentsPageContent />
    </PageErrorBoundary>
  );
};

const EstablishmentsPageContent = () => {
  const [searchParams] = useSearchParams();
  const { id } = useParams();
  const navigate = useNavigate();
  const [establishments, setEstablishments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'edit', 'details'
  const [selectedEstablishmentId, setSelectedEstablishmentId] = useState(null);

  // Get companyId from URL parameters
  const companyIdFromUrl = searchParams.get("companyId");

  // Action handlers
  const handleToggleStatus = async (establishmentId, newStatus) => {
    const establishment = establishments.find((e) => e.id === establishmentId);
    const establishmentName =
      establishment?.person?.name ||
      establishment?.code ||
      "este estabelecimento";
    const action = newStatus ? "ativar" : "inativar";

    const executeToggle = async () => {
      try {
        await establishmentsService.toggleEstablishmentStatus(
          establishmentId,
          newStatus
        );
        notify.success(
          `Estabelecimento ${
            action === "ativar" ? "ativado" : "inativado"
          } com sucesso!`
        );

        // Atualizar estado local sem reload
        setEstablishments((prev) =>
          prev.map((est) =>
            est.id === establishmentId ? { ...est, is_active: newStatus } : est
          )
        );
      } catch (err) {
        notify.error(`Erro ao ${action} estabelecimento`);
      }
    };

    notify.confirm(
      `${action === "ativar" ? "Ativar" : "Inativar"} Estabelecimento`,
      `Tem certeza que deseja ${action} o estabelecimento "${establishmentName}"?`,
      executeToggle
    );
  };

  const handleDelete = async (establishmentId) => {
    const establishment = establishments.find((e) => e.id === establishmentId);
    const establishmentName =
      establishment?.person?.name ||
      establishment?.code ||
      "este estabelecimento";

    const executeDelete = async () => {
      try {
        await establishmentsService.deleteEstablishment(establishmentId);
        notify.success("Estabelecimento excluído com sucesso!");

        // Remover do estado local sem reload
        setEstablishments((prev) =>
          prev.filter((est) => est.id !== establishmentId)
        );
      } catch (err) {
        const errorMessage =
          err.response?.data?.detail || err.message || "Erro desconhecido";
        notify.error(`Erro ao excluir estabelecimento: ${errorMessage}`);
      }
    };

    notify.confirmDelete(
      "Excluir Estabelecimento",
      `Tem certeza que deseja excluir o estabelecimento "${establishmentName}"?`,
      executeDelete
    );
  };

  // Create config with navigation and action handlers
  const config = createEstablishmentsConfig(navigate, {
    onToggleStatus: handleToggleStatus,
    onDelete: handleDelete,
  });

  // Initialize data table hook
  const tableData = useDataTable({
    config,
    initialData: establishments,
  });

  // Load establishments data
  useEffect(() => {
    const loadEstablishments = async () => {
      try {
        console.log("🚀 Iniciando carregamento de estabelecimentos...");
        setLoading(true);

        // Carregamento direto e otimizado de estabelecimentos
        console.log("🏥 Carregando estabelecimentos diretamente...");

        const establishmentsResponse =
          await establishmentsService.getEstablishments({
            page: 1,
            size: 100, // Máximo permitido pelo backend
            is_active: undefined, // Não filtrar por status aqui
          });

        console.log(
          "✅ Resposta dos estabelecimentos:",
          establishmentsResponse
        );

        // Normalizar estrutura da resposta
        let establishmentsList = [];
        if (
          establishmentsResponse?.establishments &&
          Array.isArray(establishmentsResponse.establishments)
        ) {
          establishmentsList = establishmentsResponse.establishments;
        } else if (
          establishmentsResponse?.data &&
          Array.isArray(establishmentsResponse.data)
        ) {
          establishmentsList = establishmentsResponse.data;
        } else if (Array.isArray(establishmentsResponse)) {
          establishmentsList = establishmentsResponse;
        }

        console.log(
          "🏥 Estabelecimentos carregados:",
          establishmentsList.length
        );
        setEstablishments(establishmentsList);
      } catch (err) {
        console.error("❌ Erro ao carregar estabelecimentos:", err);
        setEstablishments([]);
      } finally {
        console.log("✅ Finalizando carregamento, loading = false");
        setLoading(false);
      }
    };

    loadEstablishments();
  }, []);

  // Verificar parâmetros da URL ao carregar a página
  useEffect(() => {
    const actionParam = searchParams.get("action");
    const establishmentIdParam = searchParams.get("establishmentId");

    console.log("🔍 Parâmetros da URL:", {
      actionParam,
      establishmentIdParam,
      id,
    });

    // Prioridade: ID direto na URL (route param)
    if (id) {
      console.log("🔍 ID do estabelecimento detectado na URL (route):", id);
      setSelectedEstablishmentId(parseInt(id));
      setCurrentView("details");
    }
    // Segundo: ação de edição com ID nos query params
    else if (actionParam === "edit" && establishmentIdParam) {
      console.log("🔍 Ação de edição detectada na URL:", establishmentIdParam);
      setSelectedEstablishmentId(parseInt(establishmentIdParam));
      setCurrentView("edit");
    }
    // Terceiro: ação de criação
    else if (actionParam === "create") {
      console.log("🔍 Ação de criação detectada na URL");
      setSelectedEstablishmentId(null);
      setCurrentView("create");
    }
    // Padrão: listagem
    else {
      console.log("🔍 Exibindo listagem padrão");
      setCurrentView("list");
      setSelectedEstablishmentId(null);
    }
  }, [searchParams, id]);

  const handleCreate = () => {
    setSelectedEstablishmentId(null);
    setCurrentView("create");
  };

  const handleEdit = (establishmentId) => {
    setSelectedEstablishmentId(establishmentId);
    setCurrentView("edit");
  };

  const handleView = (establishmentId) => {
    setSelectedEstablishmentId(establishmentId);
    setCurrentView("details");
  };

  const handleSave = async () => {
    console.log("💾 Salvamento concluído, recarregando dados...");
    setCurrentView("list");
    setSelectedEstablishmentId(null);

    // Recarregar dados sem refresh da página
    try {
      setLoading(true);
      const establishmentsResponse =
        await establishmentsService.getEstablishments({
          page: 1,
          size: 100,
          is_active: undefined,
        });

      let establishmentsList = [];
      if (
        establishmentsResponse?.establishments &&
        Array.isArray(establishmentsResponse.establishments)
      ) {
        establishmentsList = establishmentsResponse.establishments;
      } else if (
        establishmentsResponse?.data &&
        Array.isArray(establishmentsResponse.data)
      ) {
        establishmentsList = establishmentsResponse.data;
      } else if (Array.isArray(establishmentsResponse)) {
        establishmentsList = establishmentsResponse;
      }

      setEstablishments(establishmentsList);
      console.log("✅ Dados recarregados com sucesso");
    } catch (err) {
      console.error("❌ Erro ao recarregar dados:", err);
      // Fallback para reload se der erro
      window.location.reload();
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setCurrentView("list");
    setSelectedEstablishmentId(null);
  };

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    return (
      <EstablishmentForm
        establishmentId={
          currentView === "edit" ? selectedEstablishmentId : null
        }
        companyId={
          currentView === "create"
            ? companyIdFromUrl
              ? parseInt(companyIdFromUrl)
              : undefined
            : undefined
        }
        onSave={handleSave}
        onCancel={handleCancel}
        onNavigateToClients={(establishmentId, establishmentCode) => {
          // Navegar para página de clientes com estabelecimento pré-selecionado
          navigate(
            `/admin/clientes?establishmentId=${establishmentId}&establishmentCode=${establishmentCode}&action=create`
          );
        }}
      />
    );
  }

  if (currentView === "details") {
    return (
      <EstablishmentDetails
        establishmentId={selectedEstablishmentId}
        onEdit={handleEdit}
        onBack={handleCancel}
        onDelete={() => {
          handleDelete(selectedEstablishmentId);
          handleCancel();
        }}
      />
    );
  }

  // Debug final render
  console.log("🔍 Debug render final:", {
    loading,
    establishments: establishments.length,
    tableDataLength: tableData?.state?.data?.length || 0,
    filteredDataLength: tableData?.state?.filteredData?.length || 0,
    currentView,
  });

  // Loading state
  if (loading) {
    console.log("🔄 Renderizando loading state");
    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 relative shadow-md sm:rounded-lg overflow-hidden">
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-300">
              Carregando estabelecimentos...
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Check if no data and show appropriate message
  if (!loading && establishments.length === 0) {
    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 relative shadow-md sm:rounded-lg overflow-hidden">
          <div className="flex flex-col items-center justify-center p-12 text-center">
            <div className="w-16 h-16 mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Nenhum estabelecimento encontrado
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6 max-w-md">
              Não foram encontrados estabelecimentos cadastrados no sistema.
              Cadastre o primeiro estabelecimento para começar.
            </p>
            <button
              onClick={() => setCurrentView("create")}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Cadastrar Primeiro Estabelecimento
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main list view using DataTableTemplate
  console.log("📋 Renderizando DataTableTemplate");
  return (
    <div className="space-y-6">
      <DataTableTemplate config={config} tableData={tableData} />
    </div>
  );
};

export default EstablishmentsPage;
