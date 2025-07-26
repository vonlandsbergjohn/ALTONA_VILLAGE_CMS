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
              {/* Add Approve/Reject buttons here later */}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PendingRegistrations;