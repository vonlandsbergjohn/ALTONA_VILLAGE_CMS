// Enhanced map data service that can work with both static data and API
import { MAP_CONFIG, PROPERTY_DATA as STATIC_PROPERTY_DATA } from './mapData';

// API service for fetching property data from backend
class MapDataService {
  constructor() {
    this.baseUrl = 'http://localhost:8000';
    this.useStaticData = true; // Set to false when backend integration is ready
  }

  // Get all properties for the map
  async getProperties(searchTerm = '') {
    if (this.useStaticData) {
      // Use static data for development/testing
      return this.filterStaticProperties(searchTerm);
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/map/properties?search=${encodeURIComponent(searchTerm)}`);
      const data = await response.json();
      
      if (data.success) {
        return data.properties;
      } else {
        console.error('Failed to fetch properties:', data.error);
        // Fallback to static data
        return this.filterStaticProperties(searchTerm);
      }
    } catch (error) {
      console.error('Error fetching properties from API:', error);
      // Fallback to static data
      return this.filterStaticProperties(searchTerm);
    }
  }

  // Get detailed information about a specific property
  async getPropertyDetails(erfNumber) {
    if (this.useStaticData) {
      return STATIC_PROPERTY_DATA.find(prop => prop.erf === erfNumber);
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/map/property/${erfNumber}`);
      const data = await response.json();
      
      if (data.success) {
        return data.property;
      } else {
        console.error('Failed to fetch property details:', data.error);
        return null;
      }
    } catch (error) {
      console.error('Error fetching property details:', error);
      return null;
    }
  }

  // Filter static properties by search term
  filterStaticProperties(searchTerm) {
    if (!searchTerm) return STATIC_PROPERTY_DATA;
    
    const term = searchTerm.toLowerCase();
    return STATIC_PROPERTY_DATA.filter(property =>
      property.erf.toLowerCase().includes(term) ||
      property.street.toLowerCase().includes(term) ||
      property.streetName.toLowerCase().includes(term) ||
      (property.section && property.section.toLowerCase().includes(term))
    );
  }

  // Switch between static and API data
  setUseStaticData(useStatic) {
    this.useStaticData = useStatic;
  }

  // Update API base URL
  setBaseUrl(url) {
    this.baseUrl = url;
  }
}

// Create singleton instance
const mapDataService = new MapDataService();

export default mapDataService;

// Export configuration and utilities
export { MAP_CONFIG };

// Utility functions
export const validatePropertyData = (property) => {
  const required = ['erf', 'street', 'coordinates'];
  return required.every(field => property[field] !== undefined);
};

export const formatPropertyForDisplay = (property) => {
  return {
    erfNumber: property.erf,
    fullAddress: property.street,
    streetNumber: property.streetNumber || property.street.split(' ')[0],
    streetName: property.streetName || property.street.split(' ').slice(1).join(' '),
    section: property.section || 'Unknown',
    status: property.status || 'available',
    coordinates: property.coordinates,
    notes: property.notes || ''
  };
};

// Configuration for different deployment environments
export const MAP_ENVIRONMENTS = {
  development: {
    useStaticData: true,
    apiUrl: 'http://localhost:8000'
  },
  staging: {
    useStaticData: false,
    apiUrl: 'https://staging-api.altonavillage.com'
  },
  production: {
    useStaticData: false,
    apiUrl: 'https://api.altonavillage.com'
  }
};

// Initialize based on environment
const currentEnv = process.env.NODE_ENV || 'development';
if (MAP_ENVIRONMENTS[currentEnv]) {
  const config = MAP_ENVIRONMENTS[currentEnv];
  mapDataService.setUseStaticData(config.useStaticData);
  mapDataService.setBaseUrl(config.apiUrl);
}
