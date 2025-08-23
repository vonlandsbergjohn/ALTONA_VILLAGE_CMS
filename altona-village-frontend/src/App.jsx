import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/lib/auth.jsx';
import Layout from '@/components/Layout';
import LoginForm from '@/components/LoginForm';
import RegisterForm from '@/components/RegisterForm';
import AdminDashboard from '@/components/AdminDashboard';
import AdminComplaints from '@/components/AdminComplaints';
import AdminResidents from '@/components/AdminResidents';
import AdminNotificationsDashboard from '@/components/AdminNotificationsDashboard';
import AdminTransitionRequests from '@/components/AdminTransitionRequests';
import AdminTransitionLinking from '@/components/AdminTransitionLinking';
import AddressMappings from '@/components/AddressMappings';
import GateRegister from '@/components/GateRegister';
import PendingRegistrations from './components/PendingRegistrations';
import AdminCommunication from '@/components/AdminCommunication';
import ResidentDashboard from '@/components/ResidentDashboard';
import ProfileManagement from '@/components/ProfileManagement';
import VehicleManagement from '@/components/VehicleManagement';
import MyComplaints from '@/components/MyComplaints';
import MyProperty from '@/components/MyProperty';
import UserTransitionRequest from '@/components/UserTransitionRequest';
import MyTransitionRequests from '@/components/MyTransitionRequests';
import ErrorBoundary from '@/components/ErrorBoundary';
import './App.css';

// 🔵 backend base (absolute URL so it doesn't hit the SPA routes)
const API = 'https://altona-village-backend.onrender.com';

// Try a few common keys where the token might be stored
function getStoredToken() {
  const keys = [
    'token',
    'access_token',
    'jwt',
    'key',
    'authToken',
  ];
  for (const k of keys) {
    const v = window.localStorage.getItem(k) || window.sessionStorage.getItem(k);
    if (v) return v.replace(/^Bearer\s+/i, '');
  }
  return null;
}

// Simple router component
const Router = () => {
  // NOTE: do NOT pull isAdmin here; compute from role
  const { user, loading, isAuthenticated, isResident, canAccessVehicles } = useAuth();

  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const [showRegister, setShowRegister] = useState(false);

  // ⇒ New: keep a copy of the live profile from the backend
  const [profile, setProfile] = useState(null);
  const [checkingProfile, setCheckingProfile] = useState(false);

  // Load live profile if we’re authenticated but don’t have role/status yet
  useEffect(() => {
    if (!isAuthenticated) return;

    const hasRoleStatus = !!(user && (user.role || user.status));
    if (hasRoleStatus || checkingProfile || profile) return;

    const token =
      (user && (user.token || user.access_token || user.jwt || user.key)) ||
      getStoredToken();

    if (!token) return;

    (async () => {
      try {
        setCheckingProfile(true);
        const res = await fetch(`${API}/api/auth/profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setProfile(data);
        } else {
          // if unauthorized, let normal auth flow handle it
          setProfile(null);
        }
      } catch {
        setProfile(null);
      } finally {
        setCheckingProfile(false);
      }
    })();
  }, [isAuthenticated, user, checkingProfile, profile]);

  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Navigate function
  const navigate = (path) => {
    if (path !== window.location.pathname) {
      window.history.pushState({}, '', path);
      setCurrentPath(path);
    }
  };

  if (loading || (isAuthenticated && checkingProfile && !profile && !(user && (user.role || user.status)))) {
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

  // --------------------------------------------------------------------
  // Account gating: compute from the best-available user (profile > user)
  // and ALWAYS allow admins through.
  // --------------------------------------------------------------------
  const bestUser = profile || user || {};
  const role   = (bestUser.role   ?? '').toLowerCase();
  const status = (bestUser.status ?? '').toLowerCase();

  const isAdmin = role === 'admin';
  const isActive = status === 'active';
  const isApproved =
    bestUser.approval_status === 'approved' ||
    bestUser.is_approved === true ||
    bestUser.approved === true;

  // Show "pending approval" ONLY when NOT admin and also NOT active/approved
  if (!(isAdmin || isActive || isApproved)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Account Pending Approval</h1>
          <p className="text-gray-600 mb-4">
            Your account is <span className="font-semibold">awaiting approval</span> from the estate management.
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
        case '/admin/transition-requests':
          return <AdminTransitionRequests />;
        case '/admin/transition-linking':
          return <AdminTransitionLinking />;
        case '/admin/pending':
          return <PendingRegistrations />;
        case '/admin/notifications':
          return <AdminNotificationsDashboard />;
        case '/admin/address-mappings':
          return <AddressMappings />;
        case '/admin/communication':
          return <AdminCommunication />;
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
          if (canAccessVehicles) return <VehicleManagement />;
          break;
        case '/resident/complaints':
          return <MyComplaints />;
        case '/resident/transition-requests':
          return <MyTransitionRequests />;
        case '/resident/transition-request/new':
          return <UserTransitionRequest />;
        case '/transition-requests':
          return <UserTransitionRequest />;
        default:
          return <ResidentDashboard />;
      }
    }

    return <div>Page not found</div>;
  };

  return <Layout>{renderRoute()}</Layout>;
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
