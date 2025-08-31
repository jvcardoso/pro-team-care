import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

const AdminLayout = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  // Verificar autenticação
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        // Salvar URL atual para redirecionar após login
        const currentPath = location.pathname + location.search;
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        navigate('/login');
        return;
      }
      setIsAuthenticated(true);
      setIsLoading(false);
    };

    checkAuth();
  }, [navigate, location]);

  // Responsive behavior - mobile overlay behavior
  useEffect(() => {
    const handleResize = () => {
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
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleSidebar = () => {
    if (isMobile) {
      setSidebarOpen(!sidebarOpen);
    } else {
      setSidebarCollapsed(!sidebarCollapsed);
    }
  };

  // Close mobile sidebar when clicking outside
  const closeMobileSidebar = () => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    }
  };

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobile, sidebarOpen]);

  // Close mobile sidebar on route change
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      setSidebarOpen(false);
    }
  }, [location.pathname]);

  // Generate breadcrumb
  const generateBreadcrumb = () => {
    const pathnames = location.pathname.split('/').filter(x => x);
    const breadcrumbs = ['Home'];
    
    pathnames.forEach((pathname) => {
      let label = pathname.charAt(0).toUpperCase() + pathname.slice(1);
      
      const customLabels = {
        'admin': 'Admin',
        'dashboard': 'Dashboard',
        'demo': 'Layout Demo',
        'notifications': 'Demo de Notificações',
      };
      
      if (customLabels[pathname]) {
        label = customLabels[pathname];
      }
      
      breadcrumbs.push(label);
    });

    return breadcrumbs.join(' / ');
  };

  // Mostrar loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Verificando autenticação...</p>
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
      {/* Desktop Sidebar */}
      {!isMobile && (
        <div
          className={`${
            sidebarCollapsed ? 'w-16' : 'w-64'
          } transition-all duration-300 ease-in-out flex-shrink-0`}
        >
          <Sidebar collapsed={sidebarCollapsed} />
        </div>
      )}

      {/* Mobile Sidebar Overlay */}
      {isMobile && (
        <>
          {/* Backdrop */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden animate-fade-in"
              onClick={closeMobileSidebar}
            />
          )}
          
          {/* Mobile Sidebar */}
          <div
            className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out lg:hidden ${
              sidebarOpen ? 'translate-x-0' : '-translate-x-full'
            }`}
          >
            <Sidebar collapsed={false} />
          </div>
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
          className="flex-1 relative overflow-y-auto focus:outline-none"
          onClick={closeMobileSidebar}
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
};

export default AdminLayout;