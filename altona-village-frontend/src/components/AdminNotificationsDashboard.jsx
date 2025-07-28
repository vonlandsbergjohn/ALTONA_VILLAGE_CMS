import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Bell, 
  Users, 
  Clock, 
  Download,
  Eye,
  AlertTriangle,
  CheckCircle,
  Phone,
  Car
} from 'lucide-react';

const AdminNotificationsDashboard = () => {
  const [changes, setChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalChanges: 0,
    usersAffected: 0,
    phoneChanges: 0,
    vehicleChanges: 0
  });

  useEffect(() => {
    fetchChanges();
  }, []);

  const fetchChanges = async () => {
    try {
      setLoading(true);
      const response = await adminAPI.getGateRegisterChanges();
      console.log('Fetched response:', response);
      
      // The API returns {success, data, count, total_changes}
      // But it's wrapped in Axios response, so we need response.data
      const apiResponse = response.data || response;
      console.log('API Response:', apiResponse);
      
      const gateRegisterData = Array.isArray(apiResponse) ? apiResponse : apiResponse.data || [];
      const totalChanges = apiResponse.total_changes || 0;
      
      console.log('Gate register data:', gateRegisterData);
      
      // Convert gate register entries to individual change records
      const changesData = [];
      gateRegisterData.forEach(entry => {
        if (entry.changes_info) {
          Object.entries(entry.changes_info).forEach(([fieldName, changeInfo]) => {
            changesData.push({
              id: `${entry.user_id}-${fieldName}`,
              user_id: entry.user_id,
              full_name: `${entry.first_name} ${entry.last_name}`.trim(),
              email: entry.email,
              field_name: fieldName,
              old_value: changeInfo.old_value,
              new_value: changeInfo.new_value,
              change_timestamp: changeInfo.timestamp,
              admin_reviewed: false
            });
          });
        }
      });
      
      console.log('Processed changes data:', changesData);
      setChanges(changesData);
      
      // Calculate stats
      const uniqueUsers = new Set(changesData.map(change => change.user_id)).size;
      const phoneChanges = changesData.filter(change => 
        change.field_name === 'cellphone_number' || change.field_name === 'phone_number' || change.field_name === 'emergency_contact'
      ).length;
      const vehicleChanges = changesData.filter(change => 
        change.field_name === 'vehicle_registration' || change.field_name === 'vehicle_make' || change.field_name === 'vehicle_model'
      ).length;
      
      setStats({
        totalChanges: changesData.length,
        usersAffected: uniqueUsers,
        phoneChanges,
        vehicleChanges
      });
      
      setError(null);
    } catch (err) {
      console.error('Error fetching changes:', err);
      setError('Failed to load notification data');
    } finally {
      setLoading(false);
    }
  };

  const exportChanges = async () => {
    try {
      console.log('Starting export...');
      const response = await adminAPI.exportGateRegisterChanges();
      console.log('Export response received:', response);
      console.log('Response type:', typeof response);
      console.log('Response constructor:', response.constructor.name);
      console.log('Response instanceof Blob:', response instanceof Blob);
      
      if (response instanceof Blob) {
        console.log('Blob size:', response.size);
        console.log('Blob type:', response.type);
      }
      
      // Check if response is actually a blob (successful export)
      if (response instanceof Blob && response.size > 0) {
        const url = window.URL.createObjectURL(response);
        const a = document.createElement('a');
        a.href = url;
        a.download = `gate_register_changes_${new Date().toISOString().split('T')[0]}.html`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        // Response is not a proper blob, might be an error response
        console.error('Invalid export response:', response);
        
        // Try to read the response as text to get error message
        if (response instanceof Blob) {
          const text = await response.text();
          console.error('Blob content:', text);
          try {
            const errorData = JSON.parse(text);
            alert(`Export failed: ${errorData.error || 'Unknown error'}`);
          } catch {
            alert(`Export failed: ${text || 'Invalid response format'}`);
          }
        } else {
          console.error('Response details:', {
            type: typeof response,
            constructor: response?.constructor?.name,
            keys: Object.keys(response || {}),
            value: response
          });
          alert('Export failed: Invalid response format - check console for details');
        }
      }
    } catch (err) {
      console.error('Export failed:', err);
      console.error('Error details:', err.response?.data || err.message);
      console.error('Error response status:', err.response?.status);
      console.error('Error response headers:', err.response?.headers);
      
      // Handle different error types
      if (err.response?.status === 404) {
        alert('No pending changes found to export');
      } else if (err.response?.status === 401) {
        alert('Authentication failed. Please refresh and try again.');
      } else if (err.response?.data?.error) {
        alert(`Export failed: ${err.response.data.error}`);
      } else {
        alert(`Export failed: ${err.message || 'Unknown error'} - Status: ${err.response?.status || 'N/A'}`);
      }
    }
  };

  const markAsProcessed = async (changeId) => {
    try {
      await adminAPI.markChangeProcessed(changeId);
      fetchChanges(); // Reload data
    } catch (err) {
      console.error('Error marking as processed:', err);
      alert('Failed to mark change as processed');
    }
  };

  const formatChangeValue = (change) => {
    if (change.field_name === 'phone_number' || change.field_name === 'emergency_contact') {
      return (
        <div className="flex items-center gap-2">
          <Phone className="h-4 w-4 text-blue-500" />
          <span className="bg-red-100 px-2 py-1 rounded text-red-800">
            {change.new_value || 'Not provided'}
          </span>
        </div>
      );
    }
    
    if (change.field_name.includes('vehicle')) {
      return (
        <div className="flex items-center gap-2">
          <Car className="h-4 w-4 text-green-500" />
          <span className="bg-red-100 px-2 py-1 rounded text-red-800">
            {change.new_value || 'Not provided'}
          </span>
        </div>
      );
    }
    
    return (
      <span className="bg-red-100 px-2 py-1 rounded text-red-800">
        {change.new_value || 'Not provided'}
      </span>
    );
  };

  const groupedChanges = changes.reduce((groups, change) => {
    const key = `${change.user_id}-${change.full_name}`;
    if (!groups[key]) {
      groups[key] = {
        user_id: change.user_id,
        full_name: change.full_name,
        email: change.email,
        changes: []
      };
    }
    groups[key].changes.push(change);
    return groups;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="h-6 w-6 text-blue-600" />
            Admin Notifications Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Track and manage resident data changes for external system synchronization
          </p>
        </div>
        <Button onClick={exportChanges} className="flex items-center gap-2">
          <Download className="h-4 w-4" />
          Export Changes
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Changes</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalChanges}</div>
            <p className="text-xs text-muted-foreground">Pending review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Users Affected</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.usersAffected}</div>
            <p className="text-xs text-muted-foreground">Residents with changes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Phone Changes</CardTitle>
            <Phone className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.phoneChanges}</div>
            <p className="text-xs text-muted-foreground">For gate system</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vehicle Changes</CardTitle>
            <Car className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.vehicleChanges}</div>
            <p className="text-xs text-muted-foreground">For camera system</p>
          </CardContent>
        </Card>
      </div>

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-800">
              <AlertTriangle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Changes by User */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Changes by User</h2>
        
        {Object.keys(groupedChanges).length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center text-gray-500">
                <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                <p>No pending changes found</p>
                <p className="text-sm">All resident data is up to date</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          Object.values(groupedChanges).map((userGroup) => (
            <Card key={userGroup.user_id} className="border-l-4 border-l-orange-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{userGroup.full_name}</CardTitle>
                    <CardDescription>
                      User ID: {userGroup.user_id} • {userGroup.email}
                    </CardDescription>
                  </div>
                  <Badge variant="secondary">
                    {userGroup.changes.length} change{userGroup.changes.length !== 1 ? 's' : ''}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {userGroup.changes.map((change, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-gray-900">
                              {change.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                            <Clock className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-500">
                              {new Date(change.change_timestamp).toLocaleString()}
                            </span>
                          </div>
                          <div className="space-y-1">
                            <div>
                              <span className="text-sm text-gray-600">Old: </span>
                              <span className="bg-gray-200 px-2 py-1 rounded text-gray-800">
                                {change.old_value || 'Not set'}
                              </span>
                            </div>
                            <div>
                              <span className="text-sm text-gray-600">New: </span>
                              {formatChangeValue(change)}
                            </div>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => markAsProcessed(change.id)}
                          className="ml-4"
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Mark Processed
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default AdminNotificationsDashboard;
