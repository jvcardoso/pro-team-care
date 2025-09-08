import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AppErrorBoundary } from "./components/error";
import AdminLayout from "./components/layout/AdminLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import PacientesPage from "./pages/PacientesPage";
import ProfissionaisPage from "./pages/ProfissionaisPage";
import ConsultasPage from "./pages/ConsultasPage";
import EmpresasPage from "./pages/EmpresasPage";
import MenusPage from "./pages/MenusPage";
import UsersPage from "./pages/UsersPage";
import secureSessionService from "./services/secureSessionService";

function App() {
  // Initialize secure session service on app start
  useEffect(() => {
    // Initialize security service if user is authenticated
    const token = localStorage.getItem("access_token");
    if (token) {
      secureSessionService.initialize();
      // Make service available globally for debugging
      window.secureSessionService = secureSessionService;
    }
  }, []);

  return (
    <AppErrorBoundary>
      <ThemeProvider>
        <div className="h-full">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Redirect root to admin */}
            <Route path="/" element={<Navigate to="/admin" replace />} />

            {/* Admin routes with AdminLTE layout */}
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="pacientes" element={<PacientesPage />} />
              <Route path="profissionais" element={<ProfissionaisPage />} />
              <Route path="consultas" element={<ConsultasPage />} />
              <Route path="empresas" element={<EmpresasPage />} />
              <Route path="menus" element={<MenusPage />} />
              <Route path="usuarios" element={<UsersPage />} />
            </Route>

            {/* 404 Page */}
            <Route
              path="*"
              element={
                <div className="h-screen flex items-center justify-center bg-background">
                  <div className="text-center">
                    <h1 className="text-6xl font-bold text-foreground">404</h1>
                    <p className="text-xl text-muted-foreground mt-4">
                      Página não encontrada
                    </p>
                    <a
                      href="/admin"
                      className="mt-6 inline-block px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                    >
                      Voltar ao Dashboard
                    </a>
                  </div>
                </div>
              }
            />
          </Routes>
        </div>
      </ThemeProvider>
    </AppErrorBoundary>
  );
}

export default App;
