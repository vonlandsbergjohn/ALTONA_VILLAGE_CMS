import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from './api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Helper function to get user's actual residency type
export const getUserResidencyType = (user) => {
  if (!user) {
    return 'Unknown';
  }
  
  // For admin users
  if (user.role === 'admin') {
    return 'Admin';
  }
  
  const isResident = user.is_resident;
  const isOwner = user.is_owner;
  
  if (isResident && isOwner) {
    return 'Owner-Resident';
  }
  if (isOwner) {
    return 'Property Owner';
  }
  if (isResident) {
    return 'Resident';
  }
  
  // Fallback - if no flags are set, check if user has resident or owner data
  if (user.resident && user.owner) {
    return 'Owner-Resident';
  }
  if (user.owner) {
    return 'Property Owner'; 
  }
  if (user.resident) {
    return 'Resident';
  }
  
  return 'Unknown';
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    
    if (token) {
      // Always fetch fresh user data from server instead of using cached data
      authAPI.getProfile()
        .then(response => {
          setUser(response.data);
          localStorage.setItem('user', JSON.stringify(response.data));
        })
        .catch(() => {
          logout();
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      return { success: true, message: response.data.message };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    try {
      await authAPI.updateProfile(profileData);
      const response = await authAPI.getProfile();
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Profile update failed' 
      };
    }
  };

  const refreshUser = async () => {
    try {
      const response = await authAPI.getProfile();
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      return { success: true };
    } catch (error) {
      return { success: false };
    }
  };

  const value = {
    user,
    login,
    register,
    logout,
    updateProfile,
    refreshUser,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isResident: user?.role === 'resident',
    // Allow vehicle access for both residents and owners (including owner-only users)
    canAccessVehicles: user && (user.is_resident || user.is_owner || user.resident || user.owner),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

