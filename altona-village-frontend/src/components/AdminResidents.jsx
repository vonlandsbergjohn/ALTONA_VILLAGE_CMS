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
  Filter,
  X,
  KeyRound
} from 'lucide-react';

const AdminResidents = () => {
  const [residents, setResidents] = useState([]);
  const [filteredResidents, setFilteredResidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, residents, owners, both
  const [selectedResident, setSelectedResident] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [updateLoading, setUpdateLoading] = useState(false);

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
      console.log('Residents data:', response.data);
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
        
        switch (filterType) {
          case 'residents':
            return isResident && !isOwner;
          case 'owners':
            return isOwner && !isResident;
          case 'both':
            return isResident && isOwner;
          default:
            return true;
        }
      });
    }

    setFilteredResidents(filtered);
  };

  const handleEditResident = (resident) => {
    console.log('=== EDIT RESIDENT CLICKED ===');
    console.log('Resident data:', resident);
    setSelectedResident({ ...resident });
    setEditDialogOpen(true);
    setMessage({ type: '', text: '' });
    console.log('Dialog should be opening...');
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
        tenant_or_owner: selectedResident.is_owner ? 'owner' : 'tenant'
      };

      console.log('Updating resident with data:', updateData);
      
      // Use the admin API to update the resident
      await adminAPI.updateResident(selectedResident.user_id, updateData);
      
      setMessage({ type: 'success', text: 'Resident updated successfully' });
      setEditDialogOpen(false);
      loadResidents(); // Reload the data
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
      'suspended': 'bg-red-100 text-red-800'
    };
    
    const icons = {
      'active': CheckCircle,
      'pending': Clock,
      'suspended': AlertCircle
    };
    
    const Icon = icons[status] || AlertCircle;
    
    return (
      <Badge className={colors[status] || 'bg-gray-100 text-gray-800'}>
        <Icon className="w-3 h-3 mr-1" />
        {status?.toUpperCase() || 'UNKNOWN'}
      </Badge>
    );
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
                <span> filtered by {filterType.replace('_', '-')}</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Residents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredResidents.map((resident) => (
          <Card key={resident.id || resident.user_id} className="hover:shadow-lg transition-shadow">
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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEditResident(resident)}
                >
                  <Edit className="w-4 h-4" />
                </Button>
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
                <div className="flex items-center text-gray-600">
                  <Home className="w-4 h-4 mr-2" />
                  Erf {resident.erf_number}
                </div>
                {resident.created_at && (
                  <div className="flex items-center text-gray-600">
                    <Calendar className="w-4 h-4 mr-2" />
                    Registered {new Date(resident.created_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
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
        <DialogContent className="sm:max-w-[600px]">
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
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminResidents;
