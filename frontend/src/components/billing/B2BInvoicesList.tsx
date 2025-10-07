import React, { useState, useEffect } from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { Badge } from "../ui/Badge";
import Input from "../ui/Input";
import Select from "react-select";
import { notify } from "../../utils/notifications";
import {
  FileText,
  Search,
  Download,
  Eye,
  CreditCard,
  Calendar,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
} from "lucide-react";
import { B2BBillingService } from "../../services/b2bBillingService";
import type {
  InvoiceListProps,
  ProTeamCareInvoice,
} from "../../types/b2b-billing.types";

const B2BInvoicesList: React.FC<InvoiceListProps> = ({
  companyId,
  status: initialStatus,
  limit = 50,
  onInvoiceClick,
  onPaymentConfirm,
}) => {
  const [invoices, setInvoices] = useState<ProTeamCareInvoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>(
    initialStatus || "all"
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<"due_date" | "amount" | "created_at">(
    "due_date"
  );

  const statusOptions = [
    { value: "all", label: "Todos os Status" },
    { value: "pending", label: "Pendentes" },
    { value: "paid", label: "Pagas" },
    { value: "overdue", label: "Vencidas" },
    { value: "cancelled", label: "Canceladas" },
  ];

  const sortOptions = [
    { value: "due_date", label: "Data de Vencimento" },
    { value: "amount", label: "Valor" },
    { value: "created_at", label: "Data de Criação" },
  ];

  useEffect(() => {
    loadInvoices();
  }, [companyId, statusFilter]);

  const loadInvoices = async () => {
    try {
      setLoading(true);

      let invoicesData: ProTeamCareInvoice[];

      if (companyId) {
        // Faturas de uma empresa específica
        const effectiveStatus =
          statusFilter === "all" ? undefined : statusFilter;
        invoicesData = await B2BBillingService.getCompanyInvoices(
          companyId,
          effectiveStatus,
          limit
        );
      } else if (statusFilter === "overdue") {
        // Faturas vencidas globais
        invoicesData = await B2BBillingService.getOverdueInvoices();
      } else if (statusFilter !== "all") {
        // Faturas por status específico
        invoicesData = await B2BBillingService.getInvoicesByStatus(
          statusFilter,
          limit
        );
      } else {
        // Todas as faturas pendentes por padrão
        invoicesData = await B2BBillingService.getInvoicesByStatus(
          "pending",
          limit
        );
      }

      setInvoices(invoicesData);
    } catch (err: any) {
      notify.error("Erro ao carregar faturas: " + err.message);
      console.error("Erro ao carregar faturas:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCheckout = async (invoice: ProTeamCareInvoice) => {
    try {
      const checkoutResponse = await B2BBillingService.createCheckoutSession(
        invoice.id
      );
      if (checkoutResponse.success && checkoutResponse.checkout_url) {
        // Check if it's a mock URL
        if (
          checkoutResponse.checkout_url.includes("mock-pagbank.proteamcare.com")
        ) {
          const amount =
            typeof invoice.amount === "string"
              ? parseFloat(invoice.amount)
              : invoice.amount;
          notify.info(
            `Checkout criado em modo demonstração. Fatura: ${
              invoice.invoice_number
            } • Valor: R$ ${amount.toFixed(2)}`,
            { duration: 5000 }
          );
        } else {
          window.open(
            checkoutResponse.checkout_url,
            "_blank",
            "noopener,noreferrer"
          );
        }
      }
    } catch (err: any) {
      notify.error("Erro ao criar checkout: " + err.message);
    }
  };

  const filteredAndSortedInvoices = invoices
    .filter((invoice) => {
      if (!searchTerm) return true;
      const term = searchTerm.toLowerCase();
      return (
        invoice.invoice_number.toLowerCase().includes(term) ||
        invoice.notes?.toLowerCase().includes(term)
      );
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "due_date":
          return (
            new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
          );
        case "amount":
          return b.amount - a.amount;
        case "created_at":
          return (
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
        default:
          return 0;
      }
    });

  const getInvoiceIcon = (invoice: ProTeamCareInvoice) => {
    if (invoice.status === "paid") {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    }
    if (B2BBillingService.isOverdue(invoice)) {
      return <AlertTriangle className="h-4 w-4 text-red-600" />;
    }
    return <Clock className="h-4 w-4 text-yellow-600" />;
  };

  const getDaysInfo = (invoice: ProTeamCareInvoice) => {
    if (invoice.status === "paid") {
      return "Pago";
    }

    const days = B2BBillingService.getDaysUntilDue(invoice);
    if (days < 0) {
      return `${Math.abs(days)} dias em atraso`;
    }
    if (days === 0) {
      return "Vence hoje";
    }
    return `${days} dias para vencer`;
  };

  const getTotalAmount = () => {
    return filteredAndSortedInvoices.reduce(
      (total, invoice) => total + invoice.amount,
      0
    );
  };

  const getStatusCounts = () => {
    const counts = {
      pending: 0,
      paid: 0,
      overdue: 0,
      cancelled: 0,
    };

    invoices.forEach((invoice) => {
      if (
        B2BBillingService.isOverdue(invoice) &&
        invoice.status === "pending"
      ) {
        counts.overdue++;
      } else {
        counts[invoice.status as keyof typeof counts]++;
      }
    });

    return counts;
  };

  const statusCounts = getStatusCounts();

  if (loading && invoices.length === 0) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Carregando faturas...</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-card-foreground flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              Faturas Pro Team Care
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              Total: {B2BBillingService.formatCurrency(getTotalAmount())}
            </span>
          </div>
        </div>

        {/* Resumo de Status */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-lg font-bold text-yellow-700">
              {statusCounts.pending}
            </div>
            <div className="text-sm text-yellow-600">Pendentes</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-lg font-bold text-green-700">
              {statusCounts.paid}
            </div>
            <div className="text-sm text-green-600">Pagas</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-lg font-bold text-red-700">
              {statusCounts.overdue}
            </div>
            <div className="text-sm text-red-600">Vencidas</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-lg font-bold text-gray-700">
              {statusCounts.cancelled}
            </div>
            <div className="text-sm text-gray-600">Canceladas</div>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 space-y-4">
        {/* Filtros */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Buscar por número da fatura..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Select
            value={statusOptions.find(
              (option) => option.value === statusFilter
            )}
            onChange={(option) => setStatusFilter(option.value)}
            options={statusOptions}
            className="w-48"
          />
          <Select
            value={sortOptions.find((option) => option.value === sortBy)}
            onChange={(option) => setSortBy(option.value)}
            options={sortOptions}
            className="w-48"
          />
        </div>

        {/* Lista de Faturas */}
        <div className="space-y-3">
          {filteredAndSortedInvoices.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>Nenhuma fatura encontrada</p>
            </div>
          ) : (
            filteredAndSortedInvoices.map((invoice) => (
              <div
                key={invoice.id}
                className={`p-4 border rounded-lg hover:shadow-sm transition-shadow cursor-pointer ${
                  B2BBillingService.isOverdue(invoice)
                    ? "border-red-200 bg-red-50"
                    : "border-gray-200"
                }`}
                onClick={() => onInvoiceClick?.(invoice)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getInvoiceIcon(invoice)}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {invoice.invoice_number}
                        </span>
                        <Badge
                          className={B2BBillingService.getStatusColor(
                            invoice.status
                          )}
                        >
                          {B2BBillingService.getStatusLabel(invoice.status)}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600">
                        <span className="flex items-center gap-1 mt-1">
                          <Calendar className="h-3 w-3" />
                          Venc: {B2BBillingService.formatDate(
                            invoice.due_date
                          )}{" "}
                          • {getDaysInfo(invoice)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-semibold text-lg">
                        {B2BBillingService.formatCurrency(invoice.amount)}
                      </div>
                      <div className="text-sm text-gray-600">
                        {B2BBillingService.getStatusLabel(
                          invoice.payment_method
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          onInvoiceClick?.(invoice);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>

                      {invoice.status === "pending" && (
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateCheckout(invoice);
                          }}
                          disabled={loading}
                        >
                          <CreditCard className="mr-2 h-4 w-4" />
                          Pagar
                        </Button>
                      )}

                      {invoice.status === "pending" && onPaymentConfirm && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            onPaymentConfirm(invoice);
                          }}
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>

                {invoice.notes && (
                  <div className="mt-2 text-sm text-gray-600 italic">
                    {invoice.notes}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {loading && invoices.length > 0 && (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default B2BInvoicesList;
