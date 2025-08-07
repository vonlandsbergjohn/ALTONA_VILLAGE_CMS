import React, { useState, useEffect } from 'react';
import { adminAPI } from '../lib/api';

const AdminCommunication = () => {
  const [activeTab, setActiveTab] = useState('email');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  // Email form state
  const [emailData, setEmailData] = useState({
    recipient_type: 'all',
    subject: '',
    message: ''
  });
  
  // WhatsApp form state
  const [whatsappData, setWhatsappData] = useState({
    recipient_type: 'all',
    message: ''
  });
  
  // Recipients statistics
  const [recipientStats, setRecipientStats] = useState({
    total_users: 0,
    residents: 0,
    owners: 0,
    active_emails: 0,
    active_phones: 0
  });

  useEffect(() => {
    loadRecipientStats();
  }, []);

  const loadRecipientStats = async () => {
    try {
      const response = await adminAPI.getCommunicationStats();
      setRecipientStats(response.data);
    } catch (error) {
      console.error('Error loading recipient stats:', error);
    }
  };

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    if (!emailData.subject.trim() || !emailData.message.trim()) {
      setMessage({ type: 'error', text: 'Subject and message are required' });
      return;
    }

    setLoading(true);
    try {
      const response = await adminAPI.sendBulkEmail(emailData);
      setMessage({ 
        type: 'success', 
        text: `Email sent successfully to ${response.data.sent_count} recipients!`
      });
      
      // Reset form
      setEmailData({
        recipient_type: 'all',
        subject: '',
        message: ''
      });
      
      // Show detailed results if there were failures
      if (response.data.failed_count > 0) {
        setTimeout(() => {
          setMessage({ 
            type: 'warning', 
            text: `${response.data.sent_count} emails sent, ${response.data.failed_count} failed. Check console for details.`
          });
          console.log('Failed emails:', response.data.failed_emails);
        }, 3000);
      }
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to send email: ' + (error.response?.data?.error || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const handleWhatsAppSubmit = async (e) => {
    e.preventDefault();
    if (!whatsappData.message.trim()) {
      setMessage({ type: 'error', text: 'Message is required' });
      return;
    }

    setLoading(true);
    try {
      const response = await adminAPI.sendBulkWhatsApp(whatsappData);
      setMessage({ 
        type: 'success', 
        text: `WhatsApp message sent successfully to ${response.data.sent_count} recipients!`
      });
      
      // Reset form
      setWhatsappData({
        recipient_type: 'all',
        message: ''
      });
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to send WhatsApp: ' + (error.response?.data?.error || error.message) });
    } finally {
      setLoading(false);
    }
  };

  const getRecipientCount = (type) => {
    switch (type) {
      case 'all': return recipientStats.total_users;
      case 'residents': return recipientStats.residents;
      case 'owners': return recipientStats.owners;
      default: return 0;
    }
  };

  const clearMessage = () => {
    setMessage({ type: '', text: '' });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">📧 Communication Center</h1>
        <p className="text-gray-600">Send bulk messages to residents, owners, or all users in the community</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">👥</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-600">Total Users</p>
              <p className="text-2xl font-bold text-blue-900">{recipientStats.total_users}</p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">🏠</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-600">Residents</p>
              <p className="text-2xl font-bold text-green-900">{recipientStats.residents}</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">🏡</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-purple-600">Owners</p>
              <p className="text-2xl font-bold text-purple-900">{recipientStats.owners}</p>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">📧</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-orange-600">Active Emails</p>
              <p className="text-2xl font-bold text-orange-900">{recipientStats.active_emails}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Message Display */}
      {message.text && (
        <div className={`p-4 rounded-md ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' :
          message.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          'bg-yellow-50 text-yellow-700 border border-yellow-200'
        }`}>
          <div className="flex justify-between items-center">
            <span>{message.text}</span>
            <button 
              onClick={clearMessage}
              className="text-sm underline ml-4"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Communication Tabs */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('email')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'email'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📧 Email Communication
            </button>
            <button
              onClick={() => setActiveTab('whatsapp')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'whatsapp'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💬 WhatsApp Communication
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Email Tab */}
          {activeTab === 'email' && (
            <form onSubmit={handleEmailSubmit} className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Send Bulk Email</h3>
                
                {/* Recipient Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recipients
                  </label>
                  <select
                    value={emailData.recipient_type}
                    onChange={(e) => setEmailData(prev => ({ ...prev, recipient_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Users ({getRecipientCount('all')} recipients)</option>
                    <option value="residents">Residents Only ({getRecipientCount('residents')} recipients)</option>
                    <option value="owners">Owners Only ({getRecipientCount('owners')} recipients)</option>
                  </select>
                </div>

                {/* Subject */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject *
                  </label>
                  <input
                    type="text"
                    value={emailData.subject}
                    onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter email subject..."
                    maxLength={200}
                  />
                  <p className="text-xs text-gray-500 mt-1">{emailData.subject.length}/200 characters</p>
                </div>

                {/* Message */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    value={emailData.message}
                    onChange={(e) => setEmailData(prev => ({ ...prev, message: e.target.value }))}
                    rows={8}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your message here..."
                    maxLength={5000}
                  />
                  <p className="text-xs text-gray-500 mt-1">{emailData.message.length}/5000 characters</p>
                </div>

                {/* Preview */}
                {emailData.subject && emailData.message && (
                  <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-md">
                    <h4 className="font-medium text-gray-900 mb-2">Preview:</h4>
                    <div className="text-sm">
                      <p><strong>To:</strong> {emailData.recipient_type === 'all' ? 'All Users' : emailData.recipient_type === 'residents' ? 'Residents' : 'Owners'} ({getRecipientCount(emailData.recipient_type)} recipients)</p>
                      <p><strong>Subject:</strong> {emailData.subject}</p>
                      <div className="mt-2 p-2 bg-white border border-gray-200 rounded">
                        <p className="whitespace-pre-wrap">{emailData.message}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Send Button */}
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-600">
                    This will send to <strong>{getRecipientCount(emailData.recipient_type)}</strong> recipients
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !emailData.subject.trim() || !emailData.message.trim()}
                    className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '📤 Sending...' : '📧 Send Email'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* WhatsApp Tab */}
          {activeTab === 'whatsapp' && (
            <form onSubmit={handleWhatsAppSubmit} className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Send Bulk WhatsApp Message</h3>
                
                {/* Recipient Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recipients
                  </label>
                  <select
                    value={whatsappData.recipient_type}
                    onChange={(e) => setWhatsappData(prev => ({ ...prev, recipient_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value="all">All Users ({recipientStats.active_phones} with phone numbers)</option>
                    <option value="residents">Residents Only</option>
                    <option value="owners">Owners Only</option>
                  </select>
                </div>

                {/* Message */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    value={whatsappData.message}
                    onChange={(e) => setWhatsappData(prev => ({ ...prev, message: e.target.value }))}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="Enter your WhatsApp message here..."
                    maxLength={1000}
                  />
                  <p className="text-xs text-gray-500 mt-1">{whatsappData.message.length}/1000 characters</p>
                </div>

                {/* Preview */}
                {whatsappData.message && (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
                    <h4 className="font-medium text-gray-900 mb-2">Preview:</h4>
                    <div className="text-sm">
                      <p><strong>To:</strong> {whatsappData.recipient_type === 'all' ? 'All Users' : whatsappData.recipient_type === 'residents' ? 'Residents' : 'Owners'} with phone numbers</p>
                      <div className="mt-2 p-3 bg-white border border-green-200 rounded-lg">
                        <p className="whitespace-pre-wrap">{whatsappData.message}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Send Button */}
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-600">
                    This will send to users with registered phone numbers
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !whatsappData.message.trim()}
                    className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? '📱 Sending...' : '💬 Send WhatsApp'}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Communication Guidelines */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-yellow-800 mb-3">📋 Communication Guidelines</h3>
        <div className="text-sm text-yellow-700 space-y-2">
          <p>• <strong>Email:</strong> Best for detailed announcements, documents, and formal communications</p>
          <p>• <strong>WhatsApp:</strong> Best for urgent updates, short notices, and quick community alerts</p>
          <p>• <strong>Recipients:</strong> 'All Users' includes both residents and owners, use specific groups when needed</p>
          <p>• <strong>Privacy:</strong> Always respect resident privacy and only send relevant community information</p>
          <p>• <strong>Frequency:</strong> Avoid over-communication to prevent message fatigue</p>
        </div>
      </div>
    </div>
  );
};

export default AdminCommunication;
