import React, { useState, useRef, useEffect } from "react";
import { MoreHorizontal } from "lucide-react";
import { createPortal } from "react-dom";

const ActionDropdown = ({
  children,
  options,
  className = "",
  actions = [], // New prop for direct actions like Brevo
  item = null, // Item data for actions
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [shouldOpenUpward, setShouldOpenUpward] = useState(false);
  const [useModalOverlay, setUseModalOverlay] = useState(false);
  const [usePortal, setUsePortal] = useState(false);
  const [portalPosition, setPortalPosition] = useState({ top: 0, left: 0 });
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      // Check if click is outside the button
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        // For portal dropdown, also check if click is not inside the portal menu
        if (usePortal) {
          const portalMenus = document.querySelectorAll('[role="menu"]');
          let isInsidePortalMenu = false;
          portalMenus.forEach((menu) => {
            if (menu.contains(event.target)) {
              isInsidePortalMenu = true;
            }
          });
          if (!isInsidePortalMenu) {
            setIsOpen(false);
          }
        } else {
          setIsOpen(false);
        }
      }
    };

    if (isOpen) {
      // Add a small delay to prevent immediate closing
      const timeoutId = setTimeout(() => {
        document.addEventListener("mousedown", handleClickOutside);
      }, 100);

      return () => {
        clearTimeout(timeoutId);
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }
  }, [isOpen, usePortal]);

  // Enhanced positioning logic with portal for table containers
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;

      // Only apply smart positioning on desktop
      if (viewportWidth >= 768) {
        // Get item count for height calculation - computed dynamically to avoid dependency loop
        const itemCount = (() => {
          if (actions && actions.length > 0) return actions.length;
          if (options) return options.length;
          return React.Children.count(children);
        })();

        const itemHeight = 44;
        const padding = 16;
        const estimatedDropdownHeight = itemCount * itemHeight + padding;

        // Find table container
        const findTableContainer = (element) => {
          let parent = element.parentElement;
          while (parent) {
            const style = window.getComputedStyle(parent);
            if (
              style.overflow === "auto" ||
              style.overflow === "scroll" ||
              style.overflowY === "auto" ||
              style.overflowY === "scroll" ||
              parent.classList.contains("table-responsive") ||
              parent.classList.contains("overflow-x-auto")
            ) {
              return parent;
            }
            parent = parent.parentElement;
          }
          return null;
        };

        const tableContainer = findTableContainer(buttonRef.current);
        const spaceBelow = viewportHeight - buttonRect.bottom;
        const spaceAbove = buttonRect.top;

        console.log("Positioning analysis:", {
          spaceBelow,
          spaceAbove,
          estimatedDropdownHeight,
          hasTableContainer: !!tableContainer,
          tableContainerClass: tableContainer?.className,
        });

        // Decision logic
        if (spaceBelow >= estimatedDropdownHeight + 20) {
          // Enough space below, but check if in table container
          if (tableContainer) {
            const containerRect = tableContainer.getBoundingClientRect();
            const spaceInContainer = containerRect.bottom - buttonRect.bottom;

            if (spaceInContainer < estimatedDropdownHeight + 20) {
              // Not enough space in container - use portal
              console.log("Using portal - not enough space in table container");
              setUsePortal(true);
              setUseModalOverlay(false);
              setShouldOpenUpward(false);
              setPortalPosition({
                top: buttonRect.bottom + 4,
                left: buttonRect.right - 192,
                width: 192,
              });
            } else {
              // Enough space in container - use normal dropdown
              console.log("Using normal dropdown downward");
              setUsePortal(false);
              setUseModalOverlay(false);
              setShouldOpenUpward(false);
            }
          } else {
            // No table container - use normal dropdown
            console.log("Using normal dropdown downward - no container");
            setUsePortal(false);
            setUseModalOverlay(false);
            setShouldOpenUpward(false);
          }
        } else if (spaceAbove >= estimatedDropdownHeight + 20) {
          // Open upward
          if (tableContainer) {
            console.log("Using portal upward");
            setUsePortal(true);
            setUseModalOverlay(false);
            setShouldOpenUpward(true);
            setPortalPosition({
              top: buttonRect.top - estimatedDropdownHeight - 4,
              left: buttonRect.right - 192,
              width: 192,
            });
          } else {
            console.log("Using normal dropdown upward");
            setUsePortal(false);
            setUseModalOverlay(false);
            setShouldOpenUpward(true);
          }
        } else {
          // Not enough space anywhere - use modal
          console.log("Using modal overlay");
          setUseModalOverlay(true);
          setUsePortal(false);
          setShouldOpenUpward(false);
        }
      } else {
        // Mobile - use simple logic
        setUsePortal(false);
        setUseModalOverlay(false);
        setShouldOpenUpward(viewportHeight - buttonRect.bottom < 200);
      }
    } else if (!isOpen) {
      // Reset position when closed
      setShouldOpenUpward(false);
      setUseModalOverlay(false);
      setUsePortal(false);
      setPortalPosition({ top: 0, left: 0 });
    }
  }, [isOpen]);

  // Render dropdown content (shared between normal dropdown and portal)
  const renderDropdownContent = () => (
    <div className="py-1" role="none">
      {/* Render actions prop first (new API) */}
      {actions && actions.length > 0
        ? actions.map((action, index) => (
            <button
              key={action.id || index}
              onClick={() => {
                setIsOpen(false);
                if (action.onClick && item) {
                  action.onClick(item);
                }
              }}
              className={`group flex items-center w-full px-4 py-2.5 text-sm transition-colors duration-150 ${getActionColorClasses(
                action.color || action.variant
              )} hover:text-gray-900 dark:hover:text-white`}
              role="menuitem"
            >
              <span className="w-4 h-4 mr-3 flex-shrink-0 opacity-60 group-hover:opacity-100 transition-opacity">
                {action.icon}
              </span>
              <span className="flex-1 text-left font-medium">
                {action.label}
              </span>
            </button>
          ))
        : options
        ? // Render from options prop (backward compatibility)
          options.map((option, index) => (
            <button
              key={index}
              onClick={(...args) => {
                setIsOpen(false);
                if (option.onClick) {
                  option.onClick(...args);
                }
              }}
              disabled={option.disabled}
              className={`
              group flex items-center w-full px-4 py-2.5 text-sm
              transition-colors duration-150
              ${
                option.disabled
                  ? "opacity-50 cursor-not-allowed text-gray-400"
                  : option.variant || option.color
                  ? getActionColorClasses(option.variant || option.color)
                  : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white"
              }
              ${option.className || ""}
            `}
              role="menuitem"
            >
              {option.icon && (
                <span className="w-4 h-4 mr-3 flex-shrink-0 opacity-60 group-hover:opacity-100 transition-opacity">
                  {option.icon}
                </span>
              )}
              <span className="flex-1 text-left font-medium">
                {option.label}
              </span>
            </button>
          ))
        : // Render from children (backward compatibility)
          React.Children.map(children, (child, index) =>
            React.cloneElement(child, {
              key: index,
              onClick: (...args) => {
                setIsOpen(false);
                if (child.props.onClick) {
                  child.props.onClick(...args);
                }
              },
            })
          )}
    </div>
  );

  return (
    <div
      className={`relative inline-block ${className}`}
      ref={dropdownRef}
      style={{
        zIndex: isOpen ? 99998 : 1,
        position: "relative",
      }}
    >
      {/* Trigger Button */}
      <button
        ref={buttonRef}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="inline-flex items-center justify-center w-8 h-8 text-gray-400 bg-transparent hover:text-gray-600 hover:bg-gray-100 dark:hover:text-gray-300 dark:hover:bg-gray-700 rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 dark:focus:ring-offset-gray-800"
        aria-label="Menu de ações"
        type="button"
        title="Mais ações"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>

      {/* Normal Dropdown Menu */}
      {isOpen && !useModalOverlay && !usePortal && (
        <div
          className={`absolute right-0 w-48 origin-top-right bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl ring-1 ring-black ring-opacity-5 focus:outline-none animate-in fade-in zoom-in-95 duration-200 min-w-max ${
            shouldOpenUpward ? "bottom-full mb-1" : "top-full mt-1"
          }`}
          style={{
            zIndex: 99999,
            position: "absolute",
          }}
          role="menu"
          aria-orientation="vertical"
        >
          {renderDropdownContent()}
        </div>
      )}

      {/* Portal Dropdown Menu - renders outside table container */}
      {isOpen &&
        !useModalOverlay &&
        usePortal &&
        createPortal(
          <div
            className="fixed bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl ring-1 ring-black ring-opacity-5 focus:outline-none animate-in fade-in zoom-in-95 duration-200"
            style={{
              zIndex: 99999,
              top: `${portalPosition.top}px`,
              left: `${portalPosition.left}px`,
              width: `${portalPosition.width}px`,
              position: "fixed",
            }}
            role="menu"
            aria-orientation="vertical"
          >
            {renderDropdownContent()}
          </div>,
          document.body
        )}

      {/* Modal Overlay for when there's no space */}
      {isOpen && useModalOverlay && (
        <div
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black bg-opacity-50"
          onClick={() => setIsOpen(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl w-64 max-w-sm mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="py-2">
              <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Ações
                </h3>
              </div>
              <div className="py-1">
                {options
                  ? // Render from options prop
                    options.map((option, index) => (
                      <button
                        key={index}
                        onClick={(...args) => {
                          setIsOpen(false);
                          if (option.onClick) {
                            option.onClick(...args);
                          }
                        }}
                        disabled={option.disabled}
                        className={`
                        w-full px-4 py-3 text-left text-sm flex items-center space-x-3
                        transition-colors duration-150
                        ${
                          option.disabled
                            ? "opacity-50 cursor-not-allowed text-gray-400"
                            : option.variant || option.color
                            ? getActionColorClasses(
                                option.variant || option.color
                              )
                            : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                        }
                        ${option.className || ""}
                      `}
                      >
                        {option.icon && (
                          <span className="flex-shrink-0 w-5 h-5">
                            {option.icon}
                          </span>
                        )}
                        <span>{option.label}</span>
                      </button>
                    ))
                  : // Render from children
                    React.Children.map(children, (child, index) =>
                      React.cloneElement(child, {
                        key: index,
                        onClick: (...args) => {
                          setIsOpen(false);
                          if (child.props.onClick) {
                            child.props.onClick(...args);
                          }
                        },
                        className: `${child.props.className || ""} px-4 py-3`,
                      })
                    )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function for action color classes
const getActionColorClasses = (variant) => {
  switch (variant) {
    case "blue":
      return "text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20";
    case "green":
      return "text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20";
    case "yellow":
    case "warning":
      return "text-yellow-600 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20";
    case "red":
    case "danger":
      return "text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20";
    case "purple":
      return "text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20";
    case "gray":
      return "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700";
    case "success":
      return "text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20";
    default:
      return "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700";
  }
};

const ActionItem = ({
  icon,
  children,
  onClick,
  variant = "default",
  disabled = false,
  className = "",
}) => {
  const getVariantClasses = () => {
    switch (variant) {
      case "danger":
        return "text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20";
      case "warning":
        return "text-yellow-600 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20";
      case "success":
        return "text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20";
      default:
        return "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700";
    }
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        w-full px-4 py-2 text-left text-sm flex items-center space-x-2
        transition-colors duration-150
        ${getVariantClasses()}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        ${className}
      `}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};

ActionDropdown.Item = ActionItem;

export default ActionDropdown;
