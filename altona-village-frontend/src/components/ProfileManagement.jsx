import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth.jsx';
import { authAPI } from '@/lib/api.js';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { User, Mail, Phone, Shield, Calendar, MapPin } from 'lucide-react';

const ProfileManagement = () => {
  const { user, updateUser } = useAuth();
  const [profile, setProfile] = useState({
    full_name: '',
    email: '',
    phone: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    property_address: '',
    tenant_or_owner: ''
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
      const response = await authAPI.updateProfile(profile);
      setMessage({ type: 'success', text: response.data.message || 'Profile updated successfully' });
      updateUser(response.data.user); // Update auth context with user data
      setProfile(response.data.user); // Update local profile state
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to update profile' 
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
      const response = await authAPI.updateProfile({
        current_password: passwords.current_password,
        password: passwords.new_password // Change key to 'password' to match backend
      });
      setMessage({ type: 'success', text: response.data.message || 'Password changed successfully' });
      setPasswords({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to change password' 
      });
    } finally {
      setLoading(false);
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'resident': return 'bg-green-100 text-green-800';
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
            {user?.role?.toUpperCase()}
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
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="profile">Personal Information</TabsTrigger>
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
