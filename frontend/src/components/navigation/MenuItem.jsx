/**
 * Componente MenuItem - Item de menu recursivo para hierarquia dinâmica
 * Suporta múltiplos níveis, ícones, badges e estados visuais
 */

import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Icon } from "../ui/Icon";
import { Badge } from "../ui/Badge";

/**
 * Componente MenuItem
 *
 * @param {Object} menu - Dados do menu
 * @param {number} level - Nível na hierarquia (0 = raiz)
 * @param {boolean} collapsed - Se a sidebar está colapsada
 * @param {Function} onToggle - Callback para expandir/colapsar
 */
export const MenuItem = ({
  menu,
  level = 0,
  collapsed = false,
  onToggle = null,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const location = useLocation();

  const hasChildren = menu.children && menu.children.length > 0;
  
  /**
   * Lógica de seleção universal para qualquer URL navegada
   * Funciona para qualquer página que o usuário acesse diretamente
   */
  const isActive = React.useMemo(() => {
    if (!menu.url || menu.url === "#") return false;
    
    const currentPath = location.pathname;
    
    // 1. CORRESPONDÊNCIA EXATA - Prioridade máxima
    const isExactMatch = currentPath === menu.url;
    
    // 2. CASOS ESPECIAIS - Dashboard
    if (menu.url === "/admin/dashboard") {
      // Dashboard ativo quando estamos em /admin ou /admin/dashboard
      return currentPath === "/admin" || currentPath === "/admin/dashboard";
    }
    
    // 3. RESOLVER CONFLITOS DE URLs DUPLICADAS
    if (menu.url === "/admin" && currentPath === "/admin") {
      // Se estamos na raiz /admin, isso é o Dashboard
      // Não ativar outros menus com URL /admin (Relatórios, Perfis, etc.)
      const conflictingMenus = ["relatorios-homecare", "perfis", "auditoria"];
      return !conflictingMenus.includes(menu.slug);
    }
    
    // 4. CORRESPONDÊNCIA EXATA NORMAL
    if (isExactMatch) {
      // Se tem filhos, só ativar se não houver filhos mais específicos ativos
      if (hasChildren) {
        const hasActiveChild = menu.children.some(child => 
          child.url && currentPath === child.url
        );
        return !hasActiveChild;
      }
      return true;
    }
    
    // 5. CORRESPONDÊNCIA POR INÍCIO DE PATH (Para navegação hierárquica)
    // Ex: Se estamos em /admin/usuarios/123, ativar menu /admin/usuarios
    if (menu.url !== "/admin" && currentPath.startsWith(menu.url + "/")) {
      // Verificar se não há um menu filho mais específico
      if (hasChildren) {
        const hasMoreSpecificChild = menu.children.some(child => 
          child.url && (currentPath === child.url || currentPath.startsWith(child.url + "/"))
        );
        return !hasMoreSpecificChild;
      }
      return true;
    }
    
    return false;
  }, [menu.url, menu.slug, location.pathname, hasChildren, menu.children]);
  
  const indentClass = level > 0 ? `ml-${Math.min(level * 4, 12)}` : "";

  /**
   * Efeito para detectar mudanças no estado collapsed e ajustar expansão
   * Importante para dispositivos móveis onde a sidebar pode ser re-renderizada
   */
  useEffect(() => {
    // Se a sidebar foi colapsada, recolher todos os submenus
    if (collapsed && isExpanded) {
      setIsExpanded(false);
    }
  }, [collapsed, isExpanded]);

  /**
   * Handler para expandir/colapsar submenu
   */
  const handleToggle = (e) => {
    if (hasChildren && !collapsed) {
      e.preventDefault();
      e.stopPropagation();

      const newExpanded = !isExpanded;
      setIsExpanded(newExpanded);

      // Callback opcional para parent
      if (onToggle) {
        onToggle(menu.id, newExpanded);
      }
    }
  };

  /**
   * Handler específico para mobile - previne conflitos de estado
   */
  const handleMobileToggle = (e) => {
    if (hasChildren && !collapsed) {
      e.preventDefault();
      e.stopPropagation();

      // Em mobile, garantir que o estado seja consistente
      // Usar setTimeout para evitar conflitos de re-renderização
      setTimeout(() => {
        setIsExpanded((prev) => {
          const newExpanded = !prev;

          // Callback opcional para parent
          if (onToggle) {
            onToggle(menu.id, newExpanded);
          }

          return newExpanded;
        });
      }, 0);
    }
  };

  /**
   * Renderiza o ícone do menu
   */
  const renderIcon = () => {
    if (!menu.icon) return null;

    try {
      return <Icon name={menu.icon} size={18} className="flex-shrink-0" />;
    } catch (error) {
      // Fallback se ícone não existir
      console.warn(`Ícone não encontrado: ${menu.icon}`);
      return (
        <div
          className="w-[18px] h-[18px] bg-gray-300 rounded flex-shrink-0"
          title={`Ícone: ${menu.icon}`}
        />
      );
    }
  };

  /**
   * Renderiza o badge do menu
   */
  const renderBadge = () => {
    if (!menu.badge_text) return null;

    return (
      <div data-testid="menu-badge">
        <Badge
          text={menu.badge_text}
          color={menu.badge_color || "bg-gray-500"}
          size="sm"
        />
      </div>
    );
  };

  /**
   * Renderiza o indicador de expansão
   */
  const renderExpansionIndicator = () => {
    if (!hasChildren || collapsed) return null;

    return (
      <div className="ml-2 flex-shrink-0" data-testid="menu-expand-button">
        {isExpanded ? (
          <ChevronDown
            size={16}
            className="transition-transform duration-200"
          />
        ) : (
          <ChevronRight
            size={16}
            className="transition-transform duration-200"
          />
        )}
      </div>
    );
  };

  /**
   * Classes CSS para o item
   */
  const getItemClasses = () => {
    const baseClasses = `
            group flex items-center px-3 py-2 text-sm rounded-lg
            transition-all duration-200 ease-in-out
            ${indentClass}
        `;

    const stateClasses = isActive
      ? "bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 font-medium border-r-2 border-blue-600"
      : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50";

    const interactionClasses =
      hasChildren && !collapsed ? "cursor-pointer" : "";

    return `${baseClasses} ${stateClasses} ${interactionClasses}`.trim();
  };

  /**
   * Conteúdo interno do menu item
   */
  const MenuContent = () => (
    <>
      {/* Ícone */}
      {renderIcon()}

      {/* Nome do menu (apenas se não colapsado) */}
      {!collapsed && (
        <span className="ml-3 flex-1 truncate min-w-0">{menu.name}</span>
      )}

      {/* Badge (apenas se não colapsado) */}
      {!collapsed && renderBadge()}

      {/* Indicador de expansão */}
      {renderExpansionIndicator()}
    </>
  );

  /**
   * Tooltip para modo colapsado
   */
  const getTooltipTitle = () => {
    if (!collapsed) return undefined;

    let title = menu.name;
    if (hasChildren) {
      const childCount = menu.children.length;
      title += ` (${childCount} ${childCount === 1 ? "item" : "itens"})`;
    }
    if (menu.badge_text) {
      title += ` • ${menu.badge_text}`;
    }

    return title;
  };

  /**
   * Renderização condicional: Link ou div
   */
  const ItemWrapper = ({ children }) => {
    const classes = getItemClasses();
    const title = getTooltipTitle();

    // Detectar se estamos em um dispositivo móvel/touch
    const isTouchDevice =
      "ontouchstart" in window || navigator.maxTouchPoints > 0;

    if (menu.url && menu.url !== "#" && !hasChildren) {
      // Link direto
      return (
        <Link
          to={menu.url}
          target={menu.target || "_self"}
          className={classes}
          title={title}
          onClick={(e) => {
            // Log para analytics
            console.log("📊 Menu clicked:", {
              menuId: menu.id,
              menuName: menu.name,
              url: menu.url,
              level: level,
            });
          }}
        >
          {children}
        </Link>
      );
    } else {
      // Div para menus sem link ou com submenu
      return (
        <div
          className={classes}
          onClick={isTouchDevice ? handleMobileToggle : handleToggle}
          title={title}
          role={hasChildren ? "button" : undefined}
          aria-expanded={hasChildren ? isExpanded : undefined}
          tabIndex={hasChildren && !collapsed ? 0 : -1}
          onKeyDown={(e) => {
            if (hasChildren && (e.key === "Enter" || e.key === " ")) {
              e.preventDefault();
              handleToggle(e);
            }
          }}
          // Prevenir conflitos de toque em dispositivos móveis
          onTouchStart={(e) => {
            if (hasChildren && isTouchDevice) {
              e.stopPropagation();
            }
          }}
          onTouchEnd={(e) => {
            if (hasChildren && isTouchDevice) {
              e.preventDefault();
              handleMobileToggle(e);
            }
          }}
        >
          {children}
        </div>
      );
    }
  };

  return (
    <div
      className="menu-item-container"
      data-testid="menu-item"
      data-menu-name={menu.name}
    >
      {/* Item principal */}
      <ItemWrapper>
        <MenuContent />
      </ItemWrapper>

      {/* Submenus recursivos */}
      {hasChildren && !collapsed && isExpanded && (
        <div className="mt-1 space-y-1" data-testid="submenu-items">
          {menu.children.map((childMenu) => (
            <div key={childMenu.id} data-testid="submenu-item">
              <MenuItem
                menu={childMenu}
                level={level + 1}
                collapsed={false}
                onToggle={onToggle}
              />
            </div>
          ))}
        </div>
      )}

      {/* Indicador visual para menus colapsados com filhos */}
      {hasChildren && collapsed && (
        <div className="flex justify-center mt-1">
          <div
            className="w-1 h-1 bg-blue-500 rounded-full opacity-60"
            title={`${menu.children.length} subitens`}
          />
        </div>
      )}
    </div>
  );
};

export default MenuItem;
