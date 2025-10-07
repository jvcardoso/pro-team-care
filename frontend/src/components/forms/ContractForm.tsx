import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { notify } from "../../utils/notifications.jsx";
import { contractsService } from "../../services/contractsService";
import { clientsService } from "../../services/clientsService";
import { parseCurrencyRobust } from "../../utils/formatters";
import {
  FileText,
  Users,
  Calendar,
  DollarSign,
  Building2,
  Save,
  X,
  AlertCircle,
} from "lucide-react";
import { AddressInputGroup } from "../contacts";

// Schema de validação baseado na estrutura exata do banco
const contractSchema = z.object({
  client_id: z.number().min(1, "Cliente é obrigatório"),
  contract_number: z.string().optional(), // Auto-gerado pelo backend
  contract_type: z.enum(["INDIVIDUAL", "CORPORATIVO", "EMPRESARIAL"], {
    required_error: "Tipo de contrato é obrigatório",
  }),
  plan_name: z.string().min(1, "Nome do plano é obrigatório"),
  monthly_value: z.number().min(0, "Valor mensal deve ser positivo"),
  lives_contracted: z.number().min(1, "Deve ter pelo menos 1 vida"),
  lives_minimum: z.number().optional(),
  lives_maximum: z.number().optional(),
  allows_substitution: z.boolean(),
  control_period: z
    .enum(["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"])
    .optional(),
  start_date: z.string().min(1, "Data de início é obrigatória"),
  end_date: z.string().optional(),
  service_address_type: z.enum(["PATIENT", "CLINIC"]).optional(),
  status: z
    .enum(["active", "inactive", "suspended", "cancelled", "expired"])
    .optional(),
  notes: z.string().optional(), // Campo para observações do contrato
});

type ContractFormData = z.infer<typeof contractSchema>;

interface ContractFormProps {
  contract?: any;
  onSave?: () => void;
  onCancel?: () => void;
}

