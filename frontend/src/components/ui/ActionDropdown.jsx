import React, { useState, useRef, useEffect } from "react";
import { MoreVertical } from "lucide-react";

const ActionDropdown = ({ children, className = "" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }
  }, [isOpen]);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        aria-label="Ações"
      >
        <MoreVertical className="h-4 w-4 text-gray-600 dark:text-gray-400" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50">
          <div className="py-1">
            {React.Children.map(children, (child, index) =>
              React.cloneElement(child, {
                key: index,
                onClick: (...args) => {
                  setIsOpen(false);
                  if (child.props.onClick) {
                    child.props.onClick(...args);
                  }
                }
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const ActionItem = ({ 
  icon, 
  children, 
  onClick, 
  variant = "default", 
  disabled = false,
  className = ""
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