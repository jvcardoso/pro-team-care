/**
 * Serviço para consulta de dados de empresa via CNPJ
 * Utiliza APENAS endpoint público - sem autenticação
 * Evita problemas de loop de login
 */

import axios from "axios";
import { createAxiosConfig } from "../config/http";

/**
 * Consulta dados de empresa pelo CNPJ
 * @param {string} cnpj - CNPJ limpo (apenas números)
 * @returns {Promise<Object>} Dados da empresa
 */
export const consultarCNPJ = async (cnpj) => {
  // Remover caracteres não numéricos
  const cnpjLimpo = cnpj.replace(/\D/g, "");

  if (cnpjLimpo.length !== 14) {
    throw new Error("CNPJ deve ter 14 dígitos");
  }

  // 🔄 Usar configuração HTTP padronizada para CNPJ service
  const cnpjApi = axios.create(createAxiosConfig("cnpj"));

  try {
    console.log("Consultando CNPJ (apenas endpoint público):", cnpjLimpo);

    // Usar apenas endpoint público - sem autenticação
    const response = await cnpjApi.get(
      `/api/v1/cnpj/publico/consultar/${cnpjLimpo}`
    );
    const data = response.data;

    if (!data.success) {
      throw new Error(data.message || "CNPJ não encontrado ou inválido");
    }

    return data.data;
  } catch (error) {
    console.error("Erro ao consultar CNPJ:", error);

    // Tratamento específico para erros da API
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }

    // Tratamento para erros de rede
    if (
      error.message.includes("Network Error") ||
      error.code === "ECONNABORTED"
    ) {
      throw new Error(
        "Erro de conexão. Verifique sua internet e tente novamente."
      );
    }

    // Tratamento para timeout
    if (error.code === "ECONNABORTED") {
      throw new Error(
        "Consulta demorou muito para responder. Tente novamente."
      );
    }

    throw new Error(error.message || "Erro inesperado ao consultar CNPJ");
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
  const cnpjLimpo = cnpj.replace(/\D/g, "");
  return cnpjLimpo.length === 14;
};

/**
 * Formata CNPJ para exibição
 * @param {string} cnpj - CNPJ limpo
 * @returns {string} CNPJ formatado
 */
export const formatarCNPJ = (cnpj) => {
  const cnpjLimpo = cnpj.replace(/\D/g, "");

  if (cnpjLimpo.length === 14) {
    return cnpjLimpo.replace(
      /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
      "$1.$2.$3/$4-$5"
    );
  }

  return cnpj;
};
