// Simple test for gate register API
// Run this in browser console on localhost:3000

// Get the token from localStorage
const token = localStorage.getItem('token');
console.log('Token:', token ? 'Found' : 'Not found');

if (!token) {
    console.error('No token found in localStorage. Please login first.');
} else {
    // Test the gate register API
    fetch('/api/admin/gate-register', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        return response.json();
    })
    .then(data => {
        console.log('Gate register response:', data);
        if (data.success) {
            console.log('Total entries:', data.total_entries);
            console.log('Sample data:', data.data?.slice(0, 2));
        } else {
            console.error('Gate register failed:', data.error);
        }
    })
    .catch(error => {
        console.error('Network error:', error);
    });
}
