/**
 * Table Themes - Sistema de temas para customização visual das tabelas
 */

export interface TableTheme {
  name: string;
  description: string;
  classes: {
    // Container
    container: string;
    tableContainer: string;

    // Table structure
    table: string;
    thead: string;
    tbody: string;
    headerRow: string;
    bodyRow: string;
    cell: string;
    headerCell: string;

    // Interactive elements
    button: string;
    checkbox: string;
    select: string;
    input: string;

    // States
    hover: string;
    selected: string;
    loading: string;

    // Spacing
    padding: {
      container: string;
      cell: string;
      headerCell: string;
    };

    // Typography
    fontSize: string;
    fontWeight: {
      header: string;
      body: string;
    };
  };
}

export const tableThemes: Record<string, TableTheme> = {
  default: {
    name: "Default",
    description: "Tema padrão baseado no Flowbite",
    classes: {
      container:
        "bg-white dark:bg-gray-800 relative shadow-md sm:rounded-lg overflow-hidden",
      tableContainer: "overflow-x-auto w-full",
      table:
        "w-full table-auto text-sm text-left text-gray-500 dark:text-gray-400",
      thead:
        "text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400",
      tbody: "",
      headerRow: "border-b border-gray-200 dark:border-gray-700",
      bodyRow: "bg-white border-b dark:bg-gray-800 dark:border-gray-700",
      cell: "px-4 py-4",
      headerCell: "px-4 py-3",
      button:
        "text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300",
      checkbox:
        "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600",
      select:
        "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
      input:
        "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
      hover: "hover:bg-gray-50 dark:hover:bg-gray-600",
      selected: "bg-blue-50 dark:bg-blue-900/20",
      loading: "animate-pulse",
      padding: {
        container: "p-4",
        cell: "px-4 py-4",
        headerCell: "px-4 py-3",
      },
      fontSize: "text-sm",
      fontWeight: {
        header: "font-medium",
        body: "font-normal",
      },
    },
  },

  compact: {
    name: "Compact",
    description: "Tema compacto para economizar espaço",
    classes: {
      container:
        "bg-white dark:bg-gray-800 relative shadow-sm rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700",
      tableContainer: "overflow-x-auto w-full",
      table:
        "w-full table-auto text-xs text-left text-gray-500 dark:text-gray-400",
      thead:
        "text-xs text-gray-700 uppercase bg-gray-100 dark:bg-gray-600 dark:text-gray-300",
      tbody: "",
      headerRow: "border-b border-gray-300 dark:border-gray-600",
      bodyRow: "bg-white border-b dark:bg-gray-800 dark:border-gray-700",
      cell: "px-2 py-2",
      headerCell: "px-2 py-2",
      button:
        "text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-xs",
      checkbox:
        "w-3 h-3 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-1 dark:bg-gray-700 dark:border-gray-600",
      select:
        "bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded focus:ring-blue-500 focus:border-blue-500 block p-1 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
      input:
        "bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded focus:ring-blue-500 focus:border-blue-500 block w-full p-1 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
      hover: "hover:bg-gray-100 dark:hover:bg-gray-700",
      selected: "bg-blue-100 dark:bg-blue-900/30",
      loading: "animate-pulse",
      padding: {
        container: "p-2",
        cell: "px-2 py-2",
        headerCell: "px-2 py-2",
      },
      fontSize: "text-xs",
      fontWeight: {
        header: "font-semibold",
        body: "font-normal",
      },
    },
  },

  comfortable: {
    name: "Comfortable",
    description: "Tema espaçoso para melhor legibilidade",
    classes: {
      container:
        "bg-white dark:bg-gray-800 relative shadow-lg rounded-xl overflow-hidden",
      tableContainer: "overflow-x-auto w-full",
      table:
        "w-full table-auto text-base text-left text-gray-600 dark:text-gray-300",
      thead:
        "text-sm text-gray-800 uppercase bg-gray-100 dark:bg-gray-700 dark:text-gray-200",
      tbody: "",
      headerRow: "border-b-2 border-gray-200 dark:border-gray-600",
      bodyRow: "bg-white border-b dark:bg-gray-800 dark:border-gray-700",
      cell: "px-6 py-6",
      headerCell: "px-6 py-4",
      button:
        "text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-base",
      checkbox:
        "w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600",
      select:
        "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-3 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
      input:
        "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-3 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white",
      hover:
        "hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200",
      selected: "bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500",
      loading: "animate-pulse",
      padding: {
        container: "p-6",
        cell: "px-6 py-6",
        headerCell: "px-6 py-4",
      },
      fontSize: "text-base",
      fontWeight: {
        header: "font-semibold",
        body: "font-normal",
      },
    },
  },

  minimal: {
    name: "Minimal",
    description: "Tema minimalista sem bordas e sombras",
    classes: {
      container: "bg-transparent relative overflow-hidden",
      tableContainer: "overflow-x-auto w-full",
      table:
        "w-full table-auto text-sm text-left text-gray-700 dark:text-gray-300",
      thead: "text-xs text-gray-900 uppercase dark:text-gray-100",
      tbody: "",
      headerRow: "border-b border-gray-200 dark:border-gray-700",
      bodyRow: "border-b border-gray-100 dark:border-gray-800",
      cell: "px-3 py-3",
      headerCell: "px-3 py-3",
      button:
        "text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100",
      checkbox:
        "w-4 h-4 text-gray-600 bg-transparent border-gray-400 rounded focus:ring-gray-500 dark:focus:ring-gray-400 focus:ring-1 dark:border-gray-500",
      select:
        "bg-transparent border border-gray-300 text-gray-900 text-sm rounded focus:ring-gray-500 focus:border-gray-500 block p-2 dark:border-gray-600 dark:text-white",
      input:
        "bg-transparent border border-gray-300 text-gray-900 text-sm rounded focus:ring-gray-500 focus:border-gray-500 block w-full p-2 dark:border-gray-600 dark:text-white",
      hover: "hover:bg-gray-50 dark:hover:bg-gray-800",
      selected: "bg-gray-100 dark:bg-gray-800",
      loading: "animate-pulse",
      padding: {
        container: "p-3",
        cell: "px-3 py-3",
        headerCell: "px-3 py-3",
      },
      fontSize: "text-sm",
      fontWeight: {
        header: "font-medium",
        body: "font-normal",
      },
    },
  },

  enterprise: {
    name: "Enterprise",
    description: "Tema empresarial com visual profissional",
    classes: {
      container:
        "bg-white dark:bg-gray-900 relative shadow-xl rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600",
      tableContainer: "overflow-x-auto w-full",
      table:
        "w-full table-auto text-sm text-left text-gray-700 dark:text-gray-200",
      thead:
        "text-xs text-gray-900 uppercase bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600 dark:text-gray-100",
      tbody: "",
      headerRow: "border-b-2 border-gray-300 dark:border-gray-600",
      bodyRow:
        "bg-white border-b dark:bg-gray-900 dark:border-gray-700 even:bg-gray-50 dark:even:bg-gray-800",
      cell: "px-4 py-4",
      headerCell: "px-4 py-4",
      button:
        "text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium",
      checkbox:
        "w-4 h-4 text-indigo-600 bg-gray-100 border-gray-400 rounded focus:ring-indigo-500 dark:focus:ring-indigo-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-500",
      select:
        "bg-white border border-gray-400 text-gray-900 text-sm rounded-md focus:ring-indigo-500 focus:border-indigo-500 block p-2.5 dark:bg-gray-800 dark:border-gray-500 dark:text-white shadow-sm",
      input:
        "bg-white border border-gray-400 text-gray-900 text-sm rounded-md focus:ring-indigo-500 focus:border-indigo-500 block w-full p-2.5 dark:bg-gray-800 dark:border-gray-500 dark:text-white shadow-sm",
      hover:
        "hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all duration-200",
      selected:
        "bg-indigo-100 dark:bg-indigo-900/30 border-l-4 border-indigo-600",
      loading: "animate-pulse",
      padding: {
        container: "p-6",
        cell: "px-4 py-4",
        headerCell: "px-4 py-4",
      },
      fontSize: "text-sm",
      fontWeight: {
        header: "font-bold",
        body: "font-medium",
      },
    },
  },
};

/**
 * Retorna as classes CSS para um tema específico
 */
export function getThemeClasses(
  themeName: string = "default"
): TableTheme["classes"] {
  return tableThemes[themeName]?.classes || tableThemes.default.classes;
}

/**
 * Lista todos os temas disponíveis
 */
export function getAvailableThemes(): Array<{
  name: string;
  key: string;
  description: string;
}> {
  return Object.entries(tableThemes).map(([key, theme]) => ({
    key,
    name: theme.name,
    description: theme.description,
  }));
}

export default {
  tableThemes,
  getThemeClasses,
  getAvailableThemes,
};
