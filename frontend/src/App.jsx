import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider } from "./contexts/AuthContext";
import { AppErrorBoundary } from "./components/error";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import AdminLayout from "./components/layout/AdminLayout";
import LoginPage from "./pages/LoginPage";
import ActivationPage from "./pages/ActivationPage";
import DashboardPage from "./pages/DashboardPage";
import PacientesPage from "./pages/PacientesPage";
import ProfissionaisPage from "./pages/ProfissionaisPage";
import ConsultasPage from "./pages/ConsultasPage";
import EmpresasPage from "./pages/EmpresasPage";
import EstablishmentsPage from "./pages/EstablishmentsPage";
import ClientsPage from "./pages/ClientsPage";
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
              <Route path="/activate/:token" element={<ActivationPage />} />

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
