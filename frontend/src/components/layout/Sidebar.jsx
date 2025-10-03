import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  UserPlus,
  Activity,
  Heart,
  Calendar,
  FileText,
  BarChart3,
  PieChart,
  TrendingUp,
  Palette,
  LayoutGrid,
  Table,
  FormInput,
  BookOpen,
  Kanban,
  Mail,
  Image,
  Receipt,
  User,
  Building,
  FileX,
  LogIn,
  Lock,
  Settings,
  ChevronDown,
  ChevronRight,
  Bell,
  Database,
  Package,
  CreditCard,
  DollarSign,
} from "lucide-react";

const Sidebar = ({ collapsed }) => {
  const location = useLocation();
  const [expandedMenus, setExpandedMenus] = useState({
    dashboard: false,
    components: false,
    examples: false,
    pages: false,
    healthcare: false,
    billing: false,
    extras: false,
  });

  const toggleSubmenu = (menuKey) => {
    setExpandedMenus((prev) => ({
      ...prev,
      [menuKey]: !prev[menuKey],
    }));
  };

  const menuItems = [
    {
      key: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard className="h-5 w-5" />,
      path: "/admin/dashboard",
    },
    {
      key: "examples",
      label: "Templates & Exemplos",
      icon: <BookOpen className="h-5 w-5" />,
      badge: { text: "Demo", color: "bg-green-500" },
      submenu: [
        {
          label: "Notificações",
          path: "/admin/notification-demo",
          icon: <Bell className="h-4 w-4" />,
          badge: { text: "Novo", color: "bg-blue-500" },
        },
      ],
    },
    {
      key: "healthcare",
      label: "Home Care",
      icon: <Heart className="h-5 w-5" />,
      badge: { text: "Pro", color: "bg-purple-500" },
      submenu: [
        {
          label: "Pacientes",
          path: "/admin/patients",
          icon: <Activity className="h-4 w-4" />,
          badge: { text: "24", color: "bg-blue-500" },
        },
        {
          label: "Consultas",
          path: "/admin/consultas",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Profissionais",
          path: "/admin/profissionais",
          icon: <Users className="h-4 w-4" />,
        },
        {
          label: "Empresas",
          path: "/admin/empresas",
          icon: <Building className="h-4 w-4" />,
        },
        {
          label: "Estabelecimentos",
          path: "/admin/estabelecimentos",
          icon: <Building className="h-4 w-4" />,
        },
        {
          label: "Clientes",
          path: "/admin/clientes",
          icon: <UserPlus className="h-4 w-4" />,
        },
        {
          label: "Contratos",
          path: "/admin/contratos",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Catálogo de Serviços",
          path: "/admin/servicos",
          icon: <Package className="h-4 w-4" />,
        },
        {
          label: "Autorizações Médicas",
          path: "/admin/autorizacoes",
          icon: <Heart className="h-4 w-4" />,
        },
        {
          label: "Usuários",
          path: "/admin/usuarios",
          icon: <Users className="h-4 w-4" />,
        },
        {
          label: "Perfis",
          path: "/admin/perfis",
          icon: <Lock className="h-4 w-4" />,
        },
        {
          label: "Menus",
          path: "/admin/menus",
          icon: <Settings className="h-4 w-4" />,
        },
      ],
    },
    {
      key: "billing",
      label: "Faturamento",
      icon: <CreditCard className="h-5 w-5" />,
      badge: { text: "B2B", color: "bg-indigo-500" },
      submenu: [
        {
          label: "Dashboard",
          path: "/admin/faturamento/dashboard",
          icon: <BarChart3 className="h-4 w-4" />,
        },
        {
          label: "Faturas",
          path: "/admin/faturamento/faturas",
          icon: <Receipt className="h-4 w-4" />,
        },
        {
          label: "Faturamento B2B",
          path: "/admin/faturamento/b2b",
          icon: <DollarSign className="h-4 w-4" />,
        },
        {
          label: "Planos de Assinatura",
          path: "/admin/faturamento/planos",
          icon: <Package className="h-4 w-4" />,
          badge: { text: "Novo", color: "bg-green-500" },
        },
      ],
    },
  ];

  const isActiveItem = (path) => {
    return location.pathname === path;
  };

  const hasActiveSubmenu = (submenu) => {
    return submenu.some((item) => isActiveItem(item.path));
  };

  return (
    <div
      className="h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col"
      data-testid="static-sidebar"
    >
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        {!collapsed && (
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-lg">PC</span>
            </div>
            <div className="min-w-0">
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                Pro Team Care
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                AdminLTE Style
              </p>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="flex justify-center">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">PC</span>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        <div className="px-3 space-y-1">
          {/* Menu Items */}
          {menuItems.map((item) => (
            <div key={item.key}>
              {item.submenu ? (
                <>
                  <button
                    onClick={() => toggleSubmenu(item.key)}
                    className={`group w-full flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors ${
                      hasActiveSubmenu(item.submenu)
                        ? "bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    }`}
                  >
                    <div className="flex items-center flex-1 min-w-0">
                      {item.icon}
                      {!collapsed && (
                        <>
                          <span className="ml-3 truncate">{item.label}</span>
                          {item.badge && (
                            <span
                              className={`ml-auto inline-block py-0.5 px-2 text-xs text-white rounded-full ${item.badge.color}`}
                            >
                              {item.badge.text}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                    {!collapsed && (
                      <ChevronDown
                        className={`ml-2 h-4 w-4 transition-transform ${
                          expandedMenus[item.key] ? "rotate-180" : ""
                        }`}
                      />
                    )}
                  </button>

                  {/* Submenu */}
                  {!collapsed && expandedMenus[item.key] && (
                    <div className="mt-1 ml-6 space-y-1">
                      {item.submenu.map((subItem, index) => (
                        <Link
                          key={index}
                          to={subItem.path}
                          className={`group flex items-center px-2 py-2 text-sm rounded-lg transition-colors ${
                            isActiveItem(subItem.path)
                              ? "bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                              : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                          }`}
                        >
                          {subItem.icon}
                          <span className="ml-3 flex-1 truncate">
                            {subItem.label}
                          </span>
                          {subItem.badge && (
                            <span
                              className={`ml-auto inline-block py-0.5 px-1.5 text-xs text-white rounded-full ${subItem.badge.color}`}
                            >
                              {subItem.badge.text}
                            </span>
                          )}
                        </Link>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <Link
                  to={item.path}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActiveItem(item.path)
                      ? "bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400"
                      : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  }`}
                >
                  {item.icon}
                  {!collapsed && (
                    <>
                      <span className="ml-3 flex-1 truncate">{item.label}</span>
                      {item.badge && (
                        <span
                          className={`ml-auto inline-block py-0.5 px-2 text-xs text-white rounded-full ${item.badge.color}`}
                        >
                          {item.badge.text}
                        </span>
                      )}
                    </>
                  )}
                </Link>
              )}
            </div>
          ))}
        </div>
      </nav>

      {/* Sidebar Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {!collapsed && (
          <div className="text-center">
            <p className="text-xs font-medium text-gray-900 dark:text-white">
              Pro Team Care
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              v1.0.0 - Build 2024
            </p>
          </div>
        )}
        {collapsed && (
          <div className="flex justify-center">
            <div className="w-6 h-6 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center">
              <Settings className="h-3 w-3 text-gray-600 dark:text-gray-400" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
