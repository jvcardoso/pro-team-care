import React from "react";
import { Phone, MessageCircle } from "lucide-react";
import Card from "../ui/Card";

interface PhoneData {
  id?: string | number;
  number: string;
  area_code?: string;
  country_code?: string;
  type: string;
  is_principal?: boolean;
  is_whatsapp?: boolean;
  description?: string;
}

interface PhoneDisplayCardProps {
  phones: PhoneData[];
  title?: string;
  formatPhone?: (phone: PhoneData) => string;
  getPhoneTypeLabel?: (type: string) => string;
  onOpenWhatsApp?: (phone: PhoneData) => void;
  onCall?: (phone: PhoneData) => void;
}

const PhoneDisplayCard: React.FC<PhoneDisplayCardProps> = ({
  phones,
  title = "Telefones",
  formatPhone = (phone) => {
    const clean = phone.number.replace(/\D/g, "");
    if (phone.area_code) {
      if (clean.length === 9) {
        return `(${phone.area_code}) ${clean.replace(
          /(\d{5})(\d{4})/,
          "$1-$2"
        )}`;
      } else if (clean.length === 8) {
        return `(${phone.area_code}) ${clean.replace(
          /(\d{4})(\d{4})/,
          "$1-$2"
        )}`;
      }
    } else if (clean.length === 11) {
      return clean.replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
    } else if (clean.length === 10) {
      return clean.replace(/(\d{2})(\d{4})(\d{4})/, "($1) $2-$3");
    }
    return phone.number;
  },
  getPhoneTypeLabel = (type) => type,
  onOpenWhatsApp = (phone) => {
    const number = phone.number.replace(/\D/g, "");
    const url = `https://wa.me/${phone.country_code || "55"}${number}`;
    window.open(url, "_blank");
  },
  onCall = (phone) => {
    window.open(`tel:${phone.number}`, "_self");
  },
}) => {
  return (
    <Card title={title}>
      {!phones || phones.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nenhum telefone cadastrado
        </p>
      ) : (
      <div className="space-y-4">
        {phones.map((phone, index) => (
          <div key={phone.id || index} className="p-3 bg-muted/30 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Phone className="h-4 w-4 text-blue-600 dark:text-blue-300" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-foreground">
                  {formatPhone(phone)}
                </p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{getPhoneTypeLabel(phone.type)}</span>
                  {phone.is_principal && (
                    <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                      Principal
                    </span>
                  )}
                  {phone.is_whatsapp && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                      WhatsApp
                    </span>
                  )}
                </div>
                {phone.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {phone.description}
                  </p>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => onCall(phone)}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
                  >
                    <Phone className="h-3 w-3" />
                    Ligar
                  </button>
                  {phone.is_whatsapp && (
                    <button
                      onClick={() => onOpenWhatsApp(phone)}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-green-50 text-green-600 rounded hover:bg-green-100 transition-colors"
                    >
                      <MessageCircle className="h-3 w-3" />
                      WhatsApp
                    </button>
                  )}
                </div>

                {/* Full-width WhatsApp button for company style (optional) */}
                {phone.is_whatsapp && (
                  <div className="mt-3 hidden">
                    <button
                      onClick={() => onOpenWhatsApp(phone)}
                      className="flex items-center justify-center gap-2 w-full p-3 bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:hover:bg-green-900/50 text-green-700 dark:text-green-300 rounded-lg transition-colors"
                    >
                      <MessageCircle className="h-5 w-5" />
                      <span className="text-sm font-medium">
                        Abrir no WhatsApp
                      </span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      )}
    </Card>
  );
};

export default PhoneDisplayCard;
