const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

export const geocodingService = {
  /**
   * Geocode an address using Google Maps Geocoding API
   * @param {string} address - Full address to geocode
   * @returns {Promise<Object>} Geocoding result with lat, lng, place_id, etc.
   */
  geocodeAddress: async (address) => {
    if (!GOOGLE_MAPS_API_KEY) {
      throw new Error('Google Maps API key not configured');
    }

    try {
      const encodedAddress = encodeURIComponent(address);
      const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodedAddress}&key=${GOOGLE_MAPS_API_KEY}`;

      const response = await fetch(url);
      const data = await response.json();

      if (data.status !== 'OK') {
        throw new Error(`Geocoding failed: ${data.status}`);
      }

      const result = data.results[0];
      const location = result.geometry.location;

      return {
        lat: location.lat,
        lng: location.lng,
        place_id: result.place_id,
        formatted_address: result.formatted_address,
        accuracy: result.geometry.location_type,
        raw_data: result
      };
    } catch (error) {
      console.error('Geocoding error:', error);
      throw error;
    }
  },

  /**
   * Reverse geocode coordinates to address
   * @param {number} lat - Latitude
   * @param {number} lng - Longitude
   * @returns {Promise<Object>} Reverse geocoding result
   */
  reverseGeocode: async (lat, lng) => {
    if (!GOOGLE_MAPS_API_KEY) {
      throw new Error('Google Maps API key not configured');
    }

    try {
      const url = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${lat},${lng}&key=${GOOGLE_MAPS_API_KEY}`;

      const response = await fetch(url);
      const data = await response.json();

      if (data.status !== 'OK') {
        throw new Error(`Reverse geocoding failed: ${data.status}`);
      }

      const result = data.results[0];

      return {
        formatted_address: result.formatted_address,
        place_id: result.place_id,
        raw_data: result
      };
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      throw error;
    }
  }
};

export default geocodingService;