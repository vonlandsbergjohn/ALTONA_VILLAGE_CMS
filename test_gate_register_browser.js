// Test gate register API call
// Paste this in browser console while logged in as admin

const testGateRegister = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        console.error('No token found. Please login first.');
        return;
    }
    
    console.log('Testing gate register API...');
    
    try {
        const response = await fetch('/api/admin/gate-register', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            return;
        }
        
        const data = await response.json();
        console.log('Success! Gate register data:', data);
        console.log('Total entries:', data.total_entries);
        console.log('First few entries:', data.data?.slice(0, 3));
        
        if (data.data && data.data.length > 0) {
            console.log('Sample entry structure:', data.data[0]);
        } else {
            console.log('No entries found in gate register');
        }
        
    } catch (error) {
        console.error('Network error:', error);
    }
};

testGateRegister();
