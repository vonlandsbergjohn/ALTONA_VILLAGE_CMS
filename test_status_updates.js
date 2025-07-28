// Test status update functionality
// Run this in browser console while logged in as admin

const testStatusUpdates = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        console.error('No token found. Please login first.');
        return;
    }
    
    console.log('Testing status update functionality...');
    
    // 1. First get list of users
    try {
        console.log('Getting user list...');
        const usersResponse = await fetch('/api/admin/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!usersResponse.ok) {
            console.error('Failed to get users:', await usersResponse.text());
            return;
        }
        
        const users = await usersResponse.json();
        console.log('Users found:', users.length);
        
        // Find a non-admin user to test with
        const testUser = users.find(u => u.role !== 'admin');
        if (!testUser) {
            console.error('No non-admin user found for testing');
            return;
        }
        
        console.log('Testing with user:', testUser.email);
        console.log('Current user status:', {
            is_resident: testUser.is_resident,
            is_owner: testUser.is_owner
        });
        
        // 2. Test admin status update
        console.log('\n--- TESTING ADMIN STATUS UPDATE ---');
        const adminUpdateData = {
            resident_status_change: 'owner' // Try to change to owner
        };
        
        console.log('Sending admin update:', adminUpdateData);
        const adminResponse = await fetch(`/api/admin/update-resident/${testUser.user_id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(adminUpdateData)
        });
        
        console.log('Admin update response status:', adminResponse.status);
        const adminResult = await adminResponse.json();
        console.log('Admin update result:', adminResult);
        
        // 3. Test user profile update (if we have a regular user token)
        console.log('\n--- TESTING USER PROFILE UPDATE ---');
        const profileUpdateData = {
            tenant_or_owner: 'resident' // Try to change to resident
        };
        
        console.log('Sending profile update:', profileUpdateData);
        const profileResponse = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileUpdateData)
        });
        
        console.log('Profile update response status:', profileResponse.status);
        const profileResult = await profileResponse.json();
        console.log('Profile update result:', profileResult);
        
    } catch (error) {
        console.error('Test error:', error);
    }
};

testStatusUpdates();
