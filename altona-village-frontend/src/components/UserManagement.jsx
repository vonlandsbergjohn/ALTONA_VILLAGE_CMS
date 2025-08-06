import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { 
  Users, 
  Archive, 
  Trash2, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  User,
  Calendar,
  Search,
  RotateCcw,
  Settings
} from 'lucide-react';
import { format } from 'date-fns';

const UserManagement = () => {
  const [activeTab, setActiveTab] = useState('inactive');
  const [inactiveUsers, setInactiveUsers] = useState([]);
  const [archivedUsers, setArchivedUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Dialog states
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showBulkArchiveDialog, setShowBulkArchiveDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [archiveReason, setArchiveReason] = useState('');
  const [bulkArchiveDays, setBulkArchiveDays] = useState(30);

  useEffect(() => {
    if (activeTab === 'inactive') {
      fetchInactiveUsers();
    } else if (activeTab === 'archived') {
      fetchArchivedUsers();
    }
  }, [activeTab]);

  const fetchInactiveUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/users/inactive', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setInactiveUsers(data.users || []);
      } else {
        setError('Failed to fetch inactive users');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchArchivedUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/users/archived', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setArchivedUsers(data.users || []);
      } else {
        setError('Failed to fetch archived users');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const archiveUser = async () => {
    if (!selectedUser) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${selectedUser.id}/archive`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          reason: archiveReason || 'Archived by admin'
        })
      });

      if (response.ok) {
        setSuccess(`User ${selectedUser.full_name} archived successfully`);
        setShowArchiveDialog(false);
        setArchiveReason('');
        setSelectedUser(null);
        fetchInactiveUsers();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to archive user');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const unarchiveUser = async (user) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${user.id}/unarchive`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setSuccess(`User ${user.full_name} unarchived successfully`);
        fetchArchivedUsers();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to unarchive user');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const permanentlyDeleteUser = async () => {
    if (!selectedUser) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/users/${selectedUser.id}/delete`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          confirm: true
        })
      });

      if (response.ok) {
        setSuccess(`User ${selectedUser.full_name} permanently deleted`);
        setShowDeleteDialog(false);
        setSelectedUser(null);
        fetchArchivedUsers();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to delete user');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const bulkArchiveOldUsers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/users/archive-old', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          days: bulkArchiveDays,
          reason: `Auto-archived: inactive for ${bulkArchiveDays}+ days`
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(data.message);
        setShowBulkArchiveDialog(false);
        fetchInactiveUsers();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to bulk archive users');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filterUsers = (users) => {
    if (!searchTerm) return users;
    return users.filter(user => 
      user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.erfs?.some(erf => erf.erf_number?.toString().includes(searchTerm))
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'PPp');
    } catch {
      return 'Invalid date';
    }
  };

  const UserCard = ({ user, isArchived = false }) => (
    <Card className="mb-4">
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-3">
            <User className="h-5 w-5 text-gray-400" />
            <div>
              <h3 className="font-semibold">{user.full_name}</h3>
              <p className="text-sm text-gray-600">{user.email}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={isArchived ? "secondary" : "destructive"}>
              {isArchived ? 'Archived' : 'Inactive'}
            </Badge>
            {user.role === 'admin' && (
              <Badge variant="outline">Admin</Badge>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <h4 className="font-medium mb-2">ERF Information</h4>
            {user.erfs && user.erfs.length > 0 ? (
              user.erfs.map((erf, index) => (
                <div key={index} className="text-sm mb-1">
                  <Badge variant="outline" className="mr-2">
                    ERF {erf.erf_number}
                  </Badge>
                  <span className="text-gray-600">{erf.type}</span>
                  {erf.migration_date && (
                    <div className="text-xs text-gray-500 mt-1">
                      Migrated: {formatDate(erf.migration_date)}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <span className="text-sm text-gray-500">No ERF information</span>
            )}
          </div>

          <div>
            <h4 className="font-medium mb-2">Dates</h4>
            <div className="text-sm space-y-1">
              <div>
                <strong>Created:</strong> {formatDate(user.created_at)}
              </div>
              <div>
                <strong>Last Updated:</strong> {formatDate(user.updated_at)}
              </div>
              {isArchived && user.archived_at && (
                <>
                  <div>
                    <strong>Archived:</strong> {formatDate(user.archived_at)}
                  </div>
                  {user.archived_by_user && (
                    <div>
                      <strong>Archived By:</strong> {user.archived_by_user}
                    </div>
                  )}
                  {user.archive_reason && (
                    <div>
                      <strong>Reason:</strong> {user.archive_reason}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-2">
          {isArchived ? (
            <>
              <Button
                onClick={() => unarchiveUser(user)}
                disabled={loading}
                variant="outline"
                size="sm"
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Unarchive
              </Button>
              <Button
                onClick={() => {
                  setSelectedUser(user);
                  setShowDeleteDialog(true);
                }}
                disabled={loading}
                variant="destructive"
                size="sm"
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete Permanently
              </Button>
            </>
          ) : (
            <Button
              onClick={() => {
                setSelectedUser(user);
                setShowArchiveDialog(true);
              }}
              disabled={loading}
              variant="outline"
              size="sm"
            >
              <Archive className="h-4 w-4 mr-1" />
              Archive
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">User Management</h1>
          <p className="text-gray-600">Manage inactive and archived users</p>
        </div>
        <Button
          onClick={() => setShowBulkArchiveDialog(true)}
          variant="outline"
        >
          <Settings className="h-4 w-4 mr-2" />
          Bulk Actions
        </Button>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50 mb-4">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-600">{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50 mb-4">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-600">{success}</AlertDescription>
        </Alert>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
            <Input
              placeholder="Search by name, email, or ERF number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="inactive" className="flex items-center">
            <Clock className="h-4 w-4 mr-2" />
            Inactive Users ({inactiveUsers.length})
          </TabsTrigger>
          <TabsTrigger value="archived" className="flex items-center">
            <Archive className="h-4 w-4 mr-2" />
            Archived Users ({archivedUsers.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="inactive" className="mt-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold mb-2">Inactive Users</h2>
            <p className="text-gray-600">
              These users are inactive but not yet archived. You can archive them to move them out of the main system.
            </p>
          </div>

          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2">Loading inactive users...</p>
            </div>
          ) : filterUsers(inactiveUsers).length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No inactive users found</p>
              </CardContent>
            </Card>
          ) : (
            <div>
              {filterUsers(inactiveUsers).map(user => (
                <UserCard key={user.id} user={user} isArchived={false} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="archived" className="mt-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold mb-2">Archived Users</h2>
            <p className="text-gray-600">
              These users have been archived. You can unarchive them to restore to inactive status, or permanently delete them.
            </p>
          </div>

          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2">Loading archived users...</p>
            </div>
          ) : filterUsers(archivedUsers).length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Archive className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No archived users found</p>
              </CardContent>
            </Card>
          ) : (
            <div>
              {filterUsers(archivedUsers).map(user => (
                <UserCard key={user.id} user={user} isArchived={true} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Archive User Dialog */}
      <Dialog open={showArchiveDialog} onOpenChange={setShowArchiveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive User</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>
              Are you sure you want to archive <strong>{selectedUser?.full_name}</strong>?
              This will move them out of the active system but keep their data for potential restoration.
            </p>
            <div>
              <label className="text-sm font-medium">Reason (optional)</label>
              <Textarea
                value={archiveReason}
                onChange={(e) => setArchiveReason(e.target.value)}
                placeholder="Enter reason for archiving..."
                rows="3"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowArchiveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={archiveUser} disabled={loading}>
              {loading ? 'Archiving...' : 'Archive User'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Permanently Delete User</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-600">
                <strong>Warning:</strong> This action cannot be undone. All user data, including ERF associations and vehicle records, will be permanently deleted.
              </AlertDescription>
            </Alert>
            <p>
              Are you sure you want to permanently delete <strong>{selectedUser?.full_name}</strong> ({selectedUser?.email})?
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={permanentlyDeleteUser} disabled={loading}>
              {loading ? 'Deleting...' : 'Delete Permanently'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Archive Dialog */}
      <Dialog open={showBulkArchiveDialog} onOpenChange={setShowBulkArchiveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Archive Old Users</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p>Archive all inactive users that have been inactive for more than a specified number of days.</p>
            <div>
              <label className="text-sm font-medium">Days threshold</label>
              <Input
                type="number"
                value={bulkArchiveDays}
                onChange={(e) => setBulkArchiveDays(parseInt(e.target.value) || 30)}
                min="1"
                max="365"
              />
              <p className="text-xs text-gray-500 mt-1">
                Users inactive for more than {bulkArchiveDays} days will be archived
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBulkArchiveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={bulkArchiveOldUsers} disabled={loading}>
              {loading ? 'Archiving...' : 'Archive Old Users'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;
