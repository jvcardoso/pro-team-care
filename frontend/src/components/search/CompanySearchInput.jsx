import React, { useState } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import CompanySearchModal from "./CompanySearchModal";
import CompanyDataCopyModal from "../ui/CompanyDataCopyModal";
import { formatTaxId } from "../../utils/formatters";
import { Search, Building, X } from "lucide-react";

const CompanySearchInput = ({
  value,
  selectedCompany: propSelectedCompany,
  onChange,
  onCompanySelect,
  placeholder = "Buscar empresa...",
  disabled = false,
  required = false,
  className = "",
  enableDataCopy = false,
  onDataCopyConfirm,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(
    propSelectedCompany || null
  );
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [pendingCompany, setPendingCompany] = useState(null);

  // Update internal state when prop changes
  React.useEffect(() => {
    setSelectedCompany(propSelectedCompany || null);
  }, [propSelectedCompany]);

  const handleSearchClick = () => {
    setIsModalOpen(true);
  };

  const handleCompanySelect = (company) => {
    if (enableDataCopy && onDataCopyConfirm) {
      // Se a cópia de dados estiver habilitada, mostrar modal de confirmação
      setPendingCompany(company);
      setShowCopyModal(true);
    } else {
      // Comportamento padrão
      setSelectedCompany(company);
      onCompanySelect(company);
    }
    setIsModalOpen(false);
  };

  const handleCopyConfirm = (shouldCopyData = true) => {
    if (pendingCompany) {
      setSelectedCompany(pendingCompany);
      onCompanySelect(pendingCompany);

      if (shouldCopyData && onDataCopyConfirm) {
        onDataCopyConfirm(pendingCompany);
      }

      setPendingCompany(null);
      setShowCopyModal(false);
    }
  };

  const handleCopyCancel = () => {
    setPendingCompany(null);
    setShowCopyModal(false);
  };

  const handleClear = () => {
    setSelectedCompany(null);
    onCompanySelect(null);
    onChange({ target: { value: "" } });
  };

  const displayValue = selectedCompany
    ? selectedCompany.name ||
      selectedCompany.people?.name ||
      selectedCompany.person?.name ||
      selectedCompany.company?.name ||
      `Empresa ${selectedCompany.id}`
    : value || "";

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-muted-foreground">
        Empresa {required && "*"}
      </label>

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            value={displayValue}
            onChange={onChange}
            placeholder={placeholder}
            disabled={disabled}
            readOnly={!!selectedCompany}
            className={selectedCompany ? "pr-8" : ""}
            icon={<Building className="h-4 w-4" />}
          />

          {selectedCompany && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              disabled={disabled}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <Button
          type="button"
          variant="secondary"
          outline
          onClick={handleSearchClick}
          disabled={disabled}
          icon={<Search className="h-4 w-4" />}
          className="shrink-0"
          aria-label="Buscar empresa"
        >
          <span className="hidden sm:inline">Buscar</span>
        </Button>
      </div>

      {selectedCompany && (
        <div className="text-xs text-muted-foreground">
          Empresa selecionada:{" "}
          {selectedCompany.name ||
            selectedCompany.people?.name ||
            selectedCompany.person?.name ||
            selectedCompany.company?.name ||
            `Empresa ${selectedCompany.id}`}
          {(selectedCompany.tax_id ||
            selectedCompany.people?.tax_id ||
            selectedCompany.person?.tax_id ||
            selectedCompany.company?.tax_id) &&
            ` (CNPJ: ${formatTaxId(
              selectedCompany.tax_id ||
                selectedCompany.people?.tax_id ||
                selectedCompany.person?.tax_id ||
                selectedCompany.company?.tax_id
            )})`}
        </div>
      )}

      {/* Modal será implementado em arquivo separado */}
      {isModalOpen && (
        <CompanySearchModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onCompanySelect={handleCompanySelect}
        />
      )}

      {/* Modal de cópia de dados */}
      {showCopyModal && (
        <CompanyDataCopyModal
          isOpen={showCopyModal}
          company={pendingCompany}
          onConfirm={(shouldCopy) => handleCopyConfirm(shouldCopy)}
          onCancel={handleCopyCancel}
        />
      )}
    </div>
  );
};

export default CompanySearchInput;
