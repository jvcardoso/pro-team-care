import React from "react";
import Card from "../ui/Card";

const ReceitaFederalInfo = ({
  metadata,
  title = "Informações da Receita Federal",
  className = "bg-blue-50 dark:bg-blue-900/20",
  showCNAEs = true,
  showSituacao = true,
  showCapital = true,
  showLocalizacao = true,
  showNaturezaJuridica = true,
}) => {
  // Debug: Verificar metadados recebidos (apenas em desenvolvimento)
  if (
    process.env.NODE_ENV === "development" &&
    (!metadata || Object.keys(metadata).length === 0)
  ) {
    console.log("ReceitaFederalInfo: Nenhum metadata disponível");
  }

  if (!metadata || Object.keys(metadata).length === 0) {
    return null;
  }

  return (
    <Card title={title} className={className}>
      <div className="space-y-4">
        {/* CNAE Principal */}
        {(metadata.cnae_fiscal || metadata.cnae_principal) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                CNAE Principal
              </label>
              <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                {metadata.cnae_fiscal || metadata.cnae_principal}
                {(metadata.cnae_fiscal_descricao ||
                  metadata.cnae_principal_descricao) &&
                  ` - ${
                    metadata.cnae_fiscal_descricao ||
                    metadata.cnae_principal_descricao
                  }`}
              </p>
            </div>
            {metadata.porte && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Porte da Empresa
                </label>
                <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                  {metadata.porte}
                </p>
              </div>
            )}
          </div>
        )}

        {/* CNAEs Secundários */}
        {showCNAEs &&
          metadata.cnaes_secundarios &&
          metadata.cnaes_secundarios.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                CNAEs Secundários
              </label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {metadata.cnaes_secundarios.map((cnae, index) => (
                  <div
                    key={index}
                    className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-3 rounded border"
                  >
                    <span className="font-mono text-primary">{cnae.code}</span>
                    <span className="text-foreground ml-2">- {cnae.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        {/* Informações da situacao */}
        {showSituacao &&
          (metadata.situacao || metadata.data_situacao || metadata.tipo) && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {metadata.situacao && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Situação na RF
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {metadata.situacao}
                  </p>
                </div>
              )}
              {metadata.data_situacao && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Data da Situação
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {metadata.data_situacao}
                  </p>
                </div>
              )}
              {metadata.tipo && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Tipo de Estabelecimento
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {metadata.tipo}
                  </p>
                </div>
              )}
            </div>
          )}

        {/* Capital social, porte e localização */}
        {showCapital &&
          (metadata.capital_social ||
            metadata.porte ||
            (metadata.municipio && metadata.uf)) && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {metadata.capital_social && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Capital Social
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    R${" "}
                    {parseFloat(metadata.capital_social).toLocaleString(
                      "pt-BR",
                      { minimumFractionDigits: 2 }
                    )}
                  </p>
                </div>
              )}
              {metadata.porte && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Porte da Empresa
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {metadata.porte}
                  </p>
                </div>
              )}
              {showLocalizacao && metadata.municipio && metadata.uf && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Localização RF
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {metadata.municipio} - {metadata.uf}
                  </p>
                </div>
              )}
            </div>
          )}

        {/* Natureza jurídica e última atualização */}
        {showNaturezaJuridica &&
          (metadata.natureza_juridica || metadata.ultima_atualizacao_rf) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {metadata.natureza_juridica && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Natureza Jurídica (RF)
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {metadata.natureza_juridica}
                  </p>
                </div>
              )}
              {metadata.ultima_atualizacao_rf && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Última Atualização RF
                  </label>
                  <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                    {new Date(
                      metadata.ultima_atualizacao_rf
                    ).toLocaleDateString("pt-BR")}
                  </p>
                </div>
              )}
            </div>
          )}
      </div>
    </Card>
  );
};

export default ReceitaFederalInfo;
