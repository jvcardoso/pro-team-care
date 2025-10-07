import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  medicalAuthorizationsService,
  MedicalAuthorization,
  MedicalAuthorizationListParams,
  MedicalAuthorizationCreate,
} from "../services/medicalAuthorizationsService";
import { PageErrorBoundary } from "../components/error";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import ActionDropdown from "../components/ui/ActionDropdown";
import { notify } from "../utils/notifications.jsx";
import {
  Heart,
  Search,
  Filter,
  Eye,
  Edit,
  Plus,
  Calendar,
  Clock,
  User,
  FileText,
  AlertCircle,
  CheckCircle,
  XCircle,
  Pause,
  RotateCcw,
  Activity,
  ArrowLeft,
  Save,
  Trash2,
  RefreshCw,
  Stethoscope,
  Check,
  Ban,
} from "lucide-react";

const MedicalAuthorizationsPage: React.FC = () => {
  return (
    <PageErrorBoundary pageName="Autorizações Médicas">
      <MedicalAuthorizationsPageContent />
    </PageErrorBoundary>
  );
};

const MedicalAuthorizationsPageContent: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();

  const [authorizations, setAuthorizations] = useState<MedicalAuthorization[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("todas");
  const [filterUrgency, setFilterUrgency] = useState<string>("todas");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingAuth, setEditingAuth] = useState<MedicalAuthorization | null>(
    null
  );
  const [viewingAuth, setViewingAuth] = useState<MedicalAuthorization | null>(
    null
  );
  const [showDetails, setShowDetails] = useState(false);

  // Form data for creating/editing authorizations
  const [formData, setFormData] = useState<MedicalAuthorizationCreate>({
    contract_life_id: 0,
    service_id: 0,
    doctor_id: 0,
    authorization_date: new Date().toISOString().split("T")[0],
    valid_from: new Date().toISOString().split("T")[0],
    valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0], // 30 days from now
    sessions_authorized: 10,
    medical_indication: "",
    urgency_level: "NORMAL",
    requires_supervision: false,
  });

  // Status and urgency options
  const statusOptions = [
    { value: "todas", label: "Todos os Status" },
    { value: "active", label: "Ativa" },
    { value: "expired", label: "Expirada" },
    { value: "cancelled", label: "Cancelada" },
    { value: "suspended", label: "Suspensa" },
  ];

  const urgencyOptions = [
    { value: "todas", label: "Todas as Urgências" },
    { value: "URGENT", label: "Urgente" },
    { value: "HIGH", label: "Alta" },
    { value: "NORMAL", label: "Normal" },
    { value: "LOW", label: "Baixa" },
  ];

  // Load authorizations
  useEffect(() => {
    loadAuthorizations();
  }, [currentPage, filterStatus, filterUrgency, searchTerm]);

  const loadAuthorizations = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: MedicalAuthorizationListParams = {
        page: currentPage,
        size: itemsPerPage,
      };

      if (filterStatus !== "todas") {
        params.status = filterStatus as any;
      }

      if (filterUrgency !== "todas") {
        params.urgency_level = filterUrgency as any;
      }

      const response = await medicalAuthorizationsService.listAuthorizations(
        params
      );

      // Filter by search term on client side
      let filteredAuthorizations = response.authorizations;
      if (searchTerm) {
        filteredAuthorizations = response.authorizations.filter(
          (auth) =>
            auth.authorization_code
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            auth.patient_name
              ?.toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            auth.doctor_name
              ?.toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            auth.service_name
              ?.toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            auth.medical_indication
              ?.toLowerCase()
              .includes(searchTerm.toLowerCase())
        );
      }

      setAuthorizations(filteredAuthorizations);
      setTotalCount(response.total);
    } catch (error) {
      console.error("Erro ao carregar autorizações:", error);
      setError("Erro ao carregar autorizações médicas");
      notify.error("Erro ao carregar autorizações médicas");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAuthorization = () => {
    setEditingAuth(null);
    setFormData({
      contract_life_id: 0,
      service_id: 0,
      doctor_id: 0,
      authorization_date: new Date().toISOString().split("T")[0],
      valid_from: new Date().toISOString().split("T")[0],
      valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
      sessions_authorized: 10,
      medical_indication: "",
      urgency_level: "NORMAL",
      requires_supervision: false,
    });
    setShowCreateForm(true);
  };

  const handleEditAuthorization = (auth: MedicalAuthorization) => {
    setEditingAuth(auth);
    setFormData({
      contract_life_id: auth.contract_life_id,
      service_id: auth.service_id,
      doctor_id: auth.doctor_id,
      authorization_date: auth.authorization_date,
      valid_from: auth.valid_from,
      valid_until: auth.valid_until,
      sessions_authorized: auth.sessions_authorized,
      medical_indication: auth.medical_indication,
      urgency_level: auth.urgency_level,
      requires_supervision: auth.requires_supervision,
    });
    setShowCreateForm(true);
  };

  const handleViewAuthorization = (auth: MedicalAuthorization) => {
    setViewingAuth(auth);
    setShowDetails(true);
  };

  const handleDeleteAuthorization = async (authId: number) => {
    if (
      !window.confirm(
        "Tem certeza que deseja cancelar esta autorização médica?"
      )
    ) {
      return;
    }

    try {
      await medicalAuthorizationsService.cancelAuthorization(authId, {
        cancellation_reason: "Cancelada pelo usuário",
      });
      notify.success("Autorização médica cancelada com sucesso");
      loadAuthorizations();
    } catch (error) {
      console.error("Erro ao cancelar autorização:", error);
      notify.error("Erro ao cancelar autorização médica");
    }
  };

  const handleApproveAuthorization = async (auth: MedicalAuthorization) => {
    if (
      !window.confirm(`Aprovar autorização médica para ${auth.patient_name}?`)
    ) {
      return;
    }

    try {
      // In a real implementation, this would call an approval endpoint
      // For now, we'll simulate by updating the status
      await medicalAuthorizationsService.updateAuthorization(auth.id, {
        status: "active",
      });
      notify.success("Autorização médica aprovada com sucesso");
      loadAuthorizations();
    } catch (error) {
      console.error("Erro ao aprovar autorização:", error);
      notify.error("Erro ao aprovar autorização médica");
    }
  };

  const handleRejectAuthorization = async (auth: MedicalAuthorization) => {
    const reason = prompt("Motivo da rejeição:");
    if (!reason) return;

    try {
      await medicalAuthorizationsService.cancelAuthorization(auth.id, {
        cancellation_reason: reason,
      });
      notify.success("Autorização médica rejeitada");
      loadAuthorizations();
    } catch (error) {
      console.error("Erro ao rejeitar autorização:", error);
      notify.error("Erro ao rejeitar autorização médica");
    }
  };

  const handleSuspendAuthorization = async (auth: MedicalAuthorization) => {
    const reason = prompt("Motivo da suspensão:");
    if (!reason) return;

    try {
      // In a real implementation, this would call a suspend endpoint
      await medicalAuthorizationsService.updateAuthorization(auth.id, {
        status: "suspended",
      });
      notify.success("Autorização médica suspensa");
      loadAuthorizations();
    } catch (error) {
      console.error("Erro ao suspender autorização:", error);
      notify.error("Erro ao suspender autorização médica");
    }
  };

  const handleRenewAuthorization = async (auth: MedicalAuthorization) => {
    const newValidUntil = prompt(
      "Nova data de validade (YYYY-MM-DD):",
      auth.valid_until
    );
    if (!newValidUntil) return;

    const additionalSessions = prompt("Sessões adicionais (opcional):");
    const renewalReason = prompt("Motivo da renovação:");
    if (!renewalReason) return;

    try {
      const result = await medicalAuthorizationsService.renewAuthorization(
        auth.id,
        {
          new_valid_until: newValidUntil,
          additional_sessions: additionalSessions
            ? parseInt(additionalSessions)
            : undefined,
          renewal_reason: renewalReason,
          changes_summary: `Renovação automática - ${renewalReason}`,
        }
      );

      notify.success(
        `Autorização renovada com sucesso. Novo código: ${result.new_authorization_code}`
      );
      loadAuthorizations();
    } catch (error) {
      console.error("Erro ao renovar autorização:", error);
      notify.error("Erro ao renovar autorização médica");
    }
  };

  const checkRenewalEligibility = (auth: MedicalAuthorization): boolean => {
    // Check if authorization is expiring soon (within 7 days)
    const daysUntilExpiry = Math.ceil(
      (new Date(auth.valid_until).getTime() - new Date().getTime()) /
        (1000 * 60 * 60 * 24)
    );
    return (
      auth.renewal_allowed &&
      auth.status === "active" &&
      daysUntilExpiry <= 7 &&
      daysUntilExpiry > 0
    );
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingAuth) {
        await medicalAuthorizationsService.updateAuthorization(
          editingAuth.id,
          formData
        );
        notify.success("Autorização médica atualizada com sucesso");
      } else {
        await medicalAuthorizationsService.createAuthorization(formData);
        notify.success("Autorização médica criada com sucesso");
      }

      setShowCreateForm(false);
      setEditingAuth(null);
      loadAuthorizations();
    } catch (error) {
      console.error("Erro ao salvar autorização:", error);
      notify.error("Erro ao salvar autorização médica");
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      active: "bg-green-100 text-green-800 border-green-200",
      expired: "bg-gray-100 text-gray-800 border-gray-200",
      cancelled: "bg-red-100 text-red-800 border-red-200",
      suspended: "bg-yellow-100 text-yellow-800 border-yellow-200",
    };
    return (
      colors[status as keyof typeof colors] ||
      "bg-gray-100 text-gray-800 border-gray-200"
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "expired":
        return <Clock className="w-4 h-4 text-gray-500 dark:text-gray-400" />;
      case "cancelled":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "suspended":
        return <Pause className="w-4 h-4 text-yellow-500" />;
      default:
        return (
          <AlertCircle className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        );
    }
  };

  const getUrgencyColor = (urgency: string) => {
    const colors = {
      URGENT: "bg-red-100 text-red-800 border-red-200",
      HIGH: "bg-orange-100 text-orange-800 border-orange-200",
      NORMAL: "bg-blue-100 text-blue-800 border-blue-200",
      LOW: "bg-gray-100 text-gray-800 border-gray-200",
    };
    return (
      colors[urgency as keyof typeof colors] ||
      "bg-gray-100 text-gray-800 border-gray-200"
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const isExpiringSoon = (validUntil: string) => {
    const today = new Date();
    const expiryDate = new Date(validUntil);
    const diffTime = expiryDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays <= 7 && diffDays > 0;
  };

  const isExpired = (validUntil: string) => {
    const today = new Date();
    const expiryDate = new Date(validUntil);
    return expiryDate < today;
  };

  // Statistics
  const totalAuthorizations = authorizations.length;
  const activeAuthorizations = authorizations.filter(
    (a) => a.status === "active"
  ).length;
  const urgentAuthorizations = authorizations.filter(
    (a) => a.urgency_level === "URGENT"
  ).length;
  const expiringSoon = authorizations.filter((a) =>
    isExpiringSoon(a.valid_until)
  ).length;
  const eligibleForRenewal = authorizations.filter((a) =>
    checkRenewalEligibility(a)
  ).length;

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  // Create/Edit Form View
  if (showCreateForm) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center space-x-4">
          <Button
            onClick={() => setShowCreateForm(false)}
            variant="outline"
            size="sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {editingAuth ? "Editar" : "Nova"} Autorização Médica
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {editingAuth
                ? "Atualize os dados da autorização"
                : "Crie uma nova autorização médica"}
            </p>
          </div>
        </div>

        <Card>
          <div className="p-6">
            <form onSubmit={handleFormSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID da Vida do Contrato *
                  </label>
                  <Input
                    type="number"
                    value={formData.contract_life_id}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        contract_life_id: parseInt(e.target.value),
                      }))
                    }
                    placeholder="Digite o ID da vida do contrato"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID do Serviço *
                  </label>
                  <Input
                    type="number"
                    value={formData.service_id}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        service_id: parseInt(e.target.value),
                      }))
                    }
                    placeholder="Digite o ID do serviço"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID do Médico *
                  </label>
                  <Input
                    type="number"
                    value={formData.doctor_id}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        doctor_id: parseInt(e.target.value),
                      }))
                    }
                    placeholder="Digite o ID do médico"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data da Autorização *
                  </label>
                  <Input
                    type="date"
                    value={formData.authorization_date}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        authorization_date: e.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Válida de *
                  </label>
                  <Input
                    type="date"
                    value={formData.valid_from}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        valid_from: e.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Válida até *
                  </label>
                  <Input
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        valid_until: e.target.value,
                      }))
                    }
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Sessões Autorizadas
                  </label>
                  <Input
                    type="number"
                    value={formData.sessions_authorized}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        sessions_authorized: parseInt(e.target.value),
                      }))
                    }
                    placeholder="Número de sessões"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nível de Urgência
                  </label>
                  <select
                    value={formData.urgency_level}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        urgency_level: e.target.value as any,
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="LOW">Baixa</option>
                    <option value="NORMAL">Normal</option>
                    <option value="HIGH">Alta</option>
                    <option value="URGENT">Urgente</option>
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Indicação Médica *
                  </label>
                  <textarea
                    value={formData.medical_indication}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        medical_indication: e.target.value,
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Descreva a indicação médica"
                    required
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.requires_supervision}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          requires_supervision: e.target.checked,
                        }))
                      }
                      className="mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Requer supervisão
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancelar
                </Button>
                <Button type="submit">
                  <Save className="w-4 h-4 mr-2" />
                  {editingAuth ? "Atualizar" : "Criar"} Autorização
                </Button>
              </div>
            </form>
          </div>
        </Card>
      </div>
    );
  }

  // Details View
  if (showDetails && viewingAuth) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center space-x-4">
          <Button
            onClick={() => {
              setShowDetails(false);
              setViewingAuth(null);
            }}
            variant="outline"
            size="sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Autorização #{viewingAuth.authorization_code}
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Detalhes da autorização médica
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card
            title="Informações Gerais"
            icon={<FileText className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Código da Autorização
                </label>
                <p className="text-gray-900 font-mono">
                  {viewingAuth.authorization_code}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Paciente
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.patient_name}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Médico
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.doctor_name}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Serviço
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.service_name}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Status
                </label>
                <div className="mt-1">
                  <span
                    className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(
                      viewingAuth.status
                    )}`}
                  >
                    {statusOptions.find((s) => s.value === viewingAuth.status)
                      ?.label || viewingAuth.status}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Urgência
                </label>
                <div className="mt-1">
                  <span
                    className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getUrgencyColor(
                      viewingAuth.urgency_level
                    )}`}
                  >
                    {urgencyOptions.find(
                      (u) => u.value === viewingAuth.urgency_level
                    )?.label || viewingAuth.urgency_level}
                  </span>
                </div>
              </div>
            </div>
          </Card>

          <Card
            title="Período de Validade"
            icon={<Calendar className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Data da Autorização
                </label>
                <p className="text-gray-900 dark:text-white">
                  {formatDate(viewingAuth.authorization_date)}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Válida de
                </label>
                <p className="text-gray-900 dark:text-white">
                  {formatDate(viewingAuth.valid_from)}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Válida até
                </label>
                <p className="text-gray-900 dark:text-white">
                  {formatDate(viewingAuth.valid_until)}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Sessões Autorizadas
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.sessions_authorized || "N/A"}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Sessões Restantes
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.sessions_remaining || "N/A"}
                </p>
              </div>
            </div>
          </Card>

          <Card
            title="Informações Médicas"
            icon={<Stethoscope className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Indicação Médica
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.medical_indication}
                </p>
              </div>
              {viewingAuth.contraindications && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Contraindicações
                  </label>
                  <p className="text-gray-900 dark:text-white">
                    {viewingAuth.contraindications}
                  </p>
                </div>
              )}
              {viewingAuth.special_instructions && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Instruções Especiais
                  </label>
                  <p className="text-gray-900 dark:text-white">
                    {viewingAuth.special_instructions}
                  </p>
                </div>
              )}
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Requer Supervisão
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.requires_supervision ? "Sim" : "Não"}
                </p>
              </div>
            </div>
          </Card>

          <Card
            title="Controles e Limites"
            icon={<Activity className="h-5 w-5" />}
          >
            <div className="space-y-4">
              {viewingAuth.monthly_limit && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Limite Mensal
                  </label>
                  <p className="text-gray-900 dark:text-white">
                    {viewingAuth.monthly_limit} sessões
                  </p>
                </div>
              )}
              {viewingAuth.weekly_limit && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Limite Semanal
                  </label>
                  <p className="text-gray-900 dark:text-white">
                    {viewingAuth.weekly_limit} sessões
                  </p>
                </div>
              )}
              {viewingAuth.daily_limit && (
                <div>
                  <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Limite Diário
                  </label>
                  <p className="text-gray-900 dark:text-white">
                    {viewingAuth.daily_limit} sessões
                  </p>
                </div>
              )}
              <div>
                <label className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Renovação Permitida
                </label>
                <p className="text-gray-900 dark:text-white">
                  {viewingAuth.renewal_allowed ? "Sim" : "Não"}
                </p>
              </div>
            </div>
          </Card>

          <Card
            title="Histórico de Alterações"
            icon={<Clock className="h-5 w-5" />}
            className="lg:col-span-2"
          >
            <div className="space-y-4">
              {/* Mock history entries - in real app, this would come from API */}
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Autorização criada
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(
                      viewingAuth.created_at || viewingAuth.authorization_date
                    )}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Status inicial: Ativa • {viewingAuth.sessions_authorized}{" "}
                    sessões autorizadas
                  </p>
                </div>
              </div>

              {viewingAuth.updated_at &&
                viewingAuth.updated_at !== viewingAuth.created_at && (
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        Informações atualizadas
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(viewingAuth.updated_at)}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        Última modificação dos dados da autorização
                      </p>
                    </div>
                  </div>
                )}

              {viewingAuth.status === "cancelled" &&
                viewingAuth.cancelled_at && (
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        Autorização cancelada
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(viewingAuth.cancelled_at)}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        Motivo:{" "}
                        {viewingAuth.cancellation_reason ||
                          "Cancelada pelo usuário"}
                      </p>
                    </div>
                  </div>
                )}

              {viewingAuth.status === "suspended" && (
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Autorização suspensa
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Status alterado temporariamente
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      Aguardando revisão ou condições específicas
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Heart className="w-6 h-6 mr-2 text-red-500" />
            Autorizações Médicas
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Gestão completa das autorizações médicas para serviços home care
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button
            onClick={handleCreateAuthorization}
            className="flex items-center"
          >
            <Plus className="w-4 h-4 mr-2" />
            Nova Autorização
          </Button>
        </div>
      </div>

      {/* Alert for expiring authorizations */}
      {expiringSoon > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <div className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-yellow-800">
                  Autorizações Expirando
                </p>
                <p className="text-lg font-bold text-yellow-900">
                  {expiringSoon} autorizações
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  Vencem nos próximos 7 dias - considere renovação
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Alert for authorizations eligible for renewal */}
      {eligibleForRenewal > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <div className="p-4">
            <div className="flex items-center">
              <RotateCcw className="w-5 h-5 text-blue-600 mr-2" />
              <div>
                <p className="text-sm font-medium text-blue-800">
                  Renovação Disponível
                </p>
                <p className="text-lg font-bold text-blue-900">
                  {eligibleForRenewal} autorizações
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  Elegíveis para renovação automática
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {totalAuthorizations}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Ativas
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {activeAuthorizations}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Urgentes
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {urgentAuthorizations}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <Clock className="w-8 h-8 text-orange-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Vencendo em 7 dias
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {expiringSoon}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <RotateCcw className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Elegíveis para Renovação
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {eligibleForRenewal}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Buscar por código, paciente, médico..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {statusOptions.map((status) => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
            <select
              value={filterUrgency}
              onChange={(e) => setFilterUrgency(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {urgencyOptions.map((urgency) => (
                <option key={urgency.value} value={urgency.value}>
                  {urgency.label}
                </option>
              ))}
            </select>
            <Button onClick={loadAuthorizations} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
          </div>
        </div>
      </Card>

      {/* Authorizations List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Carregando autorizações...</span>
          </div>
        ) : authorizations.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
            Nenhuma autorização encontrada
          </div>
        ) : (
          authorizations.map((authorization) => (
            <Card
              key={authorization.id}
              className="hover:shadow-lg transition-shadow"
            >
              <div className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">
                      {authorization.authorization_code}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {authorization.service_name}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(authorization.status)}
                    {isExpiringSoon(authorization.valid_until) && (
                      <AlertCircle
                        className="w-4 h-4 text-orange-500"
                        title="Vence em breve"
                      />
                    )}
                  </div>
                </div>

                {/* Patient and Doctor */}
                <div className="space-y-2 mb-3">
                  <div className="flex items-center text-xs">
                    <User className="w-3 h-3 mr-1 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">
                      Paciente:
                    </span>
                    <span className="ml-1 font-medium text-gray-900 dark:text-white">
                      {authorization.patient_name || "N/A"}
                    </span>
                  </div>
                  <div className="flex items-center text-xs">
                    <Activity className="w-3 h-3 mr-1 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">
                      Médico:
                    </span>
                    <span className="ml-1 font-medium text-gray-900 dark:text-white">
                      {authorization.doctor_name || "N/A"}
                    </span>
                  </div>
                </div>

                {/* Status and Urgency */}
                <div className="flex flex-wrap gap-2 mb-3">
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                      authorization.status
                    )}`}
                  >
                    {statusOptions.find((s) => s.value === authorization.status)
                      ?.label || authorization.status}
                  </span>
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getUrgencyColor(
                      authorization.urgency_level
                    )}`}
                  >
                    {urgencyOptions.find(
                      (u) => u.value === authorization.urgency_level
                    )?.label || authorization.urgency_level}
                  </span>
                </div>

                {/* Dates */}
                <div className="space-y-1 mb-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 dark:text-gray-400">
                      Válido de:
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {formatDate(authorization.valid_from)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 dark:text-gray-400">
                      Válido até:
                    </span>
                    <span
                      className={`font-medium ${
                        isExpired(authorization.valid_until)
                          ? "text-red-600"
                          : isExpiringSoon(authorization.valid_until)
                          ? "text-orange-600"
                          : "text-gray-900 dark:text-white"
                      }`}
                    >
                      {formatDate(authorization.valid_until)}
                    </span>
                  </div>
                </div>

                {/* Sessions */}
                {authorization.sessions_authorized && (
                  <div className="space-y-1 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500 dark:text-gray-400">
                        Sessões autorizadas:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {authorization.sessions_authorized}
                      </span>
                    </div>
                    {authorization.sessions_remaining !== null && (
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500 dark:text-gray-400">
                          Sessões restantes:
                        </span>
                        <span
                          className={`font-medium ${
                            authorization.sessions_remaining === 0
                              ? "text-red-600"
                              : authorization.sessions_remaining <= 3
                              ? "text-orange-600"
                              : "text-gray-900 dark:text-white"
                          }`}
                        >
                          {authorization.sessions_remaining}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Medical Indication */}
                {authorization.medical_indication && (
                  <div className="mb-3">
                    <p className="text-xs text-gray-600 line-clamp-2">
                      <span className="font-medium">Indicação:</span>{" "}
                      {authorization.medical_indication}
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewAuthorization(authorization)}
                  >
                    <Eye className="w-3 h-3" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditAuthorization(authorization)}
                    disabled={authorization.status !== "active"}
                  >
                    <Edit className="w-3 h-3" />
                  </Button>
                  {authorization.status === "active" && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleApproveAuthorization(authorization)
                        }
                        className="text-green-600 hover:text-green-900"
                      >
                        <Check className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRejectAuthorization(authorization)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Ban className="w-3 h-3" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleSuspendAuthorization(authorization)
                        }
                        className="text-yellow-600 hover:text-yellow-900"
                      >
                        <Pause className="w-3 h-3" />
                      </Button>
                      {checkRenewalEligibility(authorization) && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            handleRenewAuthorization(authorization)
                          }
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <RotateCcw className="w-3 h-3" />
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Card>
          <div className="px-4 py-3 flex items-center justify-between">
            <div className="flex-1 flex justify-between sm:hidden">
              <Button
                variant="outline"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Próximo
              </Button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  Mostrando{" "}
                  <span className="font-medium">
                    {(currentPage - 1) * itemsPerPage + 1}
                  </span>{" "}
                  até{" "}
                  <span className="font-medium">
                    {Math.min(currentPage * itemsPerPage, totalCount)}
                  </span>{" "}
                  de <span className="font-medium">{totalCount}</span>{" "}
                  autorizações
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <Button
                    variant="outline"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="rounded-r-none"
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="rounded-l-none"
                  >
                    Próximo
                  </Button>
                </nav>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default MedicalAuthorizationsPage;
