import React from 'react';
import Card from '../../ui/Card';

interface CompanyReceitaFederalSectionProps {
  metadata: Record<string, any>;
}

const CompanyReceitaFederalSection: React.FC<CompanyReceitaFederalSectionProps> = ({ metadata }) => {
  // Debug temporário - remover após correção
  console.log('🔍 CompanyReceitaFederalSection - metadata recebido:', metadata);
  console.log('🔍 CompanyReceitaFederalSection - keys:', Object.keys(metadata || {}));
  console.log('🔍 CompanyReceitaFederalSection - cnae_fiscal:', metadata?.cnae_fiscal);
  console.log('🔍 CompanyReceitaFederalSection - cnaes_secundarios:', metadata?.cnaes_secundarios);
  
  if (!metadata || Object.keys(metadata).length === 0) {
    console.log('❌ CompanyReceitaFederalSection - não exibindo (metadata vazio)');
    return null;
  }
  
  console.log('✅ CompanyReceitaFederalSection - exibindo seção');

  return (
    <Card title="Informações da Receita Federal" className="bg-blue-50 dark:bg-blue-900/20">
      <div className="space-y-4">
        {/* CNAE Principal */}
        {metadata.cnae_fiscal && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                CNAE Principal
              </label>
              <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                {metadata.cnae_fiscal} - {metadata.cnae_fiscal_descricao}
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
        {metadata.cnaes_secundarios && metadata.cnaes_secundarios.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">
              CNAEs Secundários
            </label>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {metadata.cnaes_secundarios.map((cnae: any, index: number) => (
                <p key={index} className="text-xs text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                  {cnae.code} - {cnae.text}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Informações da situação */}
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

        {/* Capital social e última atualização */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {metadata.capital_social && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Capital Social
              </label>
              <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                R$ {metadata.capital_social}
              </p>
            </div>
          )}
          {metadata.ultima_atualizacao_rf && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Última Atualização RF
              </label>
              <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                {new Date(metadata.ultima_atualizacao_rf).toLocaleDateString('pt-BR')}
              </p>
            </div>
          )}
        </div>

        {/* Situação especial e motivo */}
        {(metadata.situacao_especial || metadata.motivo_situacao) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {metadata.situacao_especial && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Situação Especial
                </label>
                <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                  {metadata.situacao_especial}
                </p>
              </div>
            )}
            {metadata.motivo_situacao && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Motivo da Situação
                </label>
                <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                  {metadata.motivo_situacao}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default CompanyReceitaFederalSection;