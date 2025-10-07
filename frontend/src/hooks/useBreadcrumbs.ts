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
      contratos: "Contratos",
      vidas: "Vidas",
      autorizacoes: "Autorizações Médicas",
      faturamento: "Faturamento",
      faturas: "Faturas",
      b2b: "Cobrança B2B",
      planos: "Planos de Assinatura",
      servicos: "Catálogo de Serviços",
      relatorios: "Relatórios",
      perfis: "Perfis de Acesso",
      "notification-demo": "Demonstração de Notificações",
      "flowbite-table-exemplo": "Exemplo de Tabela",
      visualizar: "Visualizar",
      editar: "Editar",
      configuracoes: "Configurações",
    };

    // Adicionar segmentos da rota
    pathSegments.forEach((segment, index) => {
      if (segment === "admin") return; // Já adicionado

      // Para empresas, substituir ID pelo nome da empresa se disponível
      if (
        pathSegments.includes("empresas") &&
        /^\d+$/.test(segment) &&
        index > 0
      ) {
        const companyName = localStorage.getItem(`company_name_${segment}`);
        if (companyName) {
          breadcrumbs.push({
            label: companyName,
            href: "/" + pathSegments.slice(0, index + 1).join("/"),
            current: false,
          });
        }
        return;
      }

      // Para clientes, substituir ID pelo nome do cliente se disponível
      if (
        pathSegments.includes("clientes") &&
        /^\d+$/.test(segment) &&
        index > 0
      ) {
        const clientName = localStorage.getItem(`client_name_${segment}`);
        if (clientName) {
          breadcrumbs.push({
            label: clientName,
            href: "/" + pathSegments.slice(0, index + 1).join("/"),
            current: false,
          });
        }
        return;
      }

      // Para estabelecimentos, substituir ID pelo nome se disponível
      if (
        pathSegments.includes("estabelecimentos") &&
        /^\d+$/.test(segment) &&
        index > 0
      ) {
        const establishmentName = localStorage.getItem(
          `establishment_name_${segment}`
        );
        if (establishmentName) {
          breadcrumbs.push({
            label: establishmentName,
            href: "/" + pathSegments.slice(0, index + 1).join("/"),
            current: false,
          });
        }
        return;
      }

      // Para contratos, substituir ID pelo código do contrato se disponível
      if (
        pathSegments.includes("contratos") &&
        /^\d+$/.test(segment) &&
        index > 0
      ) {
        const contractCode = localStorage.getItem(`contract_code_${segment}`);
        if (contractCode) {
          breadcrumbs.push({
            label: `Contrato ${contractCode}`,
            href: "/" + pathSegments.slice(0, index + 1).join("/"),
            current: false,
          });
        }
        return;
      }

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
        faturamento: "Faturamento",
        configuracoes: "Configurações",
        historico: "Histórico",
      };

      const tabLabel = tabLabels[tab];
      if (tabLabel) {
        breadcrumbs.push({
          label: tabLabel,
          current: true,
        });
      }
    }

    return breadcrumbs;
  }, [location.pathname, searchParams]);
};
