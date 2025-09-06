import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import GateRegisterChanges from './GateRegisterChanges';
import { 
  Users, 
  Building, 
  Car, 
  MessageSquare, 
  Clock, 
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Bell,
  Phone,
  Download,
  Eye
} from 'lucide-react';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalResidents: 0,
    totalProperties: 0,
    totalVehicles: 0,
    pendingRegistrations: 0,
    openComplaints: 0,
    recentComplaints: []
  });
  const [notifications, setNotifications] = useState({
    criticalPending: 0,
    totalPending: 0,
    recentChanges: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [residents, properties, gateRegister, pendingRegs, complaints, transitions] = await Promise.all([
        adminAPI.getAllResidents(),
        adminAPI.getAllProperties(),
        adminAPI.getGateRegister(),
        adminAPI.getPendingRegistrations(),
        adminAPI.getAllComplaints(),
        fetch('http://localhost:5000/api/transition/admin/requests', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }).then(res => res.ok ? res.json() : { requests: [] })
      ]);

      const openComplaints = complaints.data.filter(c => c.status === 'open');
      const recentComplaints = complaints.data
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);

      // Process transition data
      const transitionRequests = transitions.requests || [];
      const pendingTransitions = transitionRequests.filter(t => t.status === 'pending_review');
      const inProgressTransitions = transitionRequests.filter(t => t.status === 'in_progress');
      const urgentTransitions = transitionRequests.filter(t => t.priority === 'urgent' || t.priority === 'emergency');

      setStats({
        totalResidents: residents.data.length,
        totalProperties: properties.data.length,
        totalVehicles: gateRegister.data.total_vehicles || 0,
        pendingRegistrations: pendingRegs.data.length,
        openComplaints: openComplaints.length,
        recentComplaints,
        // Add transition metrics
        totalTransitions: transitionRequests.length,
        pendingTransitions: pendingTransitions.length,
        inProgressTransitions: inProgressTransitions.length,
        urgentTransitions: urgentTransitions.length
      });

      // Load notification data
      await loadNotificationData();
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadNotificationData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const [statsRes, criticalRes] = await Promise.all([
        fetch('http://localhost:5000/api/admin/changes/stats', { headers }),
        fetch('http://localhost:5000/api/admin/changes/critical', { headers })
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        const stats = statsData.stats || {};
        
        if (criticalRes.ok) {
          const criticalData = await criticalRes.json();
          const changes = criticalData.critical_changes || [];
          
          setNotifications({
            criticalPending: stats.critical_pending || 0,
            totalPending: stats.total_pending || 0,
            recentChanges: changes.slice(0, 3) // Show only 3 most recent
          });
        }
      }
    } catch (error) {
      console.error('Error loading notification data:', error);
      // Set default values on error
      setNotifications({
        criticalPending: 0,
        totalPending: 0,
        recentChanges: []
      });
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, description }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );

  const exportData = async (type) => {
    try {
      // Use the new gate register changes export instead of old system
      console.log(`Exporting data for ${type} system...`);
      
      const response = await adminAPI.exportGateRegisterChanges();
      
      // Create and download the HTML file with red highlighting
      const url = window.URL.createObjectURL(response);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${type}_gate_register_changes_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.html`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log(`Successfully exported ${type} data`);
    } catch (error) {
      console.error(`Export failed for ${type}:`, error);
      alert(`Export failed for ${type}: ${error.message}`);
    }
  };

  const getComplaintStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-red-100 text-red-800';
      case 'in progress': return 'bg-yellow-100 text-yellow-800';
      case 'closed': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600">Overview of Altona Village community management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Residents"
          value={stats.totalResidents}
          icon={Users}
          color="text-blue-600"
          description="Active community members"
        />
        <StatCard
          title="Properties"
          value={stats.totalProperties}
          icon={Building}
          color="text-green-600"
          description="Registered properties"
        />
        <StatCard
          title="Registered Vehicles"
          value={stats.totalVehicles}
          icon={Car}
          color="text-purple-600"
          description="Gate access vehicles"
        />
        <StatCard
          title="Open Complaints"
          value={stats.openComplaints}
          icon={MessageSquare}
          color="text-orange-600"
          description="Requiring attention"
        />
      </div>

      {/* Transition System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Pending Registrations"
          value={stats.pendingRegistrations}
          icon={Clock}
          color="text-yellow-600"
          description="New users awaiting approval"
        />
        <StatCard
          title="Transition Requests"
          value={stats.totalTransitions || 0}
          icon={TrendingUp}
          color="text-indigo-600"
          description="Total property transitions"
        />
        <StatCard
          title="Pending Transitions"
          value={stats.pendingTransitions || 0}
          icon={AlertTriangle}
          color="text-amber-600"
          description="Awaiting admin review"
        />
        <StatCard
          title="Urgent Transitions"
          value={stats.urgentTransitions || 0}
          icon={Bell}
          color="text-red-600"
          description="High priority requests"
        />
      </div>

      {/* System Notifications Section */}
      {notifications.criticalPending > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center text-red-800">
              <Bell className="h-5 w-5 mr-2" />
              🚨 Critical System Updates ({notifications.criticalPending})
            </CardTitle>
            <CardDescription className="text-red-700">
              Residents have updated phone numbers or vehicle registrations - External systems need updating!
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {notifications.recentChanges.map((change) => (
                <div key={change.id} className="bg-white p-3 rounded-lg border border-red-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {change.field_name === 'cellphone_number' ? (
                        <Phone className="w-4 h-4 text-blue-600" />
                      ) : (
                        <Car className="w-4 h-4 text-green-600" />
                      )}
                      <div>
                        <p className="font-medium text-sm">{change.user_name} (ERF {change.erf_number})</p>
                        <p className="text-xs text-gray-600">
                          {change.field_name === 'cellphone_number' ? 'Phone Number' : 'Vehicle Registration'} Updated
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {new Date(change.change_timestamp).toLocaleDateString()}
                      </p>
                      <Badge variant="destructive" className="text-xs">
                        Needs Action
                      </Badge>
                    </div>
                  </div>
                  <div className="mt-2 text-xs">
                    <span className="text-red-600 line-through">{change.old_value}</span>
                    <span className="mx-2">→</span>
                    <span className="text-green-600 font-medium">{change.new_value}</span>
                  </div>
                </div>
              ))}
              
              <div className="flex gap-2 mt-4">
                <Button 
                  onClick={() => window.location.href = '/admin/notifications'}
                  className="flex-1"
                  variant="default"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  View All Changes
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Update Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center">
              <Bell className="h-5 h-5 mr-2" />
              System Change Notifications
            </div>
            <Badge variant={notifications.criticalPending > 0 ? "destructive" : "secondary"}>
              {notifications.totalPending} Pending
            </Badge>
          </CardTitle>
          <CardDescription>
            Track resident data changes for Accentronix gate system and camera system updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
              <div className="text-2xl font-bold text-red-600">{notifications.criticalPending}</div>
              <div className="text-sm text-red-700">Critical Changes</div>
              <div className="text-xs text-gray-600">Phone & Vehicle Updates</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg border">
              <div className="text-2xl font-bold text-gray-600">{notifications.totalPending}</div>
              <div className="text-sm text-gray-700">Total Changes</div>
              <div className="text-xs text-gray-600">All Pending Reviews</div>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button 
              onClick={() => window.location.href = '/admin/notifications'}
              className="flex-1"
              variant={notifications.criticalPending > 0 ? "default" : "outline"}
            >
              Manage Changes
            </Button>
            <Button 
              onClick={() => exportData('changes')}
              variant="outline"
              className="flex-1"
            >
              <Download className="w-4 h-4 mr-2" />
              Export Changes
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Gate Register Changes Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            Gate Register - Change Tracking
          </CardTitle>
          <CardDescription>
            View only residents with recent changes, export with red highlighting for external systems
          </CardDescription>
        </CardHeader>
        <CardContent>
          <GateRegisterChanges />
        </CardContent>
      </Card>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stats.pendingRegistrations > 0 && (
          <Card className="border-orange-200 bg-orange-50">
            <CardHeader>
              <CardTitle className="flex items-center text-orange-800">
                <Clock className="h-5 w-5 mr-2" />
                Pending Registrations
              </CardTitle>
              <CardDescription>
                {stats.pendingRegistrations} new residents awaiting approval
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={() => window.location.href = '/admin/pending'}
                className="w-full"
                variant="outline"
              >
                Review Applications
              </Button>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Resident Management
            </CardTitle>
            <CardDescription>
              Manage resident profiles and properties
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.href = '/admin/residents'}
              className="w-full"
              variant="outline"
            >
              Manage Residents
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Car className="h-5 w-5 mr-2" />
              Gate Register
            </CardTitle>
            <CardDescription>
              View and manage vehicle access
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.href = '/admin/gate-register'}
              className="w-full"
              variant="outline"
            >
              View Gate Register
            </Button>
          </CardContent>
        </Card>

        {/* Transition Management Cards */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-indigo-800">
              <TrendingUp className="h-5 w-5 mr-2" />
              Transition Requests
            </CardTitle>
            <CardDescription>
              {stats.pendingTransitions || 0} pending transition requests
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.href = '/admin/transition-requests'}
              className="w-full"
              variant="outline"
            >
              Manage Transitions
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-purple-800">
              <CheckCircle className="h-5 w-5 mr-2" />
              Transition Linking
            </CardTitle>
            <CardDescription>
              Link transition requests with new registrations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.href = '/admin/transition-linking'}
              className="w-full"
              variant="outline"
            >
              Process Transitions
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Complaints */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageSquare className="h-5 w-5 mr-2" />
            Recent Complaints
          </CardTitle>
          <CardDescription>
            Latest complaints and service requests
          </CardDescription>
        </CardHeader>
        <CardContent>
          {stats.recentComplaints.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No complaints to display</p>
          ) : (
            <div className="space-y-4">
              {stats.recentComplaints.map((complaint) => (
                <div key={complaint.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium">{complaint.subject}</h4>
                    <p className="text-sm text-gray-600 truncate max-w-md">
                      {complaint.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      By: {complaint.resident.first_name} {complaint.resident.last_name}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getComplaintStatusColor(complaint.status)}>
                      {complaint.status}
                    </Badge>
                    {complaint.priority && (
                      <Badge className={getPriorityColor(complaint.priority)}>
                        {complaint.priority}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
              <Button 
                onClick={() => window.location.href = '/admin/complaints'}
                variant="outline"
                className="w-full"
              >
                View All Complaints
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;

