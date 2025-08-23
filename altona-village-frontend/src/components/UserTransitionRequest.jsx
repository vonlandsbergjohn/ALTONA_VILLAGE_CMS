import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { Calendar } from './ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { CalendarIcon, PlusIcon, TrashIcon } from 'lucide-react';
import { format } from 'date-fns';
import { authAPI, residentAPI } from '@/lib/api.js';

const UserTransitionRequest = () => {
  const [formData, setFormData] = useState({
    erf_number: '',
    request_type: '',
    new_occupant_type: '', // Future residency status
    current_role: '',
    intended_moveout_date: null,
    property_transfer_date: null,
    new_occupant_movein_date: null,
    notice_period: '',
    
    // Sale specific
    sale_agreement_signed: false,
    transfer_attorney: '',
    expected_transfer_date: null,
    new_owner_details_known: false,
    
    // Tenant specific
    lease_end_date: null,
    moveout_reason: '',
    moveout_reason_other: '',
    deposit_return_required: false,
    
    // Owner moving specific
    property_management_company: '',
    new_tenant_selected: false,
    rental_start_date: null,
    
    // Community services
    gate_access_transfer: true,
    intercom_access_transfer: true,
    vehicle_registration_transfer: true,
    visitor_access_transfer: true,
    community_notifications_transfer: true,
    
    // Outstanding matters
    unpaid_levies: false,
    pending_maintenance: false,
    community_violations: false,
    outstanding_matters_other: '',
    
    // New occupant info - removed duplicate new_occupant_type field
    new_occupant_first_name: '',
    new_occupant_last_name: '',
    new_occupant_phone: '',
    new_occupant_email: '',
    new_occupant_id_number: '',
    new_occupant_adults: 0,
    new_occupant_children: 0,
    new_occupant_pets: 0,
    
    // Address information (required for database migration)
    new_occupant_street_number: '',
    new_occupant_street_name: '',
    new_occupant_full_address: '',
    new_occupant_intercom_code: '',
    new_occupant_moving_in_date: null,
    
    // Emergency contacts (required)
    new_occupant_emergency_contact_name: '',
    new_occupant_emergency_contact_number: '',
    
    // Owner-specific fields
    new_occupant_title_deed_number: '',
    new_occupant_acquisition_date: null,
    
    // Postal address (for non-resident owners)
    new_occupant_postal_street_number: '',
    new_occupant_postal_street_name: '',
    new_occupant_postal_suburb: '',
    new_occupant_postal_city: '',
    new_occupant_postal_code: '',
    new_occupant_postal_province: '',
    new_occupant_full_postal_address: '',
    
    // Special instructions
    access_handover_requirements: '',
    property_condition_notes: '',
    community_introduction_needs: '',
    
    // Current user vehicles (auto-populated)
    vehicles: []
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [userInfo, setUserInfo] = useState(null);
  const [availableErfs, setAvailableErfs] = useState([]);

  useEffect(() => {
    fetchUserInfo();
    checkUrlParameters();
  }, []);

  const checkUrlParameters = () => {
    // Check if ERF number is passed via URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const erfFromUrl = urlParams.get('erf');
    const userIdFromUrl = urlParams.get('user_id');
    
    if (erfFromUrl) {
      console.log('ERF number from URL:', erfFromUrl);
      setFormData(prev => ({
        ...prev,
        erf_number: erfFromUrl
      }));
    }
  };

  const fetchUserInfo = async () => {
    try {
      console.log('Fetching user profile...');
      const response = await authAPI.getProfile();
      console.log('Profile response:', response);
      const data = response.data;
      console.log('Profile data:', data);
      setUserInfo(data);
      
      // Handle both old and new data structures for properties
      let userProperties = data.properties || [];
      
      // If properties array is empty but user has erfs array, use that
      if (userProperties.length === 0 && data.erfs && data.erfs.length > 0) {
        userProperties = data.erfs.map(erf => ({
          erf_number: erf.erf_number || data.erf_number,
          street_number: erf.street_number || data.property_address?.split(' ')[0] || '',
          street_name: erf.street_name || data.property_address?.replace(/^\d+\s/, '') || ''
        }));
      }
      
      // If still empty, create from main profile data
      if (userProperties.length === 0 && data.erf_number) {
        userProperties = [{
          erf_number: data.erf_number,
          street_number: data.property_address?.split(' ')[0] || '',
          street_name: data.property_address?.replace(/^\d+\s/, '') || data.property_address || ''
        }];
      }
      
      console.log('User properties:', userProperties);
      setAvailableErfs(userProperties);
      
      // Determine user role - handle both old and new API response formats
      const isResident = data.resident || data.is_resident;
      const isOwner = data.owner || data.is_owner;
      console.log('User roles - isResident:', isResident, 'isOwner:', isOwner);
      console.log('Full user data:', data);
      
      let currentRole = '';
      if (isResident && isOwner) {
        currentRole = 'owner_resident';
        console.log('User is both owner and resident');
      } else if (isOwner) {
        currentRole = 'owner';
        console.log('User is owner only');
      } else if (isResident) {
        currentRole = 'tenant';
        console.log('User is resident/tenant only');
      } else {
        console.warn('User has no defined role - neither resident nor owner');
        // Default to a basic role if none detected
        currentRole = 'owner'; // Default assumption
      }
      
      console.log('Determined current_role:', currentRole);

      // Check if ERF number is already set from URL parameters
      const urlParams = new URLSearchParams(window.location.search);
      const erfFromUrl = urlParams.get('erf');
      
      // Pre-populate form data
      setFormData(prev => {
        let erfNumber = prev.erf_number; // Keep if already set from URL
        
        // If no ERF from URL and user has properties, use the first one as default
        if (!erfNumber && userProperties.length > 0) {
          erfNumber = userProperties[0].erf_number;
        }
        
      // If ERF from URL, verify it belongs to the user
      if (erfFromUrl) {
        const userOwnsErf = userProperties.some(prop => prop.erf_number === erfFromUrl) || data.erf_number === erfFromUrl;
        if (userOwnsErf) {
          erfNumber = erfFromUrl;
        } else {
          console.warn('User does not own ERF from URL:', erfFromUrl);
          console.log('User properties:', userProperties);
          console.log('User main ERF:', data.erf_number);
          // If user's main ERF matches, allow it
          if (data.erf_number === erfFromUrl) {
            erfNumber = erfFromUrl;
          } else {
            setError(`You don't have access to ERF ${erfFromUrl}. Please select from your properties.`);
          }
        }
      }        console.log('Setting ERF number:', erfNumber);
        console.log('Setting current_role:', currentRole);
        return {
          ...prev,
          erf_number: erfNumber,
          current_role: currentRole,
        };
      });

      // Also fetch and pre-populate vehicle information
      fetchUserVehicles();
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
  };

  const fetchUserVehicles = async () => {
    try {
      const response = await residentAPI.getMyVehicles();
      const vehicles = response.data;
      
      if (vehicles && vehicles.length > 0) {
        // Pre-populate vehicles for easy reference/transfer
        const vehicleData = vehicles.map(vehicle => ({
          vehicle_make: vehicle.make || '',
          vehicle_model: vehicle.model || '',
          license_plate: vehicle.registration_number || '',
          color: vehicle.color || ''
        }));

        setFormData(prev => ({
          ...prev,
          vehicles: vehicleData
        }));
      }
    } catch (error) {
      console.error('Error fetching user vehicles:', error);
    }
  };

  const handleInputChange = (field, value) => {
    console.log('handleInputChange called:', field, value); // Debug log
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDateChange = (field, date) => {
    setFormData(prev => ({
      ...prev,
      [field]: date
    }));
  };

  const addVehicle = () => {
    setFormData(prev => ({
      ...prev,
      vehicles: [...prev.vehicles, { vehicle_make: '', vehicle_model: '', license_plate: '', color: '' }]
    }));
  };

  const removeVehicle = (index) => {
    setFormData(prev => ({
      ...prev,
      vehicles: prev.vehicles.filter((_, i) => i !== index)
    }));
  };

  const updateVehicle = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      vehicles: prev.vehicles.map((vehicle, i) => 
        i === index ? { ...vehicle, [field]: value } : vehicle
      )
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      
      // Format dates for submission and exclude new occupant fields for privacy compliance
      const submitData = {
        ...formData,
        intended_moveout_date: formData.intended_moveout_date ? format(formData.intended_moveout_date, 'yyyy-MM-dd') : null,
        property_transfer_date: formData.property_transfer_date ? format(formData.property_transfer_date, 'yyyy-MM-dd') : null,
        new_occupant_movein_date: formData.new_occupant_movein_date ? format(formData.new_occupant_movein_date, 'yyyy-MM-dd') : null,
        expected_transfer_date: formData.expected_transfer_date ? format(formData.expected_transfer_date, 'yyyy-MM-dd') : null,
        lease_end_date: formData.lease_end_date ? format(formData.lease_end_date, 'yyyy-MM-dd') : null,
        rental_start_date: formData.rental_start_date ? format(formData.rental_start_date, 'yyyy-MM-dd') : null,
        
        // Explicitly exclude new occupant personal data for privacy compliance
        new_occupant_first_name: undefined,
        new_occupant_last_name: undefined,
        new_occupant_phone: undefined,
        new_occupant_email: undefined,
        new_occupant_id_number: undefined,
      };

      console.log('Submitting transition request with data:', submitData);
      console.log('current_role value:', submitData.current_role);

      const response = await fetch('https://altona-village-backend.onrender.com/api/transition/request', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(submitData)
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess(true);
        setError('');
        // Reset form or redirect
        setTimeout(() => {
          window.location.href = '/resident/transition-requests';
        }, 2000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to submit request');
      }
    } catch (error) {
      setError('Network error. Please try again.');
      console.error('Error submitting transition request:', error);
    } finally {
      setLoading(false);
    }
  };

  const DatePicker = ({ value, onChange, placeholder }) => (
    <Popover>
      <PopoverTrigger asChild>
        <Button 
          variant="outline" 
          className="w-full justify-start text-left font-normal"
          aria-label={placeholder || "Select date"}
          title={placeholder || "Select date"}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {value ? format(value, 'PPP') : <span>{placeholder}</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar
          mode="single"
          selected={value}
          onSelect={onChange}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  );

  if (success) {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-green-600">Request Submitted Successfully!</CardTitle>
          <CardDescription>
            Your transition request has been submitted and assigned a reference number. 
            You will be redirected to view your requests shortly.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Property Transition Request</CardTitle>
          <CardDescription>
            Submit a request for property sale, move-out, or tenant change. You only need to provide your own information - the new occupant will register separately.
          </CardDescription>
        </CardHeader>

        {/* Important Information Banner */}
        <CardContent className="border-b bg-blue-50">
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-blue-700">📋 How the Transition Process Works</h3>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-start space-x-2">
                <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">1</span>
                <div>
                  <p className="font-medium text-blue-800">You Submit Request</p>
                  <p className="text-blue-600">Provide your transition details and timeline</p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">2</span>
                <div>
                  <p className="font-medium text-blue-800">New Occupant Registers</p>
                  <p className="text-blue-600">They register independently with your ERF number</p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">3</span>
                <div>
                  <p className="font-medium text-blue-800">Admin Links & Completes</p>
                  <p className="text-blue-600">Admin matches the requests and processes the transition</p>
                </div>
              </div>
            </div>
            <div className="bg-blue-100 border-l-4 border-blue-500 p-3 rounded">
              <p className="text-sm text-blue-700">
                <strong>Privacy Protected:</strong> You don't need to provide the new occupant's personal information. 
                They will register themselves, ensuring their privacy and data accuracy.
              </p>
            </div>
          </div>
        </CardContent>

        {/* Current User Information Display */}
        {userInfo && (
          <CardContent className="border-b">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-blue-600">Your Current Information</h3>
              <p className="text-sm text-gray-600">The information below is pre-populated from your profile. You only need to complete the transition-specific details.</p>
              
              <div className="grid md:grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg">
                {(userInfo.resident || userInfo.owner || userInfo.is_resident || userInfo.is_owner || userInfo.full_name) && (
                  <>
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Current Name</Label>
                      <p className="text-sm">
                        {userInfo.resident?.first_name || userInfo.owner?.first_name || userInfo.full_name || 'Not available'} 
                        {(userInfo.resident?.last_name || userInfo.owner?.last_name) && ` ${userInfo.resident?.last_name || userInfo.owner?.last_name}`}
                      </p>
                    </div>
                    {availableErfs.length > 0 && (
                      <>
                        <div>
                          <Label className="text-sm font-medium text-gray-700">Your Properties</Label>
                          {availableErfs.length === 1 ? (
                            <p className="text-sm">ERF {availableErfs[0].erf_number} - {availableErfs[0].street_number} {availableErfs[0].street_name}</p>
                          ) : (
                            <div className="text-sm">
                              {availableErfs.map((property, index) => (
                                <p key={property.erf_number} className={`${property.erf_number === formData.erf_number ? 'font-medium text-blue-600' : 'text-gray-600'}`}>
                                  ERF {property.erf_number} - {property.street_number} {property.street_name}
                                  {property.erf_number === formData.erf_number && ' (Selected for this request)'}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      </>
                    )}
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Phone Number</Label>
                      <p className="text-sm">{userInfo.resident?.phone_number || userInfo.owner?.phone_number || userInfo.phone || 'Not available'}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Intercom Code</Label>
                      <p className="text-sm">{userInfo.resident?.intercom_code || userInfo.owner?.intercom_code || userInfo.intercom_code || 'Not available'}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-gray-700">Role Type</Label>
                      <p className="text-sm">
                        {(userInfo.resident && userInfo.owner) || (userInfo.is_resident && userInfo.is_owner) ? 'Owner-Resident' : 
                         userInfo.owner || userInfo.is_owner ? 'Property Owner' : 'Tenant'}
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </CardContent>
        )}

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600">{error}</p>
              </div>
            )}

            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Basic Information</h3>
              <p className="text-sm text-gray-600">This information is automatically populated from your profile to prevent errors.</p>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="erf_number">ERF Number *</Label>
                  {availableErfs.length > 1 ? (
                    // Multiple properties - show dropdown
                    <div>
                      <Select 
                        value={formData.erf_number} 
                        onValueChange={(value) => handleInputChange('erf_number', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select your property" />
                        </SelectTrigger>
                        <SelectContent>
                          {availableErfs.map((property) => (
                            <SelectItem key={property.erf_number} value={property.erf_number}>
                              ERF {property.erf_number} - {property.street_number} {property.street_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-blue-600 mt-1">🏠 Select which property this request is for</p>
                    </div>
                  ) : (
                    // Single property or URL parameter - show disabled input
                    <div>
                      <Input
                        id="erf_number"
                        value={formData.erf_number}
                        readOnly
                        disabled
                        className="bg-gray-100 text-gray-600"
                        title="This field is auto-populated from your profile"
                      />
                      <p className="text-xs text-gray-500 mt-1">📍 Auto-filled from your profile</p>
                    </div>
                  )}
                </div>
                
                <div>
                  <Label htmlFor="request_type">Request Type *</Label>
                  <Select value={formData.request_type} onValueChange={(value) => handleInputChange('request_type', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select request type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="owner_sale">Owner Sale - Selling the property</SelectItem>
                      <SelectItem value="tenant_moveout">Tenant Move-Out - Leaving rental property</SelectItem>
                      <SelectItem value="owner_moving">Owner Moving - Will rent out property</SelectItem>
                      <SelectItem value="other">Other - Please specify</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="new_occupant_type">Future Residency Status *</Label>
                  <Select value={formData.new_occupant_type} onValueChange={(value) => handleInputChange('new_occupant_type', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select new occupant type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="resident">Resident Only (Tenant/Renter)</SelectItem>
                      <SelectItem value="owner">Owner Only (Property Owner)</SelectItem>
                      <SelectItem value="owner_resident">Owner-Resident (Owner who lives there)</SelectItem>
                      <SelectItem value="terminated">Terminated/Exiting Estate (No future status)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-1">
                    🎯 What type of access should the new occupant have?<br/>
                    ⚠️ <strong>Terminated/Exiting:</strong> Use this if you're leaving the estate entirely with no future status
                  </p>
                </div>
              </div>

                <div>
                <Label htmlFor="current_role">Current Role *</Label>
                <div className="relative">
                  <Input
                    id="current_role"
                    value={formData.current_role === 'owner' ? 'Property Owner' : 
                           formData.current_role === 'tenant' ? 'Tenant' : 
                           formData.current_role === 'owner_resident' ? 'Owner-Resident' : 
                           formData.current_role || 'Loading...'}
                    readOnly
                    disabled
                    className="bg-gray-100 text-gray-600"
                    title="This field is auto-populated from your profile"
                  />
                  <p className="text-xs text-gray-500 mt-1">👤 Auto-filled from your profile</p>
                  {!formData.current_role && (
                    <p className="text-xs text-red-500 mt-1">⚠️ Role not detected - please refresh the page</p>
                  )}
                </div>
              </div>
            </div>

            {/* Timeline Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Timeline Information</h3>
              
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>Intended Move-Out Date</Label>
                  <DatePicker
                    value={formData.intended_moveout_date}
                    onChange={(date) => handleDateChange('intended_moveout_date', date)}
                    placeholder="Select move-out date"
                  />
                </div>
                
                <div>
                  <Label htmlFor="notice_period">Notice Period Given</Label>
                  <Input
                    id="notice_period"
                    value={formData.notice_period}
                    onChange={(e) => handleInputChange('notice_period', e.target.value)}
                    placeholder="e.g., 30 days, 60 days"
                  />
                </div>
              </div>

              {formData.request_type === 'owner_sale' && (
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>Property Transfer Date</Label>
                    <DatePicker
                      value={formData.property_transfer_date}
                      onChange={(date) => handleDateChange('property_transfer_date', date)}
                      placeholder="Select transfer date"
                    />
                  </div>
                  
                  <div>
                    <Label>New Occupant Move-In Date (if known)</Label>
                    <DatePicker
                      value={formData.new_occupant_movein_date}
                      onChange={(date) => handleDateChange('new_occupant_movein_date', date)}
                      placeholder="Select move-in date"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Conditional sections based on request type */}
            {formData.request_type === 'owner_sale' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Sale Details</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="sale_agreement_signed"
                      checked={formData.sale_agreement_signed}
                      onCheckedChange={(checked) => handleInputChange('sale_agreement_signed', checked)}
                    />
                    <Label htmlFor="sale_agreement_signed">Sale agreement signed</Label>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="transfer_attorney">Transfer Attorney</Label>
                      <Input
                        id="transfer_attorney"
                        value={formData.transfer_attorney}
                        onChange={(e) => handleInputChange('transfer_attorney', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label>Expected Transfer Date</Label>
                      <DatePicker
                        value={formData.expected_transfer_date}
                        onChange={(date) => handleDateChange('expected_transfer_date', date)}
                        placeholder="Select expected date"
                      />
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="new_owner_details_known"
                      checked={formData.new_owner_details_known}
                      onCheckedChange={(checked) => handleInputChange('new_owner_details_known', checked)}
                    />
                    <Label htmlFor="new_owner_details_known">New owner details are known</Label>
                  </div>
                </div>
              </div>
            )}

            {formData.request_type === 'tenant_moveout' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Tenant Move-Out Details</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>Lease End Date</Label>
                    <DatePicker
                      value={formData.lease_end_date}
                      onChange={(date) => handleDateChange('lease_end_date', date)}
                      placeholder="Select lease end date"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="moveout_reason">Reason for Leaving</Label>
                    <Select value={formData.moveout_reason} onValueChange={(value) => handleInputChange('moveout_reason', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select reason" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="lease_expiry">Lease expiry</SelectItem>
                        <SelectItem value="early_termination">Early termination</SelectItem>
                        <SelectItem value="owner_reclaim">Owner reclaiming property</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {formData.moveout_reason === 'other' && (
                  <div>
                    <Label htmlFor="moveout_reason_other">Please specify reason</Label>
                    <Input
                      id="moveout_reason_other"
                      value={formData.moveout_reason_other}
                      onChange={(e) => handleInputChange('moveout_reason_other', e.target.value)}
                    />
                  </div>
                )}
                
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="deposit_return_required"
                    checked={formData.deposit_return_required}
                    onCheckedChange={(checked) => handleInputChange('deposit_return_required', checked)}
                  />
                  <Label htmlFor="deposit_return_required">Deposit return required</Label>
                </div>
              </div>
            )}

            {formData.request_type === 'owner_moving' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Owner Moving Details</h3>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="property_management_company">Property Management Company</Label>
                    <Input
                      id="property_management_company"
                      value={formData.property_management_company}
                      onChange={(e) => handleInputChange('property_management_company', e.target.value)}
                    />
                  </div>
                  
                  <div>
                    <Label>Rental Start Date</Label>
                    <DatePicker
                      value={formData.rental_start_date}
                      onChange={(date) => handleDateChange('rental_start_date', date)}
                      placeholder="Select rental start date"
                    />
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="new_tenant_selected"
                    checked={formData.new_tenant_selected}
                    onCheckedChange={(checked) => handleInputChange('new_tenant_selected', checked)}
                  />
                  <Label htmlFor="new_tenant_selected">New tenant already selected</Label>
                </div>
              </div>
            )}

            {/* Community Services */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Community Access & Services</h3>
              <p className="text-sm text-gray-600">Select services that need to be transferred or cancelled:</p>
              
              <div className="grid md:grid-cols-2 gap-2">
                {[
                  { key: 'gate_access_transfer', label: 'Gate access codes' },
                  { key: 'intercom_access_transfer', label: 'Intercom system access' },
                  { key: 'vehicle_registration_transfer', label: 'Vehicle registrations' },
                  { key: 'visitor_access_transfer', label: 'Visitor access permissions' },
                  { key: 'community_notifications_transfer', label: 'Community notifications' }
                ].map(({ key, label }) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Checkbox
                      id={key}
                      checked={formData[key]}
                      onCheckedChange={(checked) => handleInputChange(key, checked)}
                    />
                    <Label htmlFor={key}>{label}</Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Outstanding Matters */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Outstanding Community Matters</h3>
              
              <div className="grid md:grid-cols-2 gap-2">
                {[
                  { key: 'unpaid_levies', label: 'Unpaid levies/fees' },
                  { key: 'pending_maintenance', label: 'Pending maintenance requests' },
                  { key: 'community_violations', label: 'Community violations' }
                ].map(({ key, label }) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Checkbox
                      id={key}
                      checked={formData[key]}
                      onCheckedChange={(checked) => handleInputChange(key, checked)}
                    />
                    <Label htmlFor={key}>{label}</Label>
                  </div>
                ))}
              </div>
              
              <div>
                <Label htmlFor="outstanding_matters_other">Other outstanding matters</Label>
                <Textarea
                  id="outstanding_matters_other"
                  value={formData.outstanding_matters_other}
                  onChange={(e) => handleInputChange('outstanding_matters_other', e.target.value)}
                  rows="3"
                />
              </div>
            </div>

            {/* Current User Vehicle Information */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold">Your Current Vehicles</h3>
                  <p className="text-sm text-gray-600">These vehicles are registered under your name and will be transferred during the transition</p>
                </div>
              </div>
              
              {formData.vehicles.length > 0 ? (
                <div className="space-y-3">
                  {formData.vehicles.map((vehicle, index) => (
                    <div key={index} className="border border-blue-200 bg-blue-50 p-4 rounded-md">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium text-blue-800">Vehicle {index + 1}</h4>
                        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded">From your profile</span>
                      </div>
                      
                      <div className="grid md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <Label className="text-xs text-gray-600">Make</Label>
                          <p className="font-medium">{vehicle.vehicle_make || 'Not specified'}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-600">Model</Label>
                          <p className="font-medium">{vehicle.vehicle_model || 'Not specified'}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-600">License Plate</Label>
                          <p className="font-medium">{vehicle.license_plate || 'Not specified'}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-600">Color</Label>
                          <p className="font-medium">{vehicle.color || 'Not specified'}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <p>No vehicles found in your profile</p>
                  <p className="text-sm">You can add vehicles in your Profile Management section</p>
                </div>
              )}
            </div>

            {/* Special Instructions */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Transition Information</h3>
              <p className="text-sm text-gray-600">Provide details about your transition that will help the admin process your request.</p>
              
              <div>
                <Label htmlFor="access_handover_requirements">Access Handover Requirements</Label>
                <Textarea
                  id="access_handover_requirements"
                  value={formData.access_handover_requirements}
                  onChange={(e) => handleInputChange('access_handover_requirements', e.target.value)}
                  rows="3"
                  placeholder="Special requirements for handing over keys, remotes, access cards, etc."
                />
              </div>
              
              <div>
                <Label htmlFor="property_condition_notes">Property Condition Notes</Label>
                <Textarea
                  id="property_condition_notes"
                  value={formData.property_condition_notes}
                  onChange={(e) => handleInputChange('property_condition_notes', e.target.value)}
                  rows="3"
                  placeholder="Any notes about the current condition of the property"
                />
              </div>
              
              <div>
                <Label htmlFor="community_introduction_needs">Community Introduction Needs</Label>
                <Textarea
                  id="community_introduction_needs"
                  value={formData.community_introduction_needs}
                  onChange={(e) => handleInputChange('community_introduction_needs', e.target.value)}
                  rows="3"
                  placeholder="Any special needs for introducing new occupants to the community"
                />
              </div>
            </div>

            {/* Acknowledgments */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Acknowledgments</h3>
              <div className="p-4 bg-gray-50 rounded-md">
                <p className="text-sm text-gray-700 mb-2">By submitting this request, I acknowledge that:</p>
                <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                  <li>I have provided accurate information about my transition timeline</li>
                  <li>I understand the new occupant must register separately with their own information</li>
                  <li>I will coordinate with the new occupant to ensure they register with the correct ERF number</li>
                  <li>I will provide at least 30 days notice for any changes to this timeline</li>
                  <li>Outstanding community fees must be settled before transition</li>
                  <li>I will return all community access devices (remotes, cards, etc.)</li>
                  <li>The admin will link this request with the new occupant's registration to complete the transition</li>
                </ul>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4 pt-6">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => window.history.back()}
                aria-label="Cancel transition request"
                title="Cancel and go back to previous page"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={loading}
                aria-label={loading ? 'Submitting transition request...' : 'Submit transition request'}
                title={loading ? 'Please wait while submitting...' : 'Submit your transition request'}
              >
                {loading ? 'Submitting...' : 'Submit Transition Request'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserTransitionRequest;
