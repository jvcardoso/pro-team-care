import React, { useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { Users, Search, Plus, Filter } from "lucide-react";

const PacientesPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("todos");

  // Mock data - substituir por API real
  const pacientes = [
    {
      id: 1,
      nome: "Maria Silva Santos",
      idade: 78,
      endereco: "Rua das Flores, 123 - Centro",
      telefone: "(11) 99999-9999",
      status: "ativo",
      ultimaConsulta: "2024-08-25",
      profissional: "Dr. João Cardiologia",
    },
    {
      id: 2,
      nome: "José Santos Oliveira",
      idade: 65,
      endereco: "Av. Paulista, 456 - Bela Vista",
      telefone: "(11) 88888-8888",
      status: "ativo",
      ultimaConsulta: "2024-08-28",
      profissional: "Dra. Ana Fisioterapia",
    },
    {
      id: 3,
      nome: "Ana Costa Ferreira",
      idade: 82,
      endereco: "Rua do Comércio, 789 - Vila Madalena",
      telefone: "(11) 77777-7777",
      status: "inativo",
      ultimaConsulta: "2024-07-15",
      profissional: "Dr. Pedro Enfermagem",
    },
  ];

  const filteredPacientes = pacientes.filter((paciente) => {
    const matchesSearch = paciente.nome
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    const matchesFilter =
      filterStatus === "todos" || paciente.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (status) => {
    const baseClasses = "px-2 py-1 text-xs font-medium rounded-full";
    return status === "ativo"
      ? `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`
      : `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Pacientes</h1>
          <p className="text-muted-foreground">
            Gerencie os pacientes do sistema Home Care
          </p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />}>Novo Paciente</Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-1 gap-4">
            <Input
              placeholder="Buscar pacientes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="max-w-sm"
            />

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="todos">Todos os status</option>
              <option value="ativo">Ativos</option>
              <option value="inativo">Inativos</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button
              variant="secondary"
              outline
              icon={<Filter className="h-4 w-4" />}
            >
              Filtros
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Total Pacientes</p>
              <p className="text-2xl font-bold text-foreground">
                {pacientes.length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Users className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Ativos</p>
              <p className="text-2xl font-bold text-foreground">
                {pacientes.filter((p) => p.status === "ativo").length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
              <Users className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Inativos</p>
              <p className="text-2xl font-bold text-foreground">
                {pacientes.filter((p) => p.status === "inativo").length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Patients Table */}
      <Card title="Lista de Pacientes">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                  Nome
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                  Idade
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                  Telefone
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                  Status
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                  Última Consulta
                </th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredPacientes.map((paciente) => (
                <tr
                  key={paciente.id}
                  className="border-b border-border hover:bg-muted/50"
                >
                  <td className="py-3 px-4">
                    <div>
                      <p className="font-medium text-foreground">
                        {paciente.nome}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {paciente.endereco}
                      </p>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-foreground">
                    {paciente.idade} anos
                  </td>
                  <td className="py-3 px-4 text-foreground">
                    {paciente.telefone}
                  </td>
                  <td className="py-3 px-4">
                    <span className={getStatusBadge(paciente.status)}>
                      {paciente.status === "ativo" ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-foreground">
                    {paciente.ultimaConsulta}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-2">
                      <Button size="sm" variant="secondary" outline>
                        Ver
                      </Button>
                      <Button size="sm" variant="primary" outline>
                        Editar
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default PacientesPage;
