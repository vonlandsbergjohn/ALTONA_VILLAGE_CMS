import React, { useState, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { X, ZoomIn, ZoomOut, RotateCcw, MapPin, Search, FileImage, FileText } from 'lucide-react';
import { MAP_CONFIG, PROPERTY_DATA, searchProperties } from '@/data/mapData';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

const EnhancedAltonaVillageMap = ({ onErfSelect, selectedErf, onClose }) => {
  const [zoom, setZoom] = useState(MAP_CONFIG.defaultZoom);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredProperties, setFilteredProperties] = useState(PROPERTY_DATA);
  const [mapType, setMapType] = useState('image'); // 'image' or 'pdf'
  const [numPages, setNumPages] = useState(null);
  const [pdfError, setPdfError] = useState(false);

  const properties = filteredProperties;

  // PDF loading handlers
  const onDocumentLoadSuccess = useCallback(({ numPages }) => {
    setNumPages(numPages);
    setPdfError(false);
  }, []);

  const onDocumentLoadError = useCallback((error) => {
    console.error('Error loading PDF:', error);
    setPdfError(true);
    // Fallback to image mode
    setMapType('image');
  }, []);

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

  const handleMapTypeChange = (type) => {
    setMapType(type);
    setZoom(MAP_CONFIG.defaultZoom); // Reset zoom when switching map types
  };

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

        {/* Controls Row */}
        <div className="px-6 pb-4 flex flex-col gap-4">
          {/* Search Bar */}
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
          
          {/* Map Type Selector and Info */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Map Type:</span>
                <Select value={mapType} onValueChange={handleMapTypeChange}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="image">
                      <div className="flex items-center gap-2">
                        <FileImage className="w-4 h-4" />
                        Image
                      </div>
                    </SelectItem>
                    <SelectItem value="pdf">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        PDF
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {mapType === 'pdf' && numPages && (
                <Badge variant="secondary">
                  PDF • {numPages} page{numPages > 1 ? 's' : ''}
                </Badge>
              )}
            </div>
            
            {searchTerm && (
              <p className="text-xs text-gray-500">
                Found {filteredProperties.length} properties matching "{searchTerm}"
              </p>
            )}
          </div>
        </div>
        
        <CardContent className="p-0 h-full">
          {/* Map Controls */}
          <div className="absolute top-32 right-4 z-10 flex flex-col gap-2">
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
              className="relative w-full h-full transition-transform duration-300 flex items-center justify-center"
              style={{ transform: `scale(${zoom})` }}
            >
              {/* PDF Map Rendering */}
              {mapType === 'pdf' && (
                <div className="relative">
                  <Document
                    file="/images/altona-village-map.pdf"
                    onLoadSuccess={onDocumentLoadSuccess}
                    onLoadError={onDocumentLoadError}
                    loading={
                      <div className="flex items-center justify-center p-8">
                        <div className="text-center">
                          <FileText className="w-12 h-12 mx-auto mb-2 text-blue-600 animate-pulse" />
                          <p>Loading PDF map...</p>
                        </div>
                      </div>
                    }
                  >
                    <Page 
                      pageNumber={1}
                      renderTextLayer={false}
                      renderAnnotationLayer={false}
                      className="shadow-lg"
                    />
                  </Document>
                  
                  {/* Property Markers Overlay for PDF */}
                  <div className="absolute inset-0">
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
                  </div>
                </div>
              )}

              {/* Image Map Rendering */}
              {mapType === 'image' && (
                <div className="w-full h-full relative">
                  {/* Check if image exists, otherwise show placeholder */}
                  <div className="w-full h-full bg-gradient-to-br from-green-200 to-green-300 relative">
                    <div className="absolute inset-0 flex items-center justify-center text-gray-600">
                      <div className="text-center">
                        <MapPin className="w-16 h-16 mx-auto mb-4 text-green-600" />
                        <p className="text-lg font-semibold">Altona Village Map</p>
                        <p className="text-sm mb-2">Place your map image at:</p>
                        <code className="text-xs bg-gray-200 px-2 py-1 rounded">
                          public/images/altona-village-map.jpg
                        </code>
                        <p className="text-xs text-gray-500 mt-2">
                          Or switch to PDF mode to use your monthly PDF maps
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
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                  */}

                  {/* Property Markers for Image */}
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
                </div>
              )}

              {/* Property Labels - Show when zoomed in (works for both PDF and Image) */}
              {zoom > 1.2 && properties.map((property) => (
                <div
                  key={`label-${property.erf}`}
                  className="absolute text-xs bg-white bg-opacity-95 px-2 py-1 rounded shadow-lg pointer-events-none border z-10"
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

          {/* Error Message for PDF */}
          {pdfError && (
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-center">
                <FileText className="w-8 h-8 mx-auto mb-2 text-red-500" />
                <p className="text-red-700 font-medium">Unable to load PDF map</p>
                <p className="text-red-600 text-sm">Switched to image mode</p>
                <p className="text-xs text-gray-600 mt-1">
                  Place PDF at: public/images/altona-village-map.pdf
                </p>
              </div>
            </div>
          )}

          {/* Selected Property Info */}
          {selectedProperty && (
            <div className="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg border z-10">
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
            <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg border max-w-xs max-h-96 overflow-y-auto z-10">
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

export default EnhancedAltonaVillageMap;
