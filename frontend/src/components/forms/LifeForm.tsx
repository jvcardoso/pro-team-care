import React, { useState } from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Input from "../ui/Input";
import {
  Save,
  X,
  User,
  Calendar,
  FileText,
  MapPin,
  Mail,
  Phone,
} from "lucide-react";
import {
  PhoneInputGroup,
  EmailInputGroup,
  AddressInputGroup,
} from "../contacts";
import { Gender } from "../../types";

interface PersonData {
  name: string;
  tax_id: string; // CPF
  secondary_tax_id?: string; // RG
  birth_date: string;
  gender?: Gender;
}

interface LifeData {
  start_date: string;
  end_date?: string;
  notes?: string;
  relationship_type?: string;
  allows_substitution?: boolean;
}

export interface LifeFormData {
  person: PersonData;
  life: LifeData;
  phones: any[];
  emails: any[];
  addresses: any[];
}

interface LifeFormProps {
  initialData?: Partial<LifeFormData>;
  onSubmit: (data: LifeFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  mode?: "create" | "edit";
  title?: string;
}

const LifeForm: React.FC<LifeFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
  mode = "create",
  title = "Adicionar Nova Vida (Pessoa)",
}) => {
  const [formData, setFormData] = useState<LifeFormData>({
    person: initialData?.person || {
      name: "",
      tax_id: "",
      secondary_tax_id: "",
      birth_date: "",
      gender: undefined,
    },
    life: initialData?.life || {
      start_date: new Date().toISOString().split("T")[0],
      end_date: "",
      notes: "",
      relationship_type: "FUNCIONARIO",
      allows_substitution: true,
    },
    phones: initialData?.phones || [],
    emails: initialData?.emails || [],
    addresses: initialData?.addresses || [],
  });

  const handlePersonChange = (field: keyof PersonData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      person: { ...prev.person, [field]: value },
    }));
  };

  const handleLifeChange = (field: keyof LifeData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      life: { ...prev.life, [field]: value },
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Cabeçalho com descrição */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2 flex items-center">
            <User className="w-5 h-5 mr-2" />
            {title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Uma vida representa uma pessoa vinculada ao contrato. Preencha os
            dados pessoais obrigatórios e, opcionalmente, os contatos e
            endereço.
          </p>
        </div>
      </Card>

      {/* Dados Pessoais - Obrigatórios */}
      <Card title="Dados Pessoais" icon={<User className="h-5 w-5" />}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="md:col-span-2 lg:col-span-2">
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Nome Completo *
            </label>
            <Input
              value={formData.person.name}
              onChange={(e) => handlePersonChange("name", e.target.value)}
              placeholder="Nome completo da pessoa"
              required
              disabled={mode === "edit" || isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              CPF *
            </label>
            <Input
              value={formData.person.tax_id}
              onChange={(e) => handlePersonChange("tax_id", e.target.value)}
              placeholder="000.000.000-00"
              required
              disabled={mode === "edit" || isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              RG
            </label>
            <Input
              value={formData.person.secondary_tax_id}
              onChange={(e) =>
                handlePersonChange("secondary_tax_id", e.target.value)
              }
              placeholder="00.000.000-0"
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Data de Nascimento *
            </label>
            <Input
              type="date"
              value={formData.person.birth_date}
              onChange={(e) => handlePersonChange("birth_date", e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Sexo
            </label>
            <select
              value={formData.person.gender || ""}
              onChange={(e) =>
                handlePersonChange("gender", e.target.value as Gender)
              }
              className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={isLoading}
            >
              <option value="">Selecione...</option>
              <option value="M">Masculino</option>
              <option value="F">Feminino</option>
              <option value="O">Outro</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Dados do Contrato */}
      <Card
        title="Vínculo com o Contrato"
        icon={<Calendar className="h-5 w-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Data de Início no Contrato *
            </label>
            <Input
              type="date"
              value={formData.life.start_date}
              onChange={(e) => handleLifeChange("start_date", e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Data de Fim (opcional)
            </label>
            <Input
              type="date"
              value={formData.life.end_date}
              onChange={(e) => handleLifeChange("end_date", e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Tipo de Vínculo
            </label>
            <select
              value={formData.life.relationship_type}
              onChange={(e) =>
                handleLifeChange("relationship_type", e.target.value)
              }
              className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={isLoading}
            >
              <option value="FUNCIONARIO">Funcionário</option>
              <option value="DEPENDENTE">Dependente</option>
              <option value="AGREGADO">Agregado</option>
              <option value="OUTROS">Outros</option>
            </select>
          </div>

          <div className="md:col-span-2 lg:col-span-3">
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Observações
            </label>
            <Input
              value={formData.life.notes}
              onChange={(e) => handleLifeChange("notes", e.target.value)}
              placeholder="Observações sobre a inclusão no contrato"
              disabled={isLoading}
            />
          </div>
        </div>
      </Card>

      {/* Telefones - Opcional */}
      <Card title="Telefones (Opcionais)" icon={<Phone className="h-5 w-5" />}>
        <PhoneInputGroup
          phones={formData.phones}
          onChange={(phones) => setFormData((prev) => ({ ...prev, phones }))}
          onAdd={(phone) =>
            setFormData((prev) => ({
              ...prev,
              phones: [...prev.phones, phone],
            }))
          }
          onRemove={(index) =>
            setFormData((prev) => ({
              ...prev,
              phones: prev.phones.filter((_, i) => i !== index),
            }))
          }
          required={false}
          disabled={isLoading}
          minPhones={0}
          maxPhones={3}
          title=""
        />
      </Card>

      {/* E-mails - Opcional */}
      <Card title="E-mails (Opcionais)" icon={<Mail className="h-5 w-5" />}>
        <EmailInputGroup
          emails={formData.emails}
          onChange={(emails) => setFormData((prev) => ({ ...prev, emails }))}
          onAdd={(email) =>
            setFormData((prev) => ({
              ...prev,
              emails: [...prev.emails, email],
            }))
          }
          onRemove={(index) =>
            setFormData((prev) => ({
              ...prev,
              emails: prev.emails.filter((_, i) => i !== index),
            }))
          }
          required={false}
          disabled={isLoading}
          minEmails={0}
          maxEmails={3}
          title=""
        />
      </Card>

      {/* Endereços - Opcional */}
      <Card title="Endereços (Opcionais)" icon={<MapPin className="h-5 w-5" />}>
        <AddressInputGroup
          addresses={formData.addresses}
          onChange={(addresses) =>
            setFormData((prev) => ({ ...prev, addresses }))
          }
          onAdd={(address) =>
            setFormData((prev) => ({
              ...prev,
              addresses: [...prev.addresses, address],
            }))
          }
          onRemove={(index) =>
            setFormData((prev) => ({
              ...prev,
              addresses: prev.addresses.filter((_, i) => i !== index),
            }))
          }
          required={false}
          disabled={isLoading}
          minAddresses={0}
          maxAddresses={2}
          title=""
        />
      </Card>

      {/* Botões de Ação */}
      <Card>
        <div className="flex justify-end space-x-3 p-4">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            <X className="w-4 h-4 mr-2" />
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            <Save className="w-4 h-4 mr-2" />
            {isLoading
              ? "Salvando..."
              : mode === "edit"
              ? "Salvar Alterações"
              : "Adicionar Vida"}
          </Button>
        </div>
      </Card>
    </form>
  );
};

export default LifeForm;
