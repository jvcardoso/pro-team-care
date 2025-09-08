/**
 * MenuDebugPanel - Painel de debug para mostrar variáveis do menu
 * Usado para diagnosticar problema mobile onde variáveis não são iniciadas
 */

import React from "react";
import { useDynamicMenus } from "../../hooks/useDynamicMenus";

export const MenuDebugPanel = () => {
  console.log("🔧 DEBUG: MenuDebugPanel renderizado");

  const {
    menus,
    loading,
    error,
    isRoot,
    userInfo,
    context,
    lastFetch,
    refreshMenus,
  } = useDynamicMenus();

  console.log("🔧 DEBUG: MenuDebugPanel - hook executado");

  const debugInfo = {
    loading,
    menusLength: menus?.length || 0,
    error,
    isRoot,
    userInfo,
    context,
    lastFetch,
    hasToken: !!localStorage.getItem("access_token"),
    tokenPreview:
      localStorage.getItem("access_token")?.substring(0, 20) + "..." || "null",
  };

  console.log("🔧 DEBUG: Debug info:", debugInfo);

  return (
    <div
      className="fixed top-4 right-4 bg-black bg-opacity-75 text-white p-4 rounded-lg max-w-sm z-[9999] text-xs"
      style={{ fontSize: "10px", lineHeight: "1.2" }}
    >
      <div className="font-bold mb-2 text-red-400">🔧 MENU DEBUG</div>

      <div className="space-y-1">
        <div>
          <span className="text-yellow-300">Loading:</span>
          <span className={loading ? "text-red-400" : "text-green-400"}>
            {loading ? "TRUE" : "FALSE"}
          </span>
        </div>

        <div>
          <span className="text-yellow-300">Menus:</span>
          <span
            className={menus?.length > 0 ? "text-green-400" : "text-red-400"}
          >
            {menus?.length || 0} itens
          </span>
        </div>

        <div>
          <span className="text-yellow-300">Error:</span>
          <span className={error ? "text-red-400" : "text-green-400"}>
            {error ? "YES" : "NO"}
          </span>
        </div>

        <div>
          <span className="text-yellow-300">Token:</span>
          <span
            className={debugInfo.hasToken ? "text-green-400" : "text-red-400"}
          >
            {debugInfo.hasToken ? "EXISTS" : "MISSING"}
          </span>
        </div>

        <div>
          <span className="text-yellow-300">IsRoot:</span>
          <span className="text-blue-400">{isRoot ? "TRUE" : "FALSE"}</span>
        </div>

        <div>
          <span className="text-yellow-300">LastFetch:</span>
          <span className="text-blue-400">
            {lastFetch ? new Date(lastFetch).toLocaleTimeString() : "NULL"}
          </span>
        </div>

        {error && (
          <div className="mt-2 p-2 bg-red-900 rounded text-xs">
            <div className="text-red-300">Error Details:</div>
            <div className="text-red-100">{error}</div>
          </div>
        )}

        <div className="mt-2 pt-2 border-t border-gray-600">
          <button
            onClick={() => {
              console.log("🔄 Debug: Refresh manual");
              refreshMenus();
            }}
            className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs"
          >
            🔄 Refresh
          </button>
        </div>

        {menus?.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-600">
            <div className="text-yellow-300">Menus:</div>
            {menus.slice(0, 3).map((menu, i) => (
              <div key={menu.id || i} className="text-xs text-green-300">
                {i + 1}. {menu.name}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MenuDebugPanel;
