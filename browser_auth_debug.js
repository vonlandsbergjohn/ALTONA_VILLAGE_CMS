// Paste this into your browser console (F12 → Console) to debug token issues

console.log("🔍 AUTH DEBUG TOOL");
console.log("==================");

// Check localStorage
const token = localStorage.getItem('token');
const user = localStorage.getItem('user');

console.log("📱 LocalStorage Status:");
console.log("Token exists:", !!token);
console.log("Token length:", token ? token.length : 0);
console.log("Token preview:", token ? token.substring(0, 30) + "..." : "No token");
console.log("User data exists:", !!user);

if (user) {
    try {
        const userData = JSON.parse(user);
        console.log("User email:", userData.email);
        console.log("User role:", userData.role);
    } catch (e) {
        console.log("❌ User data is corrupted");
    }
}

// Test API call
if (token) {
    console.log("\n🧪 Testing API call...");
    
    fetch('/api/auth/profile', {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log("API Response Status:", response.status);
        if (response.status === 200) {
            console.log("✅ API call successful - token is working!");
        } else {
            console.log("❌ API call failed - token might be invalid");
        }
        return response.text();
    })
    .then(text => {
        console.log("Response:", text);
    })
    .catch(error => {
        console.log("❌ API call error:", error);
    });
} else {
    console.log("❌ No token found - please login first");
}

console.log("\n🔧 Quick Fixes:");
console.log("1. If no token: Logout and login again");
console.log("2. If token exists but API fails: Clear localStorage and login again");
console.log("3. Run: localStorage.clear() then refresh and login");
