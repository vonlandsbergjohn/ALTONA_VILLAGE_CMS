import { useState, useEffect } from 'react';
import { useAuth, getUserResidencyType } from '@/lib/auth.jsx';
import { authAPI } from '@/lib/api.js';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { User, Mail, Phone, Shield, Calendar, MapPin, KeyRound, Home, Building2, ExternalLink } from 'lucide-react';

const ProfileManagement = () => {
  const { user, updateProfile: updateUserProfile, refreshUser } = useAuth();
  const [profile, setProfile] = useState({
    full_name: '',
    email: '',
    phone: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    property_address: '',
    tenant_or_owner: '',
    intercom_code: '',
    erf_number: '',
    total_erfs: 0,
    erfs: []
  });
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      setProfile(response.data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load profile information' });
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      // Exclude admin-only fields from the update
      const { erf_number, intercom_code, ...updatableProfile } = profile;
      
      const result = await updateUserProfile(updatableProfile);
      
      if (result.success) {
        setMessage({ type: 'success', text: 'Profile updated successfully' });
        
        // Refresh the profile form data from the server
        try {
          const response = await authAPI.getProfile();
          
          if (response.data) {
            setProfile(response.data);
            
            // Also refresh the user context
            await refreshUser();
          }
        } catch (refreshError) {
          // Still show success since the update worked
        }
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      
      setMessage({ 
        type: 'error', 
        text: error.message || 'Failed to update profile' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    if (passwords.new_password !== passwords.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      setLoading(false);
      return;
    }

    if (passwords.new_password.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters long' });
      setLoading(false);
      return;
    }

    try {
      const result = await updateUserProfile({
        current_password: passwords.current_password,
        password: passwords.new_password // Change key to 'password' to match backend
      });
      
      if (result.success) {
        setMessage({ type: 'success', text: 'Password changed successfully' });
        setPasswords({
          current_password: '',
          new_password: '',
          confirm_password: ''
        });
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.message || 'Failed to change password' 
      });
    } finally {
      setLoading(false);
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'owner': return 'bg-blue-100 text-blue-800';
      case 'resident': return 'bg-green-100 text-green-800';
      case 'owner-resident': return 'bg-purple-100 text-purple-800';
      case 'unknown': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'owner': return <Building2 className="w-3 h-3" />;
      case 'resident': return <Home className="w-3 h-3" />;
      case 'owner-resident': return <Building2 className="w-3 h-3" />;
      case 'unknown': return <User className="w-3 h-3" />;
      default: return <Home className="w-3 h-3" />;
    }
  };

  const handleErfTransitionRequest = (erfNumber, userId) => {
    // This will link to the transition request page for the specific ERF
    // The userId parameter ensures the transition is linked to the correct account
    window.location.href = `/transition-requests?erf=${erfNumber}&user_id=${userId}`;
  };

  const getRoleColor = (role) => {
    // Get the actual residency type for coloring
    const residencyType = getUserResidencyType(user);
    
    switch (residencyType) {
      case 'Admin': return 'bg-red-100 text-red-800';
      case 'Property Owner': return 'bg-blue-100 text-blue-800';
      case 'Resident': return 'bg-green-100 text-green-800';
      case 'Owner-Resident': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'suspended': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Profile Management</h1>
          <p className="text-gray-600">Manage your personal information and account settings</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className={getRoleColor(user?.role)}>
            <Shield className="w-3 h-3 mr-1" />
            {getUserResidencyType(user)}
          </Badge>
          <Badge className={getStatusColor(user?.status)}>
            {user?.status?.toUpperCase()}
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

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="profile">Personal Information</TabsTrigger>
          <TabsTrigger value="properties">My Properties ({profile.total_erfs || 0})</TabsTrigger>
          <TabsTrigger value="security">Security Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <User className="w-5 h-5 mr-2" />
                Personal Information
              </CardTitle>
              <CardDescription>
                Update your personal details and contact information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileUpdate} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      value={profile.full_name}
                      onChange={(e) => setProfile({...profile, full_name: e.target.value})}
                      placeholder="Enter your full name"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        value={profile.email}
                        onChange={(e) => setProfile({...profile, email: e.target.value})}
                        placeholder="your.email@example.com"
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="phone"
                        value={profile.phone}
                        onChange={(e) => setProfile({...profile, phone: e.target.value})}
                        placeholder="076 123 4567"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tenant_or_owner">Residency Type</Label>
                    <select
                      id="tenant_or_owner"
                      value={profile.tenant_or_owner}
                      onChange={(e) => setProfile({...profile, tenant_or_owner: e.target.value})}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="">Select type</option>
                      <option value="owner">Property Owner</option>
                      <option value="tenant">Tenant</option>
                      <option value="owner-resident">Owner-Resident</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="property_address">Property Address</Label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      id="property_address"
                      value={profile.property_address}
                      onChange={(e) => setProfile({...profile, property_address: e.target.value})}
                      placeholder="Your property address in Altona Village"
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="erf_number">Primary ERF Number</Label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="erf_number"
                        value={profile.erf_number}
                        readOnly
                        disabled
                        placeholder="Admin managed"
                        className="pl-10 bg-gray-50 text-gray-600 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-gray-500">
                      ℹ️ Primary property identifier - managed by administration
                      {profile.total_erfs > 1 && (
                        <span className="text-blue-600">
                          <br />📍 You have {profile.total_erfs} total properties - view all in "My Properties" tab
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="intercom_code">Intercom Code</Label>
                    <div className="relative">
                      <KeyRound className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="intercom_code"
                        value={profile.intercom_code}
                        readOnly
                        disabled
                        placeholder="Admin managed"
                        className="pl-10 bg-gray-50 text-gray-600 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-gray-500">
                      ⚠️ This code is managed by administration and cannot be changed by users
                    </p>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="text-lg font-medium">Emergency Contact</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="emergency_contact_name">Emergency Contact Name</Label>
                      <Input
                        id="emergency_contact_name"
                        value={profile.emergency_contact_name}
                        onChange={(e) => setProfile({...profile, emergency_contact_name: e.target.value})}
                        placeholder="Contact person's name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="emergency_contact_phone">Emergency Contact Phone</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="emergency_contact_phone"
                          value={profile.emergency_contact_phone}
                          onChange={(e) => setProfile({...profile, emergency_contact_phone: e.target.value})}
                          placeholder="076 123 4567"
                          className="pl-10"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Updating...' : 'Update Profile'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="properties" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Building2 className="w-5 h-5 mr-2" />
                My Properties ({profile.total_erfs || 0} ERF{(profile.total_erfs || 0) !== 1 ? 's' : ''})
              </CardTitle>
              <CardDescription>
                View and manage all properties associated with your account
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {profile.erfs && profile.erfs.length > 0 ? (
                <div className="grid gap-4">
                  {profile.erfs.map((erf, index) => (
                    <Card key={`${erf.user_id}-${erf.erf_number}`} className={`border-l-4 ${
                      erf.is_current_account 
                        ? 'border-l-blue-500 bg-blue-50' 
                        : erf.status === 'active' 
                          ? 'border-l-green-500' 
                          : 'border-l-yellow-500'
                    }`}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="text-lg font-semibold">ERF {erf.erf_number || 'Unknown'}</h3>
                              <Badge className={getTypeColor(erf.type)}>
                                {getTypeIcon(erf.type)}
                                <span className="ml-1">{(erf.type || 'Unknown').replace('-', ' ').toUpperCase()}</span>
                              </Badge>
                              <Badge className={getStatusColor(erf.status)}>
                                {(erf.status || 'Unknown').toUpperCase()}
                              </Badge>
                              {erf.is_current_account && (
                                <Badge variant="outline" className="bg-blue-100 text-blue-800 border-blue-300">
                                  Current Session
                                </Badge>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                              <div>
                                <Label className="text-gray-500">Property Address</Label>
                                <p className="flex items-center">
                                  <MapPin className="w-4 h-4 mr-1 text-gray-400" />
                                  {erf.full_address || 'Address not available'}
                                </p>
                              </div>
                              
                              <div>
                                <Label className="text-gray-500">Street Address</Label>
                                <p>{erf.street_number && erf.street_name 
                                  ? `${erf.street_number} ${erf.street_name}` 
                                  : 'Not specified'}
                                </p>
                              </div>

                              <div>
                                <Label className="text-gray-500">Owner/Resident</Label>
                                <p>{erf.full_name || 'Name not available'}</p>
                              </div>

                              <div>
                                <Label className="text-gray-500">Intercom Code</Label>
                                <p className="flex items-center">
                                  <KeyRound className="w-4 h-4 mr-1 text-gray-400" />
                                  {erf.intercom_code || 'Not available'}
                                </p>
                              </div>

                              {erf.phone_number && (
                                <div>
                                  <Label className="text-gray-500">Phone</Label>
                                  <p className="flex items-center">
                                    <Phone className="w-4 h-4 mr-1 text-gray-400" />
                                    {erf.phone_number}
                                  </p>
                                </div>
                              )}

                              {erf.title_deed_number && (
                                <div>
                                  <Label className="text-gray-500">Title Deed</Label>
                                  <p>{erf.title_deed_number}</p>
                                </div>
                              )}
                            </div>

                            {(erf.emergency_contact_name || erf.emergency_contact_number) && (
                              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                                <Label className="text-gray-500 text-sm font-medium">Emergency Contact</Label>
                                <div className="text-sm">
                                  {erf.emergency_contact_name && <p>Name: {erf.emergency_contact_name}</p>}
                                  {erf.emergency_contact_number && (
                                    <p className="flex items-center">
                                      <Phone className="w-3 h-3 mr-1" />
                                      {erf.emergency_contact_number}
                                    </p>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="ml-4 flex flex-col space-y-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => window.open(`/map?erf=${erf.erf_number}`, '_blank')}
                              className="flex items-center"
                            >
                              <MapPin className="w-4 h-4 mr-1" />
                              View on Map
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </Button>
                            
                            {erf.status === 'active' && (
                              <Button
                                size="sm"
                                onClick={() => handleErfTransitionRequest(erf.erf_number, erf.user_id)}
                                className="flex items-center"
                              >
                                <ExternalLink className="w-4 h-4 mr-1" />
                                Transition Request
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium mb-2">No Properties Found</h3>
                  <p>No ERF registrations found for your account.</p>
                  <p className="text-sm mt-2">Contact admin if you believe this is an error.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Change Password
              </CardTitle>
              <CardDescription>
                Update your password to keep your account secure
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordChange} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current_password">Current Password</Label>
                  <Input
                    id="current_password"
                    type="password"
                    value={passwords.current_password}
                    onChange={(e) => setPasswords({...passwords, current_password: e.target.value})}
                    placeholder="Enter your current password"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new_password">New Password</Label>
                  <Input
                    id="new_password"
                    type="password"
                    value={passwords.new_password}
                    onChange={(e) => setPasswords({...passwords, new_password: e.target.value})}
                    placeholder="Enter your new password"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    value={passwords.confirm_password}
                    onChange={(e) => setPasswords({...passwords, confirm_password: e.target.value})}
                    placeholder="Confirm your new password"
                    required
                  />
                </div>
                <div className="flex justify-end">
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Changing...' : 'Change Password'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
              <CardDescription>
                View your account details and registration date
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-500">User ID</Label>
                  <p className="text-sm">{user?.id}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Registration Date</Label>
                  <p className="text-sm flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Account Role</Label>
                  <Badge className={getRoleColor(user?.role)}>
                    {user?.role?.toUpperCase()}
                  </Badge>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Account Status</Label>
                  <Badge className={getStatusColor(user?.status)}>
                    {user?.status?.toUpperCase()}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProfileManagement;
