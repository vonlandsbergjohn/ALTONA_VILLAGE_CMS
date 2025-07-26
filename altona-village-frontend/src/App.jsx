import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/lib/auth.jsx';
import Layout from '@/components/Layout';
import LoginForm from '@/components/LoginForm';
import RegisterForm from '@/components/RegisterForm';
import AdminDashboard from '@/components/AdminDashboard';
import PendingRegistrations from './components/PendingRegistrations';
import ResidentDashboard from '@/components/ResidentDashboard';
import './App.css';

// Simple router component
const Router = () => {
  const { user, loading, isAuthenticated, isAdmin, isResident } = useAuth();
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

  // Account not activated
  if (user?.status !== 'active') {
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
      } else if (isResident) {
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
          return <div>Residents Management (Coming Soon)</div>;
        case '/admin/properties':
          return <div>Properties Management (Coming Soon)</div>;
        case '/admin/gate-register':
          return <div>Gate Register (Coming Soon)</div>;
        case '/admin/complaints':
          return <div>Complaints Management (Coming Soon)</div>;
        case '/admin/pending':
         return <PendingRegistrations />;
        case '/admin/communication':
          return <div>Communication Tools (Coming Soon)</div>;
        default:
          return <AdminDashboard />;
      }
    }

    // Resident routes
    if (isResident) {
      switch (currentPath) {
        case '/resident':
          return <ResidentDashboard />;
        case '/resident/profile':
          return <div>Profile Management (Coming Soon)</div>;
        case '/resident/property':
          return <div>My Property (Coming Soon)</div>;
        case '/resident/vehicles':
          return <div>Vehicle Management (Coming Soon)</div>;
        case '/resident/complaints':
          return <div>My Complaints (Coming Soon)</div>;
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
