import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { 
  Link, 
  Search, 
  ArrowRightLeft, 
  UserCheck, 
  Home,
  Calendar,
  MapPin,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
  Mail,
  Phone
} from 'lucide-react';
import { format } from 'date-fns';

const AdminTransitionLinking = () => {
  const [transitionRequests, setTransitionRequests] = useState([]);
  const [pendingRegistrations, setPendingRegistrations] = useState([]);
  const [linkedPairs, setLinkedPairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [processingLink, setProcessingLink] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const [transitionRes, registrationRes] = await Promise.all([
        fetch('https://altona-village-backend.onrender.com/api/transition/admin/requests', { headers }),
        fetch('https://altona-village-backend.onrender.com/api/admin/pending-registrations', { headers })
      ]);

      if (transitionRes.ok && registrationRes.ok) {
        const transitionData = await transitionRes.json();
        const registrationData = await registrationRes.json();
        
        setTransitionRequests(transitionData.requests || []);
        setPendingRegistrations(registrationData.data || []);
        
        // Find potential matches based on ERF numbers
        findPotentialMatches(transitionData.requests || [], registrationData.data || []);
      } else {
        setError('Failed to load data');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const findPotentialMatches = (transitions, registrations) => {
    const matches = [];
    
    transitions.forEach(transition => {
      // Skip cancelled requests
      if (transition.status === 'cancelled') {
        return;
      }
      
      // Include transitions that are:
      // 1. Not completed yet (normal flow)
      // 2. Completed but not properly migrated (needs linking fix)
      const needsLinking = transition.status !== 'completed' || !transition.migration_completed;
      
      if (needsLinking) {
        const matchingRegistrations = registrations.filter(reg => 
          reg.erf_number === transition.erf_number && reg.status === 'pending'
        );
        
        matchingRegistrations.forEach(registration => {
          matches.push({
            transition,
            registration,
            erfNumber: transition.erf_number,
            confidence: 'high', // High confidence when ERF numbers match exactly
            status: transition.status === 'completed' ? 'needs_migration' : 'potential'
          });
        });
      }
    });
    
    setLinkedPairs(matches);
  };

  const formatOccupantType = (type) => {
    const typeMap = {
      'resident': 'Resident Only (Tenant/Renter)',
      'owner': 'Owner Only (Property Owner)',
      'owner_resident': 'Owner-Resident (Owner who lives there)',
      'terminated': 'Terminated/Exiting Estate (No future status)'
    };
    return typeMap[type] || type || 'Not specified';
  };

  const linkAndProcessTransition = async (transitionRequest, registration) => {
    setProcessingLink(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://altona-village-backend.onrender.com/api/transition/admin/link-and-process', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transition_request_id: transitionRequest.id,
          registration_id: registration.id,
          new_user_data: {
            first_name: registration.first_name,
            last_name: registration.last_name,
            email: registration.email,
            phone_number: registration.phone_number,
            emergency_contact_name: registration.emergency_contact_name,
            emergency_contact_number: registration.emergency_contact_number,
            id_number: registration.id_number,
            address: registration.address,
            is_owner: registration.is_owner,
            is_resident: registration.is_resident
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess(`Successfully processed transition for ERF ${transitionRequest.erf_number}. ${result.message}`);
        // Reload data to reflect changes
        await loadData();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to process transition');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error processing transition:', error);
    } finally {
      setProcessingLink(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'approved': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800',
      'in_progress': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800'
    };
    return variants[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredPairs = linkedPairs.filter(pair =>
    searchTerm === '' ||
    pair.erfNumber.includes(searchTerm) ||
    pair.transition.current_user_first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pair.transition.current_user_last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pair.registration.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pair.registration.last_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading transition data...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">
          Transition Request Linking
        </h1>
        <p className="text-gray-600">Link transition requests with new user registrations to complete property transitions</p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-4 bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Search and Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <ArrowRightLeft className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Transition Requests</p>
                <p className="text-2xl font-bold">{transitionRequests.filter(req => req.status !== 'cancelled').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <UserCheck className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Pending Registrations</p>
                <p className="text-2xl font-bold">{pendingRegistrations.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <Link className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Potential Matches</p>
                <p className="text-2xl font-bold">{linkedPairs.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by ERF or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Workflow Guide */}
      <Card className="mb-6 bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-800 flex items-center">
            <Users className="h-5 w-5 mr-2" />
            How Transition Linking Works
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start space-x-3">
              <div className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">1</div>
              <div>
                <p className="font-medium text-blue-800">Current User Submits</p>
                <p className="text-blue-600">Existing resident requests property transition with ERF number</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">2</div>
              <div>
                <p className="font-medium text-blue-800">New User Registers</p>
                <p className="text-blue-600">Future occupant registers independently with same ERF number</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">3</div>
              <div>
                <p className="font-medium text-blue-800">Admin Links & Processes</p>
                <p className="text-blue-600">System matches by ERF and completes the transition</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Potential Matches */}
      <div className="space-y-4">
        {filteredPairs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Link className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg text-gray-500">No potential matches found</p>
              <p className="text-sm text-gray-400 mt-2">
                Matches will appear when transition requests and registrations have the same ERF number
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredPairs.map((pair, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center text-lg">
                      <MapPin className="h-5 w-5 mr-2 text-blue-600" />
                      ERF {pair.erfNumber}
                      <Badge className={`ml-2 ${
                        pair.status === 'needs_migration' 
                          ? 'bg-orange-100 text-orange-800' 
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {pair.status === 'needs_migration' ? 'Needs Migration' : 'Potential Match'}
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      {pair.status === 'needs_migration' 
                        ? 'Completed transition requiring proper migration'
                        : 'Property transition ready for linking'
                      }
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => linkAndProcessTransition(pair.transition, pair.registration)}
                    disabled={processingLink}
                    className={`${
                      pair.status === 'needs_migration'
                        ? 'bg-orange-600 hover:bg-orange-700'
                        : 'bg-green-600 hover:bg-green-700'
                    }`}
                  >
                    {processingLink ? 'Processing...' : 
                     pair.status === 'needs_migration' ? 'Fix & Complete Migration' : 'Link & Process Transition'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Current User (Transition Request) */}
                  <div className="border rounded-lg p-4 bg-red-50">
                    <h3 className="font-semibold text-red-800 mb-3 flex items-center">
                      <ArrowRightLeft className="h-4 w-4 mr-2" />
                      Outgoing User (Transition Request)
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Name:</span>
                        <span className="font-medium">
                          {pair.transition.current_user_first_name} {pair.transition.current_user_last_name}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Current Role:</span>
                        <span className="font-medium">{pair.transition.current_role}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Future Residency Status:</span>
                        <span className="font-medium">{formatOccupantType(pair.transition.new_occupant_type)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Transition Date:</span>
                        <span className="font-medium">
                          {pair.transition.expected_transfer_date 
                            ? format(new Date(pair.transition.expected_transfer_date), 'MMM dd, yyyy')
                            : 'Not specified'
                          }
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status:</span>
                        <Badge className={getStatusBadge(pair.transition.status)}>
                          {pair.transition.status}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {/* New User (Registration) */}
                  <div className="border rounded-lg p-4 bg-green-50">
                    <h3 className="font-semibold text-green-800 mb-3 flex items-center">
                      <UserCheck className="h-4 w-4 mr-2" />
                      Incoming User (Registration)
                    </h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Name:</span>
                        <span className="font-medium">
                          {pair.registration.first_name} {pair.registration.last_name}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Email:</span>
                        <span className="font-medium text-xs">{pair.registration.email}</span>
                      </div>
                      {pair.registration.phone_number && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Phone:</span>
                          <span className="font-medium">{pair.registration.phone_number}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-gray-600">Type:</span>
                        <span className="font-medium">
                          {pair.registration.is_owner && pair.registration.is_resident ? 'Owner-Resident' :
                           pair.registration.is_owner ? 'Owner' :
                           pair.registration.is_resident ? 'Resident' : 'Other'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Registration:</span>
                        <span className="font-medium">
                          {format(new Date(pair.registration.created_at), 'MMM dd, yyyy')}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status:</span>
                        <Badge className={getStatusBadge(pair.registration.status)}>
                          {pair.registration.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Additional Details */}
                {pair.transition.additional_details && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <h4 className="font-medium text-gray-800 mb-2">Transition Details:</h4>
                    <p className="text-sm text-gray-600">{pair.transition.additional_details}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default AdminTransitionLinking;
