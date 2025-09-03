import React, { useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import {
  Calendar,
  Clock,
  Plus,
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";

const ConsultasPage = () => {
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [filterStatus, setFilterStatus] = useState("todas");

  // Mock data - substituir por API real
  const consultas = [
    {
      id: 1,
      paciente: "Maria Silva Santos",
      profissional: "Dr. João Silva",
      especialidade: "Cardiologia",
      data: "2024-08-30",
      horario: "09:00",
      endereco: "Rua das Flores, 123 - Centro",
      status: "agendada",
      observacoes: "Consulta de rotina - verificar pressão arterial",
    },
    {
      id: 2,
      paciente: "José Santos Oliveira",
      profissional: "Dra. Ana Santos",
      especialidade: "Fisioterapia",
      data: "2024-08-30",
      horario: "14:30",
      endereco: "Av. Paulista, 456 - Bela Vista",
      status: "concluida",
      observacoes: "Sessão de reabilitação pós-cirúrgica",
    },
    {
      id: 3,
      paciente: "Ana Costa Ferreira",
      profissional: "Dr. Pedro Costa",
      especialidade: "Enfermagem",
      data: "2024-08-30",
      horario: "16:00",
      endereco: "Rua do Comércio, 789 - Vila Madalena",
      status: "cancelada",
      observacoes: "Cancelada pelo paciente - remarcada para próxima semana",
    },
    {
      id: 4,
      paciente: "Carlos Mendes",
      profissional: "Dra. Maria Oliveira",
      especialidade: "Nutrição",
      data: "2024-08-30",
      horario: "10:30",
      endereco: "Rua Nova, 321 - Jardins",
      status: "em_andamento",
      observacoes: "Avaliação nutricional completa",
    },
    {
      id: 5,
      paciente: "Lucia Rodrigues",
      profissional: "Dr. João Silva",
      especialidade: "Cardiologia",
      data: "2024-08-31",
      horario: "08:00",
      endereco: "Av. Brasil, 999 - Centro",
      status: "agendada",
      observacoes: "Primeira consulta - check-up geral",
    },
  ];

  const filteredConsultas = consultas.filter((consulta) => {
    const matchesDate = consulta.data === selectedDate;
    const matchesFilter =
      filterStatus === "todas" || consulta.status === filterStatus;
    return matchesDate && matchesFilter;
  });

  const getStatusInfo = (status) => {
    const statusMap = {
      agendada: {
        label: "Agendada",
        icon: Calendar,
        classes:
          "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
        iconClasses: "text-blue-600 dark:text-blue-300",
      },
      em_andamento: {
        label: "Em Andamento",
        icon: AlertCircle,
        classes:
          "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        iconClasses: "text-yellow-600 dark:text-yellow-300",
      },
      concluida: {
        label: "Concluída",
        icon: CheckCircle,
        classes:
          "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
        iconClasses: "text-green-600 dark:text-green-300",
      },
      cancelada: {
        label: "Cancelada",
        icon: XCircle,
        classes: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
        iconClasses: "text-red-600 dark:text-red-300",
      },
    };
    return statusMap[status];
  };

  const getStatusCounts = () => {
    const today = new Date().toISOString().split("T")[0];
    const todayConsultas = consultas.filter((c) => c.data === today);

    return {
      total: todayConsultas.length,
      agendadas: todayConsultas.filter((c) => c.status === "agendada").length,
      concluidas: todayConsultas.filter((c) => c.status === "concluida").length,
      canceladas: todayConsultas.filter((c) => c.status === "cancelada").length,
    };
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Consultas</h1>
          <p className="text-muted-foreground">
            Gerencie agendamentos e consultas Home Care
          </p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />}>Nova Consulta</Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-1 gap-4">
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              leftIcon={<Calendar className="h-4 w-4" />}
            />

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="todas">Todos os status</option>
              <option value="agendada">Agendadas</option>
              <option value="em_andamento">Em Andamento</option>
              <option value="concluida">Concluídas</option>
              <option value="cancelada">Canceladas</option>
            </select>
          </div>

          <Button
            variant="secondary"
            outline
            icon={<Filter className="h-4 w-4" />}
          >
            Mais Filtros
          </Button>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Hoje</p>
              <p className="text-2xl font-bold text-foreground">
                {statusCounts.total}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
              <Clock className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Agendadas</p>
              <p className="text-2xl font-bold text-foreground">
                {statusCounts.agendadas}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Concluídas</p>
              <p className="text-2xl font-bold text-foreground">
                {statusCounts.concluidas}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <XCircle className="h-6 w-6 text-red-600 dark:text-red-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Canceladas</p>
              <p className="text-2xl font-bold text-foreground">
                {statusCounts.canceladas}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Appointments List */}
      <Card
        title={`Consultas do dia ${new Date(selectedDate).toLocaleDateString(
          "pt-BR"
        )}`}
      >
        <div className="space-y-4">
          {filteredConsultas.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                Nenhuma consulta encontrada
              </h3>
              <p className="text-muted-foreground">
                Não há consultas{" "}
                {filterStatus === "todas"
                  ? ""
                  : `com status "${getStatusInfo(
                      filterStatus
                    )?.label.toLowerCase()}" `}
                para o dia selecionado.
              </p>
            </div>
          ) : (
            filteredConsultas
              .sort((a, b) => a.horario.localeCompare(b.horario))
              .map((consulta) => {
                const statusInfo = getStatusInfo(consulta.status);
                const StatusIcon = statusInfo.icon;

                return (
                  <div
                    key={consulta.id}
                    className="p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium text-foreground">
                              {consulta.horario}
                            </span>
                          </div>
                          <span
                            className={`px-2 py-1 text-xs font-medium rounded-full ${statusInfo.classes}`}
                          >
                            {statusInfo.label}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-muted-foreground">
                              Paciente
                            </p>
                            <p className="font-medium text-foreground">
                              {consulta.paciente}
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">
                              Profissional
                            </p>
                            <p className="font-medium text-foreground">
                              {consulta.profissional}
                            </p>
                            <p className="text-sm text-primary-600 dark:text-primary-400">
                              {consulta.especialidade}
                            </p>
                          </div>
                        </div>

                        <div>
                          <p className="text-sm text-muted-foreground">
                            Endereço
                          </p>
                          <p className="text-foreground">{consulta.endereco}</p>
                        </div>

                        {consulta.observacoes && (
                          <div>
                            <p className="text-sm text-muted-foreground">
                              Observações
                            </p>
                            <p className="text-sm text-foreground">
                              {consulta.observacoes}
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        <Button size="sm" variant="primary" outline>
                          Ver Detalhes
                        </Button>
                        {consulta.status === "agendada" && (
                          <>
                            <Button size="sm" variant="success" outline>
                              Iniciar
                            </Button>
                            <Button size="sm" variant="danger" outline>
                              Cancelar
                            </Button>
                          </>
                        )}
                        {consulta.status === "em_andamento" && (
                          <Button size="sm" variant="success">
                            Finalizar
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
          )}
        </div>
      </Card>
    </div>
  );
};

export default ConsultasPage;
