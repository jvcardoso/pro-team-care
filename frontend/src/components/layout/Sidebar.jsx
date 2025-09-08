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
} from "lucide-react";

const Sidebar = ({ collapsed }) => {
  const location = useLocation();
  const [expandedMenus, setExpandedMenus] = useState({
    dashboard: false,
    components: false,
    examples: false,
    pages: false,
    healthcare: false,
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
      badge: { text: "Hot", color: "bg-red-500" },
      submenu: [
        {
          label: "Dashboard v1",
          path: "/admin/dashboard",
          icon: <BarChart3 className="h-4 w-4" />,
        },
        {
          label: "Dashboard v2",
          path: "/admin/dashboard-v2",
          icon: <PieChart className="h-4 w-4" />,
        },
        {
          label: "Dashboard v3",
          path: "/admin/dashboard-v3",
          icon: <TrendingUp className="h-4 w-4" />,
        },
      ],
    },
    {
      key: "components",
      label: "Componentes",
      icon: <LayoutGrid className="h-5 w-5" />,
      badge: { text: "New", color: "bg-blue-500" },
      submenu: [
        {
          label: "Widgets",
          path: "/admin/widgets",
          icon: <Palette className="h-4 w-4" />,
          badge: { text: "12", color: "bg-green-500" },
        },
        {
          label: "Charts",
          path: "/admin/charts",
          icon: <BarChart3 className="h-4 w-4" />,
        },
        {
          label: "UI Elements",
          path: "/admin/ui",
          icon: <LayoutGrid className="h-4 w-4" />,
        },
        {
          label: "Forms",
          path: "/admin/forms",
          icon: <FormInput className="h-4 w-4" />,
        },
        {
          label: "Tables",
          path: "/admin/tables",
          icon: <Table className="h-4 w-4" />,
        },
      ],
    },
    {
      key: "examples",
      label: "Exemplos",
      icon: <BookOpen className="h-5 w-5" />,
      submenu: [
        {
          label: "Calendar",
          path: "/admin/calendar",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Gallery",
          path: "/admin/gallery",
          icon: <Image className="h-4 w-4" />,
        },
        {
          label: "Kanban",
          path: "/admin/kanban",
          icon: <Kanban className="h-4 w-4" />,
        },
        {
          label: "Mailbox",
          path: "/admin/mailbox",
          icon: <Mail className="h-4 w-4" />,
        },
      ],
    },
    {
      key: "pages",
      label: "Páginas",
      icon: <FileText className="h-5 w-5" />,
      submenu: [
        {
          label: "Invoice",
          path: "/admin/invoice",
          icon: <Receipt className="h-4 w-4" />,
        },
        {
          label: "Profile",
          path: "/admin/profile",
          icon: <User className="h-4 w-4" />,
        },
        {
          label: "Projects",
          path: "/admin/projects",
          icon: <Building className="h-4 w-4" />,
        },
        {
          label: "Contacts",
          path: "/admin/contacts",
          icon: <Users className="h-4 w-4" />,
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
          label: "Relatórios",
          path: "/admin/reports",
          icon: <FileText className="h-4 w-4" />,
        },
      ],
    },
    {
      key: "extras",
      label: "Extras",
      icon: <Settings className="h-5 w-5" />,
      submenu: [
        {
          label: "Login",
          path: "/admin/login-demo",
          icon: <LogIn className="h-4 w-4" />,
        },
        {
          label: "Register",
          path: "/admin/register-demo",
          icon: <UserPlus className="h-4 w-4" />,
        },
        {
          label: "Lockscreen",
          path: "/admin/lockscreen",
          icon: <Lock className="h-4 w-4" />,
        },
        {
          label: "Error 404",
          path: "/admin/404-demo",
          icon: <FileX className="h-4 w-4" />,
        },
        {
          label: "DB Admin",
          path: "#",
          icon: <Database className="h-4 w-4" />,
          badge: { text: "New", color: "bg-green-500" },
          onClick: () => window.open("/simple_db_admin.html", "_blank"),
          external: true,
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
