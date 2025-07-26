import React, { useEffect, useState } from 'react';

// Helper to get JWT token from localStorage (adjust if you store it differently)
const getToken = () => localStorage.getItem('token');

const PendingRegistrations = () => {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/admin/pending-registrations', {
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    })
      .then(res => res.json())
      .then(data => {
        setPending(data);
        setLoading(false);
      });
  }, []);

  const handleApprove = (userId) => {
    fetch(`/api/admin/approve-registration/${userId}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    })
      .then(res => res.json())
      .then(() => {
        setPending(pending.filter(user => user.id !== userId));
      });
  };

  const handleReject = (userId) => {
    fetch(`/api/admin/reject-registration/${userId}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getToken()}`
      }
    })
      .then(res => res.json())
      .then(() => {
        setPending(pending.filter(user => user.id !== userId));
      });
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Pending Registrations</h2>
      {pending.length === 0 ? (
        <div>No pending registrations.</div>
      ) : (
        <ul>
          {pending.map(user => (
            <li key={user.id} style={{ marginBottom: '12px' }}>
              {user.name || user.email} ({user.email})
              <button
                onClick={() => handleApprove(user.id)}
                style={{
                  marginLeft: '10px',
                  padding: '6px 16px',
                  background: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  marginRight: '6px'
                }}
              >
                Approve
              </button>
              <button
                onClick={() => handleReject(user.id)}
                style={{
                  marginLeft: '5px',
                  padding: '6px 16px',
                  background: '#f44336',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Reject
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PendingRegistrations;