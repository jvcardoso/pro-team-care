import React, { useState, useRef, useEffect } from "react";
import { useTheme } from "../../contexts/ThemeContext";
import { authService } from "../../services/api";
import ProfileSwitcher from "../security/ProfileSwitcher";
import {
  Sun,
  Moon,
  Menu,
  Bell,
  User,
  Settings,
  LogOut,
  Mail,
  Search,
  ChevronDown,
  X,
} from "lucide-react";

const Header = ({
  sidebarCollapsed,
  onToggleSidebar,
  breadcrumb,
  isMobile,
  sidebarOpen,
}) => {
  const { theme, toggleTheme, isDark } = useTheme();
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [messagesOpen, setMessagesOpen] = useState(false);

  const notificationRef = useRef(null);
  const userMenuRef = useRef(null);
  const messagesRef = useRef(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        notificationRef.current &&
        !notificationRef.current.contains(event.target)
      ) {
        setNotificationOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
      if (messagesRef.current && !messagesRef.current.contains(event.target)) {
        setMessagesOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const notifications = [
    {
      id: 1,
      title: "Nova mensagem",
      content: "João Silva enviou uma mensagem",
      time: "2 min",
      unread: true,
    },
    {
      id: 2,
      title: "Alerta do sistema",
      content: "Backup agendado para hoje às 22:00",
      time: "1h",
      unread: true,
    },
    {
      id: 3,
      title: "Atualização",
      content: "Relatório mensal disponível",
      time: "3h",
      unread: false,
    },
  ];

  const messages = [
    {
      id: 1,
      sender: "Maria Santos",
      content: "Relatório de pacientes está pronto",
      time: "5 min",
      avatar: "MS",
    },
    {
      id: 2,
      sender: "Dr. João Silva",
      content: "Precisamos revisar os protocolos",
      time: "1h",
      avatar: "JS",
    },
    {
      id: 3,
      sender: "Ana Costa",
      content: "Reunião confirmada para amanhã",
      time: "2h",
      avatar: "AC",
    },
  ];

  const unreadNotifications = notifications.filter((n) => n.unread).length;
  const unreadMessages = messages.length;

  const handleLogout = () => {
    authService.logout();
  };

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 h-16 flex-shrink-0">
      <div className="h-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-full">
          {/* Left Section */}
          <div className="flex items-center space-x-4">
            {/* Menu Toggle & Logo */}
            <div className="flex items-center space-x-4">
              {/* Sidebar Toggle - Funciona em todas as resoluções */}
              <button
                onClick={onToggleSidebar}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors"
                title={
                  isMobile
                    ? sidebarOpen
                      ? "Fechar menu"
                      : "Abrir menu"
                    : sidebarCollapsed
                    ? "Expandir sidebar"
                    : "Recolher sidebar"
                }
              >
                {isMobile && sidebarOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </button>

              {/* Logo - Desktop only */}
              <div className="hidden lg:flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">PC</span>
                </div>
                <div className="hidden xl:block">
                  <h1 className="text-sm font-semibold text-gray-900 dark:text-white">
                    Pro Team Care
                  </h1>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    AdminLTE Style
                  </p>
                </div>
              </div>
            </div>

            {/* Breadcrumb */}
            {breadcrumb && (
              <nav className="hidden md:flex text-sm text-gray-500 dark:text-gray-400 ml-4">
                {breadcrumb}
              </nav>
            )}
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-2">
            {/* Search - Desktop only */}
            <div className="hidden lg:block">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Buscar..."
                  className="pl-10 pr-4 py-2 w-64 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-500 dark:focus:border-blue-500 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                />
              </div>
            </div>

            {/* Profile Switcher - ROOT controls */}
            <ProfileSwitcher />

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              title={`Mudar para tema ${isDark ? "claro" : "escuro"}`}
            >
              {isDark ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>

            {/* Notifications */}
            <div className="relative" ref={notificationRef}>
              <button
                onClick={() => setNotificationOpen(!notificationOpen)}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 relative"
              >
                <Bell className="h-5 w-5" />
                {unreadNotifications > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unreadNotifications}
                  </span>
                )}
              </button>

              {/* Notifications Dropdown */}
              {notificationOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 animate-fade-in z-50">
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Notificações
                      </h3>
                      <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full">
                        {unreadNotifications} novas
                      </span>
                    </div>
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className="p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                      >
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {notification.content}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                          {notification.time} atrás
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Messages */}
            <div className="relative" ref={messagesRef}>
              <button
                onClick={() => setMessagesOpen(!messagesOpen)}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 relative"
              >
                <Mail className="h-5 w-5" />
                {unreadMessages > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-4 w-4 bg-green-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unreadMessages}
                  </span>
                )}
              </button>

              {/* Messages Dropdown */}
              {messagesOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 animate-fade-in z-50">
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      Mensagens
                    </h3>
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className="p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                      >
                        <div className="flex items-start space-x-3">
                          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
                            {message.avatar}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {message.sender}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                              {message.content}
                            </p>
                            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                              {message.time} atrás
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* User Menu */}
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">AD</span>
                </div>
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
                    Admin User
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Administrador
                  </p>
                </div>
                <ChevronDown className="h-4 w-4 text-gray-400" />
              </button>

              {/* User Dropdown */}
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 animate-fade-in z-50">
                  <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      Admin User
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      admin@procare.com
                    </p>
                  </div>
                  <div className="py-1">
                    <a
                      href="#"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <User className="h-4 w-4 mr-3" />
                      Meu Perfil
                    </a>
                    <a
                      href="#"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <Settings className="h-4 w-4 mr-3" />
                      Configurações
                    </a>
                    <hr className="my-1 border-gray-200 dark:border-gray-600" />
                    <button
                      onClick={handleLogout}
                      className="w-full text-left flex items-center px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <LogOut className="h-4 w-4 mr-3" />
                      Sair
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
