import React, { useState } from "react";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { UserCheck, Search, Plus, Star } from "lucide-react";

const ProfissionaisPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterEspecialidade, setFilterEspecialidade] = useState("todas");

  // Mock data - substituir por API real
  const profissionais = [
    {
      id: 1,
      nome: "Dr. João Silva",
      especialidade: "Cardiologia",
      crm: "CRM 12345-SP",
      telefone: "(11) 99999-1111",
      email: "joao.silva@procare.com",
      status: "ativo",
      avaliacoes: 4.8,
      totalConsultas: 245,
      disponibilidade: "Manhã e Tarde",
    },
    {
      id: 2,
      nome: "Dra. Ana Santos",
      especialidade: "Fisioterapia",
      crefito: "CREFITO 67890-SP",
      telefone: "(11) 88888-2222",
      email: "ana.santos@procare.com",
      status: "ativo",
      avaliacoes: 4.9,
      totalConsultas: 189,
      disponibilidade: "Integral",
    },
    {
      id: 3,
      nome: "Dr. Pedro Costa",
      especialidade: "Enfermagem",
      coren: "COREN 11111-SP",
      telefone: "(11) 77777-3333",
      email: "pedro.costa@procare.com",
      status: "ativo",
      avaliacoes: 4.7,
      totalConsultas: 312,
      disponibilidade: "Noturno",
    },
    {
      id: 4,
      nome: "Dra. Maria Oliveira",
      especialidade: "Nutrição",
      crn: "CRN 22222-SP",
      telefone: "(11) 66666-4444",
      email: "maria.oliveira@procare.com",
      status: "inativo",
      avaliacoes: 4.6,
      totalConsultas: 95,
      disponibilidade: "Manhã",
    },
  ];

  const especialidades = [
    "todas",
    ...new Set(profissionais.map((p) => p.especialidade)),
  ];

  const filteredProfissionais = profissionais.filter((profissional) => {
    const matchesSearch = profissional.nome
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
    const matchesFilter =
      filterEspecialidade === "todas" ||
      profissional.especialidade === filterEspecialidade;
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (status) => {
    const baseClasses = "px-2 py-1 text-xs font-medium rounded-full";
    return status === "ativo"
      ? `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`
      : `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
  };

  const renderStars = (rating) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating
                ? "text-yellow-400 fill-current"
                : "text-gray-300 dark:text-gray-600"
            }`}
          />
        ))}
        <span className="ml-1 text-sm text-muted-foreground">({rating})</span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Profissionais</h1>
          <p className="text-muted-foreground">
            Gerencie a equipe de profissionais Home Care
          </p>
        </div>
        <Button icon={<Plus className="h-4 w-4" />}>Novo Profissional</Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-1 gap-4">
            <Input
              placeholder="Buscar profissionais..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="max-w-sm"
            />

            <select
              value={filterEspecialidade}
              onChange={(e) => setFilterEspecialidade(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              {especialidades.map((esp) => (
                <option key={esp} value={esp}>
                  {esp === "todas" ? "Todas as especialidades" : esp}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <UserCheck className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Total</p>
              <p className="text-2xl font-bold text-foreground">
                {profissionais.length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <UserCheck className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Ativos</p>
              <p className="text-2xl font-bold text-foreground">
                {profissionais.filter((p) => p.status === "ativo").length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <UserCheck className="h-6 w-6 text-purple-600 dark:text-purple-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Especialidades</p>
              <p className="text-2xl font-bold text-foreground">
                {especialidades.length - 1}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
              <Star className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Avaliação Média</p>
              <p className="text-2xl font-bold text-foreground">
                {(
                  profissionais.reduce((acc, p) => acc + p.avaliacoes, 0) /
                  profissionais.length
                ).toFixed(1)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Professionals Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredProfissionais.map((profissional) => (
          <Card key={profissional.id}>
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {profissional.nome}
                  </h3>
                  <p className="text-primary-600 dark:text-primary-400 font-medium">
                    {profissional.especialidade}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {profissional.crm ||
                      profissional.crefito ||
                      profissional.coren ||
                      profissional.crn}
                  </p>
                </div>
                <span className={getStatusBadge(profissional.status)}>
                  {profissional.status === "ativo" ? "Ativo" : "Inativo"}
                </span>
              </div>

              {/* Contact */}
              <div className="space-y-1">
                <p className="text-sm text-foreground">
                  {profissional.telefone}
                </p>
                <p className="text-sm text-muted-foreground">
                  {profissional.email}
                </p>
              </div>

              {/* Stats */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    Consultas realizadas
                  </p>
                  <p className="font-semibold text-foreground">
                    {profissional.totalConsultas}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    Disponibilidade
                  </p>
                  <p className="font-semibold text-foreground">
                    {profissional.disponibilidade}
                  </p>
                </div>
              </div>

              {/* Rating */}
              <div>
                <p className="text-sm text-muted-foreground mb-1">Avaliação</p>
                {renderStars(profissional.avaliacoes)}
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2 border-t border-border">
                <Button size="sm" variant="primary" outline className="flex-1">
                  Ver Perfil
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  outline
                  className="flex-1"
                >
                  Editar
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ProfissionaisPage;
