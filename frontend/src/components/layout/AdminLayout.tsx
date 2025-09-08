import React, { useState, useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import Header from "./Header";
import Sidebar from "./Sidebar";
import DynamicSidebar from "../navigation/DynamicSidebar";
import Footer from "./Footer";
import ImpersonationBanner from "../security/ImpersonationBanner";

const AdminLayout: React.FC = React.memo(() => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [useDynamicMenus, setUseDynamicMenus] = useState<boolean>(true);
  const location = useLocation();
  const navigate = useNavigate();

  // 🔒 Verificar autenticação com validação JWT real
  useEffect(() => {
    const checkAuth = async (): Promise<void> => {
      try {
        // Primeiro, verificar se existe token no localStorage
        const token = localStorage.getItem("access_token");
        if (!token) {
          console.info("Token não encontrado - redirecionando para login");
          navigate("/login");
          return;
        }

        // Se tem token, tentar validar com backend
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

  // Close mobile sidebar when clicking outside - with event detection
  const closeMobileSidebar = (event?: React.MouseEvent): void => {
    if (isMobile && sidebarOpen) {
      // Only close if it's a genuine outside click, not a menu interaction
      if (event && event.target) {
        const target = event.target as Element;
        // Don't close if clicking on menu items or their children
        if (
          target.closest(".menu-item-container") ||
          target.closest('[data-testid="menu-item"]')
        ) {
          return;
        }
      }
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

  // Close mobile sidebar on route change - but only for navigation clicks, not expansion
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      // Add a small delay to differentiate between menu expansion and navigation
      const timeoutId = setTimeout(() => {
        setSidebarOpen(false);
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [location.pathname]);

  // Garantir consistência do estado da sidebar em mobile
  useEffect(() => {
    if (isMobile) {
      // Em mobile, sempre manter sidebarCollapsed como true
      setSidebarCollapsed(true);
    }
  }, [isMobile]);

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

  // Toggle para desenvolvimento: alternar entre menus dinâmicos e estáticos
  const toggleMenuType = (): void => {
    setUseDynamicMenus((prev) => {
      const newValue = !prev;
      console.log(
        `🔄 Alternando menus: ${newValue ? "Dinâmicos" : "Estáticos"}`
      );

      // Salvar preferência localmente
      localStorage.setItem("useDynamicMenus", newValue.toString());

      return newValue;
    });
  };

  // Toggle para desenvolvimento: alternar entre usuário normal e ROOT
  const toggleUserType = (): void => {
    const isRoot = localStorage.getItem("testAsRoot") === "true";
    const newValue = !isRoot;

    localStorage.setItem("testAsRoot", newValue.toString());
    console.log(
      `🔄 Alternando usuário: ${newValue ? "ROOT (ID: 2)" : "Normal (ID: 1)"}`
    );

    // Recarregar página para aplicar mudança
    window.location.reload();
  };

  // Carregar preferência salva
  useEffect(() => {
    const saved = localStorage.getItem("useDynamicMenus");
    if (saved !== null) {
      setUseDynamicMenus(saved === "true");
    }
  }, []);

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
          {useDynamicMenus ? (
            <DynamicSidebar collapsed={sidebarCollapsed} />
          ) : (
            <Sidebar collapsed={sidebarCollapsed} />
          )}
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
            {useDynamicMenus ? (
              <DynamicSidebar collapsed={false} />
            ) : (
              <Sidebar collapsed={false} />
            )}
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

        {/* Impersonation Banner */}
        <ImpersonationBanner />

        {/* Development Controls - Only in development */}
        {import.meta.env.DEV && (
          <div className="bg-yellow-100 border-b border-yellow-200 px-4 py-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <span className="text-yellow-800">
                  🔧 Menus:{" "}
                  {useDynamicMenus ? "Dinâmicos (API)" : "Estáticos (Mock)"}
                </span>
                <span className="text-yellow-800">
                  👤 Usuário:{" "}
                  {localStorage.getItem("testAsRoot") === "true"
                    ? "ROOT (ID: 2)"
                    : "Normal (ID: 1)"}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleMenuType}
                  className="text-yellow-700 hover:text-yellow-900 underline text-xs"
                >
                  Alternar Menus
                </button>
                <button
                  onClick={toggleUserType}
                  className="text-yellow-700 hover:text-yellow-900 underline text-xs"
                >
                  Alternar Usuário
                </button>
              </div>
            </div>
          </div>
        )}

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
