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

  // Individual communication state
  const [individualData, setIndividualData] = useState({
    erf_number: '',
    subject: '',
    message: ''
  });
  
  const [foundUser, setFoundUser] = useState(null);
  const [searchingUser, setSearchingUser] = useState(false);
  
  // Recipients statistics
  const [recipientStats, setRecipientStats] = useState({
    total_users: 0,
    residents: 0,
    owners: 0,
    active_emails: 0,
    active_phones: 0
  });
  
  // File upload state
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileUploading, setFileUploading] = useState(false);
  
  // Individual message file upload state
  const [individualUploadedFile, setIndividualUploadedFile] = useState(null);
  const [individualFileUploading, setIndividualFileUploading] = useState(false);

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
      let response;
      
      // Use attachment-enabled email if file is uploaded
      if (uploadedFile) {
        const emailDataWithAttachment = {
          ...emailData,
          attachment_filename: uploadedFile.filename
        };
        response = await adminAPI.sendBulkEmailWithAttachment(emailDataWithAttachment);
      } else {
        response = await adminAPI.sendBulkEmail(emailData);
      }
      
      setMessage({ 
        type: 'success', 
        text: `Email sent successfully to ${response.data.sent_count} recipients!${uploadedFile ? ' (with attachment)' : ''}`
      });
      
      // Reset form
      setEmailData({
        recipient_type: 'all',
        subject: '',
        message: ''
      });
      
      // Clear uploaded file
      if (uploadedFile) {
        removeAttachment();
      }
      
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

  const handleFindUser = async () => {
    if (!individualData.erf_number.trim()) {
      setMessage({ type: 'error', text: 'ERF number is required' });
      return;
    }

    setSearchingUser(true);
    try {
      const response = await adminAPI.findUserByErf(individualData.erf_number);
      if (response.data.found) {
        setFoundUser(response.data.user);
        setMessage({ type: 'success', text: `Found user: ${response.data.user.full_name}` });
      } else {
        setFoundUser(null);
        setMessage({ type: 'error', text: response.data.error || 'User not found' });
      }
    } catch (error) {
      setFoundUser(null);
      setMessage({ type: 'error', text: 'Error searching for user: ' + (error.response?.data?.error || error.message) });
    } finally {
      setSearchingUser(false);
    }
  };

  const handleIndividualEmailSubmit = async (e) => {
    e.preventDefault();
    if (!foundUser) {
      setMessage({ type: 'error', text: 'Please find a user first' });
      return;
    }
    
    if (!individualData.subject.trim() || !individualData.message.trim()) {
      setMessage({ type: 'error', text: 'Subject and message are required' });
      return;
    }

    setLoading(true);
    try {
      const emailData = {
        user_id: foundUser.id,
        subject: individualData.subject,
        message: individualData.message
      };
      
      // Add attachment filename if file is uploaded
      if (individualUploadedFile) {
        emailData.attachment_filename = individualUploadedFile.filename;
      }
      
      const response = await adminAPI.sendIndividualEmail(emailData);
      
      setMessage({ 
        type: 'success', 
        text: response.data.message || `Email sent successfully!${individualUploadedFile ? ' (with attachment)' : ''}`
      });
      
      // Reset form
      setIndividualData({
        erf_number: '',
        subject: '',
        message: ''
      });
      setFoundUser(null);
      
      // Clear uploaded file
      if (individualUploadedFile) {
        removeIndividualAttachment();
      }
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to send email: ' + (error.response?.data?.error || error.message) });
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

  // File upload handlers
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File size must be less than 10MB' });
      return;
    }

    setFileUploading(true);
    setMessage({ type: '', text: '' });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await adminAPI.uploadAttachment(formData);
      setUploadedFile(response.data);
      setMessage({ type: 'success', text: 'File uploaded successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to upload file: ' + (error.response?.data?.error || error.message) });
    } finally {
      setFileUploading(false);
    }
  };

  const removeAttachment = () => {
    setUploadedFile(null);
    // Clear the file input
    document.getElementById('file-upload').value = '';
  };

  // Individual message file upload functions
  const handleIndividualFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File size must be less than 10MB' });
      return;
    }

    setIndividualFileUploading(true);
    setMessage({ type: '', text: '' });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await adminAPI.uploadAttachment(formData);
      setIndividualUploadedFile(response.data);
      setMessage({ type: 'success', text: 'File uploaded successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to upload file: ' + (error.response?.data?.error || error.message) });
    } finally {
      setIndividualFileUploading(false);
    }
  };

  const removeIndividualAttachment = () => {
    setIndividualUploadedFile(null);
    // Clear the file input
    const fileInput = document.getElementById('individual-file-upload');
    if (fileInput) {
      fileInput.value = '';
    }
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
              📧 Bulk Email
            </button>
            <button
              onClick={() => setActiveTab('whatsapp')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'whatsapp'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💬 Bulk WhatsApp
            </button>
            <button
              onClick={() => setActiveTab('individual')}
              className={`py-4 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'individual'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🎯 Individual Message
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

                {/* File Attachment */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📎 Attachment (Optional)
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-md p-4">
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="file-upload"
                    />
                    <label
                      htmlFor="file-upload"
                      className="cursor-pointer flex flex-col items-center justify-center text-center"
                    >
                      <div className="text-gray-400 mb-2">
                        📁
                      </div>
                      <div className="text-sm text-gray-600">
                        <span className="font-medium text-blue-600 hover:text-blue-500">
                          Click to upload
                        </span> or drag and drop
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        PDF, DOC, DOCX, TXT, JPG, PNG (max 10MB)
                      </div>
                    </label>
                    
                    {uploadedFile && (
                      <div className="mt-3 flex items-center justify-between bg-green-50 border border-green-200 rounded-md p-3">
                        <div className="flex items-center">
                          <span className="text-green-600 mr-2">✅</span>
                          <span className="text-sm text-green-800">{uploadedFile.original_filename}</span>
                        </div>
                        <button
                          type="button"
                          onClick={removeAttachment}
                          className="text-red-600 hover:text-red-800 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                    )}
                    
                    {fileUploading && (
                      <div className="mt-3 text-center">
                        <div className="text-sm text-blue-600">📤 Uploading...</div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Preview */}
                {emailData.subject && emailData.message && (
                  <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-md">
                    <h4 className="font-medium text-gray-900 mb-2">Preview:</h4>
                    <div className="text-sm">
                      <p><strong>To:</strong> {emailData.recipient_type === 'all' ? 'All Users' : emailData.recipient_type === 'residents' ? 'Residents' : 'Owners'} ({getRecipientCount(emailData.recipient_type)} recipients)</p>
                      <p><strong>Subject:</strong> {emailData.subject}</p>
                      {uploadedFile && (
                        <p><strong>Attachment:</strong> 📎 {uploadedFile.original_filename}</p>
                      )}
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

          {/* Individual Communication Tab */}
          {activeTab === 'individual' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Send Individual Message by ERF Number</h3>
              
              {/* ERF Number Search */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      ERF Number
                    </label>
                    <input
                      type="text"
                      value={individualData.erf_number}
                      onChange={(e) => setIndividualData(prev => ({ ...prev, erf_number: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Enter ERF number (e.g., 27681)"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleFindUser}
                    disabled={searchingUser || !individualData.erf_number.trim()}
                    className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {searchingUser ? '🔍 Searching...' : '🔍 Find User'}
                  </button>
                </div>
              </div>

              {/* Found User Display */}
              {foundUser && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <h4 className="font-medium text-purple-900 mb-2">✅ User Found:</h4>
                  <div className="text-sm text-purple-700 space-y-1">
                    <p><strong>Name:</strong> {foundUser.full_name}</p>
                    <p><strong>Email:</strong> {foundUser.email || 'No email address'}</p>
                    <p><strong>Phone:</strong> {foundUser.phone || 'No phone number'}</p>
                    <p><strong>ERF:</strong> {foundUser.erf_number}</p>
                    <p><strong>Type:</strong> {foundUser.type === 'resident' ? '🏠 Resident' : '🏡 Owner'}</p>
                  </div>
                  {!foundUser.email && (
                    <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700 text-sm">
                      ⚠️ This user does not have an email address on file.
                    </div>
                  )}
                </div>
              )}

              {/* Email Form */}
              {foundUser && foundUser.email && (
                <form onSubmit={handleIndividualEmailSubmit} className="space-y-4">
                  {/* Subject */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Subject *
                    </label>
                    <input
                      type="text"
                      value={individualData.subject}
                      onChange={(e) => setIndividualData(prev => ({ ...prev, subject: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Enter email subject..."
                      maxLength={200}
                    />
                    <p className="text-xs text-gray-500 mt-1">{individualData.subject.length}/200 characters</p>
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Message *
                    </label>
                    <textarea
                      value={individualData.message}
                      onChange={(e) => setIndividualData(prev => ({ ...prev, message: e.target.value }))}
                      rows={8}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="Enter your message here..."
                      maxLength={5000}
                    />
                    <p className="text-xs text-gray-500 mt-1">{individualData.message.length}/5000 characters</p>
                  </div>

                  {/* File Attachment */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      📎 Attachment (Optional)
                    </label>
                    
                    {!individualUploadedFile ? (
                      <div className="flex items-center">
                        <input
                          type="file"
                          id="individual-file-upload"
                          onChange={handleIndividualFileUpload}
                          disabled={individualFileUploading}
                          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
                        />
                        {individualFileUploading && (
                          <div className="ml-3 flex items-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                            <span className="ml-2 text-sm text-gray-600">Uploading...</span>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-md">
                        <div className="flex items-center">
                          <span className="text-green-600 mr-2">📄</span>
                          <div>
                            <p className="text-sm font-medium text-green-800">{individualUploadedFile.original_filename}</p>
                            <p className="text-xs text-green-600">
                              {Math.round(individualUploadedFile.file_size / 1024)} KB - Ready to send
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={removeIndividualAttachment}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                        >
                          Remove
                        </button>
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-500 mt-1">
                      Supported formats: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF (Max 10MB)
                    </p>
                  </div>

                  {/* Preview */}
                  {individualData.subject && individualData.message && foundUser && (
                    <div className="p-4 bg-purple-50 border border-purple-200 rounded-md">
                      <h4 className="font-medium text-gray-900 mb-2">Preview:</h4>
                      <div className="text-sm">
                        <p><strong>To:</strong> {foundUser.full_name} ({foundUser.email})</p>
                        <p><strong>ERF:</strong> {foundUser.erf_number}</p>
                        <p><strong>Subject:</strong> {individualData.subject}</p>
                        {individualUploadedFile && (
                          <p><strong>Attachment:</strong> {individualUploadedFile.original_filename} ({Math.round(individualUploadedFile.file_size / 1024)} KB)</p>
                        )}
                        <div className="mt-2 p-2 bg-white border border-purple-200 rounded">
                          <p className="whitespace-pre-wrap">{individualData.message}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Send Button */}
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-600">
                      This will send to <strong>{foundUser.full_name}</strong>
                    </div>
                    <button
                      type="submit"
                      disabled={loading || !individualData.subject.trim() || !individualData.message.trim()}
                      className="bg-purple-600 text-white px-6 py-2 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? '📤 Sending...' : '📧 Send Email'}
                    </button>
                  </div>
                </form>
              )}

              {/* Instructions */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📝 How to use Individual Communication:</h4>
                <div className="text-sm text-blue-700 space-y-1">
                  <p>1. Enter the ERF number to search for the property owner/resident</p>
                  <p>2. Review the found user details to confirm it's the correct person</p>
                  <p>3. Compose your email with a clear subject and message</p>
                  <p>4. Optionally attach a file (PDF, DOC, images, etc.)</p>
                  <p>5. Review the preview and send the individual message</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Communication Guidelines */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-yellow-800 mb-3">📋 Communication Guidelines</h3>
        <div className="text-sm text-yellow-700 space-y-2">
          <p>• <strong>Bulk Email:</strong> Best for detailed announcements, documents, and formal communications to groups (supports attachments)</p>
          <p>• <strong>Bulk WhatsApp:</strong> Best for urgent updates, short notices, and quick community alerts to groups</p>
          <p>• <strong>Individual Messages:</strong> Perfect for personal communication using ERF numbers as reference (supports attachments)</p>
          <p>• <strong>Recipients:</strong> 'All Users' includes both residents and owners, use specific groups when needed</p>
          <p>• <strong>Privacy:</strong> Always respect resident privacy and only send relevant community information</p>
          <p>• <strong>Frequency:</strong> Avoid over-communication to prevent message fatigue</p>
        </div>
      </div>
    </div>
  );
};

export default AdminCommunication;
