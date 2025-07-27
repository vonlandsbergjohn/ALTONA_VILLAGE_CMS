// Simple browser JavaScript test to check API endpoints
// Open browser dev tools and run these commands one by one

// 1. Test gate register
console.log("Testing gate register...");
fetch('/api/gate-register', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
})
.then(response => response.json())
.then(data => {
    console.log("Gate register response:", data);
    if (data.error) {
        console.error("Gate register error:", data.error);
    } else {
        console.log("Gate register entries:", data.total_entries);
    }
})
.catch(error => console.error("Gate register request failed:", error));

// 2. Test profile update
console.log("\nTesting profile update...");
fetch('/api/auth/profile', {
    method: 'PUT',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
        phone: '0123456789'
    })
})
.then(response => response.json())
.then(data => {
    console.log("Profile update response:", data);
    if (data.error) {
        console.error("Profile update error:", data.error);
    } else {
        console.log("Profile update successful:", data.message);
    }
})
.catch(error => console.error("Profile update request failed:", error));

// 3. Test admin users list
console.log("\nTesting admin users...");
fetch('/api/admin/users', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
})
.then(response => response.json())
.then(data => {
    console.log("Admin users response:");
    if (Array.isArray(data)) {
        console.log("Total users:", data.length);
        data.slice(0, 2).forEach(user => {
            console.log(`User: ${user.email} - Status: ${user.status} - Role: ${user.role}`);
        });
    } else if (data.error) {
        console.error("Admin users error:", data.error);
    }
})
.catch(error => console.error("Admin users request failed:", error));
