/**
 * Serviço para consulta de dados de empresa via CNPJ
 * Utiliza proxy local que consulta ReceitaWS
 */

import { api } from './api';

/**
 * Consulta dados de empresa pelo CNPJ
 * @param {string} cnpj - CNPJ limpo (apenas números)
 * @returns {Promise<Object>} Dados da empresa
 */
export const consultarCNPJ = async (cnpj) => {
  // Remover caracteres não numéricos
  const cnpjLimpo = cnpj.replace(/\D/g, '');
  
  if (cnpjLimpo.length !== 14) {
    throw new Error('CNPJ deve ter 14 dígitos');
  }

  try {
    const response = await api.get(`/api/v1/cnpj/consultar/${cnpjLimpo}`);
    
    const data = response.data;

    if (!data.success) {
      throw new Error(data.message || 'CNPJ não encontrado ou inválido');
    }

    // Dados já vêm mapeados do backend
    return data.data;
  } catch (error) {
    console.error('Erro ao consultar CNPJ:', error);
    
    // Tratamento específico para erros de autenticação
    if (error.response?.status === 401) {
      throw new Error('Sessão expirada. Faça login novamente para consultar CNPJ.');
    }
    
    // Tratamento para erros da API
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    
    // Tratamento para erros de rede
    if (error.message.includes('Network Error')) {
      throw new Error('Erro de conexão. Verifique sua internet.');
    }
    
    throw new Error(error.message || 'Erro inesperado ao consultar CNPJ');
  }
};

// Dados já vêm mapeados do backend, não precisa mais mapear

// Funções de mapeamento removidas - backend já faz isso

/**
 * Valida formato do CNPJ
 * @param {string} cnpj - CNPJ para validar
 * @returns {boolean} True se válido
 */
export const validarFormatoCNPJ = (cnpj) => {
  const cnpjLimpo = cnpj.replace(/\D/g, '');
  return cnpjLimpo.length === 14;
};

/**
 * Formata CNPJ para exibição
 * @param {string} cnpj - CNPJ limpo
 * @returns {string} CNPJ formatado
 */
export const formatarCNPJ = (cnpj) => {
  const cnpjLimpo = cnpj.replace(/\D/g, '');
  
  if (cnpjLimpo.length === 14) {
    return cnpjLimpo.replace(
      /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
      '$1.$2.$3/$4-$5'
    );
  }
  
  return cnpj;
};