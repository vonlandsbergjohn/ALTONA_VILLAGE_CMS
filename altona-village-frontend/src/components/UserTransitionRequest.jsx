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

const UserTransitionRequest = () => {
  const [formData, setFormData] = useState({
    erf_number: '',
    request_type: '',
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
    
    // New occupant info
    new_occupant_type: '',
    new_occupant_first_name: '',
    new_occupant_last_name: '',
    new_occupant_phone: '',
    new_occupant_email: '',
    new_occupant_id_number: '',
    new_occupant_adults: 0,
    new_occupant_children: 0,
    new_occupant_pets: 0,
    
    // Special instructions
    access_handover_requirements: '',
    property_condition_notes: '',
    community_introduction_needs: '',
    
    // Vehicles
    vehicles: []
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/users/profile', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserInfo(data);
        
        // Pre-fill ERF number if available
        if (data.resident?.erf_number || data.owner?.erf_number) {
          setFormData(prev => ({
            ...prev,
            erf_number: data.resident?.erf_number || data.owner?.erf_number
          }));
        }
      }
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
  };

  const handleInputChange = (field, value) => {
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
      vehicles: [...prev.vehicles, { vehicle_make: '', vehicle_model: '', license_plate: '' }]
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
      
      // Format dates for submission
      const submitData = {
        ...formData,
        intended_moveout_date: formData.intended_moveout_date ? format(formData.intended_moveout_date, 'yyyy-MM-dd') : null,
        property_transfer_date: formData.property_transfer_date ? format(formData.property_transfer_date, 'yyyy-MM-dd') : null,
        new_occupant_movein_date: formData.new_occupant_movein_date ? format(formData.new_occupant_movein_date, 'yyyy-MM-dd') : null,
        expected_transfer_date: formData.expected_transfer_date ? format(formData.expected_transfer_date, 'yyyy-MM-dd') : null,
        lease_end_date: formData.lease_end_date ? format(formData.lease_end_date, 'yyyy-MM-dd') : null,
        rental_start_date: formData.rental_start_date ? format(formData.rental_start_date, 'yyyy-MM-dd') : null,
        // Clean up integer fields - convert empty strings to null
        new_occupant_adults: formData.new_occupant_adults === '' ? null : parseInt(formData.new_occupant_adults) || 0,
        new_occupant_children: formData.new_occupant_children === '' ? null : parseInt(formData.new_occupant_children) || 0,
        new_occupant_pets: formData.new_occupant_pets === '' ? null : parseInt(formData.new_occupant_pets) || 0,
      };

      const response = await fetch('/api/transition/request', {
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
        <Button variant="outline" className="w-full justify-start text-left font-normal">
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
            Submit a request for property sale, move-out, or tenant change. Please provide as much detail as possible to help us process your request efficiently.
          </CardDescription>
        </CardHeader>
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
              
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="erf_number">ERF Number *</Label>
                  <Input
                    id="erf_number"
                    value={formData.erf_number}
                    onChange={(e) => handleInputChange('erf_number', e.target.value)}
                    required
                  />
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
              </div>

              <div>
                <Label htmlFor="current_role">Current Role *</Label>
                <Select value={formData.current_role} onValueChange={(value) => handleInputChange('current_role', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your current role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="owner">Property Owner</SelectItem>
                    <SelectItem value="tenant">Tenant</SelectItem>
                    <SelectItem value="owner_resident">Owner-Resident</SelectItem>
                  </SelectContent>
                </Select>
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
                    <Label>New Occupant Move-In Date</Label>
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

            {/* Vehicle Information */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Vehicle Information</h3>
                <Button type="button" onClick={addVehicle} variant="outline" size="sm">
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Vehicle
                </Button>
              </div>
              
              {formData.vehicles.map((vehicle, index) => (
                <div key={index} className="border p-4 rounded-md space-y-4">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">Vehicle {index + 1}</h4>
                    <Button
                      type="button"
                      onClick={() => removeVehicle(index)}
                      variant="outline"
                      size="sm"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor={`vehicle_make_${index}`}>Make</Label>
                      <Input
                        id={`vehicle_make_${index}`}
                        value={vehicle.vehicle_make}
                        onChange={(e) => updateVehicle(index, 'vehicle_make', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor={`vehicle_model_${index}`}>Model</Label>
                      <Input
                        id={`vehicle_model_${index}`}
                        value={vehicle.vehicle_model}
                        onChange={(e) => updateVehicle(index, 'vehicle_model', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor={`license_plate_${index}`}>License Plate</Label>
                      <Input
                        id={`license_plate_${index}`}
                        value={vehicle.license_plate}
                        onChange={(e) => updateVehicle(index, 'license_plate', e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* New Occupant Information */}
            {(formData.request_type === 'owner_sale' || formData.request_type === 'owner_moving') && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">New Occupant Information (if known)</h3>
                
                <div>
                  <Label htmlFor="new_occupant_type">New Occupant Type</Label>
                  <Select value={formData.new_occupant_type} onValueChange={(value) => handleInputChange('new_occupant_type', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="new_owner">New Owner (purchase)</SelectItem>
                      <SelectItem value="new_tenant">New Tenant (rental)</SelectItem>
                      <SelectItem value="unknown">Unknown at this time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {formData.new_occupant_type !== 'unknown' && (
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="new_occupant_first_name">First Name</Label>
                      <Input
                        id="new_occupant_first_name"
                        value={formData.new_occupant_first_name}
                        onChange={(e) => handleInputChange('new_occupant_first_name', e.target.value)}
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="new_occupant_last_name">Last Name</Label>
                      <Input
                        id="new_occupant_last_name"
                        value={formData.new_occupant_last_name}
                        onChange={(e) => handleInputChange('new_occupant_last_name', e.target.value)}
                        required
                      />
                    </div>
                  </div>
                )}
                
                {formData.new_occupant_type !== 'unknown' && (
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="new_occupant_phone">Phone Number</Label>
                      <Input
                        id="new_occupant_phone"
                        value={formData.new_occupant_phone}
                        onChange={(e) => handleInputChange('new_occupant_phone', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="new_occupant_email">Email Address</Label>
                      <Input
                        id="new_occupant_email"
                        type="email"
                        value={formData.new_occupant_email}
                        onChange={(e) => handleInputChange('new_occupant_email', e.target.value)}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="new_occupant_id_number">ID Number</Label>
                      <Input
                        id="new_occupant_id_number"
                        value={formData.new_occupant_id_number}
                        onChange={(e) => handleInputChange('new_occupant_id_number', e.target.value)}
                        placeholder="For user account creation"
                      />
                    </div>
                  </div>
                )}
                
                {formData.new_occupant_type !== 'unknown' && (
                  <div>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <Label htmlFor="new_occupant_adults">Adults</Label>
                        <Input
                          id="new_occupant_adults"
                          type="number"
                          min="0"
                          value={formData.new_occupant_adults}
                          onChange={(e) => handleInputChange('new_occupant_adults', e.target.value)}
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="new_occupant_children">Children</Label>
                        <Input
                          id="new_occupant_children"
                          type="number"
                          min="0"
                          value={formData.new_occupant_children}
                          onChange={(e) => handleInputChange('new_occupant_children', e.target.value)}
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="new_occupant_pets">Pets</Label>
                        <Input
                          id="new_occupant_pets"
                          type="number"
                          min="0"
                          value={formData.new_occupant_pets}
                          onChange={(e) => handleInputChange('new_occupant_pets', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Special Instructions */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Special Instructions</h3>
              
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
                  <li>I understand my community access will be updated according to the transition</li>
                  <li>I will provide at least 30 days notice for any changes to this timeline</li>
                  <li>I will coordinate with property management for smooth handover</li>
                  <li>Outstanding community fees must be settled before transition</li>
                  <li>I will return all community access devices (remotes, cards, etc.)</li>
                </ul>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4 pt-6">
              <Button type="button" variant="outline" onClick={() => window.history.back()}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
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
