import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider } from "./contexts/AuthContext";
import { AppErrorBoundary } from "./components/error";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import AdminLayout from "./components/layout/AdminLayout";
import LoginPage from "./pages/LoginPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ActivationPage from "./pages/ActivationPage";
import ContractAcceptancePage from "./pages/ContractAcceptancePage";
import CreateManagerPage from "./pages/CreateManagerPage";
import DashboardPage from "./pages/DashboardPage";
import PacientesPage from "./pages/PacientesPage";
import ProfissionaisPage from "./pages/ProfissionaisPage";
import ConsultasPage from "./pages/ConsultasPage";
import EmpresasPage from "./pages/EmpresasPage";
import CompaniesPage from "./pages/CompaniesPage";
import EstablishmentsPage from "./pages/EstablishmentsPage";
import ClientsPage from "./pages/ClientsPage";
import ContractsPage from "./pages/ContractsPage";
import ContractsPageWithTabs from "./pages/ContractsPageWithTabs";
import ContractDashboard from "./components/views/ContractDashboard";
import ContractLivesManager from "./components/views/ContractLivesManager";
import ContractDetails from "./components/views/ContractDetails";
import FlowbiteTableExamplePage from "./pages/FlowbiteTableExamplePage";
import ReportsPage from "./pages/ReportsPage";
import ServicesCatalogPage from "./pages/ServicesCatalogPage";
import MedicalAuthorizationsPage from "./pages/MedicalAuthorizationsPage";
import BillingDashboardPage from "./pages/BillingDashboardPage";
import B2BBillingPage from "./pages/B2BBillingPage";
import SubscriptionPlansPage from "./pages/SubscriptionPlansPage";
import InvoicesPage from "./pages/InvoicesPage";
import MenusPage from "./pages/MenusPage";
import UsersPage from "./pages/UsersPage";
import { RolesPage } from "./pages/RolesPage";
import NotificationDemo from "./pages/NotificationDemo";
import NotFoundPage from "./pages/NotFoundPage";
// Secure session service removido

function App() {
  // Initialize secure session service on app start
  // Secure session service removido - simplificação

  return (
    <AppErrorBoundary>
      <AuthProvider>
        <ThemeProvider>
          <div className="h-full">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
              <Route path="/activate/:token" element={<ActivationPage />} />
              <Route path="/contract-acceptance/:token" element={<ContractAcceptancePage />} />
              <Route path="/create-manager/:token" element={<CreateManagerPage />} />

              {/* Redirect root to admin */}
              <Route path="/" element={<Navigate to="/admin" replace />} />

              {/* Admin routes with AdminLTE layout */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="pacientes" element={<PacientesPage />} />
                <Route path="profissionais" element={<ProfissionaisPage />} />
                <Route path="consultas" element={<ConsultasPage />} />
                <Route path="empresas" element={<EmpresasPage />} />
                <Route path="empresas/:id" element={<EmpresasPage />} />
                <Route
                  path="estabelecimentos"
                  element={<EstablishmentsPage />}
                />
                <Route
                  path="estabelecimentos/:id"
                  element={<EstablishmentsPage />}
                />
                <Route path="clientes" element={<ClientsPage />} />
                <Route path="clientes/:id" element={<ClientsPage />} />

                {/* Rotas específicas de contratos PRIMEIRO */}
                <Route
                  path="contratos/:id/editar"
                  element={<ContractsPage />}
                />
                <Route
                  path="contratos/visualizar/:id"
                  element={<ContractDetails />}
                />
                <Route
                  path="contratos/:id/vidas"
                  element={<ContractLivesManager />}
                />
                <Route
                  path="contratos/:id/configuracoes"
                  element={<ContractsPage />}
                />
                <Route path="contratos/:id" element={<ContractsPage />} />
                <Route
                  path="vidas"
                  element={<ContractLivesManager />}
                />

                {/* Rota principal com abas */}
                <Route path="contratos" element={<ContractsPageWithTabs />} />
                <Route
                  path="flowbite-table-exemplo"
                  element={<FlowbiteTableExamplePage />}
                />
                <Route path="relatorios" element={<ReportsPage />} />
                <Route path="servicos" element={<ServicesCatalogPage />} />
                <Route
                  path="autorizacoes"
                  element={<MedicalAuthorizationsPage />}
                />
                <Route
                  path="autorizacoes/:id"
                  element={<MedicalAuthorizationsPage />}
                />
                <Route
                  path="faturamento/dashboard"
                  element={<BillingDashboardPage />}
                />
                <Route path="faturamento/faturas" element={<InvoicesPage />} />
                <Route
                  path="faturamento/b2b"
                  element={<B2BBillingPage />}
                />
                <Route
                  path="faturamento/planos"
                  element={<SubscriptionPlansPage />}
                />
                <Route path="menus" element={<MenusPage />} />
                <Route path="usuarios" element={<UsersPage />} />
                <Route path="usuarios/:id" element={<UsersPage />} />
                <Route path="perfis" element={<RolesPage />} />
                <Route path="perfis/:id" element={<RolesPage />} />
                <Route
                  path="notification-demo"
                  element={<NotificationDemo />}
                />
              </Route>

              {/* 404 Page */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </div>
        </ThemeProvider>
      </AuthProvider>
    </AppErrorBoundary>
  );
}

export default App;
