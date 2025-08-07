import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Users, 
  Search, 
  Edit,
  Phone,
  Mail,
  MapPin,
  Calendar,
  User,
  Home,
  AlertCircle,
  CheckCircle,
  Clock,
  Archive,
  Filter,
  X,
  KeyRound,
  UserCheck,
  Car,
  Plus,
  Trash2
} from 'lucide-react';

const AdminResidents = () => {
  const [residents, setResidents] = useState([]);
  const [filteredResidents, setFilteredResidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, residents, owners, both, archived
  const [selectedResident, setSelectedResident] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [updateLoading, setUpdateLoading] = useState(false);
  
  // Vehicle management state
  const [vehicles, setVehicles] = useState([]);
  const [vehicleLoading, setVehicleLoading] = useState(false);
  const [newVehicle, setNewVehicle] = useState({
    registration_number: '',
    make: '',
    model: '',
    color: ''
  });

  useEffect(() => {
    loadResidents();
  }, []);

  useEffect(() => {
    filterResidents();
  }, [residents, searchTerm, filterType]);

  const loadResidents = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.getAllResidents();
      setResidents(response.data || []);
    } catch (error) {
      console.error('Failed to load residents:', error);
      setMessage({ type: 'error', text: 'Failed to load residents data' });
    } finally {
      setLoading(false);
    }
  };

  const filterResidents = () => {
    let filtered = residents;

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(resident => 
        resident.first_name?.toLowerCase().includes(term) ||
        resident.last_name?.toLowerCase().includes(term) ||
        resident.email?.toLowerCase().includes(term) ||
        resident.phone_number?.toLowerCase().includes(term) ||
        resident.erf_number?.toLowerCase().includes(term) ||
        resident.full_address?.toLowerCase().includes(term)
      );
    }

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter(resident => {
        const isResident = resident.is_resident;
        const isOwner = resident.is_owner;
        const isArchived = resident.status === 'archived' || resident.archived === true;
        
        switch (filterType) {
          case 'residents':
            return isResident && !isOwner && !isArchived;
          case 'owners':
            return isOwner && !isResident && !isArchived;
          case 'both':
            return isResident && isOwner && !isArchived;
          case 'archived':
            return isArchived;
          default:
            return true;
        }
      });
    }

    setFilteredResidents(filtered);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setFilterType('all');
    setMessage({ type: '', text: '' });
  };

  const handleUpdateResident = async (e) => {
    e.preventDefault();
    if (!selectedResident) return;

    setUpdateLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // Prepare the data for update
      const updateData = {
        full_name: `${selectedResident.first_name} ${selectedResident.last_name}`,
        email: selectedResident.email,
        phone: selectedResident.phone_number,
        emergency_contact_name: selectedResident.emergency_contact_name,
        emergency_contact_phone: selectedResident.emergency_contact_number,
        property_address: selectedResident.full_address,
        resident_status_change: getResidentStatusValue(selectedResident),
        intercom_code: selectedResident.intercom_code
      };
      
      // Use the admin API to update the resident
      await adminAPI.updateResident(selectedResident.user_id, updateData);
      
      setMessage({ type: 'success', text: 'Resident updated successfully' });
      setEditDialogOpen(false);
      loadResidents(); // Reload the data
      
      // Reload vehicles for the updated resident to reflect any changes due to status change
      if (selectedResident?.user_id) {
        await loadVehicles(selectedResident.user_id);
      }
    } catch (error) {
      console.error('Failed to update resident:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to update resident' 
      });
    } finally {
      setUpdateLoading(false);
    }
  };

  const getResidentStatusValue = (resident) => {
    if (resident.is_resident && resident.is_owner) return 'owner-resident';
    if (resident.is_owner) return 'owner';
    if (resident.is_resident) return 'resident';
    return 'resident'; // Default fallback
  };

  const handleResidentStatusChange = (newStatus) => {
    const updates = { ...selectedResident };
    
    switch (newStatus) {
      case 'resident':
        updates.is_resident = true;
        updates.is_owner = false;
        break;
      case 'owner':
        updates.is_resident = false;
        updates.is_owner = true;
        break;
      case 'owner-resident':
        updates.is_resident = true;
        updates.is_owner = true;
        break;
      default:
        break;
    }
    
    setSelectedResident(updates);
  };

  const getResidentTypeLabel = (resident) => {
    const isResident = resident.is_resident;
    const isOwner = resident.is_owner;
    
    if (isResident && isOwner) return 'Owner-Resident';
    if (isOwner) return 'Owner';
    if (isResident) return 'Resident';
    return 'Unknown';
  };

  const getResidentTypeBadge = (resident) => {
    const type = getResidentTypeLabel(resident);
    const colors = {
      'Owner-Resident': 'bg-purple-100 text-purple-800',
      'Owner': 'bg-blue-100 text-blue-800',
      'Resident': 'bg-green-100 text-green-800',
      'Unknown': 'bg-gray-100 text-gray-800'
    };
    
    return <Badge className={colors[type]}>{type}</Badge>;
  };

  const getStatusBadge = (status) => {
    const colors = {
      'active': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'suspended': 'bg-red-100 text-red-800',
      'archived': 'bg-gray-100 text-gray-800'
    };
    
    const icons = {
      'active': CheckCircle,
      'pending': Clock,
      'suspended': AlertCircle,
      'archived': Archive
    };
    
    const Icon = icons[status] || AlertCircle;
    
    return (
      <Badge className={colors[status] || 'bg-gray-100 text-gray-800'}>
        <Icon className="w-3 h-3 mr-1" />
        {status?.toUpperCase() || 'UNKNOWN'}
      </Badge>
    );
  };

  // Vehicle Management Functions
  const loadVehicles = async (userId, filterByErf = true) => {
    if (!userId) return;
    try {
      setVehicleLoading(true);
      const params = filterByErf ? { filter_by_erf: 'true' } : {};
      const response = await adminAPI.getResidentVehicles(userId, params);
      setVehicles(response.data);
    } catch (error) {
      console.error('Error loading vehicles:', error);
      setMessage({ type: 'error', text: 'Failed to load vehicles' });
    } finally {
      setVehicleLoading(false);
    }
  };

  const handleAddVehicle = async (e) => {
    e.preventDefault();
    if (!selectedResident?.user_id || !newVehicle.registration_number) return;

    try {
      setVehicleLoading(true);
      await adminAPI.addResidentVehicle(selectedResident.user_id, newVehicle);
      await loadVehicles(selectedResident.user_id);
      setNewVehicle({ registration_number: '', make: '', model: '', color: '' });
      setMessage({ type: 'success', text: 'Vehicle added successfully' });
    } catch (error) {
      console.error('Error adding vehicle:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to add vehicle' 
      });
    } finally {
      setVehicleLoading(false);
    }
  };

  const handleDeleteVehicle = async (vehicleId) => {
    if (!selectedResident?.user_id || !confirm('Are you sure you want to delete this vehicle?')) return;

    try {
      setVehicleLoading(true);
      await adminAPI.deleteResidentVehicle(selectedResident.user_id, vehicleId);
      await loadVehicles(selectedResident.user_id);
      setMessage({ type: 'success', text: 'Vehicle deleted successfully' });
    } catch (error) {
      console.error('Error deleting vehicle:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to delete vehicle' 
      });
    } finally {
      setVehicleLoading(false);
    }
  };

  // Enhanced handleEditResident to load vehicles
  const handleEditResidentWithVehicles = (resident) => {
    setSelectedResident({ ...resident });
    setEditDialogOpen(true);
    setMessage({ type: '', text: '' });
    // Load vehicles if resident has a user_id (for both residents and owners)
    if (resident.user_id && (resident.is_resident || resident.is_owner)) {
      loadVehicles(resident.user_id);
    }
  };

  // Permanent user deletion function
  const handlePermanentDeleteUser = async (resident) => {
    // First confirmation
    const isConfirmed = window.confirm(
      `⚠️ PERMANENT DELETION WARNING\n\n` +
      `This will permanently delete ${resident.email} and ALL their data including:\n` +
      `• User account\n` +
      `• Resident/Owner profiles\n` +
      `• All vehicles\n` +
      `• All complaints\n` +
      `• All related records\n\n` +
      `This action CANNOT be undone!\n\n` +
      `Are you absolutely sure you want to continue?`
    );

    if (!isConfirmed) return;

    // Second confirmation - require typing DELETE
    const deleteConfirmation = window.prompt(
      `To confirm this permanent deletion, type "DELETE" (case sensitive):`
    );

    if (deleteConfirmation !== "DELETE") {
      alert("Deletion cancelled - confirmation text does not match");
      return;
    }

    // Get deletion reason
    const deletionReason = window.prompt(
      `Please provide a reason for deleting ${resident.email}:\n\n` +
      `Examples:\n` +
      `• Incorrectly approved registration\n` +
      `• Mistaken registration\n` +
      `• Test account\n` +
      `• Not a valid resident/owner`
    );

    if (!deletionReason || deletionReason.trim() === "") {
      alert("Deletion cancelled - reason is required");
      return;
    }

    setUpdateLoading(true);
    try {
      const result = await adminAPI.permanentlyDeleteUser(resident.user_id, {
        deletion_reason: deletionReason.trim(),
        confirm_deletion: true
      });

      setMessage({ 
        type: 'success', 
        text: `User ${resident.email} has been permanently deleted. Deletion ID: ${result.data.deletion_id}` 
      });

      // Reload residents list to reflect the deletion
      await loadResidents();

    } catch (error) {
      console.error('Error deleting user:', error);
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to delete user permanently' 
      });
    } finally {
      setUpdateLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Users className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p className="text-gray-600">Loading residents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Residents Management</h1>
          <p className="text-gray-600">View and manage all residents and property owners</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            <Users className="w-4 h-4 mr-1" />
            {filteredResidents.length} of {residents.length}
          </Badge>
        </div>
      </div>

      {message.text && (
        <Alert className={message.type === 'error' ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
          <AlertDescription className={message.type === 'error' ? 'text-red-800' : 'text-green-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {/* Search and Filter Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Search & Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by name, email, phone, erf number, or address..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-full md:w-48">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="all">All Types</option>
                <option value="residents">Residents Only</option>
                <option value="owners">Owners Only</option>
                <option value="both">Owner-Residents</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            <Button 
              variant="outline" 
              onClick={handleClearFilters}
              className="w-full md:w-auto"
              disabled={!searchTerm && filterType === 'all'}
            >
              <X className="w-4 h-4 mr-2" />
              Clear
            </Button>
          </div>
          {(searchTerm || filterType !== 'all') && (
            <div className="mt-3 text-sm text-gray-600">
              Showing {filteredResidents.length} of {residents.length} residents
              {searchTerm && (
                <span> matching "{searchTerm}"</span>
              )}
              {filterType !== 'all' && (
                <span> filtered by {
                  filterType === 'both' ? 'owner-residents' : 
                  filterType === 'residents' ? 'residents only' :
                  filterType === 'owners' ? 'owners only' :
                  filterType === 'archived' ? 'archived users' :
                  filterType
                }</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Residents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredResidents.map((resident) => {
          const isArchived = resident.status === 'archived' || resident.archived === true;
          return (
          <Card 
            key={resident.id || resident.user_id} 
            className={`hover:shadow-lg transition-shadow ${
              isArchived ? 'opacity-75 bg-gray-50 border-gray-300' : ''
            }`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">
                      {resident.first_name} {resident.last_name}
                    </CardTitle>
                    <div className="flex items-center space-x-2 mt-1">
                      {getResidentTypeBadge(resident)}
                      {getStatusBadge(resident.status)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditResidentWithVehicles(resident)}
                    disabled={isArchived || updateLoading}
                    className={isArchived ? 'opacity-50 cursor-not-allowed' : ''}
                  >
                    <Edit className="w-4 h-4" />
                    {isArchived && <span className="ml-1 text-xs">(Archived)</span>}
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handlePermanentDeleteUser(resident)}
                    disabled={updateLoading}
                    className="bg-red-600 hover:bg-red-700"
                    title="Permanently delete user - WARNING: Cannot be undone!"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2 text-sm">
                <div className="flex items-center text-gray-600">
                  <Mail className="w-4 h-4 mr-2" />
                  {resident.email}
                </div>
                {resident.phone_number && (
                  <div className="flex items-center text-gray-600">
                    <Phone className="w-4 h-4 mr-2" />
                    {resident.phone_number}
                  </div>
                )}
                <div className="flex items-center text-gray-600">
                  <MapPin className="w-4 h-4 mr-2" />
                  {resident.full_address || 'No address provided'}
                </div>
                {resident.intercom_code && (
                  <div className="flex items-center text-gray-600">
                    <KeyRound className="w-4 h-4 mr-2" />
                    Code: {resident.intercom_code}
                  </div>
                )}
                <div className="flex items-center text-gray-600">
                  <Home className="w-4 h-4 mr-2" />
                  Erf {resident.erf_number}
                </div>
                {/* Vehicle Information */}
                {resident.vehicles && resident.vehicles.length > 0 && (
                  <div className="flex items-center text-gray-600">
                    <Car className="w-4 h-4 mr-2" />
                    {resident.vehicles.length === 1 ? (
                      <span>{resident.vehicles[0].registration_number}</span>
                    ) : (
                      <span>{resident.vehicles.length} vehicles</span>
                    )}
                  </div>
                )}
                {resident.created_at && (
                  <div className="flex items-center text-gray-600">
                    <Calendar className="w-4 h-4 mr-2" />
                    Registered {new Date(resident.created_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          );
        })}
      </div>

      {filteredResidents.length === 0 && !loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Users className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No residents found</h3>
            <p className="text-gray-600 text-center">
              {searchTerm || filterType !== 'all' 
                ? 'No residents match your search criteria. Try adjusting your filters.'
                : 'No residents are registered in the system yet.'
              }
            </p>
          </CardContent>
        </Card>
      )}

      {/* Edit Resident Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Resident Information</DialogTitle>
            <DialogDescription>
              Update the information for {selectedResident?.first_name} {selectedResident?.last_name}
            </DialogDescription>
          </DialogHeader>
          
          {selectedResident && (
            <form onSubmit={handleUpdateResident} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit_first_name">First Name</Label>
                  <Input
                    id="edit_first_name"
                    value={selectedResident.first_name || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      first_name: e.target.value
                    })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit_last_name">Last Name</Label>
                  <Input
                    id="edit_last_name"
                    value={selectedResident.last_name || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      last_name: e.target.value
                    })}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_email">Email</Label>
                <Input
                  id="edit_email"
                  type="email"
                  value={selectedResident.email || ''}
                  onChange={(e) => setSelectedResident({
                    ...selectedResident,
                    email: e.target.value
                  })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit_phone">Phone Number</Label>
                  <Input
                    id="edit_phone"
                    value={selectedResident.phone_number || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      phone_number: e.target.value
                    })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit_erf">Erf Number</Label>
                  <Input
                    id="edit_erf"
                    value={selectedResident.erf_number || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      erf_number: e.target.value
                    })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_address">Property Address</Label>
                <Input
                  id="edit_address"
                  value={selectedResident.full_address || ''}
                  onChange={(e) => setSelectedResident({
                    ...selectedResident,
                    full_address: e.target.value
                  })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit_emergency_name">Emergency Contact Name</Label>
                  <Input
                    id="edit_emergency_name"
                    value={selectedResident.emergency_contact_name || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      emergency_contact_name: e.target.value
                    })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit_emergency_phone">Emergency Contact Phone</Label>
                  <Input
                    id="edit_emergency_phone"
                    value={selectedResident.emergency_contact_number || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      emergency_contact_number: e.target.value
                    })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_intercom_code">Intercom Code</Label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="edit_intercom_code"
                    value={selectedResident.intercom_code || ''}
                    onChange={(e) => setSelectedResident({
                      ...selectedResident,
                      intercom_code: e.target.value
                    })}
                    placeholder="Enter intercom access code"
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_resident_status">Resident Status</Label>
                <div className="relative">
                  <UserCheck className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <select
                    id="edit_resident_status"
                    value={getResidentStatusValue(selectedResident)}
                    onChange={(e) => handleResidentStatusChange(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pl-10 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  >
                    <option value="resident">Resident</option>
                    <option value="owner">Property Owner</option>
                    <option value="owner-resident">Owner-Resident</option>
                  </select>
                </div>
                <p className="text-xs text-gray-500">
                  Change the user's status between resident, owner, or both
                </p>
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setEditDialogOpen(false)}
                  disabled={updateLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={updateLoading}>
                  {updateLoading ? 'Updating...' : 'Update Resident'}
                </Button>
              </div>
            </form>
          )}
            
          {/* Vehicle Management Section - Show for all users who can have vehicles */}
          {selectedResident && (selectedResident.is_resident || selectedResident.is_owner) && (
              <div className="mt-6 pt-6 border-t space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Car className="w-5 h-5" />
                    Vehicle Management
                  </h3>
                  <Badge variant="secondary">
                    {vehicles.length} vehicle{vehicles.length !== 1 ? 's' : ''}
                  </Badge>
                </div>

                {/* Add Vehicle Form */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Add New Vehicle</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleAddVehicle} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="reg_number">Registration Number *</Label>
                          <Input
                            id="reg_number"
                            value={newVehicle.registration_number}
                            onChange={(e) => setNewVehicle({
                              ...newVehicle,
                              registration_number: e.target.value.toUpperCase()
                            })}
                            placeholder="e.g. ABC123GP"
                            required
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="make">Make</Label>
                          <Input
                            id="make"
                            value={newVehicle.make}
                            onChange={(e) => setNewVehicle({
                              ...newVehicle,
                              make: e.target.value
                            })}
                            placeholder="e.g. Toyota"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="model">Model</Label>
                          <Input
                            id="model"
                            value={newVehicle.model}
                            onChange={(e) => setNewVehicle({
                              ...newVehicle,
                              model: e.target.value
                            })}
                            placeholder="e.g. Corolla"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="color">Color</Label>
                          <Input
                            id="color"
                            value={newVehicle.color}
                            onChange={(e) => setNewVehicle({
                              ...newVehicle,
                              color: e.target.value
                            })}
                            placeholder="e.g. White"
                          />
                        </div>
                      </div>
                      <Button type="submit" disabled={vehicleLoading} className="w-full">
                        <Plus className="w-4 h-4 mr-2" />
                        {vehicleLoading ? 'Adding...' : 'Add Vehicle'}
                      </Button>
                    </form>
                  </CardContent>
                </Card>

                {/* Vehicles List */}
                <div className="space-y-2">
                  <h4 className="font-medium">Current Vehicles</h4>
                  {vehicleLoading && vehicles.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">Loading vehicles...</p>
                  ) : vehicles.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">No vehicles registered</p>
                  ) : (
                    vehicles.map((vehicle) => (
                      <Card key={vehicle.id}>
                        <CardContent className="flex items-center justify-between p-4">
                          <div className="flex items-center space-x-4">
                            <Car className="w-5 h-5 text-gray-400" />
                            <div>
                              <div className="font-mono font-semibold text-lg">
                                {vehicle.registration_number}
                              </div>
                              <div className="text-sm text-gray-600">
                                {[vehicle.make, vehicle.model, vehicle.color]
                                  .filter(Boolean)
                                  .join(' • ')}
                              </div>
                              {vehicle.erf_number && (
                                <div className="text-xs text-blue-600 mt-1">
                                  ERF {vehicle.erf_number}
                                </div>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDeleteVehicle(vehicle.id)}
                            disabled={vehicleLoading}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminResidents;
