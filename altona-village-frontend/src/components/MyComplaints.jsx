import { useState, useEffect } from 'react';
import { residentAPI } from '@/lib/api.js';
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
import { MessageSquare, Plus, Calendar, Clock, AlertCircle, CheckCircle, XCircle, FileText } from 'lucide-react';

const MyComplaints = () => {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    category: '',
    priority: 'medium'
  });

  useEffect(() => {
    fetchComplaints();
  }, []);

  const fetchComplaints = async () => {
    try {
      const response = await residentAPI.getMyComplaints();
      setComplaints(response.data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load complaints' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      subject: '',
      description: '',
      category: '',
      priority: 'medium'
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      await residentAPI.submitComplaint(formData);
      setMessage({ type: 'success', text: 'Complaint submitted successfully' });
      await fetchComplaints();
      setIsDialogOpen(false);
      resetForm();
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.message || 'Failed to submit complaint' 
      });
    } finally {
      setLoading(false);
    }
  };

  const viewComplaint = async (complaintId) => {
    try {
      const response = await residentAPI.getComplaint(complaintId);
      setSelectedComplaint(response.data);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load complaint details' });
    }
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
          <h1 className="text-3xl font-bold text-gray-900">My Complaints</h1>
          <p className="text-gray-600">Track and manage your submitted complaints and service requests</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="w-4 h-4 mr-2" />
              Submit Complaint
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Submit New Complaint</DialogTitle>
              <DialogDescription>
                Describe your issue or service request. Provide as much detail as possible to help us resolve it quickly.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="subject">Subject *</Label>
                <Input
                  id="subject"
                  value={formData.subject}
                  onChange={(e) => setFormData({...formData, subject: e.target.value})}
                  placeholder="Brief description of the issue"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">Category *</Label>
                  <select
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    required
                  >
                    <option value="">Select category</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="security">Security</option>
                    <option value="noise">Noise Complaint</option>
                    <option value="utilities">Utilities</option>
                    <option value="garden">Garden/Landscaping</option>
                    <option value="roads">Roads/Infrastructure</option>
                    <option value="general">General Inquiry</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <select
                    id="priority"
                    value={formData.priority}
                    onChange={(e) => setFormData({...formData, priority: e.target.value})}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Provide detailed information about the issue, including location, time, and any relevant circumstances..."
                  rows={4}
                  required
                />
              </div>
              <DialogFooter>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Submitting...' : 'Submit Complaint'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
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
            Complaint History
          </CardTitle>
          <CardDescription>
            View and track all your submitted complaints and service requests
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
                    <p className="text-gray-600 mb-4">
                      {tabValue === 'all' 
                        ? "You haven't submitted any complaints yet." 
                        : `You don't have any ${tabValue} complaints.`
                      }
                    </p>
                    {tabValue === 'all' && (
                      <Button onClick={() => setIsDialogOpen(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Submit Your First Complaint
                      </Button>
                    )}
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Subject</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Submitted</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filterComplaints(tabValue === 'all' ? 'all' : tabValue).map((complaint) => (
                        <TableRow key={complaint.id}>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="font-medium">{complaint.subject}</div>
                              <div className="text-sm text-gray-500 truncate max-w-xs">
                                {complaint.description}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {complaint.category?.charAt(0).toUpperCase() + complaint.category?.slice(1) || 'General'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className={getPriorityColor(complaint.priority)}>
                              {complaint.priority?.toUpperCase() || 'MEDIUM'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center">
                              <Badge className={getStatusColor(complaint.status)}>
                                <span className="flex items-center">
                                  {getStatusIcon(complaint.status)}
                                  <span className="ml-1">
                                    {complaint.status?.toUpperCase() || 'SUBMITTED'}
                                  </span>
                                </span>
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-gray-500">
                            <div className="flex items-center">
                              <Calendar className="w-4 h-4 mr-1" />
                              {complaint.created_at ? new Date(complaint.created_at).toLocaleDateString() : 'N/A'}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => viewComplaint(complaint.id)}
                            >
                              View Details
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Complaint Details Dialog */}
      <Dialog open={!!selectedComplaint} onOpenChange={() => setSelectedComplaint(null)}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Complaint Details</DialogTitle>
            <DialogDescription>
              View the full details and status of your complaint
            </DialogDescription>
          </DialogHeader>
          {selectedComplaint && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-gray-500">Reference ID</Label>
                  <p className="text-sm font-mono">{selectedComplaint.id}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Status</Label>
                  <Badge className={getStatusColor(selectedComplaint.status)}>
                    {selectedComplaint.status?.toUpperCase() || 'SUBMITTED'}
                  </Badge>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Category</Label>
                  <p className="text-sm">{selectedComplaint.category?.charAt(0).toUpperCase() + selectedComplaint.category?.slice(1) || 'General'}</p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-gray-500">Priority</Label>
                  <Badge className={getPriorityColor(selectedComplaint.priority)}>
                    {selectedComplaint.priority?.toUpperCase() || 'MEDIUM'}
                  </Badge>
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Subject</Label>
                <p className="text-sm font-medium">{selectedComplaint.subject}</p>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Description</Label>
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm whitespace-pre-wrap">{selectedComplaint.description}</p>
                </div>
              </div>
              <div>
                <Label className="text-sm font-medium text-gray-500">Submitted</Label>
                <p className="text-sm flex items-center">
                  <Calendar className="w-4 h-4 mr-1" />
                  {selectedComplaint.created_at ? new Date(selectedComplaint.created_at).toLocaleString() : 'N/A'}
                </p>
              </div>
              {selectedComplaint.admin_response && (
                <div>
                  <Label className="text-sm font-medium text-gray-500">Admin Response</Label>
                  <div className="bg-blue-50 p-3 rounded-md">
                    <p className="text-sm">{selectedComplaint.admin_response}</p>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setSelectedComplaint(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MyComplaints;
