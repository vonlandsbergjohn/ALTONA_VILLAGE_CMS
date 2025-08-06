import { useState, useEffect } from 'react';
import { residentAPI, authAPI } from '@/lib/api.js';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Car, Plus, Edit, Trash2, Calendar, Palette, Settings, Home } from 'lucide-react';

const VehicleManagement = () => {
  const [vehicles, setVehicles] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [formData, setFormData] = useState({
    registration_number: '',
    make: '',
    model: '',
    year: '',
    color: '',
    vehicle_type: 'car',
    erf_selection: '' // New field for ERF selection
  });

  useEffect(() => {
    // Clear any existing error messages when component loads
    setMessage({ type: '', text: '' });
    fetchVehicles();
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setUserProfile(response.data);
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  const fetchVehicles = async () => {
    try {
      const response = await residentAPI.getMyVehicles();
      setVehicles(response.data);
      // Clear any error messages on successful load
      setMessage({ type: '', text: '' });
    } catch (error) {
      console.error('Error loading vehicles:', error);
      // Only show error if we're not just initializing (user hasn't interacted yet)
      if (!loading) {
        setMessage({ type: 'error', text: 'Failed to load vehicles' });
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      registration_number: '',
      make: '',
      model: '',
      year: '',
      color: '',
      vehicle_type: 'car',
      erf_selection: userProfile?.erfs?.length === 1 ? userProfile.erfs[0].user_id : '' // Auto-select if single ERF
    });
    setEditingVehicle(null);
    // Clear any existing error messages when opening the form
    setMessage({ type: '', text: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // Validate registration number format (basic South African format)
      const regPattern = /^[A-Z]{1,3}[\s-]?\d{1,6}[\s-]?[A-Z]{0,2}$/i;
      if (!regPattern.test(formData.registration_number.replace(/\s/g, ''))) {
        setMessage({ type: 'error', text: 'Please enter a valid South African registration number' });
        setLoading(false);
        return;
      }

      // Validate ERF selection for multi-ERF users
      if (userProfile?.erfs && userProfile.erfs.length > 1 && !formData.erf_selection) {
        setMessage({ type: 'error', text: 'Please select which property this vehicle belongs to' });
        setLoading(false);
        return;
      }

      // Validate year
      const currentYear = new Date().getFullYear();
      if (formData.year && (formData.year < 1900 || formData.year > currentYear + 1)) {
        setMessage({ type: 'error', text: 'Please enter a valid year' });
        setLoading(false);
        return;
      }

      if (editingVehicle) {
        await residentAPI.updateVehicle(editingVehicle.id, formData);
        setMessage({ type: 'success', text: 'Vehicle updated successfully' });
      } else {
        await residentAPI.addVehicle(formData);
        setMessage({ type: 'success', text: 'Vehicle added successfully' });
      }

      await fetchVehicles();
      setIsDialogOpen(false);
      resetForm();
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.message || 'Failed to save vehicle' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (vehicle) => {
    setEditingVehicle(vehicle);
    setFormData({
      registration_number: vehicle.registration_number,
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year?.toString() || '',
      color: vehicle.color,
      vehicle_type: vehicle.vehicle_type || 'car'
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (vehicleId) => {
    if (!confirm('Are you sure you want to remove this vehicle? This will revoke gate access immediately.')) {
      return;
    }

    setLoading(true);
    try {
      await residentAPI.deleteVehicle(vehicleId);
      setMessage({ type: 'success', text: 'Vehicle removed successfully' });
      await fetchVehicles();
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.message || 'Failed to remove vehicle' 
      });
    } finally {
      setLoading(false);
    }
  };

  const formatRegistration = (reg) => {
    // Format registration number for display
    return reg?.toUpperCase().replace(/\s+/g, ' ') || '';
  };

  const getVehicleTypeColor = (type) => {
    switch (type) {
      case 'car': return 'bg-blue-100 text-blue-800';
      case 'motorcycle': return 'bg-orange-100 text-orange-800';
      case 'truck': return 'bg-green-100 text-green-800';
      case 'van': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading && vehicles.length === 0) {
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
          <h1 className="text-3xl font-bold text-gray-900">Vehicle Management</h1>
          <p className="text-gray-600">Manage your registered vehicles for gate access</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={(open) => {
          setIsDialogOpen(open);
          // Clear error messages when dialog opens
          if (open) {
            setMessage({ type: '', text: '' });
          }
        }}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="w-4 h-4 mr-2" />
              Add Vehicle
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>
                {editingVehicle ? 'Edit Vehicle' : 'Add New Vehicle'}
              </DialogTitle>
              <DialogDescription>
                {editingVehicle 
                  ? 'Update the vehicle information below.' 
                  : 'Enter the details of the vehicle you want to register for gate access.'
                }
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="registration_number">Registration Number *</Label>
                  <Input
                    id="registration_number"
                    value={formData.registration_number}
                    onChange={(e) => setFormData({...formData, registration_number: e.target.value.toUpperCase()})}
                    placeholder="ABC123GP"
                    required
                  />
                </div>
                
                {/* ERF Selection for Multi-ERF Users */}
                {userProfile?.erfs && userProfile.erfs.length > 1 && (
                  <div className="col-span-2 space-y-2">
                    <Label htmlFor="erf_selection">Property / ERF *</Label>
                    <Select
                      value={formData.erf_selection}
                      onValueChange={(value) => setFormData({...formData, erf_selection: value})}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select which property this vehicle belongs to" />
                      </SelectTrigger>
                      <SelectContent>
                        {userProfile.erfs.map((erf) => (
                          <SelectItem key={erf.user_id} value={erf.user_id}>
                            <div className="flex items-center space-x-2">
                              <Home className="w-4 h-4" />
                              <span>ERF {erf.erf_number} - {erf.full_address}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-gray-500">
                      This vehicle will be associated with the selected property for gate access.
                    </p>
                  </div>
                )}
                
                {/* Single ERF Users - Show current property */}
                {userProfile?.erfs && userProfile.erfs.length === 1 && (
                  <div className="col-span-2 space-y-2">
                    <Label>Property</Label>
                    <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-md">
                      <Home className="w-4 h-4 text-gray-500" />
                      <span className="text-sm">ERF {userProfile.erfs[0].erf_number} - {userProfile.erfs[0].full_address}</span>
                    </div>
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="make">Make *</Label>
                  <Input
                    id="make"
                    value={formData.make}
                    onChange={(e) => setFormData({...formData, make: e.target.value})}
                    placeholder="Toyota"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="model">Model *</Label>
                  <Input
                    id="model"
                    value={formData.model}
                    onChange={(e) => setFormData({...formData, model: e.target.value})}
                    placeholder="Corolla"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="year">Year</Label>
                  <Input
                    id="year"
                    type="number"
                    value={formData.year}
                    onChange={(e) => setFormData({...formData, year: e.target.value})}
                    placeholder="2020"
                    min="1900"
                    max={new Date().getFullYear() + 1}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="color">Color *</Label>
                  <Input
                    id="color"
                    value={formData.color}
                    onChange={(e) => setFormData({...formData, color: e.target.value})}
                    placeholder="White"
                    required
                  />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="vehicle_type">Vehicle Type</Label>
                  <select
                    id="vehicle_type"
                    value={formData.vehicle_type}
                    onChange={(e) => setFormData({...formData, vehicle_type: e.target.value})}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="car">Car</option>
                    <option value="motorcycle">Motorcycle</option>
                    <option value="truck">Truck</option>
                    <option value="van">Van</option>
                  </select>
                </div>
              </div>
              <DialogFooter>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Saving...' : (editingVehicle ? 'Update Vehicle' : 'Add Vehicle')}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {message.text && (
        <Alert className={message.type === 'error' ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
          <AlertDescription className={message.type === 'error' ? 'text-red-800' : 'text-green-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Car className="w-5 h-5 mr-2" />
            Registered Vehicles ({vehicles.length})
          </CardTitle>
          <CardDescription>
            All vehicles registered for gate access. Security staff can identify your vehicles using this information.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {vehicles.length === 0 ? (
            <div className="text-center py-8">
              <Car className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No vehicles registered</h3>
              <p className="text-gray-600 mb-4">
                Add your first vehicle to enable gate access for your household.
              </p>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Vehicle
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Registration</TableHead>
                  <TableHead>Vehicle Details</TableHead>
                  {userProfile?.erfs && userProfile.erfs.length > 1 && (
                    <TableHead>Property / ERF</TableHead>
                  )}
                  <TableHead>Type</TableHead>
                  <TableHead>Registered</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {vehicles.map((vehicle) => (
                  <TableRow key={vehicle.id}>
                    <TableCell className="font-medium">
                      {formatRegistration(vehicle.registration_number)}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium">
                          {vehicle.make} {vehicle.model}
                        </div>
                        <div className="text-sm text-gray-500 flex items-center">
                          {vehicle.year && (
                            <>
                              <Calendar className="w-3 h-3 mr-1" />
                              {vehicle.year}
                            </>
                          )}
                          {vehicle.year && vehicle.color && (
                            <span className="mx-2">•</span>
                          )}
                          {vehicle.color && (
                            <>
                              <Palette className="w-3 h-3 mr-1" />
                              {vehicle.color}
                            </>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    
                    {/* ERF/Property column for multi-ERF users */}
                    {userProfile?.erfs && userProfile.erfs.length > 1 && (
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Home className="w-4 h-4 text-gray-400" />
                          <span className="text-sm">
                            {(() => {
                              // Find which ERF this vehicle belongs to
                              if (vehicle.owner_id) {
                                const matchingErf = userProfile.erfs.find(erf => erf.user_id === vehicle.owner_id);
                                return matchingErf ? `ERF ${matchingErf.erf_number}` : 'Unknown ERF';
                              }
                              if (vehicle.resident_id) {
                                const matchingErf = userProfile.erfs.find(erf => erf.user_id === vehicle.resident_id);
                                return matchingErf ? `ERF ${matchingErf.erf_number}` : 'Unknown ERF';
                              }
                              return 'Unknown ERF';
                            })()}
                          </span>
                        </div>
                      </TableCell>
                    )}
                    
                    <TableCell>
                      <Badge className={getVehicleTypeColor(vehicle.vehicle_type)}>
                        {vehicle.vehicle_type?.charAt(0).toUpperCase() + vehicle.vehicle_type?.slice(1) || 'Car'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {vehicle.created_at ? new Date(vehicle.created_at).toLocaleDateString() : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(vehicle)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(vehicle.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Important Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Gate Access</h4>
            <p className="text-sm text-blue-800">
              Only registered vehicles can access the estate. Security staff will verify vehicles against this list.
            </p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h4 className="font-medium text-yellow-900 mb-2">Registration Format</h4>
            <p className="text-sm text-yellow-800">
              Please use the correct South African registration format (e.g., ABC123GP, 123ABC, CA123456).
            </p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-medium text-green-900 mb-2">Updates</h4>
            <p className="text-sm text-green-800">
              Vehicle information updates take effect immediately. Notify security if you make changes during your visit.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VehicleManagement;
