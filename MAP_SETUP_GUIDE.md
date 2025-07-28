# Altona Village Map Setup Guide

## 🗺️ How to Add Your Village Map

### Step 1: Prepare Your Map Image
1. **Get your village map** - This could be:
   - A surveyor's plot map
   - Aerial/satellite image from Google Maps
   - Estate development layout plan
   - Hand-drawn map with property boundaries

2. **Image requirements**:
   - Format: JPG, PNG, or SVG
   - Resolution: At least 1200x800 pixels (higher is better for zoom)
   - Clear visibility of streets and property boundaries
   - Properties should be distinguishable

3. **Save the image**:
   - Place it in: `altona-village-frontend/public/images/altona-village-map.jpg`
   - Or update the path in `src/data/mapData.js`

### Step 2: Configure Property Locations
1. **Open**: `src/data/mapData.js`
2. **Update PROPERTY_DATA array** with your actual properties:

```javascript
{
  erf: '1234',                    // ERF number as string
  street: '25 Baobab Avenue',     // Full street address
  streetNumber: '25',             // Street number only
  streetName: 'Baobab Avenue',    // Street name only
  coordinates: { x: 75, y: 50 },  // Position on map (percentage)
  section: 'East Section',        // Optional grouping
  notes: 'Corner property'        // Optional notes
}
```

### Step 3: Position Properties on Map
**Finding coordinates (x, y percentages)**:

1. **Open your map image** in any image editor (Paint, GIMP, Photoshop)
2. **Measure the image dimensions** (e.g., 1200x800 pixels)
3. **For each property**:
   - Find the property location on the map
   - Measure pixels from left edge = X pixels
   - Measure pixels from top edge = Y pixels
   - Calculate: `x = (X pixels / total width) × 100`
   - Calculate: `y = (Y pixels / total height) × 100`

**Example**: Property at 300px from left, 200px from top on 1200x800 image:
- x = (300 / 1200) × 100 = 25%
- y = (200 / 800) × 100 = 25%
- coordinates: { x: 25, y: 25 }

### Step 4: Enable the Map Image
1. **In `AltonaVillageMap.jsx`**, find this section:
```javascript
{/* Uncomment this when you have your map image ready */}
{/* 
<img 
  src={MAP_CONFIG.mapImage.src}
  alt={MAP_CONFIG.mapImage.alt}
  className="w-full h-full object-contain"
/>
*/}
```

2. **Uncomment it** to:
```javascript
<img 
  src={MAP_CONFIG.mapImage.src}
  alt={MAP_CONFIG.mapImage.alt}
  className="w-full h-full object-contain"
/>
```

3. **Comment out or remove the placeholder**:
```javascript
{/* Remove or comment this placeholder */}
<div className="w-full h-full bg-gradient-to-br from-green-200 to-green-300 relative">
  ...
</div>
```

## 🎯 Quick Start with Sample Data

The map is already configured with sample properties. You can:

1. **Test the functionality** immediately
2. **Replace sample data** with your actual properties
3. **Add your map image** when ready

## 🛠️ Advanced Customization

### Map Styling (in `mapData.js`):
```javascript
export const MAP_CONFIG = {
  mapImage: {
    src: '/images/your-custom-map.jpg',
    width: 1400,  // Adjust to your image
    height: 1000
  },
  defaultZoom: 1.2,    // Start zoomed in
  minZoom: 0.3,        // Allow more zoom out
  maxZoom: 4,          // Allow more zoom in
  backgroundColor: '#e0f2fe', // Light blue
  markers: {
    default: {
      size: 20,              // Smaller markers
      color: '#f59e0b',      // Orange color
      borderColor: '#d97706'
    }
  }
};
```

### Adding More Property Data Fields:
You can extend properties with additional information:
```javascript
{
  erf: '1234',
  street: '25 Baobab Avenue',
  // ... existing fields ...
  propertyType: 'Residential',
  size: '500 sqm',
  buildingStatus: 'Complete',
  owner: 'John Smith',
  // Any custom fields you need
}
```

## 📱 Mobile Optimization

The map is responsive and works on mobile devices with:
- Touch zoom and pan
- Responsive layout
- Touch-friendly markers
- Mobile-optimized search

## 🔧 Troubleshooting

**Map image not showing?**
- Check file path: `public/images/altona-village-map.jpg`
- Verify image format (JPG, PNG, SVG)
- Check browser console for errors

**Property markers in wrong positions?**
- Double-check coordinate calculations
- Ensure percentages (0-100, not 0-1)
- Test with a few properties first

**Map too slow with many properties?**
- Consider grouping properties by section
- Implement marker clustering for large datasets
- Optimize image size and format

## 🚀 Next Steps

Once your map is working:
1. **Add all village properties** to the data file
2. **Test the registration flow** end-to-end
3. **Customize styling** to match your estate branding
4. **Add additional features** like:
   - Property status indicators
   - Different marker types for different property types
   - Integration with your property database

This interactive map will greatly improve the user experience for new residents registering in your system! 🏡✨
