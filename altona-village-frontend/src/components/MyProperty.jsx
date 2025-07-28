import { useState, useEffect } from 'react';
import { residentAPI } from '@/lib/api.js';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Home, 
  MapPin, 
  User, 
  Calendar, 
  Zap, 
  Droplets, 
  Phone, 
  Mail,
  Users,
  Info
} from 'lucide-react';

const MyProperty = () => {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const response = await residentAPI.getMyProperties();
      setProperties(response.data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load property information' });
    } finally {
      setLoading(false);
    }
  };

  const getOwnershipTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'owner': return 'bg-green-100 text-green-800';
      case 'tenant': return 'bg-blue-100 text-blue-800';
      case 'caretaker': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatMeterReading = (reading) => {
    if (!reading) return 'N/A';
    return new Intl.NumberFormat().format(reading);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Property</h1>
          <p className="text-gray-600">View your property details and utility information</p>
        </div>
      </div>

      {message.text && (
        <Alert className={message.type === 'error' ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
          <AlertDescription className={message.type === 'error' ? 'text-red-800' : 'text-green-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {properties.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Home className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Properties Found</h3>
              <p className="text-gray-600 mb-4">
                You don't appear to be associated with any properties yet.
              </p>
              <p className="text-sm text-gray-500">
                Contact estate management if you believe this is an error.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {properties.map((property, index) => (
            <div key={property.id || index} className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Home className="w-5 h-5 mr-2" />
                    Property Information
                  </CardTitle>
                  <CardDescription>
                    Basic details about your property in Altona Village
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <MapPin className="w-4 h-4 mr-1" />
                        Address
                      </div>
                      <p className="text-lg font-medium">
                        {property.address || 'No address on file'}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <Info className="w-4 h-4 mr-1" />
                        Erf Number
                      </div>
                      <p className="text-lg font-medium">
                        {property.erf_number || 'N/A'}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <Home className="w-4 h-4 mr-1" />
                        Property Type
                      </div>
                      <Badge variant="outline">
                        {property.property_type?.charAt(0).toUpperCase() + property.property_type?.slice(1) || 'Residential'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <User className="w-4 h-4 mr-1" />
                        Ownership Status
                      </div>
                      <Badge className={getOwnershipTypeColor(property.ownership_type)}>
                        {property.ownership_type?.toUpperCase() || 'RESIDENT'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <Calendar className="w-4 h-4 mr-1" />
                        Move-in Date
                      </div>
                      <p className="text-sm">
                        {property.move_in_date ? new Date(property.move_in_date).toLocaleDateString() : 'Not specified'}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <Users className="w-4 h-4 mr-1" />
                        Occupants
                      </div>
                      <p className="text-sm">
                        {property.occupant_count || 'Not specified'}
                      </p>
                    </div>
                  </div>

                  <Separator />

                  {/* Utility Information */}
                  <div>
                    <h3 className="text-lg font-medium mb-4">Utility Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Electricity */}
                      <Card className="bg-yellow-50 border-yellow-200">
                        <CardContent className="pt-6">
                          <div className="flex items-center mb-4">
                            <div className="p-2 bg-yellow-100 rounded-lg">
                              <Zap className="w-6 h-6 text-yellow-600" />
                            </div>
                            <div className="ml-4">
                              <h4 className="text-lg font-medium text-yellow-900">Electricity</h4>
                              <p className="text-sm text-yellow-700">Power supply details</p>
                            </div>
                          </div>
                          <div className="space-y-3">
                            <div>
                              <p className="text-sm font-medium text-yellow-800">Meter Number</p>
                              <p className="text-sm text-yellow-700">
                                {property.electricity_meter_number || 'Not available'}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-yellow-800">Last Reading</p>
                              <p className="text-sm text-yellow-700">
                                {property.electricity_reading ? 
                                  `${formatMeterReading(property.electricity_reading)} kWh` : 
                                  'No reading available'
                                }
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-yellow-800">Reading Date</p>
                              <p className="text-sm text-yellow-700">
                                {property.electricity_reading_date ? 
                                  new Date(property.electricity_reading_date).toLocaleDateString() : 
                                  'N/A'
                                }
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Water */}
                      <Card className="bg-blue-50 border-blue-200">
                        <CardContent className="pt-6">
                          <div className="flex items-center mb-4">
                            <div className="p-2 bg-blue-100 rounded-lg">
                              <Droplets className="w-6 h-6 text-blue-600" />
                            </div>
                            <div className="ml-4">
                              <h4 className="text-lg font-medium text-blue-900">Water</h4>
                              <p className="text-sm text-blue-700">Water supply details</p>
                            </div>
                          </div>
                          <div className="space-y-3">
                            <div>
                              <p className="text-sm font-medium text-blue-800">Meter Number</p>
                              <p className="text-sm text-blue-700">
                                {property.water_meter_number || 'Not available'}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-blue-800">Last Reading</p>
                              <p className="text-sm text-blue-700">
                                {property.water_reading ? 
                                  `${formatMeterReading(property.water_reading)} kL` : 
                                  'No reading available'
                                }
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-blue-800">Reading Date</p>
                              <p className="text-sm text-blue-700">
                                {property.water_reading_date ? 
                                  new Date(property.water_reading_date).toLocaleDateString() : 
                                  'N/A'
                                }
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  <Separator />

                  {/* Emergency Contacts */}
                  <div>
                    <h3 className="text-lg font-medium mb-4">Important Contacts</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <Card className="bg-red-50 border-red-200">
                        <CardContent className="pt-4">
                          <div className="text-center">
                            <Phone className="w-8 h-8 text-red-600 mx-auto mb-2" />
                            <h4 className="font-medium text-red-900">Emergency</h4>
                            <p className="text-sm text-red-700">10111 / 10177</p>
                          </div>
                        </CardContent>
                      </Card>
                      <Card className="bg-green-50 border-green-200">
                        <CardContent className="pt-4">
                          <div className="text-center">
                            <Phone className="w-8 h-8 text-green-600 mx-auto mb-2" />
                            <h4 className="font-medium text-green-900">Estate Security</h4>
                            <p className="text-sm text-green-700">Contact gate house</p>
                          </div>
                        </CardContent>
                      </Card>
                      <Card className="bg-blue-50 border-blue-200">
                        <CardContent className="pt-4">
                          <div className="text-center">
                            <Mail className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                            <h4 className="font-medium text-blue-900">Estate Management</h4>
                            <p className="text-sm text-blue-700">Use complaint system</p>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Property Notes/Additional Info */}
              {property.notes && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Info className="w-5 h-5 mr-2" />
                      Additional Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm whitespace-pre-wrap">{property.notes}</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start">
              <Info className="w-6 h-6 text-blue-600 mt-1 mr-3 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-blue-900 mb-2">Property Updates</h4>
                <p className="text-sm text-blue-800 mb-2">
                  If any of your property information is incorrect or outdated, please contact estate management.
                </p>
                <p className="text-sm text-blue-700">
                  Updates may take 24-48 hours to reflect in the system.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-start">
              <Zap className="w-6 h-6 text-green-600 mt-1 mr-3 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-green-900 mb-2">Utility Readings</h4>
                <p className="text-sm text-green-800 mb-2">
                  Meter readings are updated monthly by estate management or municipality staff.
                </p>
                <p className="text-sm text-green-700">
                  Report any meter issues through the complaint system.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MyProperty;
