/**
 * Componente DynamicSidebar - Sidebar dinâmica com menus baseados em permissões
 * Substitui a sidebar estática carregando menus da API conforme o usuário
 */

import React, { useState, useEffect } from "react";
import { useDynamicMenus } from "../../hooks/useDynamicMenus";
import { MenuItem } from "./MenuItem";
import { MobileSafeMenuItem } from "./MobileSafeMenuItem";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { Alert } from "../ui/Alert";
import {
  RefreshCw,
  AlertCircle,
  Crown,
  Clock,
  Database,
  Wifi,
  WifiOff,
} from "lucide-react";

/**
 * Componente DynamicSidebar
 *
 * @param {boolean} collapsed - Se a sidebar está colapsada
 * @param {string} className - Classes CSS adicionais
 */
export const DynamicSidebar = ({ collapsed = false, className = "" }) => {
  console.log("🔧 DEBUG: DynamicSidebar renderizado - collapsed:", collapsed);

  const {
    menus,
    loading,
    error,
    refreshMenus,
    isRoot,
    userInfo,
    context,
    lastFetch,
    cacheAge,
  } = useDynamicMenus();

  console.log(
    "🔧 DEBUG: Hook retornou - loading:",
    loading,
    "menus:",
    menus?.length,
    "error:",
    error
  );

  const [expandedMenus, setExpandedMenus] = useState(new Set());
  const [showDebugInfo, setShowDebugInfo] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);

  // Detect touch device
  useEffect(() => {
    const hasTouch =
      "ontouchstart" in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0 ||
      (window.DocumentTouch && document instanceof window.DocumentTouch);
    setIsTouchDevice(hasTouch);
  }, []);

  /**
   * Handler para expandir/colapsar menus
   */
  const handleMenuToggle = (menuId, isExpanded) => {
    setExpandedMenus((prev) => {
      const newSet = new Set(prev);
      if (isExpanded) {
        newSet.add(menuId);
      } else {
        newSet.delete(menuId);
      }
      return newSet;
    });
  };

  /**
   * Auto-expandir menus com apenas 1 filho
   */
  useEffect(() => {
    if (menus.length > 0 && !collapsed) {
      const autoExpand = new Set();

      menus.forEach((menu) => {
        if (menu.children && menu.children.length === 1) {
          autoExpand.add(menu.id);
        }
      });

      if (autoExpand.size > 0) {
        setExpandedMenus((prev) => new Set([...prev, ...autoExpand]));
      }
    }
  }, [menus, collapsed]);

  /**
   * Renderiza header da sidebar
   */
  const renderHeader = () => (
    <div className="p-4 border-b border-gray-200 dark:border-gray-700">
      {!collapsed ? (
        <div className="flex items-center space-x-3">
          {/* Logo */}
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-lg">PC</span>
          </div>

          {/* Título e info */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                Pro Team Care
              </h1>
              {isRoot && (
                <Crown
                  size={16}
                  className="text-yellow-500 flex-shrink-0"
                  title="Usuário ROOT"
                />
              )}
            </div>

            {/* Contexto atual */}
            <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
              <Database size={12} />
              <span className="truncate">
                {context?.name || "Carregando..."}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center space-y-2">
          {/* Logo colapsado */}
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">PC</span>
          </div>

          {/* Indicadores colapsados */}
          {isRoot && (
            <Crown size={14} className="text-yellow-500" title="Usuário ROOT" />
          )}
        </div>
      )}
    </div>
  );

  /**
   * Renderiza estado de loading
   */
  const renderLoading = () => (
    <div
      className={`${className} flex items-center justify-center p-8`}
      data-testid="loading-spinner"
    >
      <div className="text-center">
        <LoadingSpinner className="mx-auto mb-3" />
        {!collapsed && (
          <div className="space-y-1">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Carregando menus...
            </p>
            <p className="text-xs text-gray-500">Aguarde um momento</p>
          </div>
        )}
      </div>
    </div>
  );

  /**
   * Renderiza estado de erro
   */
  const renderError = () => (
    <div className={`${className} p-4`} data-testid="error-message">
      <Alert
        type="error"
        title={collapsed ? "" : "Erro ao carregar menus"}
        className="mb-4"
      >
        {collapsed ? (
          <div className="flex flex-col items-center space-y-2">
            <WifiOff size={20} className="text-red-500" />
            <button
              onClick={refreshMenus}
              className="text-xs text-red-600 hover:underline"
              title="Tentar novamente"
            >
              Tentar
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm">{error}</p>
            <div className="flex items-center space-x-2">
              <button
                onClick={refreshMenus}
                className="text-sm text-red-600 hover:underline flex items-center space-x-1"
              >
                <RefreshCw size={14} />
                <span>Tentar novamente</span>
              </button>

              {/* Toggle debug info */}
              <button
                onClick={() => setShowDebugInfo(!showDebugInfo)}
                className="text-xs text-gray-500 hover:underline"
              >
                Debug
              </button>
            </div>

            {/* Debug info */}
            {showDebugInfo && (
              <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                <p>Usuário: {userInfo?.email || "N/A"}</p>
                <p>Contexto: {context?.type || "N/A"}</p>
                <p>Último fetch: {lastFetch || "Nunca"}</p>
                <p>Menus fallback: {menus.length}</p>
              </div>
            )}
          </div>
        )}
      </Alert>
    </div>
  );

  /**
   * Renderiza lista de menus
   */
  const renderMenus = () => {
    if (menus.length === 0) {
      return (
        <div className="p-4 text-center">
          {collapsed ? (
            <AlertCircle
              size={20}
              className="text-gray-400 mx-auto"
              title="Nenhum menu disponível"
            />
          ) : (
            <div className="space-y-2">
              <AlertCircle size={24} className="text-gray-400 mx-auto" />
              <p className="text-sm text-gray-500">Nenhum menu disponível</p>
              <button
                onClick={refreshMenus}
                className="text-xs text-blue-600 hover:underline"
              >
                Recarregar menus
              </button>
            </div>
          )}
        </div>
      );
    }

    return (
      <nav className="flex-1 overflow-y-auto py-4">
        <div className="px-3 space-y-1">
          {menus.map((menu) => {
            // Use MobileSafeMenuItem for touch devices to prevent toggle issues
            const MenuComponent = isTouchDevice ? MobileSafeMenuItem : MenuItem;

            return (
              <MenuComponent
                key={menu.id}
                menu={menu}
                level={0}
                collapsed={collapsed}
                onToggle={handleMenuToggle}
              />
            );
          })}
        </div>
      </nav>
    );
  };

  /**
   * Renderiza footer da sidebar
   */
  const renderFooter = () => (
    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
      {!collapsed ? (
        <div className="space-y-2">
          {/* Info do usuário */}
          <div className="text-center">
            <p className="text-xs font-medium text-gray-900 dark:text-white truncate">
              {userInfo?.name || "Pro Team Care"}
            </p>
            <div className="flex items-center justify-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
              <span>v1.0.0</span>
              {error ? (
                <WifiOff size={10} className="text-red-500" title="Offline" />
              ) : (
                <Wifi size={10} className="text-green-500" title="Online" />
              )}
            </div>
          </div>

          {/* Cache info (só em development) */}
          {process.env.NODE_ENV === "development" && lastFetch && (
            <div className="flex items-center justify-center space-x-1 text-xs text-gray-400">
              <Clock size={10} />
              <span title={`Última atualização: ${lastFetch}`}>
                Cache: {cacheAge}s
              </span>
            </div>
          )}

          {/* Botão de refresh */}
          <div className="flex justify-center">
            <button
              onClick={refreshMenus}
              disabled={loading}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
              title="Atualizar menus"
              data-testid="refresh-menus-button"
            >
              <RefreshCw
                size={14}
                className={`text-gray-500 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center space-y-2">
          {/* Status indicator */}
          {error ? (
            <WifiOff
              size={14}
              className="text-red-500"
              title="Erro de conexão"
            />
          ) : (
            <Wifi size={14} className="text-green-500" title="Conectado" />
          )}

          {/* Refresh button */}
          <button
            onClick={refreshMenus}
            disabled={loading}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
            title="Atualizar menus"
          >
            <RefreshCw
              size={12}
              className={`text-gray-500 ${loading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div
      className={`h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col ${className}`}
      data-testid="dynamic-sidebar"
    >
      {/* Header */}
      {renderHeader()}

      {/* Content */}
      {loading ? renderLoading() : error ? renderError() : renderMenus()}

      {/* Footer */}
      {renderFooter()}
    </div>
  );
};

export default DynamicSidebar;
