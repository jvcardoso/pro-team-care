import React, { useState, useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Footer from "./Footer";

const AdminLayout: React.FC = React.memo(() => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const location = useLocation();
  const navigate = useNavigate();

  // 🔒 Verificar autenticação com validação JWT real
  useEffect(() => {
    const checkAuth = async (): Promise<void> => {
      try {
        const { authService } = await import("../../services/api");
        const validation = await authService.validateToken();

        if (!validation.valid) {
          console.info("Token inválido:", validation.reason);

          // Limpar dados de autenticação
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");

          // Salvar URL atual para redirecionar após login
          const currentPath = location.pathname + location.search;
          sessionStorage.setItem("redirectAfterLogin", currentPath);

          navigate("/login");
          return;
        }

        // Token válido - usuário autenticado
        setIsAuthenticated(true);
        setIsLoading(false);
      } catch (error) {
        console.error("Erro na validação de autenticação:", error);

        // Em caso de erro, redirecionar para login
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        navigate("/login");
      }
    };

    checkAuth();
  }, [navigate, location]);

  // Responsive behavior - mobile overlay behavior
  useEffect(() => {
    const handleResize = (): void => {
      const mobile = window.innerWidth < 1024; // lg breakpoint
      setIsMobile(mobile);

      if (mobile) {
        setSidebarCollapsed(true);
        setSidebarOpen(false); // Close sidebar when switching to mobile
      } else {
        setSidebarOpen(false); // Ensure overlay is closed on desktop
      }
    };

    handleResize(); // Check initial size
    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleSidebar = (): void => {
    if (isMobile) {
      setSidebarOpen(!sidebarOpen);
    } else {
      setSidebarCollapsed(!sidebarCollapsed);
    }
  };

  // Close mobile sidebar when clicking outside
  const closeMobileSidebar = (): void => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    }
  };

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isMobile, sidebarOpen]);

  // Close mobile sidebar on route change
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    }
  }, [location.pathname, isMobile, sidebarOpen]);

  // Generate breadcrumb
  const generateBreadcrumb = (): string => {
    const pathnames = location.pathname.split("/").filter((x) => x);
    const breadcrumbs = ["Home"];

    pathnames.forEach((pathname) => {
      let label = pathname.charAt(0).toUpperCase() + pathname.slice(1);

      const customLabels: Record<string, string> = {
        admin: "Admin",
        dashboard: "Dashboard",
        demo: "Layout Demo",
        notifications: "Demo de Notificações",
      };

      if (customLabels[pathname]) {
        label = customLabels[pathname];
      }

      breadcrumbs.push(label);
    });

    return breadcrumbs.join(" / ");
  };

  // Mostrar loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"
            role="status"
            aria-label="Carregando"
          ></div>
          <p className="mt-4 text-muted-foreground">
            Verificando autenticação...
          </p>
        </div>
      </div>
    );
  }

  // Só renderizar se estiver autenticado
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-100 dark:bg-gray-900">
      {/* Skip Link */}
      <a
        href="#main-content"
        className="skip-link sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[9999] focus:bg-primary focus:text-white focus:px-4 focus:py-2 focus:rounded-md focus:no-underline"
      >
        Pular para conteúdo principal
      </a>

      {/* Desktop Sidebar */}
      {!isMobile && (
        <aside
          className={`${
            sidebarCollapsed ? "w-16" : "w-64"
          } transition-all duration-300 ease-in-out flex-shrink-0`}
          role="navigation"
          aria-label="Menu principal"
        >
          <Sidebar collapsed={sidebarCollapsed} />
        </aside>
      )}

      {/* Mobile Sidebar Overlay */}
      {isMobile && (
        <>
          {/* Backdrop */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden animate-fade-in"
              onClick={closeMobileSidebar}
              aria-hidden="true"
            />
          )}

          {/* Mobile Sidebar */}
          <aside
            className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out lg:hidden ${
              sidebarOpen ? "translate-x-0" : "-translate-x-full"
            }`}
            role="navigation"
            aria-label="Menu principal"
            aria-hidden={!sidebarOpen}
          >
            <Sidebar collapsed={false} />
          </aside>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header
          sidebarCollapsed={isMobile ? false : sidebarCollapsed}
          onToggleSidebar={toggleSidebar}
          breadcrumb={generateBreadcrumb()}
          isMobile={isMobile}
          sidebarOpen={sidebarOpen}
        />

        {/* Main Content Area */}
        <main
          id="main-content"
          className="flex-1 relative overflow-y-auto focus:outline-none"
          onClick={closeMobileSidebar}
          role="main"
          aria-label="Conteúdo principal da página"
          tabIndex={-1}
        >
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              <Outlet />
            </div>
          </div>
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
});

AdminLayout.displayName = "AdminLayout";

export default AdminLayout;
