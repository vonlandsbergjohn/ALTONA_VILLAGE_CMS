import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { CalendarIcon, ClockIcon, UserIcon, MessageSquareIcon, CarIcon, RefreshCwIcon } from 'lucide-react';
import { format } from 'date-fns';

const MyTransitionRequests = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [newUpdate, setNewUpdate] = useState('');
  const [updatingRequest, setUpdatingRequest] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  useEffect(() => {
    fetchRequests();
  }, []);

  // Auto-refresh every 30 seconds when user is active
  useEffect(() => {
    const interval = setInterval(() => {
      if (!loading && !refreshing) {
        refreshData();
      }
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [loading, refreshing]);

  // Focus refresh - refresh when window gains focus
  useEffect(() => {
    const handleFocus = () => {
      if (!loading && !refreshing) {
        refreshData();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [loading, refreshing]);

  const fetchRequests = async () => {
    try {
      setRefreshing(true);
      const token = localStorage.getItem('token');
      const response = await fetch('https://altona-village-backend.onrender.com/api/transition/requests', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRequests(data.requests);
        setLastRefresh(new Date());
      } else {
        setError('Failed to fetch requests');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const refreshData = async () => {
    await fetchRequests();
    // If a request is selected, refresh its details too
    if (selectedRequest) {
      await fetchRequestDetails(selectedRequest.id);
    }
  };

  const fetchRequestDetails = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/transition/request/${requestId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(data);
        
        // Update the main list with fresh status info
        setRequests(prev => prev.map(req => 
          req.id === requestId 
            ? { ...req, status: data.status, priority: data.priority, updated_at: data.updated_at }
            : req
        ));
      } else {
        setError('Failed to fetch request details');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error fetching request details:', error);
    }
  };

  const addUpdate = async () => {
    if (!newUpdate.trim()) return;

    setUpdatingRequest(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/transition/request/${selectedRequest.id}/update`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          update_text: newUpdate,
          update_type: 'comment'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(prev => ({
          ...prev,
          updates: [data.update, ...prev.updates]
        }));
        setNewUpdate('');
      } else {
        setError('Failed to add update');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error adding update:', error);
    } finally {
      setUpdatingRequest(false);
    }
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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading requests...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">My Transition Requests</h1>
          <div className="flex items-center space-x-4">
            <p className="text-gray-600">Track your property transition requests and communicate with admin</p>
            {lastRefresh && (
              <p className="text-xs text-gray-400">
                Last updated: {format(lastRefresh, 'HH:mm:ss')}
              </p>
            )}
          </div>
        </div>
        <div className="space-x-2">
          <Button 
            variant="outline" 
            onClick={refreshData}
            disabled={refreshing}
          >
            <RefreshCwIcon className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button onClick={() => window.location.href = '/resident/transition-request/new'}>
            New Request
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {requests.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-gray-500 mb-4">
              <CalendarIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">No transition requests found</p>
              <p className="text-sm">Submit your first request to get started</p>
            </div>
            <Button onClick={() => window.location.href = '/resident/transition-request/new'}>
              Create First Request
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {requests.map((request) => (
            <Card key={request.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center space-x-2">
                      <span>ERF {request.erf_number} - {formatRequestType(request.request_type)}</span>
                    </CardTitle>
                    <CardDescription>
                      Created {format(new Date(request.created_at), 'PPP')}
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
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <CalendarIcon className="h-4 w-4" />
                    <span>Move-out: {formatDate(request.intended_moveout_date)}</span>
                  </div>
                  {request.property_transfer_date && (
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <ClockIcon className="h-4 w-4" />
                      <span>Transfer: {formatDate(request.property_transfer_date)}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <UserIcon className="h-4 w-4" />
                    <span>Role: {request.current_role.replace('_', ' ')}</span>
                  </div>
                  {request.notice_period && (
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <ClockIcon className="h-4 w-4" />
                      <span>Notice: {request.notice_period}</span>
                    </div>
                  )}
                </div>

                <div className="flex justify-end">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button 
                        variant="outline" 
                        onClick={() => fetchRequestDetails(request.id)}
                      >
                        View Details
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <div className="flex justify-between items-start">
                          <div>
                            <DialogTitle>
                              Transition Request - ERF {request.erf_number}
                            </DialogTitle>
                            <DialogDescription>
                              {formatRequestType(request.request_type)} request details and updates
                            </DialogDescription>
                          </div>
                          <div className="text-right">
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => fetchRequestDetails(request.id)}
                              disabled={refreshing}
                            >
                              <RefreshCwIcon className={`h-3 w-3 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                              Refresh
                            </Button>
                            {selectedRequest && selectedRequest.updated_at && (
                              <p className="text-xs text-gray-500 mt-1">
                                Last updated: {format(new Date(selectedRequest.updated_at), 'PPp')}
                              </p>
                            )}
                          </div>
                        </div>
                      </DialogHeader>

                      {selectedRequest && selectedRequest.id === request.id && (
                        <Tabs defaultValue="details" className="w-full">
                          <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="details">Details</TabsTrigger>
                            <TabsTrigger value="updates">Updates</TabsTrigger>
                            <TabsTrigger value="vehicles">Vehicles</TabsTrigger>
                          </TabsList>

                          <TabsContent value="details" className="space-y-4">
                            <div className="grid md:grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-semibold mb-2">Basic Information</h4>
                                <div className="space-y-1 text-sm">
                                  <p><strong>ERF:</strong> {selectedRequest.erf_number}</p>
                                  <p><strong>Type:</strong> {formatRequestType(selectedRequest.request_type)}</p>
                                  <p><strong>Role:</strong> {selectedRequest.current_role.replace('_', ' ')}</p>
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

                            {selectedRequest.request_type === 'owner_sale' && (
                              <div>
                                <h4 className="font-semibold mb-2">Sale Details</h4>
                                <div className="grid md:grid-cols-2 gap-4 text-sm">
                                  <p><strong>Agreement Signed:</strong> {selectedRequest.sale_agreement_signed ? 'Yes' : 'No'}</p>
                                  <p><strong>Transfer Attorney:</strong> {selectedRequest.transfer_attorney || 'Not specified'}</p>
                                  <p><strong>Expected Transfer:</strong> {formatDate(selectedRequest.expected_transfer_date)}</p>
                                  <p><strong>New Owner Known:</strong> {selectedRequest.new_owner_details_known ? 'Yes' : 'No'}</p>
                                </div>
                              </div>
                            )}

                            {selectedRequest.request_type === 'tenant_moveout' && (
                              <div>
                                <h4 className="font-semibold mb-2">Move-out Details</h4>
                                <div className="grid md:grid-cols-2 gap-4 text-sm">
                                  <p><strong>Lease End:</strong> {formatDate(selectedRequest.lease_end_date)}</p>
                                  <p><strong>Reason:</strong> {selectedRequest.moveout_reason?.replace('_', ' ') || 'Not specified'}</p>
                                  {selectedRequest.moveout_reason_other && (
                                    <p><strong>Other Reason:</strong> {selectedRequest.moveout_reason_other}</p>
                                  )}
                                  <p><strong>Deposit Return:</strong> {selectedRequest.deposit_return_required ? 'Required' : 'Not required'}</p>
                                </div>
                              </div>
                            )}

                            {selectedRequest.request_type === 'owner_moving' && (
                              <div>
                                <h4 className="font-semibold mb-2">Rental Details</h4>
                                <div className="grid md:grid-cols-2 gap-4 text-sm">
                                  <p><strong>Property Manager:</strong> {selectedRequest.property_management_company || 'Not specified'}</p>
                                  <p><strong>Tenant Selected:</strong> {selectedRequest.new_tenant_selected ? 'Yes' : 'No'}</p>
                                  <p><strong>Rental Start:</strong> {formatDate(selectedRequest.rental_start_date)}</p>
                                </div>
                              </div>
                            )}

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

                            {(selectedRequest.access_handover_requirements || 
                              selectedRequest.property_condition_notes || 
                              selectedRequest.community_introduction_needs) && (
                              <div>
                                <h4 className="font-semibold mb-2">Special Instructions</h4>
                                {selectedRequest.access_handover_requirements && (
                                  <div className="mb-2">
                                    <p className="font-medium text-sm">Access Handover:</p>
                                    <p className="text-sm text-gray-600">{selectedRequest.access_handover_requirements}</p>
                                  </div>
                                )}
                                {selectedRequest.property_condition_notes && (
                                  <div className="mb-2">
                                    <p className="font-medium text-sm">Property Condition:</p>
                                    <p className="text-sm text-gray-600">{selectedRequest.property_condition_notes}</p>
                                  </div>
                                )}
                                {selectedRequest.community_introduction_needs && (
                                  <div className="mb-2">
                                    <p className="font-medium text-sm">Introduction Needs:</p>
                                    <p className="text-sm text-gray-600">{selectedRequest.community_introduction_needs}</p>
                                  </div>
                                )}
                              </div>
                            )}

                            {selectedRequest.admin_notes && (
                              <div>
                                <h4 className="font-semibold mb-2">Admin Notes</h4>
                                <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                                  {selectedRequest.admin_notes}
                                </p>
                              </div>
                            )}
                          </TabsContent>

                          <TabsContent value="updates" className="space-y-4">
                            <div>
                              <h4 className="font-semibold mb-4">Add Update</h4>
                              <div className="space-y-2">
                                <Textarea
                                  value={newUpdate}
                                  onChange={(e) => setNewUpdate(e.target.value)}
                                  placeholder="Add a comment or update..."
                                  rows="3"
                                />
                                <Button 
                                  onClick={addUpdate} 
                                  disabled={!newUpdate.trim() || updatingRequest}
                                  size="sm"
                                >
                                  {updatingRequest ? 'Adding...' : 'Add Update'}
                                </Button>
                              </div>
                            </div>

                            <div>
                              <h4 className="font-semibold mb-4">Request Updates</h4>
                              {selectedRequest.updates && selectedRequest.updates.length > 0 ? (
                                <div className="space-y-3 max-h-64 overflow-y-auto">
                                  {selectedRequest.updates.map((update) => (
                                    <div key={update.id} className="border rounded p-3">
                                      <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center space-x-2">
                                          <MessageSquareIcon className="h-4 w-4 text-gray-400" />
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
                                        <CarIcon className="h-4 w-4 text-gray-400" />
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

export default MyTransitionRequests;
