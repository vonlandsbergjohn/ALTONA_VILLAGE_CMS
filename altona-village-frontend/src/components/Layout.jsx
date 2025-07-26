import { useState } from 'react';
import { useAuth } from '@/lib/auth.jsx';
import { Button } from '@/components/ui/button';
import { 
  Home, 
  Users, 
  Building, 
  Car, 
  MessageSquare, 
  Settings, 
  LogOut,
  Menu,
  X,
  Shield,
  User
} from 'lucide-react';

const Layout = ({ children }) => {
  const { user, logout, isAdmin, isResident } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const adminNavItems = [
    { icon: Home, label: 'Dashboard', path: '/admin' },
    { icon: Users, label: 'Residents', path: '/admin/residents' },
    { icon: Building, label: 'Properties', path: '/admin/properties' },
    { icon: Car, label: 'Gate Register', path: '/admin/gate-register' },
    { icon: MessageSquare, label: 'Complaints', path: '/admin/complaints' },
    { icon: Shield, label: 'Pending Approvals', path: '/admin/pending' },
    { icon: Settings, label: 'Communication', path: '/admin/communication' },
  ];

  const residentNavItems = [
    { icon: Home, label: 'Dashboard', path: '/resident' },
    { icon: User, label: 'Profile', path: '/resident/profile' },
    { icon: Building, label: 'My Property', path: '/resident/property' },
    { icon: Car, label: 'My Vehicles', path: '/resident/vehicles' },
    { icon: MessageSquare, label: 'My Complaints', path: '/resident/complaints' },
  ];

  const navItems = isAdmin ? adminNavItems : residentNavItems;

  const handleNavigation = (path) => {
    window.location.href = path;
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between h-16 px-6 border-b">
          <h1 className="text-xl font-bold text-blue-600">Altona Village</h1>
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="mt-6">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => handleNavigation(item.path)}
              className="w-full flex items-center px-6 py-3 text-left text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full p-6 border-t">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">{user?.email}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="w-full"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="bg-white shadow-sm border-b h-16 flex items-center justify-between px-6">
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              Welcome back, {user?.resident?.first_name || user?.email}
            </span>
          </div>
        </div>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;

