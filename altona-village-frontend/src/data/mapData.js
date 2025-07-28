// Altona Village Map Configuration
// This file contains the property data and map configuration for the interactive map

export const MAP_CONFIG = {
  // Map image settings
  mapImage: {
    // You can replace this with your actual map image path
    src: '/images/altona-village-map.jpg', // Place your map image in public/images/
    alt: 'Altona Village Layout Map',
    width: 1200, // Adjust based on your map image dimensions
    height: 800
  },
  
  // PDF map settings
  mapPdf: {
    src: '/images/altona-village-map.pdf', // Place your PDF map here
    alt: 'Altona Village PDF Map',
    // PDF maps automatically scale to fit container
  },
  
  // Default zoom and view settings
  defaultZoom: 1,
  minZoom: 0.5,
  maxZoom: 3,
  
  // Map container styling
  backgroundColor: '#f0f9ff', // Light blue background
  
  // Property marker styling
  markers: {
    default: {
      size: 24,
      color: '#ef4444', // Red
      borderColor: '#dc2626',
      borderWidth: 2
    },
    selected: {
      size: 28,
      color: '#3b82f6', // Blue
      borderColor: '#1d4ed8',
      borderWidth: 3
    },
    confirmed: {
      size: 24,
      color: '#10b981', // Green
      borderColor: '#059669',
      borderWidth: 2
    }
  }
};

// Property locations and details
// Coordinates are in percentage (0-100) relative to the map image
// Replace this demo data with your actual property data
export const PROPERTY_DATA = [
  // Add your actual property data here when available
  // Example format:
  // {
  //   erf: '1234',
  //   street: '123 Street Name',
  //   streetNumber: '123',
  //   streetName: 'Street Name',
  //   coordinates: { x: 50, y: 50 }, // X: 50% from left, Y: 50% from top
  //   section: 'Section Name',
  //   notes: 'Any additional notes'
  // }
];

// Search functionality
export const searchProperties = (searchTerm) => {
  if (!searchTerm) return PROPERTY_DATA;
  
  const term = searchTerm.toLowerCase();
  return PROPERTY_DATA.filter(property =>
    property.erf.toLowerCase().includes(term) ||
    property.street.toLowerCase().includes(term) ||
    property.streetName.toLowerCase().includes(term) ||
    property.section.toLowerCase().includes(term)
  );
};

// Get property by ERF number
export const getPropertyByErf = (erfNumber) => {
  return PROPERTY_DATA.find(property => property.erf === erfNumber);
};

// Group properties by section
export const getPropertiesBySection = () => {
  const sections = {};
  PROPERTY_DATA.forEach(property => {
    if (!sections[property.section]) {
      sections[property.section] = [];
    }
    sections[property.section].push(property);
  });
  return sections;
};
