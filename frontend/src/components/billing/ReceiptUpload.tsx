/**
 * ReceiptUpload Component
 * File upload component for payment receipts
 */

import React, { useState, useRef } from "react";
import billingService from "../../services/billingService";
import { PaymentReceipt } from "../../types/billing.types";

interface ReceiptUploadProps {
  invoiceId: number;
  onUploadSuccess?: (receipt: PaymentReceipt) => void;
  onUploadError?: (error: string) => void;
  maxFileSize?: number;
  className?: string;
}

const ReceiptUpload: React.FC<ReceiptUploadProps> = ({
  invoiceId,
  onUploadSuccess,
  onUploadError,
  maxFileSize = 10 * 1024 * 1024, // 10MB
  className = "",
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [notes, setNotes] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    const validation = billingService.validateReceiptFile(file, maxFileSize);

    if (!validation.valid) {
      onUploadError?.(validation.error || "Arquivo inválido");
      return;
    }

    uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    setUploading(true);

    try {
      const receipt = await billingService.uploadPaymentReceipt(
        invoiceId,
        file,
        notes || undefined
      );

      onUploadSuccess?.(receipt);
      setNotes("");

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || "Erro ao enviar comprovante";
      onUploadError?.(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* File upload area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${
            dragOver
              ? "border-blue-400 bg-blue-50"
              : "border-gray-300 hover:border-gray-400"
          }
          ${uploading ? "opacity-50 cursor-not-allowed" : ""}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={uploading ? undefined : openFileDialog}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleFileInputChange}
          disabled={uploading}
        />

        {uploading ? (
          <div className="space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-600">Enviando comprovante...</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-4xl">📁</div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                Clique para selecionar ou arraste o arquivo aqui
              </p>
              <p className="text-xs text-gray-500 mt-1">
                JPG, PNG ou PDF até {Math.round(maxFileSize / 1024 / 1024)}MB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Notes input */}
      <div>
        <label
          htmlFor="receipt-notes"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Observações (opcional)
        </label>
        <textarea
          id="receipt-notes"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Adicione observações sobre o comprovante..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          disabled={uploading}
        />
      </div>

      {/* Upload guidelines */}
      <div className="bg-gray-50 rounded-md p-3">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Orientações:</h4>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• Envie comprovantes de pagamento em formato JPG, PNG ou PDF</li>
          <li>• Certifique-se de que o documento está legível</li>
          <li>
            • Inclua observações se necessário (número de referência, etc.)
          </li>
          <li>• Arquivos serão analisados pela equipe financeira</li>
        </ul>
      </div>
    </div>
  );
};

export default ReceiptUpload;
