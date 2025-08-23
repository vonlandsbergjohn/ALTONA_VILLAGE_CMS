import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Upload, 
  Download, 
  Search, 
  Trash2, 
  AlertCircle, 
  CheckCircle,
  MapPin,
  FileText,
  RefreshCw,
  X
} from 'lucide-react';

const AddressMappings = () => {
  const [mappings, setMappings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [file, setFile] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50); // Show 50 items per page for large datasets

  useEffect(() => {
    loadMappings();
  }, []);

  const loadMappings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://altona-village-backend.onrender.com/api/admin/address-mappings', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMappings(data.data || []);
      } else {
        setError('Failed to load address mappings');
      }
    } catch (error) {
      setError('Network error loading mappings');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    // Confirm replacement of existing data
    const confirmed = window.confirm(
      '⚠️ IMPORTANT: This upload will completely replace ALL existing address mappings.\n\n' +
      'Are you sure you want to continue? This action cannot be undone.\n\n' +
      `File to upload: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`
    );
    
    if (!confirmed) {
      return;
    }

    // Check file size (limit to 10MB for large uploads)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError('File size too large. Please keep files under 10MB.');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('https://altona-village-backend.onrender.com/api/admin/address-mappings/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(`Successfully imported ${data.imported_count} address mappings`);
        setFile(null);
        // Reset file input
        const fileInput = document.getElementById('file-upload');
        if (fileInput) fileInput.value = '';
        await loadMappings();
      } else {
        // Show detailed error information for large uploads
        if (data.errors && data.errors.length > 0) {
          const errorSummary = `Upload failed with ${data.total_errors || data.errors.length} errors. First few: ${data.errors.slice(0, 3).join('; ')}`;
          setError(errorSummary);
        } else {
          setError(data.error || 'Upload failed');
        }
      }
    } catch (error) {
      setError('Network error during upload. For large files, this may indicate a timeout.');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://altona-village-backend.onrender.com/api/admin/address-mappings/template', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'erf_address_template.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Failed to download template');
      }
    } catch (error) {
      setError('Network error downloading template');
    }
  };

  const downloadCurrentData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://altona-village-backend.onrender.com/api/admin/address-mappings/export', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // Filename is set by the backend with timestamp
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition 
          ? contentDisposition.split('filename=')[1].replace(/"/g, '')
          : 'address_mappings_backup.csv';
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setSuccess('Address mappings backed up successfully');
      } else {
        setError('Failed to download current data');
      }
    } catch (error) {
      setError('Network error downloading current data');
    }
  };

  const clearAllMappings = async () => {
    if (!window.confirm('Are you sure you want to clear all address mappings? This cannot be undone.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://altona-village-backend.onrender.com/api/admin/address-mappings/clear', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setSuccess('All address mappings cleared successfully');
        await loadMappings();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to clear mappings');
      }
    } catch (error) {
      setError('Network error clearing mappings');
    }
  };

  const deleteMapping = async (mappingId) => {
    if (!window.confirm('Are you sure you want to delete this mapping?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/address-mappings/${mappingId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setSuccess('Address mapping deleted successfully');
        await loadMappings();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to delete mapping');
      }
    } catch (error) {
      setError('Network error deleting mapping');
    }
  };

  const filteredMappings = mappings.filter(mapping =>
    mapping.erf_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    mapping.street_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    mapping.street_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination logic
  const totalPages = Math.ceil(filteredMappings.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentMappings = filteredMappings.slice(startIndex, endIndex);

  // Reset pagination when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Address Mappings</h1>
        <Button onClick={loadMappings} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-700">{error}</AlertDescription>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={() => setError('')}
          >
            <X className="h-4 w-4" />
          </Button>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700">{success}</AlertDescription>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={() => setSuccess('')}
          >
            <X className="h-4 w-4" />
          </Button>
        </Alert>
      )}

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Street Map
          </CardTitle>
          <CardDescription>
            Upload a CSV or Excel file with ERF numbers and their corresponding street addresses.
            The file should contain columns: erf_number, street_number, street_name.
            <br />
            <strong>Supports large files:</strong> Can handle up to 300+ address mappings (10MB max file size).
            <br />
            <span className="text-red-600 font-medium">⚠️ Warning: Uploading will completely replace all existing address mappings.</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
                Select CSV or Excel File
              </label>
              <Input
                id="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => setFile(e.target.files[0])}
                disabled={uploading}
              />
              {file && (
                <div className="mt-2 text-sm text-gray-600">
                  <p>Selected: {file.name}</p>
                  <p>Size: {(file.size / 1024).toFixed(1)} KB</p>
                </div>
              )}
            </div>
            <Button 
              onClick={handleFileUpload} 
              disabled={!file || uploading}
              className="shrink-0"
            >
              {uploading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload
                </>
              )}
            </Button>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <h4 className="text-sm font-medium text-blue-800 mb-2">Large File Upload Tips:</h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• For 300+ records, ensure good internet connection</li>
              <li>• Upload may take 30-60 seconds for large files</li>
              <li>• CSV format is generally faster than Excel</li>
              <li>• Required columns: erf_number, street_number, street_name</li>
              <li>• Optional columns: suburb, postal_code</li>
            </ul>
          </div>

          <div className="bg-red-50 border border-red-200 p-3 rounded-lg">
            <h4 className="text-sm font-medium text-red-800 mb-2">⚠️ Data Replacement Warning:</h4>
            <ul className="text-xs text-red-700 space-y-1">
              <li>• Each upload completely replaces ALL existing address mappings</li>
              <li>• Previous address data will be permanently deleted</li>
              <li>• Make sure your file contains all addresses you want to keep</li>
              <li>• Use "Download Current Data" to backup before uploading</li>
            </ul>
          </div>

          <div className="flex gap-2 flex-wrap">
            <Button onClick={downloadTemplate} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download Template
            </Button>
            <Button onClick={downloadCurrentData} variant="outline" size="sm" className="bg-blue-50 hover:bg-blue-100">
              <Download className="h-4 w-4 mr-2" />
              Download Current Data
            </Button>
            <Button onClick={clearAllMappings} variant="destructive" size="sm">
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Search and Statistics */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search by ERF or street..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
          <Badge variant="secondary">
            {filteredMappings.length} of {mappings.length} mappings
            {totalPages > 1 && ` (Page ${currentPage} of ${totalPages})`}
          </Badge>
        </div>
      </div>

      {/* Mappings List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Current Address Mappings
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">Loading address mappings...</p>
            </div>
          ) : filteredMappings.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-8 w-8 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">
                {mappings.length === 0 ? 'No address mappings found. Upload a file to get started.' : 'No mappings match your search.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-700">ERF Number</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Street Number</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Street Name</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Full Address</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Suburb</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Postal Code</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentMappings.map((mapping) => (
                    <tr key={mapping.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-mono text-sm">{mapping.erf_number}</td>
                      <td className="py-3 px-4">{mapping.street_number}</td>
                      <td className="py-3 px-4">{mapping.street_name}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{mapping.full_address}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{mapping.suburb || '-'}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{mapping.postal_code || '-'}</td>
                      <td className="py-3 px-4">
                        <Button
                          onClick={() => deleteMapping(mapping.id)}
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-800 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                Showing {startIndex + 1} to {Math.min(endIndex, filteredMappings.length)} of {filteredMappings.length} entries
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <div className="flex gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCurrentPage(pageNum)}
                        className="w-10"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AddressMappings;
