import React from "react";
import ContextSwitcher from "../components/security/ContextSwitcher";

const DashboardPage = () => {
  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
            <p className="text-gray-600">
              Visão geral das atividades e métricas do sistema
            </p>
          </div>

          {/* Context Switcher */}
          <div className="flex items-center space-x-4">
            <ContextSwitcher />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Atividade Recente</h3>
          </div>
          <div className="card-content">
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Novo cliente cadastrado
                  </p>
                  <p className="text-xs text-gray-500">
                    Maria Silva - há 2 horas
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full mt-2"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Agendamento confirmado
                  </p>
                  <p className="text-xs text-gray-500">
                    João Santos - há 3 horas
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Profissional atualizado
                  </p>
                  <p className="text-xs text-gray-500">
                    Dr. Carlos - há 5 horas
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Status do Sistema</h3>
          </div>
          <div className="card-content">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  API Backend
                </span>
                <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  ✓ Online
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Banco de Dados
                </span>
                <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  ✓ Conectado
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Cache Redis
                </span>
                <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  ✓ Ativo
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Monitoramento
                </span>
                <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  ✓ Funcionando
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Métricas de Performance</h3>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">99.9%</div>
                <div className="text-sm text-gray-500">Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">142ms</div>
                <div className="text-sm text-gray-500">Response Time</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">1,247</div>
                <div className="text-sm text-gray-500">Requests/hour</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">94%</div>
                <div className="text-sm text-gray-500">Cache Hit Rate</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
