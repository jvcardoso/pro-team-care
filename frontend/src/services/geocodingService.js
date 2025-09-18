/**
 * Serviço de Geocoding usando APIs públicas
 * Estratégia híbrida: Nominatim (gratuito) como principal
 */

class GeocodingService {
  constructor() {
    this.cache = new Map(); // Cache em memória para sessão
  }

  /**
   * Geocoding usando backend como proxy para Nominatim
   */
  async nominatimGeocode(address) {
    // Importar api dinamicamente para evitar dependências circulares
    const { api } = await import("./api");

    const response = await api.post("/api/v1/geocoding/geocode", {
      address: address,
    });

    const result = response.data;

    return {
      latitude: result.latitude,
      longitude: result.longitude,
      formatted_address: result.formatted_address,
      geocoding_accuracy: result.geocoding_accuracy,
      geocoding_source: result.geocoding_source,
      google_place_id: null, // Para uso futuro
      api_data: result.api_data,
    };
  }

  /**
   * Geocoding principal com cache
   */
  async geocode(address) {
    if (!address || address.trim().length === 0) {
      throw new Error("Endereço não pode estar vazio");
    }

    // Verificar cache
    const cacheKey = address.toLowerCase().trim();
    if (this.cache.has(cacheKey)) {
      console.log("🔄 Usando geocoding do cache:", address);
      return this.cache.get(cacheKey);
    }

    try {
      // Usar backend como proxy para Nominatim
      const result = await this.nominatimGeocode(address);

      // Salvar no cache
      this.cache.set(cacheKey, result);

      return result;
    } catch (error) {
      console.warn("Geocoding falhou:", error.message);
      return null;
    }
  }

  /**
   * Geocoding específico para endereços brasileiros (ViaCEP + coordenadas)
   */
  async geocodeBrazilianAddress(viaCepData) {
    if (!viaCepData) return null;

    // Construir endereço completo
    const addressParts = [
      viaCepData.logradouro,
      viaCepData.bairro,
      viaCepData.localidade,
      viaCepData.uf,
      "Brasil",
    ].filter(Boolean);

    const fullAddress = addressParts.join(", ");

    try {
      const geoData = await this.geocode(fullAddress);

      if (geoData) {
        return {
          ...viaCepData,
          ...geoData,
          // Manter campo number em branco se não houver
          number: viaCepData.number || "",
          // Manter dados de validação do ViaCEP
          is_validated: true,
          validation_source: "viacep",
          last_validated_at: new Date().toISOString(),
        };
      }

      return viaCepData;
    } catch (error) {
      console.warn("Erro ao enriquecer endereço com coordenadas:", error);
      return viaCepData;
    }
  }

  /**
   * Reverse geocoding (coordenadas para endereço)
   * TODO: Implementar endpoint no backend se necessário
   */
  async reverseGeocode(latitude, longitude) {
    console.warn("Reverse geocoding não implementado ainda via backend");
    return null;
  }

  /**
   * Limpar cache (útil para desenvolvimento)
   */
  clearCache() {
    this.cache.clear();
  }
}

// Instância singleton
const geocodingService = new GeocodingService();

export default geocodingService;
