/**
 * Types for Reusable Data Table Template
 * Defines all interfaces needed for the generic table component
 */

export interface BaseEntity {
  id: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DataTableColumn<T = any> {
  key: keyof T;
  label: string;
  type: "text" | "number" | "date" | "currency" | "badge" | "custom";
  width?: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
  className?: string;
}

export interface DataTableMetric {
  id: string;
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  color: "blue" | "green" | "purple" | "yellow" | "red" | "gray";
  percentage?: number;
  trend?: "up" | "down" | "neutral";
}

export interface DataTableFilter {
  key: string;
  label: string;
  type:
    | "select"
    | "search"
    | "date"
    | "range"
    | "multiselect"
    | "daterange"
    | "number";
  options?: { value: string; label: string; icon?: string }[];
  placeholder?: string;
  multiple?: boolean;
  min?: number;
  max?: number;
  step?: number;
  dateFormat?: string;
}

export interface DataTableAction<T = any> {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: "blue" | "green" | "yellow" | "red" | "purple" | "gray";
  onClick: (item: T) => void;
  show?: (item: T) => boolean;
}

export interface DataTableExportConfig {
  filename: string;
  formats: ("csv" | "json" | "print")[];
  includeFiltered?: boolean;
  customData?: (items: any[]) => any[];
}

export interface DataTableConfig<T extends BaseEntity = any> {
  // Basic Info
  entity: string;
  title: string;
  description: string;

  // Data Structure
  columns: DataTableColumn<T>[];
  searchFields: (keyof T)[];
  sortField?: keyof T;
  sortDirection?: "asc" | "desc";

  // Metrics
  metrics: {
    primary: DataTableMetric[];
    detailed?: {
      title: string;
      sections: {
        title: string;
        items: DataTableMetric[];
      }[];
      quickActions?: {
        label: string;
        action: () => void;
        color: string;
      }[];
    };
  };

  // Filters
  filters: DataTableFilter[];

  // Actions
  actions: DataTableAction<T>[];
  bulkActions?: DataTableAction<T[]>[];
  showAddButton?: boolean;

  // Export
  export: DataTableExportConfig;

  // Pagination
  defaultPageSize: number;
  pageSizeOptions: number[];

  // Customization
  className?: string;
  theme?: "default" | "compact" | "comfortable" | "minimal" | "enterprise";
}

export interface DataTableState {
  // Data
  data: any[];
  filteredData: any[];
  loading: boolean;
  error: string | null;

  // Pagination
  currentPage: number;
  pageSize: number;
  totalPages: number;

  // Filters
  searchTerm: string;
  activeFilters: Record<string, any>;

  // Selection
  selectedItems: number[];

  // UI State
  showDetailedMetrics: boolean;
  showExportDropdown: boolean;
  selectedItemForModal: any | null;
  isModalOpen: boolean;
}

export interface DataTableCallbacks<T = any> {
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onSearch: (term: string) => void;
  onFilter: (key: string, value: any) => void;
  onClearFilters: () => void;
  onSelectAll: (selected: boolean) => void;
  onSelectItem: (id: number, selected: boolean) => void;
  onExport: (format: string, data?: T[]) => void;
  onAction: (actionId: string, item: T) => void;
  onBulkAction: (actionId: string, items: T[]) => void;

  // UI State callbacks
  onToggleDetailedMetrics: () => void;
  onToggleExportDropdown: () => void;
  onOpenModal: (item: T) => void;
  onCloseModal: () => void;
}

export interface UseDataTableConfig<T extends BaseEntity = any> {
  config: DataTableConfig<T>;
  apiEndpoint?: string;
  initialData?: T[];
  onDataChange?: (data: T[]) => void;
}

export interface UseDataTableReturn<T extends BaseEntity = any> {
  state: DataTableState;
  callbacks: DataTableCallbacks<T>;
  metrics: DataTableMetric[];
  detailedMetrics?: DataTableConfig<T>["metrics"]["detailed"];
}
