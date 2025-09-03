/**
 * Servico para enriquecer dados de endereco usando ViaCEP e geocoding
 * Complementa dados basicos do CNPJ com informacoes completas
 */

import geocodingService from "./geocodingService";
import { serviceLogger } from "../utils/logger";

const logger = serviceLogger.setContext("AddressEnrichment");

/**
 * Mapeamento de UF para codigo IBGE do estado
 */
const IBGE_STATE_CODES = {
  AC: 12,
  AL: 27,
  AP: 16,
  AM: 13,
  BA: 29,
  CE: 23,
  DF: 53,
  ES: 32,
  GO: 52,
  MA: 21,
  MT: 51,
  MS: 50,
  MG: 31,
  PA: 15,
  PB: 25,
  PR: 41,
  PE: 26,
  PI: 22,
  RJ: 33,
  RN: 24,
  RS: 43,
  RO: 11,
  RR: 14,
  SC: 42,
  SP: 35,
  SE: 28,
  TO: 17,
};

/**
 * Converte UF para codigo IBGE do estado
 * @param {string} uf - Unidade Federativa (ex: 'SP', 'RJ')
 * @returns {number|null} Codigo IBGE do estado ou null se invalido
 */
function getIbgeStateCode(uf) {
  if (!uf || typeof uf !== "string") return null;
  const upperUf = uf.toUpperCase();
  return IBGE_STATE_CODES[upperUf] || null;
}

/**
 * Classe para enriquecer dados de endereco
 */
class AddressEnrichmentService {
  constructor() {
    this.cache = new Map(); // Cache para evitar consultas repetidas
  }

