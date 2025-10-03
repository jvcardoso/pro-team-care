import React from "react";
import { Mail, Send } from "lucide-react";
import Card from "../ui/Card";

interface EmailData {
  id?: string | number;
  email_address: string;
  type: string;
  is_principal?: boolean;
  is_verified?: boolean;
  description?: string;
}

interface EmailDisplayCardProps {
  emails: EmailData[];
  title?: string;
  getEmailTypeLabel?: (type: string) => string;
  onOpenEmail?: (email: EmailData) => void;
}

const EmailDisplayCard: React.FC<EmailDisplayCardProps> = ({
  emails,
  title = "E-mails",
  getEmailTypeLabel = (type) => type,
  onOpenEmail = (email) => {
    const url = `mailto:${email.email_address}`;
    window.open(url, "_blank");
  },
}) => {
  return (
    <Card title={title}>
      {!emails || emails.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nenhum e-mail cadastrado
        </p>
      ) : (
      <div className="space-y-4">
        {emails.map((email, index) => (
          <div key={email.id || index} className="p-3 bg-muted/30 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <Mail className="h-4 w-4 text-green-600 dark:text-green-300" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-foreground break-all">
                  {email.email_address}
                </p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{getEmailTypeLabel(email.type)}</span>
                  {email.is_principal && (
                    <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                      Principal
                    </span>
                  )}
                  {email.is_verified && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                      Verificado
                    </span>
                  )}
                </div>
                {email.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {email.description}
                  </p>
                )}

                {/* Action Button */}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => onOpenEmail(email)}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-green-50 text-green-600 rounded hover:bg-green-100 transition-colors"
                  >
                    <Send className="h-3 w-3" />
                    Enviar Email
                  </button>
                </div>

                {/* Full-width button for company style (optional) */}
                <div className="mt-3 hidden">
                  <button
                    onClick={() => onOpenEmail(email)}
                    className="flex items-center justify-center gap-2 w-full p-3 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-lg transition-colors"
                  >
                    <Send className="h-5 w-5" />
                    <span className="text-sm font-medium">Enviar Email</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      )}
    </Card>
  );
};

export default EmailDisplayCard;
