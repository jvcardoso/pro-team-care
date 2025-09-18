import React from "react";
import Button from "../ui/Button";
import ActionDropdown from "../ui/ActionDropdown";
import {
  Building,
  Calendar,
  Phone,
  Mail,
  MapPin,
  Edit,
  Eye,
  Trash2,
} from "lucide-react";

const CompanyMobileCard = React.memo(
  ({
    company,
    onView,
    onEdit,
    onDelete,
    getStatusBadge,
    getStatusLabel,
    formatTaxId,
  }) => {
    if (!company) return null;

    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
        {/* Company Info */}
        <div className="mb-3">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 dark:text-white text-base break-words">
                {company.name || "Nome não informado"}
              </h3>
              {company.trade_name && company.trade_name !== company.name && (
                <p className="text-sm text-gray-600 dark:text-gray-300 break-words">
                  {company.trade_name}
                </p>
              )}
            </div>
            <span className={getStatusBadge(company.status || "active")}>
              {getStatusLabel(company.status || "active")}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div className="flex items-center">
              <Building className="h-4 w-4 mr-2 text-gray-500" />
              <span className="font-mono text-gray-900 dark:text-white">
                {formatTaxId(company.tax_id)}
              </span>
            </div>
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-2 text-gray-500" />
              <span className="text-gray-600 dark:text-gray-300">
                {company.created_at
                  ? new Date(company.created_at).toLocaleDateString("pt-BR")
                  : "-"}
              </span>
            </div>
          </div>
        </div>

        {/* Contact Info */}
        <div className="flex flex-wrap gap-4 mb-4 text-sm text-gray-600 dark:text-gray-300">
          <div className="flex items-center">
            <Phone className="h-3 w-3 mr-1" />
            {company.phones_count || 0} tel
          </div>
          <div className="flex items-center">
            <Mail className="h-3 w-3 mr-1" />
            {company.emails_count || 0} email
          </div>
          <div className="flex items-center">
            <MapPin className="h-3 w-3 mr-1" />
            {company.addresses_count || 0} end
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end pt-3 border-t border-gray-200 dark:border-gray-700">
          <ActionDropdown>
            <ActionDropdown.Item
              icon={<Eye className="h-4 w-4" />}
              onClick={() => onView(company.id)}
            >
              Ver Detalhes
            </ActionDropdown.Item>

            <ActionDropdown.Item
              icon={<Edit className="h-4 w-4" />}
              onClick={() => onEdit(company.id)}
            >
              Editar
            </ActionDropdown.Item>

            <ActionDropdown.Item
              icon={<Trash2 className="h-4 w-4" />}
              onClick={() => onDelete(company.id)}
              variant="danger"
            >
              Excluir
            </ActionDropdown.Item>
          </ActionDropdown>
        </div>
      </div>
    );
  }
);

CompanyMobileCard.displayName = "CompanyMobileCard";

export default CompanyMobileCard;
