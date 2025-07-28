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
export const PROPERTY_DATA = [
  {
    erf: '5555',
    street: '15 Coral Tree',
    streetNumber: '15',
    streetName: 'Coral Tree',
    coordinates: { x: 20, y: 30 }, // X: 20% from left, Y: 30% from top
    section: 'North Section',
    notes: 'Corner property'
  },
  {
    erf: '8888',
    street: '88 Milkwood',
    streetNumber: '88',
    streetName: 'Milkwood',
    coordinates: { x: 35, y: 25 },
    section: 'Central Section',
    notes: ''
  },
  {
    erf: '4562',
    street: '40 Rosewood',
    streetNumber: '40',
    streetName: 'Rosewood',
    coordinates: { x: 50, y: 40 },
    section: 'East Section',
    notes: 'Near community center'
  },
  {
    erf: '4568',
    street: '10 Sagewood',
    streetNumber: '10',
    streetName: 'Sagewood',
    coordinates: { x: 25, y: 55 },
    section: 'South Section',
    notes: ''
  },
  {
    erf: '27727',
    street: '33 Yellowwood Crescent',
    streetNumber: '33',
    streetName: 'Yellowwood Crescent',
    coordinates: { x: 60, y: 35 },
    section: 'East Section',
    notes: 'Crescent property'
  },
  {
    erf: '1234',
    street: '25 Baobab Avenue',
    streetNumber: '25',
    streetName: 'Baobab Avenue',
    coordinates: { x: 75, y: 50 },
    section: 'East Section',
    notes: 'Main avenue'
  },
  {
    erf: '5678',
    street: '12 Marula Street',
    streetNumber: '12',
    streetName: 'Marula Street',
    coordinates: { x: 40, y: 65 },
    section: 'South Section',
    notes: ''
  },
  {
    erf: '9999',
    street: '78 Kiaat Close',
    streetNumber: '78',
    streetName: 'Kiaat Close',
    coordinates: { x: 80, y: 20 },
    section: 'North Section',
    notes: 'Cul-de-sac'
  }
  
  // Add more properties here as needed
  // To add a new property:
  // 1. Get the ERF number
  // 2. Get the full street address
  // 3. Determine coordinates by looking at your map image:
  //    - x: percentage from left edge (0-100)
  //    - y: percentage from top edge (0-100)
  // 4. Add any additional notes
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