  /**
   * Consulta ViaCEP para obter dados completos do endereco
   * @param {string} cep - CEP limpo (8 digitos)
   * @returns {Promise<Object|null>} Dados do ViaCEP ou null se erro
   */
  async consultarViaCEP(cep) {
    if (!cep || cep.length !== 8) {
      logger.warn("CEP inválido para consulta ViaCEP", { cep });
      return null;
    }

    // Verificar cache
    const cacheKey = `viacep_${cep}`;
    if (this.cache.has(cacheKey)) {
      logger.cache("hit", cacheKey, { cep });
      return this.cache.get(cacheKey);
    }

    try {
      logger.service("consultando ViaCEP", { cep });

      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`, {
        timeout: 10000, // 10 segundos de timeout
      });

      if (!response.ok) {
        throw new Error(`ViaCEP API error: ${response.status}`);
      }

      const data = await response.json();

      if (data.erro) {
        logger.warn("CEP não encontrado no ViaCEP", { cep });
        return null;
      }

      // Verificar se ViaCEP retornou dados validos
      if (!data.logradouro && !data.bairro && !data.localidade) {
        logger.warn("ViaCEP retornou dados incompletos", { data });
        return null;
      }

      // Cache do resultado
      this.cache.set(cacheKey, data);

      logger.enrichment("ViaCEP", "consultado com sucesso", data);
      return data;
    } catch (error) {
      logger.error("Erro ao consultar ViaCEP", { cep, error: error.message });
      return null;
    }
  }

  /**
   * Enriquecer endereco com dados do ViaCEP
   * @param {Object} addressData - Dados basicos do endereco
   * @returns {Promise<Object>} Endereco enriquecido
   */
  async enriquecerComViaCEP(addressData) {
    if (!addressData || !addressData.zip_code) {
      console.warn("Endereco sem CEP para enriquecimento:", addressData);
      return addressData;
    }

    const cleanCEP = addressData.zip_code.replace(/\D/g, "");
    if (cleanCEP.length !== 8) {
      console.warn("CEP invalido para enriquecimento:", addressData.zip_code);
      return addressData;
    }

    try {
      const viaCepData = await this.consultarViaCEP(cleanCEP);

      if (!viaCepData) {
        console.warn("ViaCEP nao retornou dados para CEP:", cleanCEP);
        return addressData;
      }

      // Criar datas naive (sem timezone) para o banco - formato YYYY-MM-DD HH:MM:SS
      const now = new Date();
      const naiveDateTime = now.toISOString().replace("T", " ").split(".")[0];

      // Mesclar dados do ViaCEP com dados existentes
      // IMPORTANTE: ViaCEP apenas enriquece dados, nunca sobrescreve informações existentes importantes
      const enrichedAddress = {
        ...addressData,
        // Dados basicos do endereco - preservar dados originais quando existem
        street:
          viaCepData.logradouro && viaCepData.logradouro.trim()
            ? viaCepData.logradouro
            : addressData.street || "",
        number: addressData.number || "", // SEMPRE preservar número original do CNPJ
        neighborhood:
          viaCepData.bairro && viaCepData.bairro.trim()
            ? viaCepData.bairro
            : addressData.neighborhood || "",
        city:
          viaCepData.localidade && viaCepData.localidade.trim()
            ? viaCepData.localidade
            : addressData.city || "",
        state:
          viaCepData.uf && viaCepData.uf.trim()
            ? viaCepData.uf
            : addressData.state || "",
        details:
          viaCepData.complemento && viaCepData.complemento.trim()
            ? viaCepData.complemento
            : addressData.details || "",

        // Codigos oficiais brasileiros do ViaCEP
        ibge_city_code: viaCepData.ibge
          ? parseInt(viaCepData.ibge)
          : addressData.ibge_city_code,
        gia_code: viaCepData.gia || addressData.gia_code,
        siafi_code: viaCepData.siafi || addressData.siafi_code,
        area_code: viaCepData.ddd || addressData.area_code,

        // Inferir codigo IBGE do estado baseado no UF
        ibge_state_code: viaCepData.uf
          ? getIbgeStateCode(viaCepData.uf)
          : addressData.ibge_state_code,

        // Manter campos originais se ViaCEP nao tiver
        zip_code: addressData.zip_code, // Manter formato original
        country: addressData.country || "BR",
        type: addressData.type || "commercial",
        is_principal:
          addressData.is_principal !== undefined
            ? addressData.is_principal
            : true,

        // Adicionar metadados de validacao
        enrichment_source: "viacep",
        validation_source: "viacep",
        is_validated: true,

        // Armazenar dados completos do ViaCEP para referencia futura
        via_cep_data: viaCepData,
      };

      console.log("✅ Endereco enriquecido com ViaCEP:", {
        original_number: addressData.number,
        preserved_number: enrichedAddress.number,
        original_street: addressData.street,
        enriched_street: enrichedAddress.street,
        full_address: `${enrichedAddress.street}, ${enrichedAddress.number}, ${enrichedAddress.neighborhood}, ${enrichedAddress.city}, ${enrichedAddress.state}`,
        // 🔍 FORENSIC DEBUG - Códigos ViaCEP
        viacep_codes: {
          ibge: viaCepData.ibge,
          gia: viaCepData.gia,
          siafi: viaCepData.siafi,
          ddd: viaCepData.ddd,
        },
        mapped_codes: {
          ibge_city_code: enrichedAddress.ibge_city_code,
          gia_code: enrichedAddress.gia_code,
          siafi_code: enrichedAddress.siafi_code,
          area_code: enrichedAddress.area_code,
        },
      });

      return enrichedAddress;
    } catch (error) {
      console.error("Erro ao enriquecer endereco com ViaCEP:", error);
      return addressData;
    }
  }

  /**
   * Adicionar coordenadas geograficas ao endereco
   * @param {Object} addressData - Dados do endereco
   * @returns {Promise<Object>} Dados com coordenadas
   */
  async adicionarCoordenadas(addressData) {
    if (!addressData) {
      return addressData;
    }

    try {
      // Criar data naive para o banco (definir no início) - formato YYYY-MM-DD HH:MM:SS
      const now = new Date();
      const naiveDateTime = now.toISOString().replace("T", " ").split(".")[0];

      // Tentar múltiplas variações do endereço para melhorar as chances de sucesso
      const addressVariations = [
        // 1. Endereço completo
        [
          addressData.street,
          addressData.number,
          addressData.neighborhood,
          addressData.city,
          addressData.state,
          "Brasil",
        ],
        // 2. Sem número (mais genérico)
        [
          addressData.street,
          addressData.neighborhood,
          addressData.city,
          addressData.state,
          "Brasil",
        ],
        // 3. Apenas rua e cidade
        [addressData.street, addressData.city, addressData.state, "Brasil"],
        // 4. Apenas bairro e cidade
        [
          addressData.neighborhood,
          addressData.city,
          addressData.state,
          "Brasil",
        ],
        // 5. Apenas cidade
        [addressData.city, addressData.state, "Brasil"],
      ];

      let geoData = null;

      for (const parts of addressVariations) {
        const fullAddress = parts.filter(Boolean).join(", ");

        if (!fullAddress.trim()) continue;

        console.log("🗺️ Tentando geocoding para:", fullAddress);

        try {
          geoData = await geocodingService.geocode(fullAddress);
          if (geoData) {
            console.log("✅ Geocoding encontrado para:", fullAddress);
            break;
          }
        } catch (error) {
          console.warn(
            "Tentativa de geocoding falhou para:",
            fullAddress,
            error.message
          );
          continue;
        }
      }

      if (!geoData) {
        console.warn(
          "Geocoding nao retornou coordenadas para nenhuma variacao do endereco"
        );
        return addressData;
      }

      // Adicionar coordenadas aos dados do endereco
      const addressWithCoordinates = {
        ...addressData,
        latitude: geoData.latitude,
        longitude: geoData.longitude,
        geocoding_accuracy: geoData.geocoding_accuracy,
        geocoding_source: geoData.geocoding_source,
        formatted_address: geoData.formatted_address,
        coordinates_source: "nominatim",
      };

      console.log("✅ Coordenadas adicionadas:", {
        latitude: geoData.latitude,
        longitude: geoData.longitude,
        accuracy: geoData.geocoding_accuracy,
      });

      return addressWithCoordinates;
    } catch (error) {
      console.error("Erro ao adicionar coordenadas:", error);
      return addressData;
    }
  }

  /**
   * Enriquecer endereco completo (ViaCEP + geocoding)
   * @param {Object} addressData - Dados basicos do endereco
   * @returns {Promise<Object>} Dados completamente enriquecidos
   */
  async enriquecerEnderecoCompleto(addressData) {
    if (!addressData) {
      return addressData;
    }

    console.log(
      "🚀 Iniciando enriquecimento completo do endereco:",
      addressData
    );

    try {
      // Primeiro: enriquecer com ViaCEP
      const viaCepEnriched = await this.enriquecerComViaCEP(addressData);

      // Segundo: adicionar coordenadas
      const fullyEnriched = await this.adicionarCoordenadas(viaCepEnriched);

      console.log("🎉 Endereco completamente enriquecido:", fullyEnriched);
      return fullyEnriched;
    } catch (error) {
      console.error("Erro no enriquecimento completo do endereco:", error);
      return addressData;
    }
  }

  /**
   * Enriquecer multiplos enderecos
   * @param {Array} addresses - Lista de enderecos
   * @returns {Promise<Array>} Lista de enderecos enriquecidos
   */
  async enriquecerMultiplosEnderecos(addresses) {
    if (!Array.isArray(addresses) || addresses.length === 0) {
      return addresses;
    }

    console.log(`📋 Enriquecendo ${addresses.length} enderecos...`);

    const enrichedAddresses = await Promise.all(
      addresses.map(async (address, index) => {
        try {
          console.log(
            `🔄 Enriquecendo endereco ${index + 1}/${addresses.length}`
          );
          return await this.enriquecerEnderecoCompleto(address);
        } catch (error) {
          console.error(`Erro ao enriquecer endereco ${index + 1}:`, error);
          return address; // Retornar endereco original em caso de erro
        }
      })
    );

    console.log("✅ Todos os enderecos foram processados");
    return enrichedAddresses;
  }

  /**
   * Limpar cache (util para desenvolvimento)
   */
  clearCache() {
    this.cache.clear();
    console.log("🧹 Cache do servico de enriquecimento limpo");
  }
}

// Instancia singleton
const addressEnrichmentService = new AddressEnrichmentService();

export default addressEnrichmentService;
