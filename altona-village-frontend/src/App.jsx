import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/lib/auth.jsx';
import Layout from '@/components/Layout';
import LoginForm from '@/components/LoginForm';
import RegisterForm from '@/components/RegisterForm';
import AdminDashboard from '@/components/AdminDashboard';
// import SimpleTest from '@/components/SimpleTest';
import AdminComplaints from '@/components/AdminComplaints';
import AdminResidents from '@/components/AdminResidents';
import AdminNotificationsDashboard from '@/components/AdminNotificationsDashboard';
import GateRegister from '@/components/GateRegister';
import PendingRegistrations from './components/PendingRegistrations';
import ResidentDashboard from '@/components/ResidentDashboard';
import ProfileManagement from '@/components/ProfileManagement';
import VehicleManagement from '@/components/VehicleManagement';
import MyComplaints from '@/components/MyComplaints';
import MyProperty from '@/components/MyProperty';
import './App.css';

// Simple router component
const Router = () => {
  const { user, loading, isAuthenticated, isAdmin, isResident, canAccessVehicles } = useAuth();
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Navigate function
  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Authentication check
  if (!isAuthenticated) {
    if (showRegister) {
      return <RegisterForm onSwitchToLogin={() => setShowRegister(false)} />;
    }
    return <LoginForm onSwitchToRegister={() => setShowRegister(true)} />;
  }

  // Account not activated (but allow admins)
  if (user?.status !== 'active' && user?.role !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Account Pending Approval</h1>
          <p className="text-gray-600 mb-4">
            Your account is awaiting approval from the estate management.
          </p>
          <p className="text-gray-600">
            You will receive an email notification once your account is approved.
          </p>
        </div>
      </div>
    );
  }

  // Route rendering
  const renderRoute = () => {
    // Redirect to appropriate dashboard based on role
    if (currentPath === '/' || currentPath === '/dashboard') {
      if (isAdmin) {
        navigate('/admin');
        return <AdminDashboard />;
      } else if (isResident || canAccessVehicles) {
        navigate('/resident');
        return <ResidentDashboard />;
      }
    }

    // Admin routes
    if (isAdmin) {
      switch (currentPath) {
        case '/admin':
          return <AdminDashboard />;
        case '/admin/residents':
          return <AdminResidents />;
        case '/admin/properties':
          return <div>Properties Management (Coming Soon)</div>;
        case '/admin/gate-register':
          return <GateRegister />;
        case '/admin/complaints':
          return <AdminComplaints />;
        case '/admin/pending':
          return <PendingRegistrations />;
        case '/admin/notifications':
          return <AdminNotificationsDashboard />;
        case '/admin/communication':
          return <div>Communication Tools (Coming Soon)</div>;
        default:
          return <AdminDashboard />;
      }
    }

    // Resident and Owner routes
    if (isResident || canAccessVehicles) {
      switch (currentPath) {
        case '/resident':
          return <ResidentDashboard />;
        case '/resident/profile':
          return <ProfileManagement />;
        case '/resident/property':
          return <MyProperty />;
        case '/resident/vehicles':
          // Allow both residents and owners to access vehicles
          if (canAccessVehicles) {
            return <VehicleManagement />;
          }
          break;
        case '/resident/complaints':
          return <MyComplaints />;
        default:
          return <ResidentDashboard />;
      }
    }

    return <div>Page not found</div>;
  };

  return (
    <Layout>
      {renderRoute()}
    </Layout>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router />
    </AuthProvider>
  );
}

export default App;