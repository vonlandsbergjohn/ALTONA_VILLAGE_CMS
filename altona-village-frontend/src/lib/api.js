import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
};

// Admin API
export const adminAPI = {
  getPendingRegistrations: () => api.get('/admin/pending-registrations'),
  approveRegistration: (userId) => api.post(`/admin/approve-registration/${userId}`),
  rejectRegistration: (userId) => api.post(`/admin/reject-registration/${userId}`),
  getAllResidents: () => api.get('/admin/residents'),
  updateResident: (userId, data) => api.put(`/admin/residents/${userId}`, data),
  getAllProperties: () => api.get('/admin/properties'),
  createProperty: (data) => api.post('/admin/properties', data),
  createBuilder: (data) => api.post('/admin/builders', data),
  createMeter: (data) => api.post('/admin/meters', data),
  getAllComplaints: () => api.get('/admin/complaints'),
  updateComplaint: (complaintId, data) => api.post(`/admin/complaints/${complaintId}/update`, data),
  getGateRegister: () => api.get('/admin/gate-register'),
  exportGateRegister: () => api.get('/admin/gate-register/export', { responseType: 'blob' }),
  getGateRegisterChanges: () => api.get('/admin/gate-register/changes'),
  exportGateRegisterChanges: async () => {
    try {
      const response = await api.get('/admin/gate-register/export-changes', { responseType: 'blob' });
      return response.data;
    } catch (error) {
      // If there's an error with blob response, try without blob to get proper error message
      if (error.response && error.response.status >= 400) {
        try {
          const errorResponse = await api.get('/admin/gate-register/export-changes');
          throw new Error(errorResponse.data?.error || `HTTP ${error.response.status}`);
        } catch (secondError) {
          throw error; // Use original error if second request also fails
        }
      }
      throw error;
    }
  },
  // Change tracking API methods
  getCriticalChanges: () => api.get('/admin/changes/critical'),
  getNonCriticalChanges: (params = {}) => api.get('/admin/changes/non-critical', { params }),
  getChangeStats: () => api.get('/admin/changes/stats'),
  reviewChanges: (changeIds, notes = '') => api.post('/admin/changes/review', { change_ids: changeIds, notes }),
  markChangeProcessed: (changeId) => api.post(`/admin/changes/${changeId}/mark-processed`),
  // Admin Vehicle Management
  getResidentVehicles: (userId) => api.get(`/admin/residents/${userId}/vehicles`),
  addResidentVehicle: (userId, data) => api.post(`/admin/residents/${userId}/vehicles`, data),
  updateResidentVehicle: (userId, vehicleId, data) => api.put(`/admin/residents/${userId}/vehicles/${vehicleId}`, data),
  deleteResidentVehicle: (userId, vehicleId) => api.delete(`/admin/residents/${userId}/vehicles/${vehicleId}`),
  getResidentEmails: () => api.get('/admin/communication/emails'),
  getResidentPhones: () => api.get('/admin/communication/phones'),
  // User Management
  permanentlyDeleteUser: (userId, data) => api.delete(`/admin/users/${userId}/permanent-delete`, { data }),
  getDeletionLogs: (daysBack = 30) => api.get(`/admin/users/deletion-logs?days_back=${daysBack}`),
  // Communication API methods
  getCommunicationStats: () => api.get('/communication/stats'),
  sendBulkEmail: (data) => api.post('/communication/send-email', data),
  sendBulkWhatsApp: (data) => api.post('/communication/send-whatsapp', data),
  // Individual communication methods
  findUserByErf: (erfNumber) => api.post('/communication/find-user-by-erf', { erf_number: erfNumber }),
  sendIndividualEmail: (data) => api.post('/communication/send-individual-email', data),
};

// Resident API
export const residentAPI = {
  getMyVehicles: () => api.get('/resident/vehicles'),
  addVehicle: (data) => api.post('/resident/vehicles', data),
  updateVehicle: (vehicleId, data) => api.put(`/resident/vehicles/${vehicleId}`, data),
  deleteVehicle: (vehicleId) => api.delete(`/resident/vehicles/${vehicleId}`),
  getMyComplaints: () => api.get('/resident/complaints'),
  submitComplaint: (data) => api.post('/resident/complaints', data),
  getComplaint: (complaintId) => api.get(`/resident/complaints/${complaintId}`),
  getMyProperties: () => api.get('/resident/properties'),
};

export default api;

