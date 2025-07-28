import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { X, ZoomIn, ZoomOut, RotateCcw, MapPin, Search } from 'lucide-react';
import { MAP_CONFIG, PROPERTY_DATA, searchProperties } from '@/data/mapData';

const AltonaVillageMap = ({ onErfSelect, selectedErf, onClose }) => {
  const [zoom, setZoom] = useState(MAP_CONFIG.defaultZoom);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredProperties, setFilteredProperties] = useState(PROPERTY_DATA);

  // Sample property data - you'll replace this with your actual map data
  const properties = filteredProperties;

  const handlePropertyClick = (property) => {
    setSelectedProperty(property);
    if (onErfSelect) {
      onErfSelect(property.erf, property.street);
    }
  };

  const handleSearch = (e) => {
    const term = e.target.value;
    setSearchTerm(term);
    setFilteredProperties(searchProperties(term));
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, MAP_CONFIG.maxZoom));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, MAP_CONFIG.minZoom));
  const handleResetZoom = () => setZoom(MAP_CONFIG.defaultZoom);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-11/12 h-5/6 max-w-6xl max-h-4xl">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Altona Village Map
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              Select your property to auto-fill ERF number
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        {/* Search Bar */}
        <div className="px-6 pb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Search by ERF number, street name, or section..."
              value={searchTerm}
              onChange={handleSearch}
              className="pl-10"
            />
          </div>
          {searchTerm && (
            <p className="text-xs text-gray-500 mt-1">
              Found {filteredProperties.length} properties matching "{searchTerm}"
            </p>
          )}
        </div>
        
        <CardContent className="p-0 h-full">
          {/* Map Controls */}
          <div className="absolute top-20 right-4 z-10 flex flex-col gap-2">
            <Button variant="outline" size="sm" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleResetZoom}>
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>

          {/* Map Container */}
          <div className="relative h-full overflow-hidden" style={{ backgroundColor: MAP_CONFIG.backgroundColor }}>
            <div 
              className="relative w-full h-full transition-transform duration-300"
              style={{ transform: `scale(${zoom})` }}
            >
              {/* Map Image - Replace this with your actual map */}
              <div className="w-full h-full relative">
                {/* This is where your actual map image will go */}
                <div className="w-full h-full bg-gradient-to-br from-green-200 to-green-300 relative">
                  <div className="absolute inset-0 flex items-center justify-center text-gray-600">
                    <div className="text-center">
                      <MapPin className="w-16 h-16 mx-auto mb-4 text-green-600" />
                      <p className="text-lg font-semibold">Altona Village Map</p>
                      <p className="text-sm">Place your map image at: public/images/altona-village-map.jpg</p>
                      <p className="text-xs text-gray-500 mt-2">
                        Or update MAP_CONFIG.mapImage.src in src/data/mapData.js
                      </p>
                    </div>
                  </div>
                </div>

                {/* Uncomment this when you have your map image ready */}
                {/* 
                <img 
                  src={MAP_CONFIG.mapImage.src}
                  alt={MAP_CONFIG.mapImage.alt}
                  className="w-full h-full object-contain"
                />
                */}

                {/* Property Markers */}
                {properties.map((property) => (
                  <button
                    key={property.erf}
                    className={`absolute transform -translate-x-1/2 -translate-y-1/2 rounded-full border transition-all hover:scale-125 ${
                      selectedProperty?.erf === property.erf
                        ? 'bg-blue-500 border-blue-700 scale-125'
                        : selectedErf === property.erf
                        ? 'bg-green-500 border-green-700'
                        : 'bg-red-500 border-red-700 hover:bg-red-400'
                    }`}
                    style={{
                      left: `${property.coordinates.x}%`,
                      top: `${property.coordinates.y}%`,
                      width: `${MAP_CONFIG.markers.default.size}px`,
                      height: `${MAP_CONFIG.markers.default.size}px`,
                      borderWidth: `${MAP_CONFIG.markers.default.borderWidth}px`,
                    }}
                    onClick={() => handlePropertyClick(property)}
                    title={`ERF ${property.erf} - ${property.street}`}
                  />
                ))}

                {/* Property Labels - Show when zoomed in */}
                {zoom > 1.2 && properties.map((property) => (
                  <div
                    key={`label-${property.erf}`}
                    className="absolute text-xs bg-white bg-opacity-95 px-2 py-1 rounded shadow-lg pointer-events-none border"
                    style={{
                      left: `${property.coordinates.x}%`,
                      top: `${property.coordinates.y - 8}%`,
                      transform: 'translate(-50%, -100%)',
                    }}
                  >
                    <div className="font-semibold">ERF {property.erf}</div>
                    <div className="text-gray-600">{property.street}</div>
                    {property.section && (
                      <div className="text-xs text-gray-500">{property.section}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Selected Property Info */}
          {selectedProperty && (
            <div className="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg border">
              <h4 className="font-semibold text-lg">Selected Property</h4>
              <div className="space-y-1 text-sm">
                <p><span className="font-medium">ERF Number:</span> {selectedProperty.erf}</p>
                <p><span className="font-medium">Address:</span> {selectedProperty.street}</p>
                {selectedProperty.section && (
                  <p><span className="font-medium">Section:</span> {selectedProperty.section}</p>
                )}
                {selectedProperty.notes && (
                  <p className="text-gray-600 text-xs">{selectedProperty.notes}</p>
                )}
              </div>
              <Button 
                className="mt-3 w-full" 
                size="sm"
                onClick={() => onErfSelect && onErfSelect(selectedProperty.erf, selectedProperty.street)}
              >
                Use This Property
              </Button>
            </div>
          )}

          {/* Property List Sidebar */}
          {searchTerm && (
            <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg border max-w-xs max-h-96 overflow-y-auto">
              <h4 className="font-semibold text-sm mb-2">Search Results</h4>
              <div className="space-y-2">
                {filteredProperties.slice(0, 10).map((property) => (
                  <button
                    key={property.erf}
                    className="w-full text-left p-2 rounded hover:bg-gray-50 border text-xs"
                    onClick={() => handlePropertyClick(property)}
                  >
                    <div className="font-medium">ERF {property.erf}</div>
                    <div className="text-gray-600">{property.street}</div>
                  </button>
                ))}
                {filteredProperties.length > 10 && (
                  <p className="text-xs text-gray-500 p-2">
                    ... and {filteredProperties.length - 10} more results
                  </p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AltonaVillageMap;
