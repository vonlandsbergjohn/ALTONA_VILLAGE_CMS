// Direct API Testing Script
// Open browser console and paste this to test APIs

console.log("Starting API tests...");

// Test 1: Login and get token
async function testLogin() {
    console.log("\n=== Testing Login ===");
    try {
        const response = await fetch('http://localhost:5001/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'user1',
                password: 'password123'
            })
        });
        
        const data = await response.json();
        console.log('Login response:', data);
        
        if (data.access_token) {
            console.log('✅ Login successful');
            return data.access_token;
        } else {
            console.log('❌ Login failed');
            return null;
        }
    } catch (error) {
        console.error('❌ Login error:', error);
        return null;
    }
}

// Test 2: Get profile
async function testGetProfile(token) {
    console.log("\n=== Testing Get Profile ===");
    try {
        const response = await fetch('http://localhost:5001/auth/profile', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        console.log('Profile response:', data);
        
        if (response.ok) {
            console.log('✅ Profile fetch successful');
            return data;
        } else {
            console.log('❌ Profile fetch failed');
            return null;
        }
    } catch (error) {
        console.error('❌ Profile fetch error:', error);
        return null;
    }
}

// Test 3: Update profile
async function testUpdateProfile(token) {
    console.log("\n=== Testing Update Profile ===");
    try {
        const response = await fetch('http://localhost:5001/auth/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                first_name: 'Test',
                last_name: 'User',
                email: 'test@example.com',
                phone: '1234567890',
                building_id: 'A',
                unit_number: '101',
                tenant_or_owner: 'tenant'
            })
        });
        
        const data = await response.json();
        console.log('Update profile response:', response.status, data);
        
        if (response.ok) {
            console.log('✅ Profile update successful');
            return data;
        } else {
            console.log('❌ Profile update failed');
            return null;
        }
    } catch (error) {
        console.error('❌ Profile update error:', error);
        return null;
    }
}

// Test 4: Admin login and test admin functions
async function testAdminLogin() {
    console.log("\n=== Testing Admin Login ===");
    try {
        const response = await fetch('http://localhost:5001/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'admin',
                password: 'admin123'
            })
        });
        
        const data = await response.json();
        console.log('Admin login response:', data);
        
        if (data.access_token) {
            console.log('✅ Admin login successful');
            return data.access_token;
        } else {
            console.log('❌ Admin login failed');
            return null;
        }
    } catch (error) {
        console.error('❌ Admin login error:', error);
        return null;
    }
}

// Test 5: Get residents list (admin)
async function testGetResidents(adminToken) {
    console.log("\n=== Testing Get Residents (Admin) ===");
    try {
        const response = await fetch('http://localhost:5001/admin/residents', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${adminToken}`,
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        console.log('Residents response:', data);
        
        if (response.ok) {
            console.log('✅ Residents fetch successful');
            return data;
        } else {
            console.log('❌ Residents fetch failed');
            return null;
        }
    } catch (error) {
        console.error('❌ Residents fetch error:', error);
        return null;
    }
}

// Test 6: Update resident status (admin)
async function testUpdateResident(adminToken, userId) {
    console.log("\n=== Testing Update Resident Status (Admin) ===");
    try {
        const response = await fetch(`http://localhost:5001/admin/residents/${userId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${adminToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resident_status_change: 'owner'
            })
        });
        
        const data = await response.json();
        console.log('Update resident response:', response.status, data);
        
        if (response.ok) {
            console.log('✅ Resident update successful');
            return data;
        } else {
            console.log('❌ Resident update failed');
            return null;
        }
    } catch (error) {
        console.error('❌ Resident update error:', error);
        return null;
    }
}

// Run all tests
async function runAllTests() {
    console.log("🧪 Starting comprehensive API tests...");
    
    // Test user functionality
    const userToken = await testLogin();
    if (userToken) {
        const profile = await testGetProfile(userToken);
        await testUpdateProfile(userToken);
    }
    
    // Test admin functionality
    const adminToken = await testAdminLogin();
    if (adminToken) {
        const residents = await testGetResidents(adminToken);
        if (residents && residents.length > 0) {
            await testUpdateResident(adminToken, residents[0].id);
        }
    }
    
    console.log("\n🏁 All tests completed!");
}

// Call this function to run tests
console.log("Run: runAllTests()");
