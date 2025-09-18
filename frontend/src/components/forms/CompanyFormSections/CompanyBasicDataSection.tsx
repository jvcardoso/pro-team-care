import React from "react";
import Card from "../../ui/Card";
import Input from "../../ui/Input";
import { InputCNPJ } from "../../inputs";
import { People } from "@/types";

interface CompanyBasicDataSectionProps {
  formData: {
    people: People;
  };
  loading: boolean;
  isEditing: boolean;
  onUpdatePeople: (updates: any) => void;
  onCompanyFound: (companyData: any) => Promise<void>;
}

const CompanyBasicDataSection: React.FC<CompanyBasicDataSectionProps> =
  React.memo(
    ({ formData, loading, isEditing, onUpdatePeople, onCompanyFound }) => {
      return (
        <Card title="Dados da Empresa">
          <div className="space-y-6">
            {/* CNPJ - Primeiro campo com consulta */}
            <InputCNPJ
              label="CNPJ"
              value={formData.people.tax_id}
              onChange={(event: any) => {
                const value = event?.rawValue || event?.target?.value || event;
                onUpdatePeople({ people: { tax_id: value } });
              }}
              onCompanyFound={onCompanyFound}
              placeholder="00.000.000/0000-00"
              required
              disabled={loading || isEditing}
              showValidation={true}
              showConsultButton={!isEditing}
              autoConsult={false}
            />

            {/* Campos principais */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Input
                label="Razão Social"
                value={formData.people.name}
                onChange={(e) =>
                  onUpdatePeople({ people: { name: e.target.value } })
                }
                placeholder="Nome completo da empresa"
                required
              />
              <Input
                label="Nome Fantasia"
                value={formData.people.trade_name || ""}
                onChange={(e) =>
                  onUpdatePeople({ people: { trade_name: e.target.value } })
                }
                placeholder="Nome comercial"
              />
            </div>

            {/* Campos secundários */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <Input
                label="Inscrição Estadual"
                value={formData.people.secondary_tax_id || ""}
                onChange={(e) =>
                  onUpdatePeople({
                    people: { secondary_tax_id: e.target.value },
                  })
                }
                placeholder="123.456.789"
              />
              <Input
                label="Inscrição Municipal"
                value={formData.people.municipal_registration || ""}
                onChange={(e) =>
                  onUpdatePeople({
                    people: { municipal_registration: e.target.value },
                  })
                }
                placeholder="12345678"
              />
              <Input
                label="Website"
                value={formData.people.website || ""}
                onChange={(e) =>
                  onUpdatePeople({ people: { website: e.target.value } })
                }
                placeholder="https://www.empresa.com.br"
                type="url"
              />
            </div>

            {/* Natureza e regime */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <Input
                label="Natureza Jurídica"
                value={formData.people.legal_nature || ""}
                onChange={(e) =>
                  onUpdatePeople({ people: { legal_nature: e.target.value } })
                }
                placeholder="Sociedade Limitada"
              />
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Regime Tributário
                </label>
                <select
                  value={formData.people.tax_regime || "simples_nacional"}
                  onChange={(e) =>
                    onUpdatePeople({ people: { tax_regime: e.target.value } })
                  }
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  <option value="simples_nacional">Simples Nacional</option>
                  <option value="lucro_presumido">Lucro Presumido</option>
                  <option value="lucro_real">Lucro Real</option>
                  <option value="mei">MEI</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Status
                </label>
                <select
                  value={formData.people.status}
                  onChange={(e) =>
                    onUpdatePeople({ people: { status: e.target.value } })
                  }
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  <option value="active">Ativo</option>
                  <option value="inactive">Inativo</option>
                  <option value="suspended">Suspenso</option>
                </select>
              </div>
            </div>

            {/* Data de abertura */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Input
                label="Data de Abertura"
                value={formData.people.incorporation_date || ""}
                onChange={(e) =>
                  onUpdatePeople({
                    people: { incorporation_date: e.target.value },
                  })
                }
                type="date"
              />
            </div>

            {/* Descrição */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Descrição da Empresa
              </label>
              <textarea
                value={formData.people.description || ""}
                onChange={(e) =>
                  onUpdatePeople({ people: { description: e.target.value } })
                }
                placeholder="Breve descrição das atividades da empresa..."
                rows={3}
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none resize-none"
              />
            </div>
          </div>
        </Card>
      );
    }
  );

CompanyBasicDataSection.displayName = "CompanyBasicDataSection";

export default CompanyBasicDataSection;
