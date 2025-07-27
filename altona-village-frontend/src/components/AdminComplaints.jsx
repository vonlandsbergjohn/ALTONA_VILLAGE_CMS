import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api.js';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, Calendar, Clock, AlertCircle, CheckCircle, XCircle, FileText, User, MapPin, Phone, Mail, Edit } from 'lucide-react';

const AdminComplaints = () => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [isUpdateDialogOpen, setIsUpdateDialogOpen] = useState(false);
  const [updateData, setUpdateData] = useState({
    status: '',
    response: '',
    assigned_to: ''
  });

  useEffect(() => {
    fetchComplaints();
  }, []);

  const fetchComplaints = async () => {
    try {
      const response = await adminAPI.getAllComplaints();
      setComplaints(response.data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load complaints' });
      console.error('Error fetching complaints:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateComplaint = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await adminAPI.updateComplaint(selectedComplaint.id, updateData);
      setMessage({ type: 'success', text: 'Complaint updated successfully' });
      await fetchComplaints();
      setIsUpdateDialogOpen(false);
      setSelectedComplaint(null);
      setUpdateData({ status: '', response: '', assigned_to: '' });
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.message || 'Failed to update complaint' 
      });
    } finally {
      setLoading(false);
    }
  };

  const openUpdateDialog = (complaint) => {
    setSelectedComplaint(complaint);
    setUpdateData({
      status: complaint.status || '',
      response: complaint.response || '',
      assigned_to: complaint.assigned_to || ''
    });
    setIsUpdateDialogOpen(true);
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'open': 
      case 'submitted': 
        return 'bg-blue-100 text-blue-800';
      case 'in_progress': 
      case 'assigned': 
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved': 
      case 'completed': 
        return 'bg-green-100 text-green-800';
      case 'closed': 
        return 'bg-gray-100 text-gray-800';
      case 'rejected': 
        return 'bg-red-100 text-red-800';
      default: 
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'open': 
      case 'submitted': 
        return <AlertCircle className="w-4 h-4" />;
      case 'in_progress': 
      case 'assigned': 
        return <Clock className="w-4 h-4" />;
      case 'resolved': 
      case 'completed': 
        return <CheckCircle className="w-4 h-4" />;
      case 'closed': 
        return <XCircle className="w-4 h-4" />;
      case 'rejected': 
        return <XCircle className="w-4 h-4" />;
      default: 
        return <FileText className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high': 
      case 'urgent': 
        return 'bg-red-100 text-red-800';
      case 'medium': 
        return 'bg-yellow-100 text-yellow-800';
      case 'low': 
        return 'bg-green-100 text-green-800';
      default: 
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filterComplaints = (status) => {
    if (status === 'all') return complaints;
    return complaints.filter(complaint => 
      complaint.status?.toLowerCase() === status.toLowerCase()
    );
  };

  const openComplaints = filterComplaints('open').length + filterComplaints('submitted').length + filterComplaints('in_progress').length + filterComplaints('assigned').length;
  const resolvedComplaints = filterComplaints('resolved').length + filterComplaints('completed').length;
  const closedComplaints = filterComplaints('closed').length;

  if (loading && complaints.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Complaints Management</h1>
          <p className="text-gray-600">Manage and respond to resident complaints and service requests</p>
        </div>
      </div>

      {message.text && (
        <Alert className={message.type === 'error' ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
          <AlertDescription className={message.type === 'error' ? 'text-red-800' : 'text-green-800'}>
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <AlertCircle className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Open</p>
                <p className="text-2xl font-bold text-gray-900">{openComplaints}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Resolved</p>
                <p className="text-2xl font-bold text-gray-900">{resolvedComplaints}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-gray-100 rounded-lg">
                <XCircle className="w-6 h-6 text-gray-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Closed</p>
                <p className="text-2xl font-bold text-gray-900">{closedComplaints}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <MessageSquare className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total</p>
                <p className="text-2xl font-bold text-gray-900">{complaints.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <MessageSquare className="w-5 h-5 mr-2" />
            All Complaints
          </CardTitle>
          <CardDescription>
            View and manage all resident complaints and service requests
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="all" className="space-y-4">
            <TabsList>
              <TabsTrigger value="all">All ({complaints.length})</TabsTrigger>
              <TabsTrigger value="open">Open ({openComplaints})</TabsTrigger>
              <TabsTrigger value="resolved">Resolved ({resolvedComplaints})</TabsTrigger>
              <TabsTrigger value="closed">Closed ({closedComplaints})</TabsTrigger>
            </TabsList>

            {['all', 'open', 'resolved', 'closed'].map((tabValue) => (
              <TabsContent key={tabValue} value={tabValue}>
                {filterComplaints(tabValue === 'all' ? 'all' : tabValue).length === 0 ? (
                  <div className="text-center py-8">
                    <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No {tabValue === 'all' ? '' : tabValue} complaints
                    </h3>
                    <p className="text-gray-600">
                      {tabValue === 'all' 
                        ? "No complaints have been submitted yet." 
                        : `There are no ${tabValue} complaints at the moment.`
                      }
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>ID</TableHead>
                          <TableHead>Subject</TableHead>
                          <TableHead>Category</TableHead>
                          <TableHead>Priority</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Resident</TableHead>
                          <TableHead>Submitted</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filterComplaints(tabValue === 'all' ? 'all' : tabValue).map((complaint) => (
                          <TableRow key={complaint.id}>
                            <TableCell className="font-mono text-sm">
                              #{complaint.id}
                            </TableCell>
                            <TableCell className="max-w-xs">
                              <div className="truncate font-medium">{complaint.subject}</div>
                              <div className="text-sm text-gray-500 truncate">{complaint.description}</div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="capitalize">
                                {complaint.category}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge className={getPriorityColor(complaint.priority)}>
                                {complaint.priority?.toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge className={getStatusColor(complaint.status)}>
                                <span className="flex items-center">
                                  {getStatusIcon(complaint.status)}
                                  <span className="ml-1 capitalize">{complaint.status}</span>
                                </span>
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center">
                                <User className="w-4 h-4 mr-2 text-gray-400" />
                                <div>
                                  <div className="font-medium">{complaint.resident_name || 'Unknown'}</div>
                                  <div className="text-sm text-gray-500">{complaint.resident_email || ''}</div>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center text-sm text-gray-500">
                                <Calendar className="w-4 h-4 mr-1" />
                                {complaint.created_at ? new Date(complaint.created_at).toLocaleDateString() : 'N/A'}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openUpdateDialog(complaint)}
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                Update
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Update Complaint Dialog */}
      <Dialog open={isUpdateDialogOpen} onOpenChange={setIsUpdateDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Update Complaint #{selectedComplaint?.id}</DialogTitle>
            <DialogDescription>
              Update the status and provide a response to the resident
            </DialogDescription>
          </DialogHeader>
          
          {selectedComplaint && (
            <div className="space-y-4">
              {/* Complaint Details */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Complaint Details</h4>
                <div className="space-y-2 text-sm">
                  <div><strong>Subject:</strong> {selectedComplaint.subject}</div>
                  <div><strong>Category:</strong> {selectedComplaint.category}</div>
                  <div><strong>Priority:</strong> {selectedComplaint.priority}</div>
                  <div><strong>Description:</strong> {selectedComplaint.description}</div>
                  <div><strong>Resident:</strong> {selectedComplaint.resident_name} ({selectedComplaint.resident_email})</div>
                  <div><strong>Submitted:</strong> {selectedComplaint.created_at ? new Date(selectedComplaint.created_at).toLocaleDateString() : 'N/A'}</div>
                </div>
              </div>

              <form onSubmit={handleUpdateComplaint} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="status">Status *</Label>
                    <select
                      id="status"
                      value={updateData.status}
                      onChange={(e) => setUpdateData({...updateData, status: e.target.value})}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      required
                    >
                      <option value="">Select status</option>
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="assigned_to">Assigned To</Label>
                    <Input
                      id="assigned_to"
                      value={updateData.assigned_to}
                      onChange={(e) => setUpdateData({...updateData, assigned_to: e.target.value})}
                      placeholder="Assign to staff member"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="response">Response to Resident</Label>
                  <Textarea
                    id="response"
                    value={updateData.response}
                    onChange={(e) => setUpdateData({...updateData, response: e.target.value})}
                    placeholder="Provide an update or response to the resident..."
                    rows={4}
                  />
                </div>
                <DialogFooter>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setIsUpdateDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Updating...' : 'Update Complaint'}
                  </Button>
                </DialogFooter>
              </form>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminComplaints;
