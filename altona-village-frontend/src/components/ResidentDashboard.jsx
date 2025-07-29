import { useState, useEffect } from 'react';
import { residentAPI } from '@/lib/api';
import { useAuth, getUserResidencyType } from '@/lib/auth.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Home, 
  Car, 
  MessageSquare, 
  User, 
  Plus,
  Building,
  Phone,
  Mail,
  MapPin,
  KeyRound
} from 'lucide-react';

const ResidentDashboard = () => {
  const { user, refreshUser } = useAuth();
  const [data, setData] = useState({
    vehicles: [],
    properties: [],
    complaints: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    // Refresh user data to ensure we have the latest status information
    refreshUser();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [vehicles, complaints, properties] = await Promise.all([
        residentAPI.getMyVehicles(),
        residentAPI.getMyComplaints(),
        residentAPI.getMyProperties()
      ]);

      setData({
        vehicles: vehicles.data,
        complaints: complaints.data,
        properties: properties.data
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
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

  const StatCard = ({ title, value, icon: Icon, color, description, action }) => (
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
        {action && (
          <Button size="sm" variant="outline" className="mt-2" onClick={action.onClick}>
            {action.label}
          </Button>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const openComplaints = data.complaints.filter(c => c.status === 'open').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome, {user?.resident?.first_name || user?.owner?.first_name || user?.full_name || 'Resident'}!
        </h1>
        <p className="text-gray-600">Manage your Altona Village account and services</p>
      </div>

      {/* Profile Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <User className="h-5 w-5 mr-2" />
            Your Profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Name</p>
              <p className="font-medium">
                {user?.resident?.first_name && user?.resident?.last_name 
                  ? `${user.resident.first_name} ${user.resident.last_name}`
                  : user?.owner?.first_name && user?.owner?.last_name
                    ? `${user.owner.first_name} ${user.owner.last_name}`
                    : user?.full_name || 'Not available'
                }
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium">{user?.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <Badge className="bg-green-100 text-green-800">
                {getUserResidencyType(user)}
              </Badge>
            </div>
            {user?.resident?.phone_number && (
              <div>
                <p className="text-sm text-gray-600">Phone</p>
                <p className="font-medium">{user?.resident?.phone_number}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600 flex items-center">
                <MapPin className="h-4 w-4 mr-1" />
                ERF Number
              </p>
              <p className="font-medium">
                {user?.resident?.erf_number || user?.owner?.erf_number || 'Not available'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 flex items-center">
                <KeyRound className="h-4 w-4 mr-1" />
                Intercom Code
              </p>
              <p className="font-medium">
                {user?.resident?.intercom_code || user?.owner?.intercom_code || 'Not available'}
              </p>
            </div>
          </div>
          <Button 
            onClick={() => window.location.href = '/resident/profile'}
            variant="outline"
            className="mt-4"
          >
            Update Profile
          </Button>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="My Vehicles"
          value={data.vehicles.length}
          icon={Car}
          color="text-blue-600"
          description="Registered for gate access"
          action={{
            label: "Manage Vehicles",
            onClick: () => window.location.href = '/resident/vehicles'
          }}
        />
        <StatCard
          title="My Properties"
          value={data.properties.length}
          icon={Building}
          color="text-green-600"
          description="Associated properties"
          action={{
            label: "View Details",
            onClick: () => window.location.href = '/resident/property'
          }}
        />
        <StatCard
          title="Open Complaints"
          value={openComplaints}
          icon={MessageSquare}
          color="text-orange-600"
          description="Pending resolution"
          action={{
            label: "View Complaints",
            onClick: () => window.location.href = '/resident/complaints'
          }}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Car className="h-5 w-5 mr-2" />
              Vehicle Management
            </CardTitle>
            <CardDescription>
              Add or update your vehicles for gate access
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.vehicles.length === 0 ? (
                <p className="text-gray-500 text-sm">No vehicles registered</p>
              ) : (
                data.vehicles.slice(0, 3).map((vehicle) => (
                  <div key={vehicle.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="font-medium">{vehicle.registration_number}</span>
                    <span className="text-sm text-gray-600">
                      {vehicle.make} {vehicle.model}
                    </span>
                  </div>
                ))
              )}
            </div>
            <Button 
              onClick={() => window.location.href = '/resident/vehicles'}
              variant="outline"
              className="w-full mt-4"
            >
              <Plus className="h-4 w-4 mr-2" />
              {data.vehicles.length === 0 ? 'Add Vehicle' : 'Manage Vehicles'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <MessageSquare className="h-5 w-5 mr-2" />
              Submit Complaint
            </CardTitle>
            <CardDescription>
              Report issues or request services
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Need to report a maintenance issue, security concern, or request a service? 
              Submit a complaint and track its progress.
            </p>
            <Button 
              onClick={() => window.location.href = '/resident/complaints'}
              className="w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Submit New Complaint
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Complaints */}
      {data.complaints.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <MessageSquare className="h-5 w-5 mr-2" />
              Recent Complaints
            </CardTitle>
            <CardDescription>
              Your latest complaints and their status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.complaints.slice(0, 3).map((complaint) => (
                <div key={complaint.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium">{complaint.subject}</h4>
                    <p className="text-sm text-gray-600 truncate max-w-md">
                      {complaint.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Submitted: {new Date(complaint.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge className={getComplaintStatusColor(complaint.status)}>
                    {complaint.status}
                  </Badge>
                </div>
              ))}
              <Button 
                onClick={() => window.location.href = '/resident/complaints'}
                variant="outline"
                className="w-full"
              >
                View All Complaints
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ResidentDashboard;

