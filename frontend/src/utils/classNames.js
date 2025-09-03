/**
 * Utilitário para centralizar classes CSS comuns e eliminar duplicação
 * 🎯 Reduz duplicação de className em todos os componentes
 */

// Função para combinar classes condicionalmente (como clsx)
export const cn = (...classes) => {
  return classes.flat().filter(Boolean).join(" ");
};

// Classes base reutilizáveis
export const baseClasses = {
  // Botões
  button: {
    base: "inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
    sizes: {
      sm: "px-3 py-1.5 text-sm min-h-[32px]",
      md: "px-4 py-2 text-sm min-h-[40px]",
      lg: "px-6 py-3 text-base min-h-[44px]",
    },
    variants: {
      primary:
        "bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500",
      secondary:
        "bg-secondary-600 text-white hover:bg-secondary-700 focus:ring-secondary-500",
      success:
        "bg-green-600 text-white hover:bg-green-700 focus:ring-green-500",
      danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
      warning:
        "bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500",
      outline:
        "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-gray-500",
      ghost: "text-gray-700 hover:bg-gray-100 focus:ring-gray-500",
    },
  },

  // Cards
  card: {
    base: "bg-white rounded-lg border border-gray-200 shadow-sm",
    header: "px-6 py-4 border-b border-gray-200",
    body: "px-6 py-4",
    footer: "px-6 py-4 border-t border-gray-200 bg-gray-50",
  },

  // Inputs
  input: {
    base: "w-full border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none transition-colors placeholder-muted-foreground",
    sizes: {
      sm: "px-3 py-1.5 text-sm",
      md: "px-3 py-2 text-sm",
      lg: "px-4 py-3 text-base",
    },
    states: {
      default: "border-border",
      error: "border-red-500 focus:ring-red-500 focus:border-red-500",
      success: "border-green-500 focus:ring-green-500 focus:border-green-500",
      disabled: "opacity-50 cursor-not-allowed",
    },
  },

  // Labels
  label: {
    base: "text-sm font-medium text-foreground",
    required: "flex items-center",
  },

  // Badges
  badge: {
    base: "inline-block px-2 py-0.5 text-xs rounded-full font-medium",
    variants: {
      default: "bg-gray-100 text-gray-800",
      primary: "bg-primary/10 text-primary",
      secondary: "bg-secondary/10 text-secondary",
      success: "bg-green-100 text-green-800",
      danger: "bg-red-100 text-red-800",
      warning: "bg-yellow-100 text-yellow-800",
      info: "bg-blue-100 text-blue-800",
    },
  },

  // Containers
  container: {
    base: "mx-auto px-4 sm:px-6 lg:px-8",
    sizes: {
      sm: "max-w-3xl",
      md: "max-w-5xl",
      lg: "max-w-7xl",
      full: "max-w-full",
    },
  },

  // Layout
  layout: {
    page: "min-h-screen bg-background",
    section: "py-6 sm:py-8",
    grid: {
      cols1: "grid grid-cols-1 gap-6",
      cols2: "grid grid-cols-1 md:grid-cols-2 gap-6",
      cols3: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
      cols4: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
    },
  },

  // Estados de validação
  validation: {
    message: {
      base: "text-xs mt-1",
      error: "text-red-600",
      success: "text-green-600",
      info: "text-muted-foreground",
    },
    icon: {
      success: "h-4 w-4 text-green-500",
      error: "h-4 w-4 text-red-500",
      loading: "h-4 w-4 text-blue-500 animate-spin",
    },
  },

  // Sidebar
  sidebar: {
    item: {
      base: "group flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors",
      active:
        "bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
      inactive:
        "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700",
    },
    badge: {
      hot: "bg-red-500",
      new: "bg-blue-500",
      pro: "bg-purple-500",
      count: "bg-green-500",
    },
  },
};

// Funções auxiliares para criar classes específicas
export const createButtonClass = (
  variant = "primary",
  size = "md",
  className = ""
) => {
  return cn(
    baseClasses.button.base,
    baseClasses.button.sizes[size],
    baseClasses.button.variants[variant],
    className
  );
};

export const createInputClass = (
  size = "md",
  state = "default",
  className = ""
) => {
  return cn(
    baseClasses.input.base,
    baseClasses.input.sizes[size],
    baseClasses.input.states[state],
    className
  );
};

export const createCardClass = (section = "base", className = "") => {
  return cn(baseClasses.card[section], className);
};

export const createBadgeClass = (variant = "default", className = "") => {
  return cn(
    baseClasses.badge.base,
    baseClasses.badge.variants[variant],
    className
  );
};

export const createSidebarItemClass = (isActive = false, className = "") => {
  return cn(
    baseClasses.sidebar.item.base,
    isActive
      ? baseClasses.sidebar.item.active
      : baseClasses.sidebar.item.inactive,
    className
  );
};

export default {
  cn,
  baseClasses,
  createButtonClass,
  createInputClass,
  createCardClass,
  createBadgeClass,
  createSidebarItemClass,
};
