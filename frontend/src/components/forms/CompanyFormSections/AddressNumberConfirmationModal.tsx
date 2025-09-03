import React from "react";
import Button from "../../ui/Button";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";

interface AddressNumberConfirmationModalProps {
  show: boolean;
  onConfirm: (confirmed: boolean) => Promise<void>;
}

const AddressNumberConfirmationModal: React.FC<
  AddressNumberConfirmationModalProps
> = ({ show, onConfirm }) => {
  if (!show) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <AlertTriangle className="h-6 w-6 text-yellow-500" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Número do Endereço Não Informado
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Você não informou o número do endereço. Deseja salvar com "S/N"
              (Sem Número) ou voltar para corrigir?
            </p>

            <div className="flex gap-3">
              <Button
                onClick={() => onConfirm(false)}
                variant="secondary"
                className="flex-1"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Corrigir
              </Button>
              <Button onClick={() => onConfirm(true)} className="flex-1">
                <CheckCircle className="h-4 w-4 mr-2" />
                Salvar com S/N
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddressNumberConfirmationModal;
