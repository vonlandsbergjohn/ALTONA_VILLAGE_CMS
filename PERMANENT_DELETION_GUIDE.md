# 🗑️ PERMANENT USER DELETION SYSTEM

## 📋 **OVERVIEW**

The Permanent User Deletion System provides a complete solution for removing users who were incorrectly approved or mistakenly registered in the Altona Village CMS. This is **not** for normal user lifecycle management - use the archive system for that.

## ⚠️ **CRITICAL WARNING**

**This system performs PERMANENT deletion that cannot be undone!**

Use this system ONLY for:
- ✅ Users who were incorrectly approved by admin
- ✅ Mistaken registrations (wrong person registered)
- ✅ Users who should never have been in the system
- ✅ Test accounts that need complete removal

**DO NOT USE for:**
- ❌ Normal user lifecycle management (use archive system)
- ❌ Users who legitimately left the village (use archive system)
- ❌ Temporary suspensions

## 🛠️ **USAGE METHODS**

### 1. Interactive Admin Tool
```bash
python admin_permanent_deletion.py
```

**Features:**
- List all users in the system
- Search users by email or name
- View detailed user information
- Guided deletion with multiple confirmations
- View deletion audit logs

### 2. API Endpoint (for Frontend)
```http
DELETE /admin/users/{user_id}/permanent-delete
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "deletion_reason": "User was incorrectly approved - not a valid resident",
  "confirm_deletion": true
}
```

**Response:**
```json
{
  "message": "User user@email.com has been permanently deleted",
  "deletion_id": "uuid-string",
  "summary": {
    "user_deleted": true,
    "resident_deleted": true,
    "owner_deleted": false,
    "vehicles_deleted": 2,
    "complaints_deleted": 1,
    "complaint_updates_deleted": 3,
    "transitions_deleted": 0,
    "pending_deleted": 0,
    "tokens_deleted": 1,
    "sessions_deleted": 2
  }
}
```

### 3. Programmatic Usage
```python
from user_archive_deletion_system import UserArchiveDeletionSystem

system = UserArchiveDeletionSystem()

result = system.permanently_delete_user(
    user_id="user_uuid",
    deletion_reason="Incorrectly approved registration",
    performed_by_admin_id="admin_uuid",
    confirm_deletion=True  # Must be True for deletion to proceed
)

if result['success']:
    print(f"User deleted: {result['deletion_id']}")
else:
    print(f"Deletion failed: {result['error']}")
```

## 🔍 **WHAT GETS DELETED**

The system removes **ALL** traces of the user from these tables:

### User Data
- ✅ **users** - Main user account
- ✅ **residents** - Resident profile
- ✅ **owners** - Owner profile

### Related Data
- ✅ **vehicles** - All registered vehicles
- ✅ **complaints** - All complaints filed
- ✅ **complaint_updates** - All complaint responses
- ✅ **user_transition_requests** - Moving requests
- ✅ **password_reset_tokens** - Password reset tokens
- ✅ **user_sessions** - Active sessions
- ✅ **pending_registrations** - Any pending registration records

## 📝 **AUDIT TRAIL**

Every deletion is logged with:
- **Deletion ID** - Unique identifier for the deletion
- **User Information** - Email, role, names, ERF numbers
- **Admin Details** - Who performed the deletion
- **Timestamp** - When the deletion occurred
- **Reason** - Why the user was deleted
- **Summary** - What data was removed

### View Deletion Logs
```python
# Get logs from last 30 days
logs = system.get_deletion_logs(days_back=30)

# Or via API
GET /admin/users/deletion-logs?days_back=30
```

## 🔒 **SAFETY FEATURES**

### 1. Multiple Confirmations Required
- Must set `confirm_deletion=True`
- Interactive tool requires typing "DELETE" and user email
- API requires explicit confirmation in request body

### 2. Deletion Verification
```python
# Verify user is completely removed
verification = system.verify_user_completely_deleted("user@email.com")
if verification:
    print("✅ User completely removed")
else:
    print("❌ Some data may remain")
```

### 3. Complete Data Removal
- Follows foreign key constraints
- Removes data in correct order
- Handles all related records
- Provides detailed summary of what was deleted

## 🚀 **FRONTEND INTEGRATION**

### Add Delete Button to User Profile
```javascript
const deleteUser = async (userId, reason) => {
  const response = await fetch(`/admin/users/${userId}/permanent-delete`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      deletion_reason: reason,
      confirm_deletion: true
    })
  });
  
  if (response.ok) {
    const result = await response.json();
    alert(`User deleted successfully: ${result.deletion_id}`);
    // Refresh user list
  } else {
    const error = await response.json();
    alert(`Deletion failed: ${error.error}`);
  }
};
```

### Confirmation Dialog
```javascript
const confirmDeletion = (userEmail) => {
  if (!confirm(`⚠️ PERMANENT DELETION WARNING\n\nThis will permanently delete ${userEmail} and all their data.\n\nThis action cannot be undone!\n\nAre you sure?`)) {
    return false;
  }
  
  const reason = prompt("Enter reason for deletion:");
  if (!reason || reason.trim() === "") {
    alert("Deletion reason is required");
    return false;
  }
  
  return reason;
};
```

## 📊 **SYSTEM STATUS**

The permanent deletion system is:
- ✅ **Fully Operational** - Ready for production use
- ✅ **Safety Tested** - Multiple confirmation layers
- ✅ **Audit Compliant** - Complete logging system
- ✅ **Database Safe** - Handles foreign key constraints
- ✅ **API Ready** - Frontend integration available
- ✅ **Interactive** - Admin tool for manual deletions

## 🔧 **TROUBLESHOOTING**

### Database Connection Issues
```python
# Check if database exists
import os
db_path = "altona_village_cms/src/database/app.db"
if not os.path.exists(db_path):
    print("❌ Database not found")
```

### Table Creation Issues
```python
# Ensure deletion log table exists
system = UserArchiveDeletionSystem()
conn = system.get_connection()
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_deletion_log (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36),
        deleted_at DATETIME,
        deleted_by VARCHAR(36),
        deletion_reason TEXT,
        deletion_type VARCHAR(100),
        original_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
```

### Verification Failures
If verification shows remaining data:
1. Check foreign key constraints
2. Manually inspect remaining tables
3. Use the interactive tool to see what's left
4. Contact system administrator

## 📞 **SUPPORT**

For issues with the permanent deletion system:
1. Check the deletion logs for any errors
2. Run the verification function
3. Use the interactive tool for manual inspection
4. Review the API response details
5. Check database foreign key constraints

---

**Remember: This is a PERMANENT deletion system. Use with extreme caution and only for incorrectly registered users!**
