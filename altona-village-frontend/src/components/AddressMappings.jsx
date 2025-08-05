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

  useEffect(() => {
    loadMappings();
  }, []);

  const loadMappings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/address-mappings', {
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

    setUploading(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/admin/address-mappings/upload', {
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
        await loadMappings();
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (error) {
      setError('Network error during upload');
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/address-mappings/template', {
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

  const clearAllMappings = async () => {
    if (!window.confirm('Are you sure you want to clear all address mappings? This cannot be undone.')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/address-mappings/clear', {
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
            The file should contain columns: erf_number, street_number, street_name
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

          <div className="flex gap-2">
            <Button onClick={downloadTemplate} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download Template
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
                  {filteredMappings.map((mapping) => (
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
        </CardContent>
      </Card>
    </div>
  );
};

export default AddressMappings;