const ContractForm: React.FC<ContractFormProps> = ({
  contract,
  onSave,
  onCancel,
}) => {
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState<any[]>([]);
  const [serviceAddresses, setServiceAddresses] = useState<any[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset,
  } = useForm<ContractFormData>({
    resolver: zodResolver(contractSchema),
    defaultValues: {
      contract_type: "INDIVIDUAL",
      lives_contracted: 1,
      allows_substitution: false,
      control_period: "MONTHLY",
      service_address_type: "PATIENT",
      status: "active",
    },
  });

  // Carregar clientes para o select
  useEffect(() => {
    const loadClients = async () => {
      try {
        const response = await clientsService.getAll({ page: 1, size: 100 });
        const activeClients = (response.clients || []).filter(
          (client) => client.status === "active"
        );
        setClients(activeClients);
      } catch (error) {
        console.error("Erro ao carregar clientes:", error);
        notify.error("Erro ao carregar lista de clientes");
      }
    };

    loadClients();
  }, []);

  // Carregar dados do contrato quando fornecido
  useEffect(() => {
    if (!contract) {
      return;
    }

    console.log("📝 Carregando contrato:", contract);

    // Processar endereços
    const addresses = contract.service_addresses;
    let processedAddresses = [];
    let addressType = "PATIENT";

    if (Array.isArray(addresses) && addresses.length > 0) {
      processedAddresses = addresses;
      addressType = "CLINIC";
    } else if (
      addresses &&
      typeof addresses === "object" &&
      Object.keys(addresses).length > 0
    ) {
      processedAddresses = Object.values(addresses);
      addressType = "CLINIC";
    }

    // Preparar dados do formulário
    const formData = {
      client_id: contract.client_id || 0,
      contract_number: contract.contract_number || "",
      contract_type: contract.contract_type || "INDIVIDUAL",
      plan_name: contract.plan_name || "",
      monthly_value: parseFloat(contract.monthly_value) || 0,
      lives_contracted: contract.lives_contracted || 1,
      lives_minimum: contract.lives_minimum ?? undefined,
      lives_maximum: contract.lives_maximum ?? undefined,
      allows_substitution: contract.allows_substitution ?? false,
      control_period: contract.control_period || "MONTHLY",
      service_address_type: addressType,
      start_date: contract.start_date
        ? new Date(contract.start_date).toISOString().split("T")[0]
        : "",
      end_date: contract.end_date
        ? new Date(contract.end_date).toISOString().split("T")[0]
        : "",
      status: contract.status || "active",
      notes: contract.notes || "", // Campo para observações
    };

    reset(formData);
    setServiceAddresses(processedAddresses);

    console.log("✅ Formulário carregado com dados do contrato");
  }, [contract, reset]);

  const onSubmit = async (data: ContractFormData) => {
    try {
      setLoading(true);

      // Preparar dados do contrato para envio (campos exatos da tabela)
      const contractData = {
        client_id: data.client_id,
        contract_number: data.contract_number || undefined, // Auto-gerado no backend
        contract_type: data.contract_type,
        plan_name: data.plan_name,
        monthly_value: data.monthly_value,
        lives_contracted: data.lives_contracted,
        lives_minimum: data.lives_minimum || null,
        lives_maximum: data.lives_maximum || null,
        allows_substitution: data.allows_substitution,
        control_period: data.control_period,
        service_address_type: data.service_address_type,
        start_date: data.start_date,
        end_date: data.end_date || null,
        service_addresses:
          data.service_address_type === "CLINIC" && serviceAddresses.length > 0
            ? serviceAddresses.reduce(
                (acc, addr, index) => ({ ...acc, [index]: addr }),
                {}
              )
            : {},
        status: data.status,
        notes: data.notes || null, // Campo para observações
      };

      console.log("📤 Dados sendo enviados para API:", contractData);

      if (contract?.id) {
        const response = await contractsService.updateContract(
          contract.id,
          contractData
        );
        console.log("📥 Resposta do backend após UPDATE:", response);
        contractsService.clearContractsCache();
        notify.success("Contrato atualizado com sucesso!");
      } else {
        const response = await contractsService.createContract(contractData);
        console.log("📥 Resposta do backend após CREATE:", response);
        contractsService.clearContractsCache();
        notify.success("Contrato criado com sucesso!");
      }

      onSave?.();
    } catch (error: any) {
      console.error("Erro ao salvar contrato:", error);
      console.error("📋 Resposta completa do erro:", error.response?.data);

      const errorMessage =
        error.response?.data?.message ||
        (Array.isArray(error.response?.data?.detail)
          ? error.response.data.detail
              .map((d: any) => d.msg || d.message || JSON.stringify(d))
              .join(", ")
          : error.response?.data?.detail) ||
        error.message ||
        "Erro desconhecido";

      notify.error(`Erro ao salvar contrato: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading && contract?.id) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Carregando contrato...</span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">
            {contract?.id ? "Editar Contrato" : "Novo Contrato"}
          </h2>
          <p className="text-muted-foreground">
            {contract?.id
              ? "Atualize as informações do contrato"
              : "Preencha os dados para criar um novo contrato"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            icon={<X className="h-4 w-4" />}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            loading={loading}
            icon={<Save className="h-4 w-4" />}
          >
            {contract?.id ? "Atualizar" : "Criar"} Contrato
          </Button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Seção 1: Informações Básicas */}
        <Card
          title="Informações Básicas"
          icon={<FileText className="h-5 w-5" />}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Cliente *
              </label>
              {contract?.id ? (
                <div className="w-full px-3 py-2 border border-border rounded-md bg-muted text-muted-foreground">
                  {clients.find((client) => client.id === watch("client_id"))
                    ?.person?.name ||
                    clients.find((client) => client.id === watch("client_id"))
                      ?.name ||
                    `Cliente ${watch("client_id")}`}
                </div>
              ) : (
                <select
                  {...register("client_id", { valueAsNumber: true })}
                  value={watch("client_id") || ""}
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  <option value="">Selecione um cliente</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.person?.name ||
                        client.name ||
                        `Cliente ${client.id}`}
                    </option>
                  ))}
                </select>
              )}
              {errors.client_id && (
                <p className="text-sm text-red-600 mt-1">
                  {errors.client_id.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Número do Contrato
              </label>
              <Input
                {...register("contract_number")}
                value={watch("contract_number") || "Auto-gerado"}
                placeholder="Auto-gerado ao salvar"
                disabled={true}
                className="bg-muted text-muted-foreground"
              />
              <p className="text-xs text-muted-foreground mt-1">
                O número será gerado automaticamente ao salvar o contrato
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Nome do Plano *
              </label>
              <Input
                {...register("plan_name")}
                value={watch("plan_name") || ""}
                placeholder="Ex: Plano Home Care Básico"
                error={errors.plan_name?.message}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Tipo de Contrato *
              </label>
              <select
                {...register("contract_type")}
                value={watch("contract_type") || ""}
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
              >
                <option value="INDIVIDUAL">Individual</option>
                <option value="CORPORATIVO">Corporativo</option>
                <option value="EMPRESARIAL">Empresarial</option>
              </select>
              {errors.contract_type && (
                <p className="text-sm text-red-600 mt-1">
                  {errors.contract_type.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Status do Contrato
              </label>
              <select
                {...register("status")}
                value={watch("status") || ""}
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
              >
                <option value="active">Ativo</option>
                <option value="inactive">Inativo</option>
                <option value="suspended">Suspenso</option>
                <option value="cancelled">Cancelado</option>
                <option value="expired">Expirado</option>
              </select>
              {errors.status && (
                <p className="text-sm text-red-600 mt-1">
                  {errors.status.message}
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Seção 2: Período e Vidas */}
        <Card title="Período e Vidas" icon={<Calendar className="h-5 w-5" />}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Data de Início *
              </label>
              <Input
                {...register("start_date")}
                value={watch("start_date") || ""}
                type="date"
                error={errors.start_date?.message}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Data de Fim
              </label>
              <Input
                {...register("end_date")}
                value={watch("end_date") || ""}
                type="date"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Deixe em branco para contrato por tempo indeterminado
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Vidas Contratadas *
              </label>
              <Input
                {...register("lives_contracted", { valueAsNumber: true })}
                value={watch("lives_contracted") || ""}
                type="number"
                min="1"
                leftIcon={<Users className="h-4 w-4" />}
                error={errors.lives_contracted?.message}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Vidas Mínimas
                </label>
                <Input
                  {...register("lives_minimum", { valueAsNumber: true })}
                  value={watch("lives_minimum") || ""}
                  type="number"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Vidas Máximas
                </label>
                <Input
                  {...register("lives_maximum", { valueAsNumber: true })}
                  value={watch("lives_maximum") || ""}
                  type="number"
                  min="0"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                {...register("allows_substitution")}
                checked={watch("allows_substitution") || false}
                type="checkbox"
                className="rounded border-border"
              />
              <label className="text-sm font-medium text-foreground">
                Permite Substituição de Vidas
              </label>
            </div>
          </div>
        </Card>

        {/* Seção 3: Valores e Cobrança */}
        <Card
          title="Valores e Cobrança"
          icon={<DollarSign className="h-5 w-5" />}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Valor Mensal (R$) *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </div>
                <input
                  {...register("monthly_value", {
                    setValueAs: (value) => {
                      if (!value || value === "") return null;

                      // 🔧 CORREÇÃO: Usar função utilitária robusta existente
                      const numericValue = parseCurrencyRobust(value);
                      return numericValue || null;
                    },
                  })}
                  type="text"
                  inputMode="decimal"
                  onBlur={(e) => {
                    // Formatar apenas quando sair do campo
                    const value = e.target.value;
                    if (value && value !== "") {
                      const numericValue = parseFloat(
                        value
                          .replace(/[^\d.,]/g, "")
                          .replace(/\./g, "")
                          .replace(",", ".")
                      );
                      if (!isNaN(numericValue)) {
                        e.target.value = numericValue.toLocaleString("pt-BR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        });
                      }
                    }
                  }}
                  onKeyDown={(e) => {
                    // Permitir teclas especiais
                    if (
                      [
                        "Backspace",
                        "Delete",
                        "Tab",
                        "Escape",
                        "Enter",
                        "Home",
                        "End",
                        "ArrowLeft",
                        "ArrowRight",
                        "ArrowUp",
                        "ArrowDown",
                      ].includes(e.key)
                    ) {
                      return;
                    }
                    // Permitir Ctrl+A, Ctrl+C, Ctrl+V, etc.
                    if (e.ctrlKey || e.metaKey) {
                      return;
                    }
                    // Permitir apenas números, vírgula e ponto
                    if (!/[0-9.,]/.test(e.key)) {
                      e.preventDefault();
                    }
                  }}
                  placeholder="Ex: 1999,50 ou 1.999,50"
                  className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                />
              </div>
              {errors.monthly_value && (
                <p className="text-sm text-red-600 mt-1">
                  {errors.monthly_value.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Período de Controle
              </label>
              <select
                {...register("control_period")}
                value={watch("control_period") || ""}
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
              >
                <option value="DAILY">Diário</option>
                <option value="WEEKLY">Semanal</option>
                <option value="MONTHLY">Mensal</option>
                <option value="QUARTERLY">Trimestral</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Frequência de controle de vidas e faturamento
              </p>
            </div>
          </div>
        </Card>

        {/* Seção 4: Local de Atendimento */}
        <Card
          title="Local de Atendimento"
          icon={<Building2 className="h-5 w-5" />}
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Onde os serviços serão prestados? *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="flex items-center space-x-3 p-4 border border-border rounded-lg hover:bg-muted/30 cursor-pointer">
                  <input
                    {...register("service_address_type")}
                    type="radio"
                    value="PATIENT"
                    checked={watch("service_address_type") === "PATIENT"}
                    className="text-primary"
                  />
                  <div>
                    <div className="font-medium">🏠 Endereço do paciente</div>
                    <div className="text-xs text-muted-foreground">
                      Atendimento domiciliar
                    </div>
                  </div>
                </label>
                <label className="flex items-center space-x-3 p-4 border border-border rounded-lg hover:bg-muted/30 cursor-pointer">
                  <input
                    {...register("service_address_type")}
                    type="radio"
                    value="CLINIC"
                    checked={watch("service_address_type") === "CLINIC"}
                    className="text-primary"
                  />
                  <div>
                    <div className="font-medium">🏥 Endereço fixo</div>
                    <div className="text-xs text-muted-foreground">
                      Clínica ou consultório
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {watch("service_address_type") === "CLINIC" && (
              <div className="mt-4">
                <AddressInputGroup
                  addresses={serviceAddresses}
                  onChange={setServiceAddresses}
                  onAdd={(newAddress) =>
                    setServiceAddresses([...serviceAddresses, newAddress])
                  }
                  onRemove={(index) =>
                    setServiceAddresses(
                      serviceAddresses.filter((_, i) => i !== index)
                    )
                  }
                  required={false}
                  disabled={false}
                  showValidation={false}
                  minAddresses={0}
                  maxAddresses={3}
                  title="Endereço(s) da Clínica/Consultório"
                />
              </div>
            )}
          </div>
        </Card>

        {/* Seção 5: Observações */}
        <Card title="Observações" icon={<FileText className="h-5 w-5" />}>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              Observações sobre o contrato
            </label>
            <textarea
              {...register("notes")}
              value={watch("notes") || ""}
              rows={4}
              placeholder="Digite observações adicionais sobre este contrato..."
              className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none resize-none"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Informações adicionais sobre o contrato (opcional)
            </p>
          </div>
        </Card>
      </div>

      {/* Alertas de Validação */}
      {Object.keys(errors).length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">
                Erros de Validação
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <ul className="list-disc list-inside space-y-1">
                  {Object.entries(errors).map(([field, error]) => (
                    <li key={field}>{error?.message}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Card>
      )}
    </form>
  );
};

export default ContractForm;
