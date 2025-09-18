import React, { useState, useEffect } from "react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Card from "../ui/Card";
import { companiesService } from "../../services/api";
import { formatTaxId } from "../../utils/formatters";
import { Search, Building, Check, X, Loader2 } from "lucide-react";

const CompanySearchModal = ({ isOpen, onClose, onCompanySelect }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);

  useEffect(() => {
    if (isOpen) {
      // Reset state when modal opens
      setSearchTerm("");
      setCompanies([]);
      setSelectedCompany(null);
      setError(null);
    }
  }, [isOpen]);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const term = searchTerm.trim();

      // Verificar se é um CNPJ (formato: XX.XXX.XXX/XXXX-XX ou apenas números)
      const cnpjRegex = /^(\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}|\d{14})$/;
      const isCNPJ = cnpjRegex.test(term);

      let companiesData = [];

      if (isCNPJ) {
        // Se for CNPJ, tentar busca específica
        try {
          const cleanCNPJ = term.replace(/\D/g, ""); // Remove formatação
          const response = await companiesService.getCompanyByCNPJ(cleanCNPJ);
          companiesData = response ? [response] : [];
        } catch (cnpjError) {
          console.log("CNPJ não encontrado, tentando busca geral:", cnpjError);
          // Se CNPJ específico não funcionar, tentar busca geral
          const params = {
            search: term,
            page: 1,
            size: 20,
          };
          const response = await companiesService.getCompanies(params);
          companiesData =
            response?.items || response?.companies || response || [];
        }
      } else {
        // Busca geral por nome ou parte do nome
        const params = {
          search: term,
          page: 1,
          size: 20,
        };
        const response = await companiesService.getCompanies(params);
        companiesData =
          response?.items || response?.companies || response || [];
      }

      setCompanies(Array.isArray(companiesData) ? companiesData : []);
    } catch (err) {
      console.error("Erro ao buscar empresas:", err);
      setError(
        `Erro ao buscar empresas: ${err.message || "Erro desconhecido"}`
      );
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;

    // Se o valor parece ser um CNPJ (14 dígitos), formatar automaticamente
    if (value.replace(/\D/g, "").length === 14) {
      setSearchTerm(formatTaxId(value));
    } else {
      setSearchTerm(value);
    }
  };

  const handleCompanyClick = (company) => {
    setSelectedCompany(company);
  };

  const handleConfirmSelection = async () => {
    if (selectedCompany) {
      try {
        setLoading(true);
        // Fetch detailed company data to include phones, emails, and addresses
        const detailedCompany = await companiesService.getCompany(
          selectedCompany.id
        );
        onCompanySelect(detailedCompany);
        onClose();
      } catch (error) {
        console.error("Erro ao buscar dados detalhados da empresa:", error);
        setError(
          "Erro ao carregar dados completos da empresa. Tente novamente."
        );
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCancel = () => {
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-background border border-border rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Building className="h-5 w-5" />
            Buscar Empresa
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCancel}
            icon={<X className="h-4 w-4" />}
            aria-label="Fechar modal"
          />
        </div>

        {/* Search Section */}
        <div className="p-6 border-b border-border">
          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="Digite o nome, CNPJ ou parte do nome da empresa..."
                value={searchTerm}
                onChange={handleInputChange}
                icon={<Search className="h-4 w-4" />}
                autoFocus
              />
            </div>
            <Button
              onClick={handleSearch}
              disabled={loading || !searchTerm.trim()}
              icon={
                loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )
              }
            >
              {loading ? "Buscando..." : "Buscar"}
            </Button>
          </div>

          {/* Help text */}
          <div className="mt-3 text-xs text-muted-foreground">
            <p>• Digite o nome da empresa para buscar por nome</p>
            <p>
              • Digite o CNPJ completo (com ou sem formatação) para busca exata
            </p>
            <p>• Clique em "Buscar" para iniciar a pesquisa</p>
            <p>
              • O CNPJ será formatado automaticamente quando atingir 14 dígitos
            </p>
          </div>

          {error && (
            <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="flex-1 overflow-y-auto max-h-96">
          {loading && companies.length === 0 && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <span className="text-muted-foreground">
                  Buscando empresas...
                </span>
              </div>
            </div>
          )}

          {!loading && companies.length === 0 && !searchTerm && (
            <div className="text-center py-12">
              <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                Digite o nome ou CNPJ da empresa para começar a busca
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Você pode buscar por nome parcial ou CNPJ completo
              </p>
            </div>
          )}

          {!loading && companies.length === 0 && searchTerm && (
            <div className="text-center py-12">
              <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                Nenhuma empresa encontrada para "{searchTerm}"
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Tente usar termos diferentes, verificar a ortografia ou buscar
                por CNPJ
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSearchTerm("")}
                className="mt-4"
              >
                Limpar busca
              </Button>
            </div>
          )}

          {!loading && companies.length > 0 && (
            <div className="p-4 space-y-2">
              <p className="text-sm text-muted-foreground mb-4">
                {companies.length} empresa{companies.length !== 1 ? "s" : ""}{" "}
                encontrada{companies.length !== 1 ? "s" : ""}
              </p>

              {companies.map((company) => (
                <Card
                  key={company.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedCompany?.id === company.id
                      ? "ring-2 ring-primary bg-primary/5"
                      : ""
                  }`}
                  onClick={() => handleCompanyClick(company)}
                >
                  <div className="flex items-center justify-between p-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <Building className="h-5 w-5 text-primary" />
                        <div className="flex-1">
                          <h3 className="font-medium text-foreground">
                            {company.name ||
                              company.people?.name ||
                              company.person?.name ||
                              company.company?.name ||
                              `Empresa ${company.id}`}
                          </h3>
                          <div className="flex flex-col gap-1 mt-1">
                            {(company.tax_id ||
                              company.people?.tax_id ||
                              company.person?.tax_id ||
                              company.company?.tax_id) && (
                              <p className="text-sm text-muted-foreground">
                                CNPJ:{" "}
                                {formatTaxId(
                                  company.tax_id ||
                                    company.people?.tax_id ||
                                    company.person?.tax_id ||
                                    company.company?.tax_id
                                )}
                              </p>
                            )}
                            {company.description && (
                              <p className="text-sm text-muted-foreground">
                                {company.description}
                              </p>
                            )}
                            {/* Email não está disponível no schema CompanyList */}
                          </div>
                        </div>
                      </div>
                    </div>

                    {selectedCompany?.id === company.id && (
                      <div className="flex items-center justify-center w-6 h-6 bg-primary rounded-full">
                        <Check className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-border">
          <Button variant="secondary" outline onClick={handleCancel}>
            Cancelar
          </Button>
          <Button
            onClick={handleConfirmSelection}
            disabled={!selectedCompany || loading}
            icon={
              loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )
            }
          >
            {loading ? "Carregando..." : "Selecionar Empresa"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CompanySearchModal;
