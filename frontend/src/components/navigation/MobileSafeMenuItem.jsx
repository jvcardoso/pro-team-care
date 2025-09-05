/**
 * MobileSafeMenuItem - Componente MenuItem otimizado para dispositivos móveis
 * Corrige o problema de menu que abre e recolhe imediatamente
 */

import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Icon } from '../ui/Icon';
import { Badge } from '../ui/Badge';

/**
 * Hook personalizado para detectar dispositivos touch de forma mais precisa
 */
const useIsTouchDevice = () => {
    const [isTouchDevice, setIsTouchDevice] = useState(false);
    
    useEffect(() => {
        // Múltiplas verificações para detectar touch
        const hasTouch = (
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            navigator.msMaxTouchPoints > 0 ||
            window.DocumentTouch && document instanceof window.DocumentTouch
        );
        
        setIsTouchDevice(hasTouch);
    }, []);
    
    return isTouchDevice;
};

/**
 * MobileSafeMenuItem - Componente corrigido
 */
export const MobileSafeMenuItem = ({ 
    menu, 
    level = 0, 
    collapsed = false, 
    onToggle = null 
}) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const location = useLocation();
    const itemRef = useRef(null);
    const isTouchDevice = useIsTouchDevice();

    const hasChildren = menu.children && menu.children.length > 0;
    const isActive = menu.url && location.pathname === menu.url;
    const indentClass = level > 0 ? `ml-${Math.min(level * 4, 12)}` : '';

    /**
     * Reset expansion when sidebar is collapsed
     */
    useEffect(() => {
        if (collapsed && isExpanded) {
            setIsExpanded(false);
        }
    }, [collapsed]);

    /**
     * Mobile-safe toggle handler
     */
    const handleMobileToggle = async (e) => {
        if (!hasChildren || collapsed || isProcessing) return;

        e.preventDefault();
        e.stopPropagation();
        
        // Prevent rapid clicks
        setIsProcessing(true);
        
        try {
            // Use double RAF to ensure state consistency
            await new Promise(resolve => {
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        setIsExpanded(prev => {
                            const newExpanded = !prev;
                            
                            console.log('🔄 Menu toggle:', {
                                menuId: menu.id,
                                menuName: menu.name,
                                oldExpanded: prev,
                                newExpanded: newExpanded,
                                level: level
                            });
                            
                            if (onToggle) {
                                onToggle(menu.id, newExpanded);
                            }
                            
                            return newExpanded;
                        });
                        resolve();
                    });
                });
            });
        } finally {
            // Re-enable after a safe delay
            setTimeout(() => setIsProcessing(false), 200);
        }
    };

    /**
     * Desktop toggle handler (more responsive)
     */
    const handleDesktopToggle = (e) => {
        if (!hasChildren || collapsed) return;

        e.preventDefault();
        e.stopPropagation();

        setIsExpanded(prev => {
            const newExpanded = !prev;
            
            if (onToggle) {
                onToggle(menu.id, newExpanded);
            }
            
            return newExpanded;
        });
    };

    /**
     * Combined click handler
     */
    const handleClick = (e) => {
        if (!hasChildren || collapsed) return;
        
        if (isTouchDevice) {
            handleMobileToggle(e);
        } else {
            handleDesktopToggle(e);
        }
    };

    /**
     * Touch event handlers for mobile
     */
    const handleTouchStart = (e) => {
        if (hasChildren && isTouchDevice && !collapsed) {
            e.stopPropagation();
        }
    };

    const handleTouchEnd = (e) => {
        if (hasChildren && isTouchDevice && !collapsed) {
            e.preventDefault();
            e.stopPropagation();
            handleMobileToggle(e);
        }
    };

    /**
     * Render icon
     */
    const renderIcon = () => {
        if (!menu.icon) return null;
        
        try {
            return (
                <Icon 
                    name={menu.icon} 
                    size={18}
                    className="flex-shrink-0"
                />
            );
        } catch (error) {
            return (
                <div className="w-[18px] h-[18px] bg-gray-300 rounded flex-shrink-0" 
                     title={`Ícone: ${menu.icon}`}
                />
            );
        }
    };

    /**
     * Render badge
     */
    const renderBadge = () => {
        if (!menu.badge_text) return null;
        
        return (
            <Badge 
                text={menu.badge_text} 
                color={menu.badge_color || 'blue'} 
                size="sm"
            />
        );
    };

    /**
     * Render expansion indicator
     */
    const renderExpansionIndicator = () => {
        if (!hasChildren || collapsed) return null;
        
        return (
            <div className="ml-auto flex-shrink-0">
                {isExpanded ? (
                    <ChevronDown size={16} className="transition-transform duration-200" />
                ) : (
                    <ChevronRight size={16} className="transition-transform duration-200" />
                )}
            </div>
        );
    };

    /**
     * CSS classes
     */
    const getItemClasses = () => {
        const baseClasses = `
            group flex items-center px-3 py-2 text-sm rounded-lg
            transition-all duration-200 ease-in-out
            ${indentClass}
        `;
        
        const stateClasses = isActive 
            ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 font-medium border-r-2 border-blue-600' 
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50';
        
        const interactionClasses = hasChildren && !collapsed ? 'cursor-pointer select-none' : '';
        const processingClass = isProcessing ? 'opacity-75' : '';
        
        return `${baseClasses} ${stateClasses} ${interactionClasses} ${processingClass}`.trim();
    };

    /**
     * Menu content
     */
    const MenuContent = () => (
        <>
            {renderIcon()}
            
            {!collapsed && (
                <span className="ml-3 flex-1 truncate min-w-0">
                    {menu.name}
                </span>
            )}
            
            {!collapsed && renderBadge()}
            
            {renderExpansionIndicator()}
        </>
    );

    /**
     * Item wrapper
     */
    const ItemWrapper = ({ children }) => {
        const classes = getItemClasses();
        const title = collapsed ? menu.name : undefined;

        if (menu.url && menu.url !== '#' && !hasChildren) {
            // Direct link
            return (
                <Link
                    to={menu.url}
                    target={menu.target || '_self'}
                    className={classes}
                    title={title}
                    onClick={(e) => {
                        console.log('📊 Menu navigation:', {
                            menuId: menu.id,
                            menuName: menu.name,
                            url: menu.url,
                            level: level
                        });
                    }}
                >
                    {children}
                </Link>
            );
        } else {
            // Menu with children or no link
            return (
                <div
                    ref={itemRef}
                    className={classes}
                    onClick={handleClick}
                    onTouchStart={handleTouchStart}
                    onTouchEnd={isTouchDevice ? handleTouchEnd : undefined}
                    title={title}
                    role={hasChildren ? "button" : undefined}
                    aria-expanded={hasChildren ? isExpanded : undefined}
                    tabIndex={hasChildren && !collapsed ? 0 : -1}
                    onKeyDown={(e) => {
                        if (hasChildren && (e.key === 'Enter' || e.key === ' ')) {
                            e.preventDefault();
                            handleDesktopToggle(e);
                        }
                    }}
                    data-menu-processing={isProcessing}
                >
                    {children}
                </div>
            );
        }
    };

    return (
        <div className="menu-item-container" data-testid="menu-item" data-menu-name={menu.name}>
            {/* Main item */}
            <ItemWrapper>
                <MenuContent />
            </ItemWrapper>
            
            {/* Recursive submenus */}
            {hasChildren && !collapsed && isExpanded && (
                <div className="mt-1 space-y-1" data-testid="submenu-items">
                    {menu.children.map((childMenu) => (
                        <div key={childMenu.id} data-testid="submenu-item">
                            <MobileSafeMenuItem 
                                menu={childMenu}
                                level={level + 1}
                                collapsed={false}
                                onToggle={onToggle}
                            />
                        </div>
                    ))}
                </div>
            )}
            
            {/* Collapsed indicator */}
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

export default MobileSafeMenuItem;