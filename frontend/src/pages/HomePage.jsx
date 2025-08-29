import React from 'react'

const HomePage = () => {
  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Bem-vindo ao Pro Team Care
        </h1>
        <p className="text-gray-600">
          Sistema de gestão profissional de equipe para área da saúde
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Clientes Ativos</h3>
          </div>
          <div className="card-content">
            <div className="text-3xl font-bold text-blue-600 mb-2">247</div>
            <p className="text-sm text-gray-500">+12% em relação ao mês anterior</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Profissionais</h3>
          </div>
          <div className="card-content">
            <div className="text-3xl font-bold text-green-600 mb-2">18</div>
            <p className="text-sm text-gray-500">Ativos no sistema</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Atendimentos Hoje</h3>
          </div>
          <div className="card-content">
            <div className="text-3xl font-bold text-purple-600 mb-2">32</div>
            <p className="text-sm text-gray-500">8 em andamento</p>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Funcionalidades Principais</h3>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Gestão de Clientes</h4>
                <p className="text-gray-600 text-sm">
                  Cadastro completo de clientes com histórico médico, endereços e contatos.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Equipe Profissional</h4>
                <p className="text-gray-600 text-sm">
                  Controle de profissionais, especialidades e disponibilidade.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Agendamentos</h4>
                <p className="text-gray-600 text-sm">
                  Sistema completo de agendamento de consultas e procedimentos.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Relatórios</h4>
                <p className="text-gray-600 text-sm">
                  Relatórios detalhados de atendimentos, faturamento e performance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage