import React, { useEffect, useState } from 'react';

const PendingRegistrations = () => {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Replace with your actual API endpoint
    fetch('/api/pending-registrations')
      .then(res => res.json())
      .then(data => {
        setPending(data);
        setLoading(false);
      });
  }, []);

  const handleApprove = (userId) => {
    // TODO: Replace with your actual API endpoint
    fetch(`/api/pending-registrations/${userId}/approve`, { method: 'POST' })
      .then(res => res.json())
      .then(() => {
        setPending(pending.filter(user => user.id !== userId));
      });
  };

  const handleReject = (userId) => {
    // TODO: Replace with your actual API endpoint
    fetch(`/api/pending-registrations/${userId}/reject`, { method: 'POST' })
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
            <li key={user.id}>
              {user.name} ({user.email})
              <button onClick={() => handleApprove(user.id)} style={{ marginLeft: '10px' }}>Approve</button>
              <button onClick={() => handleReject(user.id)} style={{ marginLeft: '5px' }}>Reject</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PendingRegistrations;