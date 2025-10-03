import React from "react";
import Breadcrumb from "../ui/Breadcrumb";
import { useBreadcrumbs } from "../../hooks/useBreadcrumbs";

/**
 * BreadcrumbBar - Barra fixa/sticky para navegação breadcrumb
 *
 * Características:
 * - Posição sticky no topo da área de conteúdo (abaixo do header)
 * - Background sólido com borda inferior para separação visual
 * - Responsivo: esconde em telas muito pequenas se necessário
 * - z-index controlado para hierarquia correta (abaixo de dropdowns, acima de conteúdo)
 */
const BreadcrumbBar: React.FC = () => {
  const breadcrumbs = useBreadcrumbs();

  // Não renderizar se não houver breadcrumbs
  if (!breadcrumbs || breadcrumbs.length === 0) {
    return null;
  }

  return (
    <div
      className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm"
      role="navigation"
      aria-label="Navegação hierárquica (breadcrumb)"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-3">
        <Breadcrumb items={breadcrumbs} />
      </div>
    </div>
  );
};

export default BreadcrumbBar;
