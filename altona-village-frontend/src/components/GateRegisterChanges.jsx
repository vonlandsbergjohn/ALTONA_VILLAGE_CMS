import React, { useState, useEffect } from 'react';
import { Download, AlertCircle, Clock, User, Phone, Car } from 'lucide-react';
import { adminAPI } from '@/lib/api';

const GateRegisterChanges = () => {
  const [changes, setChanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadChanges();
  }, []);

  const loadChanges = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Use the adminAPI with proper error handling
      const response = await adminAPI.getGateRegisterChanges();
      console.log('Gate register changes response:', response);
      
      // Handle different response formats
      const changesData = response?.data?.data || response?.data || [];
      setChanges(Array.isArray(changesData) ? changesData : []);
      
    } catch (err) {
      console.error('Error loading gate register changes:', err);
      const errorMessage = err?.response?.data?.error || 
                          err?.response?.data?.message || 
                          err?.message || 
                          'Failed to load changes';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const exportChanges = async () => {
    try {
      setExporting(true);
      setError('');
      
      const response = await adminAPI.exportGateRegisterChanges();
      
      // Create blob and download
      const url = window.URL.createObjectURL(response);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `gate_register_changes_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.html`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Export error:', err);
      const errorMessage = err?.response?.data?.error || 
                          err?.response?.data?.message || 
                          err?.message || 
                          'Export failed';
      setError(errorMessage);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading changes...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
        <div className="mt-3 flex gap-2">
          <button
            onClick={loadChanges}
            className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
          >
            Retry
          </button>
          <div className="text-xs text-red-600 mt-1">
            {error.includes('401') || error.includes('Authorization') ? 
              'Authentication required - please refresh and log in again' : 
              'Check server connection and try again'
            }
          </div>
        </div>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <div className="flex flex-col items-center">
          <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mb-3">
            <User className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-medium text-green-800 mb-2">All Changes Reviewed</h3>
          <p className="text-green-600">No pending changes found in the gate register.</p>
        </div>
      </div>
    );
  }

  // Group changes by user for better display
  const groupedChanges = changes.reduce((acc, entry) => {
    const key = `${entry.user_id}-${entry.first_name}-${entry.last_name}`;
    if (!acc[key]) {
      acc[key] = {
        userInfo: {
          user_id: entry.user_id,
          first_name: entry.first_name,
          last_name: entry.last_name,
          surname: entry.surname,
          resident_status: entry.resident_status,
          street_number: entry.street_number,
          street_name: entry.street_name,
          erf_number: entry.erf_number,
          intercom_code: entry.intercom_code,
          phone_number: entry.phone_number,
          phone_changed: entry.phone_changed,
          email: entry.email
        },
        vehicles: []
      };
    }
    
    if (entry.vehicle_registration) {
      acc[key].vehicles.push({
        registration: entry.vehicle_registration,
        changed: entry.vehicle_changed
      });
    }
    
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Clock className="h-6 w-6 text-blue-600 mr-2" />
              Gate Register - Pending Changes
            </h2>
            <p className="text-gray-600 mt-1">
              Showing {changes.length} entries with recent changes. Changed information is highlighted in red.
            </p>
          </div>
          
          <button
            onClick={exportChanges}
            disabled={exporting}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            {exporting ? 'Exporting...' : 'Export Changes'}
          </button>
        </div>
      </div>

      {/* Changes Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  First Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Surname
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone Number
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Street Nr
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Street Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Vehicle Registration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ERF Nr
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Intercom
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.values(groupedChanges).map((group, groupIndex) => {
                const { userInfo, vehicles } = group;
                
                if (vehicles.length > 0) {
                  return vehicles.map((vehicle, vehicleIndex) => (
                    <tr key={`${groupIndex}-${vehicleIndex}`} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.resident_status}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.first_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.surname}
                      </td>
                      <td className={`px-4 py-3 whitespace-nowrap text-sm font-medium ${
                        userInfo.phone_changed && vehicleIndex === 0
                          ? 'bg-red-100 text-red-900 border-2 border-red-300 rounded'
                          : 'text-gray-900'
                      }`}>
                        <div className="flex items-center">
                          {userInfo.phone_changed && vehicleIndex === 0 && (
                            <Phone className="h-4 w-4 mr-1 text-red-600" />
                          )}
                          {userInfo.phone_number}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.street_number}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.street_name}
                      </td>
                      <td className={`px-4 py-3 whitespace-nowrap text-sm font-medium ${
                        vehicle.changed
                          ? 'bg-red-100 text-red-900 border-2 border-red-300 rounded'
                          : 'text-gray-900'
                      }`}>
                        <div className="flex items-center">
                          {vehicle.changed && (
                            <Car className="h-4 w-4 mr-1 text-red-600" />
                          )}
                          {vehicle.registration}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.erf_number}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.intercom_code}
                      </td>
                    </tr>
                  ));
                } else {
                  // No vehicles case
                  return (
                    <tr key={groupIndex} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.resident_status}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.first_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.surname}
                      </td>
                      <td className={`px-4 py-3 whitespace-nowrap text-sm font-medium ${
                        userInfo.phone_changed
                          ? 'bg-red-100 text-red-900 border-2 border-red-300 rounded'
                          : 'text-gray-900'
                      }`}>
                        <div className="flex items-center">
                          {userInfo.phone_changed && (
                            <Phone className="h-4 w-4 mr-1 text-red-600" />
                          )}
                          {userInfo.phone_number}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.street_number}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.street_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 italic">
                        No vehicles
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.erf_number}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {userInfo.intercom_code}
                      </td>
                    </tr>
                  );
                }
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-yellow-800 mb-2">Legend:</h3>
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-100 border-2 border-red-300 rounded mr-2"></div>
            <span className="text-yellow-700">Changed Information (red background)</span>
          </div>
          <div className="flex items-center">
            <Phone className="h-4 w-4 text-red-600 mr-1" />
            <span className="text-yellow-700">Phone number changed</span>
          </div>
          <div className="flex items-center">
            <Car className="h-4 w-4 text-red-600 mr-1" />
            <span className="text-yellow-700">Vehicle registration changed</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GateRegisterChanges;
