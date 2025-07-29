import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bell, 
  Users, 
  Clock, 
  Download,
  Eye,
  AlertTriangle,
  CheckCircle,
  Phone,
  Car,
  Info,
  Settings,
  User,
  MapPin
} from 'lucide-react';

const AdminNotificationsDashboard = () => {
  const [changes, setChanges] = useState([]);
  const [criticalChanges, setCriticalChanges] = useState([]);
  const [nonCriticalChanges, setNonCriticalChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('critical');
  const [stats, setStats] = useState({
    totalChanges: 0,
    usersAffected: 0,
    phoneChanges: 0,
    vehicleChanges: 0,
    criticalPending: 0,
    nonCriticalPending: 0
  });

  useEffect(() => {
    fetchChanges();
    fetchStats();
  }, []);

  const fetchChanges = async () => {
    try {
      setLoading(true);
      
      // Fetch both critical and non-critical changes
      const [criticalResponse, nonCriticalResponse] = await Promise.all([
        adminAPI.getCriticalChanges(),
        adminAPI.getNonCriticalChanges()
      ]);
      
      console.log('Critical changes:', criticalResponse);
      console.log('Non-critical changes:', nonCriticalResponse);
      
      setCriticalChanges(criticalResponse.data?.critical_changes || []);
      setNonCriticalChanges(nonCriticalResponse.data?.non_critical_changes || []);
      
      // Legacy: combine for backward compatibility
      const allChanges = [
        ...(criticalResponse.data?.critical_changes || []),
        ...(nonCriticalResponse.data?.non_critical_changes || [])
      ];
      setChanges(allChanges);
      
    } catch (err) {
      console.error('Error fetching changes:', err);
      setError(err.message || 'Failed to load changes');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await adminAPI.getChangeStats();
      const statsData = response.data?.stats || {};
      
      setStats({
        totalChanges: statsData.total_pending || 0,
        criticalPending: statsData.critical_pending || 0,
        nonCriticalPending: statsData.non_critical_pending || 0,
        usersAffected: Object.keys(statsData.by_field_name || {}).length,
        phoneChanges: statsData.by_field_name?.cellphone_number || 0,
        vehicleChanges: (statsData.by_field_name?.vehicle_registration || 0) + 
                       (statsData.by_field_name?.vehicle_registration_2 || 0)
      });
      
    } catch (err) {
      console.error('Error fetching stats:', err);
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
    if (change.field_name === 'cellphone_number' || change.field_name === 'phone_number' || change.field_name === 'emergency_contact') {
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

    // Non-critical changes
    if (change.field_name === 'intercom_code') {
      return (
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-purple-500" />
          <span className="bg-blue-100 px-2 py-1 rounded text-blue-800">
            {change.new_value || 'Not provided'}
          </span>
        </div>
      );
    }

    if (change.field_name === 'full_name') {
      return (
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-indigo-500" />
          <span className="bg-blue-100 px-2 py-1 rounded text-blue-800">
            {change.new_value || 'Not provided'}
          </span>
        </div>
      );
    }

    if (change.field_name === 'property_address') {
      return (
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-emerald-500" />
          <span className="bg-blue-100 px-2 py-1 rounded text-blue-800">
            {change.new_value || 'Not provided'}
          </span>
        </div>
      );
    }
    
    return (
      <div className="flex items-center gap-2">
        <Info className="h-4 w-4 text-gray-500" />
        <span className="bg-blue-100 px-2 py-1 rounded text-blue-800">
          {change.new_value || 'Not provided'}
        </span>
      </div>
    );
  };

  const markAsReviewed = async (changeIds) => {
    try {
      await adminAPI.reviewChanges(changeIds, 'Reviewed by admin');
      fetchChanges(); // Reload data
      fetchStats();   // Update stats
    } catch (err) {
      console.error('Error marking as reviewed:', err);
      alert('Failed to mark changes as reviewed');
    }
  };

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
            <CardTitle className="text-sm font-medium">Critical Changes</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.criticalPending}</div>
            <p className="text-xs text-muted-foreground">Phone & Vehicle Updates</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Non-Critical</CardTitle>
            <Info className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.nonCriticalPending}</div>
            <p className="text-xs text-muted-foreground">Names, Addresses, etc.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Users Affected</CardTitle>
            <Users className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.usersAffected}</div>
            <p className="text-xs text-muted-foreground">Different fields</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabbed Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="critical" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Critical Changes ({stats.criticalPending})
          </TabsTrigger>
          <TabsTrigger value="non-critical" className="flex items-center gap-2">
            <Info className="h-4 w-4" />
            Non-Critical Changes ({stats.nonCriticalPending})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="critical" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                    Critical Changes - Require Immediate Attention
                  </CardTitle>
                  <CardDescription>
                    Phone and vehicle registration changes for external system integration
                  </CardDescription>
                </div>
                <Button 
                  onClick={exportChanges} 
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {criticalChanges.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                  <p>No critical changes pending review</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {criticalChanges.map((change, index) => (
                    <div key={change.id || index} className="border rounded-lg p-4 bg-red-50 border-red-200">
                      <div className="flex justify-between items-start">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="destructive">{change.change_type}</Badge>
                            <span className="font-medium">{change.user_name}</span>
                            <span className="text-sm text-gray-600">ERF: {change.erf_number}</span>
                          </div>
                          <div className="space-y-1">
                            <div className="text-sm text-gray-600">
                              <strong>{change.field_name.replace('_', ' ').toUpperCase()}:</strong>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">
                                {change.old_value || 'None'} →
                              </span>
                              {formatChangeValue(change)}
                            </div>
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(change.change_timestamp).toLocaleString()}
                          </div>
                        </div>
                        <Button
                          onClick={() => markAsReviewed([change.id])}
                          size="sm"
                          variant="outline"
                          className="flex items-center gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          Mark Reviewed
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="non-critical" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Info className="h-5 w-5 text-blue-500" />
                    Non-Critical Changes - General Updates
                  </CardTitle>
                  <CardDescription>
                    Name, address, and other profile changes for record keeping
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => markAsReviewed(nonCriticalChanges.map(c => c.id))}
                    variant="outline"
                    disabled={nonCriticalChanges.length === 0}
                    className="flex items-center gap-2"
                  >
                    <CheckCircle className="h-4 w-4" />
                    Mark All Reviewed
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {nonCriticalChanges.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                  <p>No non-critical changes pending review</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {nonCriticalChanges.map((change, index) => (
                    <div key={change.id || index} className="border rounded-lg p-4 bg-blue-50 border-blue-200">
                      <div className="flex justify-between items-start">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">{change.change_type}</Badge>
                            <span className="font-medium">{change.user_name}</span>
                            <span className="text-sm text-gray-600">ERF: {change.erf_number}</span>
                          </div>
                          <div className="space-y-1">
                            <div className="text-sm text-gray-600">
                              <strong>{change.field_name.replace('_', ' ').toUpperCase()}:</strong>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">
                                {change.old_value || 'None'} →
                              </span>
                              {formatChangeValue(change)}
                            </div>
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(change.change_timestamp).toLocaleString()}
                          </div>
                        </div>
                        <Button
                          onClick={() => markAsReviewed([change.id])}
                          size="sm"
                          variant="outline"
                          className="flex items-center gap-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          Mark Reviewed
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

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
    </div>
  );
};

export default AdminNotificationsDashboard;
