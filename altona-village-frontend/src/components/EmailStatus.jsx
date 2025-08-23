import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mail, CheckCircle, XCircle, Clock } from 'lucide-react';

// Helper to get JWT token from localStorage
const getToken = () => localStorage.getItem('token');

const EmailStatus = () => {
  const [emailData, setEmailData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('https://altona-village-backend.onrender.com/api/admin/email-status', {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    })
      .then(res => res.json())
      .then(data => {
        setEmailData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching email status:', error);
        setLoading(false);
      });
  }, []);

  const getEmailStatusBadge = (user) => {
    if (user.status === 'pending') {
      return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
    }
    
    if (user.status === 'active' && user.approval_email_sent) {
      return <Badge variant="default" className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" /> Approved & Emailed</Badge>;
    }
    
    if (user.status === 'active' && !user.approval_email_sent) {
      return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" /> Approved (Email Failed)</Badge>;
    }
    
    if (user.rejection_email_sent) {
      return <Badge variant="outline" className="border-red-500 text-red-600"><Mail className="w-3 h-3 mr-1" /> Rejected & Emailed</Badge>;
    }
    
    return <Badge variant="outline">Unknown Status</Badge>;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading) return <div className="p-4">Loading email status...</div>;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="w-5 h-5" />
          Email Notification Status
        </CardTitle>
        <CardDescription>
          Track email notifications sent to users for approvals and rejections
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {emailData.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No users found.
            </div>
          ) : (
            <div className="grid gap-4">
              {emailData.map(user => (
                <div key={user.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold">{user.name || user.email}</h3>
                      <p className="text-sm text-gray-600">{user.email}</p>
                    </div>
                    {getEmailStatusBadge(user)}
                  </div>
                  
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>Account Status: <span className="font-medium">{user.status}</span> | Role: <span className="font-medium">{user.role}</span></div>
                    
                    {user.approval_email_sent_at && (
                      <div className="text-green-600">
                        ✅ Approval email sent: {formatDate(user.approval_email_sent_at)}
                      </div>
                    )}
                    
                    {user.rejection_email_sent_at && (
                      <div className="text-red-600">
                        📧 Rejection email sent: {formatDate(user.rejection_email_sent_at)}
                      </div>
                    )}
                    
                    {user.status === 'active' && !user.approval_email_sent && (
                      <div className="text-amber-600">
                        ⚠️ User is approved but no confirmation email was sent
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default EmailStatus;
