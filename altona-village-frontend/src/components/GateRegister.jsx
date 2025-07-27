import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Download, RefreshCw, Shield, Users, Car, Building } from 'lucide-react';
import { adminAPI } from '../lib/api';

const GateRegister = () => {
  const [gateData, setGateData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    totalEntries: 0,
    residents: 0,
    owners: 0,
    ownerResidents: 0,
    vehiclesTotal: 0
  });

  useEffect(() => {
    fetchGateRegister();
  }, []);

  const fetchGateRegister = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await adminAPI.getGateRegister();
      
      if (response.data.success) {
        setGateData(response.data.data);
        calculateStats(response.data.data);
      } else {
        setError('Failed to load gate register');
      }
    } catch (error) {
      console.error('Error fetching gate register:', error);
      setError(error.response?.data?.error || 'Failed to load gate register');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (data) => {
    const stats = {
      totalEntries: data.length,
      residents: 0,
      owners: 0,
      ownerResidents: 0,
      vehiclesTotal: 0
    };

    data.forEach(entry => {
      switch (entry.resident_status) {
        case 'Resident':
          stats.residents++;
          break;
        case 'Non-Resident Owner':
          stats.owners++;
          break;
        case 'Owner-Resident':
          stats.ownerResidents++;
          break;
      }
      stats.vehiclesTotal += entry.vehicle_registrations?.length || 0;
    });

    setStats(stats);
  };

  const handleExport = async () => {
    try {
      const response = await adminAPI.exportGateRegister();
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with current date
      const date = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `gate_register_${date}.csv`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting gate register:', error);
      setError('Failed to export gate register');
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      'Resident': 'bg-blue-100 text-blue-800',
      'Non-Resident Owner': 'bg-green-100 text-green-800',
      'Owner-Resident': 'bg-purple-100 text-purple-800'
    };
    
    return (
      <Badge className={variants[status] || 'bg-gray-100 text-gray-800'}>
        {status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin mr-2" />
        Loading gate register...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="h-6 w-6" />
            Gate Security Register
          </h1>
          <p className="text-muted-foreground mt-1">
            Comprehensive register for security guards - sorted alphabetically by street name
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={fetchGateRegister}
            disabled={loading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button 
            onClick={handleExport}
            className="bg-green-600 hover:bg-green-700"
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center p-6">
            <Users className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Total Entries</p>
              <p className="text-2xl font-bold">{stats.totalEntries}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="flex items-center p-6">
            <Building className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Owner-Residents</p>
              <p className="text-2xl font-bold">{stats.ownerResidents}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="flex items-center p-6">
            <Users className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Residents Only</p>
              <p className="text-2xl font-bold">{stats.residents}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="flex items-center p-6">
            <Car className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Total Vehicles</p>
              <p className="text-2xl font-bold">{stats.vehiclesTotal}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Gate Register Table */}
      <Card>
        <CardHeader>
          <CardTitle>Security Gate Register</CardTitle>
          <CardDescription>
            Sorted alphabetically by street name. All status groups can have intercom codes if assigned.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Resident Status</TableHead>
                  <TableHead>Surname</TableHead>
                  <TableHead>Street Nr</TableHead>
                  <TableHead>Street Name</TableHead>
                  <TableHead>Vehicle Registration</TableHead>
                  <TableHead>ERF Nr</TableHead>
                  <TableHead>Intercom Nr</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {gateData.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-6 text-muted-foreground">
                      No gate register entries found
                    </TableCell>
                  </TableRow>
                ) : (
                  gateData.map((entry, index) => (
                    <React.Fragment key={index}>
                      {/* If multiple vehicles, create a row for each vehicle */}
                      {entry.vehicle_registrations && entry.vehicle_registrations.length > 0 ? (
                        entry.vehicle_registrations.map((vehicle, vehicleIndex) => (
                          <TableRow key={`${index}-${vehicleIndex}`}>
                            <TableCell>
                              {vehicleIndex === 0 && getStatusBadge(entry.resident_status)}
                            </TableCell>
                            <TableCell className="font-medium">
                              {vehicleIndex === 0 ? entry.surname : ''}
                            </TableCell>
                            <TableCell>
                              {vehicleIndex === 0 ? entry.street_number : ''}
                            </TableCell>
                            <TableCell>
                              {vehicleIndex === 0 ? entry.street_name : ''}
                            </TableCell>
                            <TableCell>
                              <span className="font-mono bg-gray-100 px-2 py-1 rounded text-sm">
                                {vehicle}
                              </span>
                            </TableCell>
                            <TableCell>
                              {vehicleIndex === 0 ? entry.erf_number : ''}
                            </TableCell>
                            <TableCell>
                              {vehicleIndex === 0 && entry.intercom_code && (
                                <span className="font-mono bg-blue-100 px-2 py-1 rounded text-sm">
                                  {entry.intercom_code}
                                </span>
                              )}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        // No vehicles - still show the entry
                        <TableRow key={index}>
                          <TableCell>{getStatusBadge(entry.resident_status)}</TableCell>
                          <TableCell className="font-medium">{entry.surname}</TableCell>
                          <TableCell>{entry.street_number}</TableCell>
                          <TableCell>{entry.street_name}</TableCell>
                          <TableCell>
                            <span className="text-muted-foreground text-sm">No vehicles</span>
                          </TableCell>
                          <TableCell>{entry.erf_number}</TableCell>
                          <TableCell>
                            {entry.intercom_code && (
                              <span className="font-mono bg-blue-100 px-2 py-1 rounded text-sm">
                                {entry.intercom_code}
                              </span>
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Instructions for Guards */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Instructions for Security Guards</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <span className="font-semibold text-blue-600">•</span>
            <span>All status groups (<strong>Residents</strong>, <strong>Owner-Residents</strong>, and <strong>Non-Resident Owners</strong>) can have intercom codes if assigned</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold text-green-600">•</span>
            <span>If no intercom code is shown, verify identity and contact using alternative methods</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold text-purple-600">•</span>
            <span>Register is sorted alphabetically by street name for quick lookup</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="font-semibold text-red-600">•</span>
            <span>Each resident/owner may have multiple vehicle registrations listed</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GateRegister;
