import { useLocation, useSearchParams } from "react-router-dom";
import { useMemo } from "react";

interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

export const useBreadcrumbs = (): BreadcrumbItem[] => {
  const location = useLocation();
  const [searchParams] = useSearchParams();

  return useMemo(() => {
    const pathSegments = location.pathname.split("/").filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Sempre começar com Admin
    if (pathSegments.includes("admin")) {
      breadcrumbs.push({
        label: "Admin",
        href: "/admin",
        current: pathSegments.length === 1,
      });
    }

    // Mapear rotas para labels
    const routeLabels: Record<string, string> = {
      dashboard: "Dashboard",
      empresas: "Empresas",
      estabelecimentos: "Estabelecimentos",
      clientes: "Clientes",
      profissionais: "Profissionais",
      pacientes: "Pacientes",
      usuarios: "Usuários",
      menus: "Menus",
      consultas: "Consultas",
      "notification-demo": "Demonstração de Notificações",
    };

    // Adicionar segmentos da rota
    pathSegments.forEach((segment, index) => {
      if (segment === "admin") return; // Já adicionado

      const label =
        routeLabels[segment] ||
        segment.charAt(0).toUpperCase() + segment.slice(1);
      const href = "/" + pathSegments.slice(0, index + 1).join("/");
      const isLast = index === pathSegments.length - 1;

      breadcrumbs.push({
        label,
        href: isLast ? undefined : href,
        current: isLast,
      });
    });

    // Verificar se há parâmetros de navegação específicos
    const tab = searchParams.get("tab");
    const companyId = searchParams.get("companyId");

    if (tab && breadcrumbs.length > 0) {
      const tabLabels: Record<string, string> = {
        informacoes: "Informações",
        estabelecimentos: "Estabelecimentos",
        clientes: "Clientes",
        profissionais: "Profissionais",
        pacientes: "Pacientes",
        usuarios: "Usuários",
        lgpd: "LGPD",
      };

      const tabLabel = tabLabels[tab];
      if (tabLabel) {
        // Se estamos em empresas e temos companyId, adicionar nome da empresa
        if (
          pathSegments.includes("empresas") &&
          companyId &&
          tab !== "estabelecimentos"
        ) {
          breadcrumbs.push({
            label: `Empresa #${companyId}`,
            href: `/admin/empresas?companyId=${companyId}&tab=informacoes`,
            current: false,
          });
        }

        breadcrumbs.push({
          label: tabLabel,
          current: true,
        });
      }
    } else if (companyId && pathSegments.includes("empresas")) {
      // Se estamos em empresas com companyId mas sem tab específica
      breadcrumbs.push({
        label: `Empresa #${companyId}`,
        current: true,
      });
    }

    return breadcrumbs;
  }, [location.pathname, searchParams]);
};
