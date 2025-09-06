import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { 
  ArrowRightLeft, 
  Search, 
  Filter, 
  CalendarIcon, 
  ClockIcon, 
  UserIcon, 
  MessageSquareIcon, 
  CarIcon,
  CheckCircle,
  AlertCircle,
  Clock,
  X
} from 'lucide-react';
import { format } from 'date-fns';

const AdminTransitionRequests = () => {
  const [requests, setRequests] = useState([]);
  const [filteredRequests, setFilteredRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [updateLoading, setUpdateLoading] = useState(false);

  // Update form state
  const [statusUpdate, setStatusUpdate] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  const [updateText, setUpdateText] = useState('');

  useEffect(() => {
    fetchRequests();
  }, []);

  useEffect(() => {
    filterRequests();
  }, [requests, searchTerm, statusFilter, typeFilter]);

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/transition/admin/requests', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRequests(data.requests);
      } else {
        setError('Failed to fetch requests');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRequestDetails = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/transition/admin/request/${requestId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(data);
        setStatusUpdate(data.status);
        setAdminNotes(data.admin_notes || '');
      } else {
        setError('Failed to fetch request details');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error fetching request details:', error);
    }
  };

  const updateRequestStatus = async () => {
    if (!selectedRequest) return;

    setUpdateLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/transition/admin/request/${selectedRequest.id}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: statusUpdate,
          admin_notes: adminNotes
        })
      });

      if (response.ok) {
        setSuccess('Request status updated successfully');
        fetchRequests();
        setSelectedRequest(prev => ({
          ...prev,
          status: statusUpdate,
          admin_notes: adminNotes
        }));
      } else {
        setError('Failed to update request status');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error updating request status:', error);
    } finally {
      setUpdateLoading(false);
    }
  };

  const addAdminUpdate = async () => {
    if (!updateText.trim() || !selectedRequest) return;

    setUpdateLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/transition/admin/request/${selectedRequest.id}/update`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          update_text: updateText,
          update_type: 'admin_response'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(prev => ({
          ...prev,
          updates: [data.update, ...prev.updates]
        }));
        setUpdateText('');
        setSuccess('Update added successfully');
      } else {
        setError('Failed to add update');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error adding update:', error);
    } finally {
      setUpdateLoading(false);
    }
  };

  const cancelRequest = async (requestId) => {
    if (!window.confirm('Are you sure you want to cancel this transition request? This action cannot be undone.')) {
      return;
    }

    setUpdateLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/transition/admin/request/${requestId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: 'cancelled',
          admin_notes: 'Request cancelled by admin'
        })
      });

      if (response.ok) {
        setSuccess('Request cancelled successfully');
        fetchRequests();
        setSelectedRequest(null);
      } else {
        setError('Failed to cancel request');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error cancelling request:', error);
    } finally {
      setUpdateLoading(false);
    }
  };

  const filterRequests = () => {
    let filtered = requests;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(request => 
        request.erf_number.toString().includes(searchTerm) ||
        request.user_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        request.request_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(request => request.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(request => request.request_type === typeFilter);
    }

    setFilteredRequests(filtered);
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_review': 'bg-yellow-100 text-yellow-800',
      'in_progress': 'bg-blue-100 text-blue-800',
      'awaiting_docs': 'bg-orange-100 text-orange-800',
      'ready_for_transition': 'bg-green-100 text-green-800',
      'completed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'standard': 'bg-gray-100 text-gray-800',
      'urgent': 'bg-orange-100 text-orange-800',
      'emergency': 'bg-red-100 text-red-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const formatRequestType = (type) => {
    const types = {
      'owner_sale': 'Owner Sale',
      'tenant_moveout': 'Tenant Move-Out',
      'owner_moving': 'Owner Moving',
      'other': 'Other'
    };
    return types[type] || type;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not specified';
    return format(new Date(dateString), 'PPP');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" aria-label="Completed status" />;
      case 'cancelled':
        return <X className="h-4 w-4 text-red-600" aria-label="Cancelled status" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-600" aria-label="In progress status" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-600" aria-label="Pending status" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading transition requests...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center">
            <ArrowRightLeft className="h-6 w-6 mr-2" />
            Transition Requests Management
          </h1>
          <p className="text-gray-600">Manage property transition requests from residents</p>
        </div>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-600">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-600">{success}</AlertDescription>
        </Alert>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="ERF, email, or type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending_review">Pending Review</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="awaiting_docs">Awaiting Documents</SelectItem>
                  <SelectItem value="ready_for_transition">Ready for Transition</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Request Type</label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="owner_sale">Owner Sale</SelectItem>
                  <SelectItem value="tenant_moveout">Tenant Move-Out</SelectItem>
                  <SelectItem value="owner_moving">Owner Moving</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Results</label>
              <div className="text-sm text-gray-600 pt-2">
                {filteredRequests.length} of {requests.length} requests
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Requests List */}
      {filteredRequests.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ArrowRightLeft className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p className="text-lg text-gray-500">No transition requests found</p>
            <p className="text-sm text-gray-400">Adjust your filters or wait for new requests</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredRequests.map((request) => (
            <Card key={request.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      {getStatusIcon(request.status)}
                      <span>ERF {request.erf_number} - {formatRequestType(request.request_type)}</span>
                    </CardTitle>
                    <CardDescription>
                      {request.user_email} • Created {format(new Date(request.created_at), 'PPp')}
                    </CardDescription>
                  </div>
                  <div className="flex space-x-2">
                    <Badge className={getPriorityColor(request.priority)}>
                      {request.priority}
                    </Badge>
                    <Badge className={getStatusColor(request.status)}>
                      {request.status.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <CalendarIcon className="h-4 w-4" aria-label="Move-out date" />
                    <span>Move-out: {formatDate(request.intended_moveout_date)}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <UserIcon className="h-4 w-4" aria-label="User role" />
                    <span>Role: {request.current_role?.replace('_', ' ')}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <ClockIcon className="h-4 w-4" aria-label="Last updated time" />
                    <span>Last updated: {format(new Date(request.updated_at), 'PPp')}</span>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button 
                        variant="outline" 
                        onClick={() => fetchRequestDetails(request.id)}
                      >
                        Manage Request
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>
                          Manage Request - ERF {request.erf_number}
                        </DialogTitle>
                        <DialogDescription>
                          {formatRequestType(request.request_type)} request management
                        </DialogDescription>
                      </DialogHeader>

                      {selectedRequest && selectedRequest.id === request.id && (
                        <Tabs defaultValue="details" className="w-full">
                          <TabsList className="grid w-full grid-cols-4">
                            <TabsTrigger value="details">Details</TabsTrigger>
                            <TabsTrigger value="manage">Manage</TabsTrigger>
                            <TabsTrigger value="updates">Updates</TabsTrigger>
                            <TabsTrigger value="vehicles">Vehicles</TabsTrigger>
                          </TabsList>

                          <TabsContent value="details" className="space-y-4">
                            {/* Same details content as in MyTransitionRequests but read-only */}
                            <div className="grid md:grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-semibold mb-2">Basic Information</h4>
                                <div className="space-y-1 text-sm">
                                  <p><strong>User:</strong> {selectedRequest.user_email}</p>
                                  <p><strong>ERF:</strong> {selectedRequest.erf_number}</p>
                                  <p><strong>Type:</strong> {formatRequestType(selectedRequest.request_type)}</p>
                                  <p><strong>Role:</strong> {selectedRequest.current_role?.replace('_', ' ')}</p>
                                  <p><strong>Status:</strong> <Badge className={getStatusColor(selectedRequest.status)}>{selectedRequest.status.replace('_', ' ')}</Badge></p>
                                  <p><strong>Priority:</strong> <Badge className={getPriorityColor(selectedRequest.priority)}>{selectedRequest.priority}</Badge></p>
                                </div>
                              </div>

                              <div>
                                <h4 className="font-semibold mb-2">Timeline</h4>
                                <div className="space-y-1 text-sm">
                                  <p><strong>Move-out Date:</strong> {formatDate(selectedRequest.intended_moveout_date)}</p>
                                  {selectedRequest.property_transfer_date && (
                                    <p><strong>Transfer Date:</strong> {formatDate(selectedRequest.property_transfer_date)}</p>
                                  )}
                                  {selectedRequest.new_occupant_movein_date && (
                                    <p><strong>New Move-in:</strong> {formatDate(selectedRequest.new_occupant_movein_date)}</p>
                                  )}
                                  <p><strong>Notice Period:</strong> {selectedRequest.notice_period || 'Not specified'}</p>
                                </div>
                              </div>
                            </div>

                            {selectedRequest.new_occupant_name && (
                              <div>
                                <h4 className="font-semibold mb-2">New Occupant Information</h4>
                                <div className="grid md:grid-cols-2 gap-4 text-sm">
                                  <p><strong>Name:</strong> {selectedRequest.new_occupant_name}</p>
                                  <p><strong>Type:</strong> {selectedRequest.new_occupant_type?.replace('_', ' ')}</p>
                                  <p><strong>Phone:</strong> {selectedRequest.new_occupant_phone || 'Not provided'}</p>
                                  <p><strong>Email:</strong> {selectedRequest.new_occupant_email || 'Not provided'}</p>
                                  <p><strong>Adults:</strong> {selectedRequest.new_occupant_adults || 0}</p>
                                  <p><strong>Children:</strong> {selectedRequest.new_occupant_children || 0}</p>
                                  <p><strong>Pets:</strong> {selectedRequest.new_occupant_pets || 0}</p>
                                </div>
                              </div>
                            )}
                          </TabsContent>

                          <TabsContent value="manage" className="space-y-4">
                            <div className="grid md:grid-cols-2 gap-6">
                              <div className="space-y-4">
                                <h4 className="font-semibold">Update Status</h4>
                                <div className="space-y-2">
                                  <label className="text-sm font-medium">Status</label>
                                  <Select value={statusUpdate} onValueChange={setStatusUpdate}>
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="pending_review">Pending Review</SelectItem>
                                      <SelectItem value="in_progress">In Progress</SelectItem>
                                      <SelectItem value="awaiting_docs">Awaiting Documents</SelectItem>
                                      <SelectItem value="ready_for_transition">Ready for Transition</SelectItem>
                                      <SelectItem value="completed">Completed</SelectItem>
                                      <SelectItem value="cancelled">Cancelled</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                                <div className="space-y-2">
                                  <label className="text-sm font-medium">Admin Notes</label>
                                  <Textarea
                                    value={adminNotes}
                                    onChange={(e) => setAdminNotes(e.target.value)}
                                    placeholder="Internal notes (not visible to user)"
                                    rows="4"
                                  />
                                </div>
                                <Button 
                                  onClick={updateRequestStatus} 
                                  disabled={updateLoading}
                                  className="w-full"
                                >
                                  {updateLoading ? 'Updating...' : 'Update Status'}
                                </Button>
                                <Button 
                                  onClick={() => cancelRequest(selectedRequest.id)} 
                                  disabled={updateLoading || selectedRequest.status === 'cancelled'}
                                  className="w-full bg-red-600 hover:bg-red-700 text-white"
                                  variant="destructive"
                                >
                                  {updateLoading ? 'Cancelling...' : 'Cancel Request'}
                                </Button>
                              </div>

                              <div className="space-y-4">
                                <h4 className="font-semibold">Add Update for User</h4>
                                <div className="space-y-2">
                                  <label className="text-sm font-medium">Update Message</label>
                                  <Textarea
                                    value={updateText}
                                    onChange={(e) => setUpdateText(e.target.value)}
                                    placeholder="Message to send to user..."
                                    rows="4"
                                  />
                                </div>
                                <Button 
                                  onClick={addAdminUpdate} 
                                  disabled={!updateText.trim() || updateLoading}
                                  className="w-full"
                                >
                                  {updateLoading ? 'Sending...' : 'Send Update'}
                                </Button>
                              </div>
                            </div>
                          </TabsContent>

                          <TabsContent value="updates" className="space-y-4">
                            <div>
                              <h4 className="font-semibold mb-4">Request Updates</h4>
                              {selectedRequest.updates && selectedRequest.updates.length > 0 ? (
                                <div className="space-y-3 max-h-96 overflow-y-auto">
                                  {selectedRequest.updates.map((update) => (
                                    <div key={update.id} className="border rounded p-3">
                                      <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center space-x-2">
                                          <MessageSquareIcon className="h-4 w-4 text-gray-400" aria-label="Message update" />
                                          <Badge variant="outline" size="sm">
                                            {update.update_type}
                                          </Badge>
                                        </div>
                                        <span className="text-xs text-gray-500">
                                          {format(new Date(update.created_at), 'PPp')}
                                        </span>
                                      </div>
                                      <p className="text-sm">{update.update_text}</p>
                                      {update.old_status && update.new_status && (
                                        <p className="text-xs text-gray-500 mt-1">
                                          Status changed from {update.old_status} to {update.new_status}
                                        </p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-gray-500 text-sm">No updates yet</p>
                              )}
                            </div>
                          </TabsContent>

                          <TabsContent value="vehicles" className="space-y-4">
                            <div>
                              <h4 className="font-semibold mb-4">Vehicle Information</h4>
                              {selectedRequest.vehicles && selectedRequest.vehicles.length > 0 ? (
                                <div className="space-y-3">
                                  {selectedRequest.vehicles.map((vehicle) => (
                                    <div key={vehicle.id} className="border rounded p-3">
                                      <div className="flex items-center space-x-2 mb-2">
                                        <CarIcon className="h-4 w-4 text-gray-400" aria-label="Vehicle information" />
                                        <span className="font-medium">{vehicle.license_plate}</span>
                                      </div>
                                      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                                        <p><strong>Make:</strong> {vehicle.vehicle_make || 'Not specified'}</p>
                                        <p><strong>Model:</strong> {vehicle.vehicle_model || 'Not specified'}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-gray-500 text-sm">No vehicles specified</p>
                              )}
                            </div>
                          </TabsContent>
                        </Tabs>
                      )}
                    </DialogContent>
                  </Dialog>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminTransitionRequests;
