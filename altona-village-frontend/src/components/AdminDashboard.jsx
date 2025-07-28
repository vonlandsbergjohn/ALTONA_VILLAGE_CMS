import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  Building, 
  Car, 
  MessageSquare, 
  Clock, 
  CheckCircle,
  AlertTriangle,
  TrendingUp
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [residents, properties, gateRegister, pendingRegs, complaints] = await Promise.all([
        adminAPI.getAllResidents(),
        adminAPI.getAllProperties(),
        adminAPI.getGateRegister(),
        adminAPI.getPendingRegistrations(),
        adminAPI.getAllComplaints()
      ]);

      const openComplaints = complaints.data.filter(c => c.status === 'open');
      const recentComplaints = complaints.data
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);

      setStats({
        totalResidents: residents.data.length,
        totalProperties: properties.data.length,
        totalVehicles: gateRegister.data.total_vehicles || 0,
        pendingRegistrations: pendingRegs.data.length,
        openComplaints: openComplaints.length,
        recentComplaints
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
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

