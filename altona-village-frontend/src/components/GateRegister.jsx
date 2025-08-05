import React, { useState, useEffect, useMemo } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Download, RefreshCw, Shield, Users, Car, Building, Filter, X, ChevronUp, ChevronDown, RotateCcw } from 'lucide-react';
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

  // Enhanced filtering and sorting state
  const [filters, setFilters] = useState({
    statusFilter: 'all', // 'all', 'resident', 'owner', 'owner-resident'
    searchTerm: ''
  });
  
  const [sorting, setSorting] = useState({
    column: 'street_name', // default sort by street name
    direction: 'asc' // 'asc' or 'desc'
  });

  console.log('[DEBUG] GateRegister component mounted');

  useEffect(() => {
    console.log('[DEBUG] GateRegister useEffect triggered');
    fetchGateRegister();
  }, []);

  // Memoized filtered and sorted data
  const filteredAndSortedData = useMemo(() => {
    let filtered = [...gateData];

    // Apply status filter
    if (filters.statusFilter !== 'all') {
      filtered = filtered.filter(entry => {
        const status = entry.resident_status?.toLowerCase() || '';
        switch (filters.statusFilter) {
          case 'resident':
            return status === 'resident';
          case 'owner':
            return status === 'owner';
          case 'owner-resident':
            return status === 'owner-resident';
          default:
            return true;
        }
      });
    }

    // Apply search filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      filtered = filtered.filter(entry => 
        (entry.first_name?.toLowerCase() || '').includes(searchLower) ||
        (entry.surname?.toLowerCase() || '').includes(searchLower) ||
        (entry.street_name?.toLowerCase() || '').includes(searchLower) ||
        (entry.street_number?.toString() || '').includes(searchLower) ||
        (entry.erf_number?.toString() || '').includes(searchLower) ||
        (entry.phone_number?.toLowerCase() || '').includes(searchLower) ||
        (entry.intercom_code?.toLowerCase() || '').includes(searchLower) ||
        entry.vehicle_registrations?.some(vehicle => 
          vehicle.toLowerCase().includes(searchLower)
        )
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sorting.column) {
        case 'resident_status':
          aValue = a.resident_status?.toLowerCase() || '';
          bValue = b.resident_status?.toLowerCase() || '';
          break;
        case 'first_name':
          aValue = a.first_name?.toLowerCase() || '';
          bValue = b.first_name?.toLowerCase() || '';
          break;
        case 'surname':
          aValue = a.surname?.toLowerCase() || '';
          bValue = b.surname?.toLowerCase() || '';
          break;
        case 'phone_number':
          aValue = a.phone_number?.toLowerCase() || '';
          bValue = b.phone_number?.toLowerCase() || '';
          break;
        case 'street_nr':
          aValue = parseInt(a.street_number) || 0;
          bValue = parseInt(b.street_number) || 0;
          break;
        case 'street_name':
          aValue = a.street_name?.toLowerCase() || '';
          bValue = b.street_name?.toLowerCase() || '';
          break;
        case 'vehicle_registrations':
          // Sort by first vehicle registration or empty string
          aValue = (a.vehicle_registrations && a.vehicle_registrations.length > 0) 
            ? a.vehicle_registrations[0].toLowerCase() 
            : '';
          bValue = (b.vehicle_registrations && b.vehicle_registrations.length > 0) 
            ? b.vehicle_registrations[0].toLowerCase() 
            : '';
          break;
        case 'erf_nr':
          aValue = parseInt(a.erf_number) || 0;
          bValue = parseInt(b.erf_number) || 0;
          break;
        case 'intercom_code':
          aValue = a.intercom_code?.toLowerCase() || '';
          bValue = b.intercom_code?.toLowerCase() || '';
          break;
        default:
          aValue = '';
          bValue = '';
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sorting.direction === 'asc' ? aValue - bValue : bValue - aValue;
      } else {
        const comparison = aValue.localeCompare(bValue);
        return sorting.direction === 'asc' ? comparison : -comparison;
      }
    });

    return filtered;
  }, [gateData, filters, sorting]);

  // Update stats based on filtered data
  const filteredStats = useMemo(() => {
    const stats = {
      totalEntries: filteredAndSortedData.length,
      residents: 0,
      owners: 0,
      ownerResidents: 0,
      vehiclesTotal: 0
    };

    filteredAndSortedData.forEach(entry => {
      const status = entry.resident_status?.toLowerCase() || '';
      switch (status) {
        case 'resident':
          stats.residents++;
          break;
        case 'owner':
          stats.owners++;
          break;
        case 'owner-resident':
          stats.ownerResidents++;
          break;
      }
      stats.vehiclesTotal += entry.total_vehicles || 0;
    });

    return stats;
  }, [filteredAndSortedData]);

  const fetchGateRegister = async () => {
    try {
      setLoading(true);
      setError('');
      console.log('[DEBUG] Fetching gate register...');
      const response = await adminAPI.getGateRegister();
      console.log('[DEBUG] Gate register response:', response);
      
      if (response.data.success) {
        setGateData(response.data.data);
        calculateStats(response.data.data);
        console.log('[DEBUG] Gate register data loaded successfully');
      } else {
        setError('Failed to load gate register');
        console.error('[DEBUG] Gate register failed:', response.data);
      }
    } catch (error) {
      console.error('[DEBUG] Error fetching gate register:', error);
      setError(error.response?.data?.error || 'Failed to load gate register');
    } finally {
      setLoading(false);
    }
  };

  // Filter and sorting functions
  const handleStatusFilter = (status) => {
    setFilters(prev => ({ ...prev, statusFilter: status }));
  };

  const handleSearchChange = (e) => {
    setFilters(prev => ({ ...prev, searchTerm: e.target.value }));
  };

  const handleSort = (column) => {
    setSorting(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const clearFilters = () => {
    setFilters({
      statusFilter: 'all',
      searchTerm: ''
    });
    setSorting({
      column: 'street_name',
      direction: 'asc'
    });
  };

  const getSortIcon = (column) => {
    if (sorting.column !== column) return null;
    return sorting.direction === 'asc' ? 
      <ChevronUp className="w-4 h-4 ml-1" /> : 
      <ChevronDown className="w-4 h-4 ml-1" />;
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
        case 'Owner':
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
      console.log('[DEBUG] Starting gate register export...');
      
      // Create CSV content from filtered data
      const csvContent = generateCSVFromFilteredData(filteredAndSortedData);
      
      // Create and trigger download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      
      // Generate filename with current filters
      const timestamp = new Date().toISOString().slice(0,19).replace(/:/g, '-');
      const filterSuffix = filters.statusFilter !== 'all' ? `_${filters.statusFilter}` : '';
      const searchSuffix = filters.searchTerm ? `_search` : '';
      link.setAttribute('download', `gate_register${filterSuffix}${searchSuffix}_${timestamp}.csv`);
      
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log('[DEBUG] Gate register export completed');
    } catch (error) {
      console.error('[DEBUG] Export error:', error);
      setError('Failed to export gate register');
    }
  };

  const generateCSVFromFilteredData = (data) => {
    const headers = [
      'RESIDENT STATUS',
      'FIRST NAME', 
      'SURNAME',
      'PHONE NUMBER',
      'STREET NR',
      'STREET NAME',
      'VEHICLE REGISTRATION NR',
      'ERF NR',
      'INTERCOM NR'
    ];

    let csvContent = headers.join(',') + '\n';

    data.forEach(entry => {
      if (entry.vehicle_registrations && entry.vehicle_registrations.length > 0) {
        // Create separate row for each vehicle
        entry.vehicle_registrations.forEach(vehicle => {
          const row = [
            `"${entry.resident_status || ''}"`,
            `"${entry.first_name || ''}"`,
            `"${entry.surname || ''}"`,
            `"${entry.phone_number || ''}"`,
            `"${entry.street_number || ''}"`,
            `"${entry.street_name || ''}"`,
            `"${vehicle || ''}"`,
            `"${entry.erf_number || ''}"`,
            `"${entry.intercom_code || ''}"`
          ];
          csvContent += row.join(',') + '\n';
        });
      } else {
        // No vehicles - single row
        const row = [
          `"${entry.resident_status || ''}"`,
          `"${entry.first_name || ''}"`,
          `"${entry.surname || ''}"`,
          `"${entry.phone_number || ''}"`,
          `"${entry.street_number || ''}"`,
          `"${entry.street_name || ''}"`,
          `""`,
          `"${entry.erf_number || ''}"`,
          `"${entry.intercom_code || ''}"`
        ];
        csvContent += row.join(',') + '\n';
      }
    });

    return csvContent;
  };

  const getStatusBadge = (status) => {
    const variants = {
      'Resident': 'bg-blue-100 text-blue-800',
      'Owner': 'bg-green-100 text-green-800',
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

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center p-8">
          <div className="text-red-600 text-lg font-semibold mb-2">Error Loading Gate Register</div>
          <div className="text-gray-600 mb-4">{error}</div>
          <Button onClick={fetchGateRegister} className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
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
            Export Filtered CSV
          </Button>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters & Search
          </CardTitle>
          <CardDescription>
            Filter by resident status, search, and sort the gate register
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Status Filter Buttons */}
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={filters.statusFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('all')}
              >
                All ({stats.totalEntries})
              </Button>
              <Button
                variant={filters.statusFilter === 'resident' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('resident')}
                className="flex items-center gap-1"
              >
                <Users className="h-3 w-3" />
                Residents ({stats.residents})
              </Button>
              <Button
                variant={filters.statusFilter === 'owner' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('owner')}
                className="flex items-center gap-1"
              >
                <Building className="h-3 w-3" />
                Owners ({stats.owners})
              </Button>
              <Button
                variant={filters.statusFilter === 'owner-resident' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleStatusFilter('owner-resident')}
                className="flex items-center gap-1"
              >
                <Shield className="h-3 w-3" />
                Owner-Residents ({stats.ownerResidents})
              </Button>
            </div>

            {/* Search Input */}
            <div className="flex gap-2 flex-1">
              <input
                type="text"
                placeholder="Search by name, street, ERF, phone, or vehicle..."
                value={filters.searchTerm}
                onChange={handleSearchChange}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {(filters.statusFilter !== 'all' || filters.searchTerm) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearFilters}
                  className="flex items-center gap-1"
                >
                  <RotateCcw className="h-3 w-3" />
                  Clear
                </Button>
              )}
            </div>
          </div>

          {/* Active Filters Display */}
          {(filters.statusFilter !== 'all' || filters.searchTerm) && (
            <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">Active filters:</span>
              {filters.statusFilter !== 'all' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Status: {filters.statusFilter}
                  <X 
                    className="h-3 w-3 cursor-pointer hover:text-red-600" 
                    onClick={() => handleStatusFilter('all')}
                  />
                </Badge>
              )}
              {filters.searchTerm && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Search: "{filters.searchTerm}"
                  <X 
                    className="h-3 w-3 cursor-pointer hover:text-red-600" 
                    onClick={() => setFilters(prev => ({ ...prev, searchTerm: '' }))}
                  />
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center p-6">
            <Users className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Total Entries</p>
              <p className="text-2xl font-bold">{filteredStats.totalEntries}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="flex items-center p-6">
            <Building className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Owner-Residents</p>
              <p className="text-2xl font-bold">{filteredStats.ownerResidents}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="flex items-center p-6">
            <Users className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Residents Only</p>
              <p className="text-2xl font-bold">{filteredStats.residents}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="flex items-center p-6">
            <Car className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-muted-foreground">Total Vehicles</p>
              <p className="text-2xl font-bold">{filteredStats.vehiclesTotal}</p>
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
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('resident_status')}
                  >
                    <div className="flex items-center">
                      Resident Status
                      {getSortIcon('resident_status')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('first_name')}
                  >
                    <div className="flex items-center">
                      Name
                      {getSortIcon('first_name')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('surname')}
                  >
                    <div className="flex items-center">
                      Surname
                      {getSortIcon('surname')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('phone_number')}
                  >
                    <div className="flex items-center">
                      Phone Number
                      {getSortIcon('phone_number')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('street_nr')}
                  >
                    <div className="flex items-center">
                      Street Nr
                      {getSortIcon('street_nr')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('street_name')}
                  >
                    <div className="flex items-center">
                      Street Name
                      {getSortIcon('street_name')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('vehicle_registrations')}
                  >
                    <div className="flex items-center">
                      Vehicle Registration
                      {getSortIcon('vehicle_registrations')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('erf_nr')}
                  >
                    <div className="flex items-center">
                      ERF Nr
                      {getSortIcon('erf_nr')}
                    </div>
                  </TableHead>
                  <TableHead 
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort('intercom_code')}
                  >
                    <div className="flex items-center">
                      Intercom Nr
                      {getSortIcon('intercom_code')}
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedData.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-6 text-muted-foreground">
                      No gate register entries found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAndSortedData.map((entry, index) => (
                    <React.Fragment key={index}>
                      {/* If multiple vehicles, create a row for each vehicle */}
                      {entry.vehicle_registrations && entry.vehicle_registrations.length > 0 ? (
                        entry.vehicle_registrations.map((vehicle, vehicleIndex) => (
                          <TableRow key={`${index}-${vehicleIndex}`}>
                            <TableCell>
                              {vehicleIndex === 0 && getStatusBadge(entry.resident_status)}
                            </TableCell>
                            <TableCell className="font-medium">
                              {vehicleIndex === 0 ? entry.first_name : ''}
                            </TableCell>
                            <TableCell className="font-medium">
                              {vehicleIndex === 0 ? entry.surname : ''}
                            </TableCell>
                            <TableCell>
                              {vehicleIndex === 0 && entry.phone_number && (
                                <span className="font-mono bg-green-100 px-2 py-1 rounded text-sm">
                                  {entry.phone_number}
                                </span>
                              )}
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
                          <TableCell className="font-medium">{entry.first_name}</TableCell>
                          <TableCell className="font-medium">{entry.surname}</TableCell>
                          <TableCell>
                            {entry.phone_number && (
                              <span className="font-mono bg-green-100 px-2 py-1 rounded text-sm">
                                {entry.phone_number}
                              </span>
                            )}
                          </TableCell>
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
            <span>All status groups (<strong>Residents</strong>, <strong>Owner-Residents</strong>, and <strong>Owners</strong>) can have intercom codes if assigned</span>
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
