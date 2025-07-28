# 🔔 Admin Change Notification System

## Overview

This system tracks critical resident data changes and provides admin notifications for external system synchronization. It's specifically designed to help estate management teams keep their **Accentronix gate system** and **camera identification system** up-to-date with resident information.

## 🎯 Problem Solved

**Challenge**: When residents update their cellphone numbers or vehicle registrations in the CMS, how do admins know to update external systems (Accentronix & camera system)?

**Solution**: Automatic change tracking with admin notifications and export functionality.

## 🛠️ System Components

### 1. Backend Change Tracking (`admin_notifications.py`)

**Database Table**: `user_changes`
```sql
- id: Change record ID
- user_id: User who made the change
- user_name: Full name for easy identification
- erf_number: Property ERF number
- change_type: Type of change (profile_update, vehicle_update)
- field_name: Which field changed
- old_value: Previous value
- new_value: New value
- change_timestamp: When change occurred
- admin_reviewed: Whether admin has seen this
- exported_to_external: Whether exported to external systems
```

**API Endpoints**:
- `GET /api/admin/changes/pending` - All unreviewed changes
- `GET /api/admin/changes/critical` - Critical changes (phone/vehicle only)
- `POST /api/admin/changes/review` - Mark changes as reviewed
- `GET /api/admin/changes/export-critical?type=accentronix` - Export phone data
- `GET /api/admin/changes/export-critical?type=camera` - Export vehicle data
- `GET /api/admin/changes/stats` - Dashboard statistics

### 2. Automatic Change Detection

**Profile Updates** (`auth.py`):
```python
# Tracks when users update their profile
track_change('cellphone_number', old_phone, new_phone)
```

**Vehicle Updates** (`resident.py`):
```python
# Tracks when users update vehicle registrations  
track_change('vehicle_registration', old_reg, new_reg)
```

**Critical Fields Monitored**:
- `cellphone_number` - For Accentronix gate system
- `vehicle_registration` - For camera identification system
- `vehicle_registration_2` - Secondary vehicle for camera system

### 3. Admin Dashboard (`AdminNotificationsDashboard.jsx`)

**Features**:
- 📊 **Real-time stats**: Critical pending, total pending, today's changes
- 🚨 **Critical alerts**: Highlighted phone/vehicle changes
- ✅ **Bulk review**: Mark multiple changes as reviewed
- 📤 **Export functions**: Generate CSV files for external systems
- 🔄 **Auto-refresh**: Updates every 30 seconds

## 🚀 How It Works

### When a Resident Updates Information:

1. **User Action**: Resident updates phone number or vehicle registration
2. **Automatic Logging**: System logs change to `user_changes` table
3. **Admin Notification**: Change appears in admin dashboard
4. **Admin Review**: Admin sees critical change highlighted
5. **Export Data**: Admin exports updated data for external systems
6. **System Update**: Admin updates Accentronix/camera systems
7. **Mark Complete**: Admin marks changes as reviewed

### Workflow Example:

```
Resident changes phone: 082 123 4567 → 083 987 6543
        ↓
System logs change automatically
        ↓
Admin dashboard shows red alert: "Critical Change - ERF 1234"
        ↓
Admin clicks "Export Accentronix Data"
        ↓
CSV downloaded with updated phone numbers
        ↓
Admin imports CSV into Accentronix gate system
        ↓
Admin marks change as "Reviewed"
```

## 📊 Export Formats

### Accentronix Export (Phone Numbers):
```csv
erf_number,resident_name,cellphone_number,intercom_code,last_updated
1234,John Smith,083 987 6543,ERF1234,2025-01-15 14:30:00
5678,Jane Doe,082 555 7890,ERF5678,2025-01-14 09:15:00
```

### Camera System Export (Vehicle Registrations):
```csv
erf_number,resident_name,vehicle_registration,vehicle_type,last_updated
1234,John Smith,ABC123GP,primary,2025-01-15 14:30:00
1234,John Smith,XYZ789GP,secondary,2025-01-15 12:00:00
5678,Jane Doe,DEF456GP,primary,2025-01-14 16:45:00
```

## 🔧 Installation & Setup

### 1. Backend Setup:
```bash
# System is automatically initialized when server starts
# No manual setup required - tables created automatically
```

### 2. Frontend Integration:
```jsx
// Add to your admin routes
import AdminNotificationsDashboard from '@/components/AdminNotificationsDashboard';

// Route configuration
<Route path="/admin/notifications" component={AdminNotificationsDashboard} />
```

### 3. Access Dashboard:
- URL: `/admin/notifications`
- Requires: Admin authentication
- Auto-refresh: Every 30 seconds

## 📈 Admin Dashboard Features

### Statistics Cards:
- **Critical Pending**: Changes requiring immediate attention
- **Total Pending**: All unreviewed changes
- **Today**: Changes made today
- **This Week**: Changes made this week

### Critical Changes Alert:
- Red highlighted section for urgent changes
- Shows phone number and vehicle registration changes
- One-click review and export

### Export Functions:
- **Accentronix Button**: Downloads phone numbers for gate system
- **Camera Button**: Downloads vehicle registrations for camera system
- **CSV Format**: Ready to import into external systems

### Change Management:
- **Bulk Selection**: Select multiple changes to review
- **Individual Review**: Mark single changes as complete
- **Change History**: See old vs new values
- **Timestamps**: When changes were made

## 🎯 Usage Scenarios

### Daily Admin Workflow:
1. **Morning Check**: Open notifications dashboard
2. **Review Alerts**: Check critical changes overnight
3. **Export Updates**: Download data for external systems
4. **Update Systems**: Import data into Accentronix/camera systems
5. **Mark Complete**: Review changes in dashboard

### Weekly Maintenance:
1. **Review Stats**: Check weekly change patterns
2. **Bulk Export**: Download all recent changes
3. **System Sync**: Ensure external systems are current
4. **Clean Database**: Archive old reviewed changes

## 🛡️ Security Features

- **Admin Only**: All endpoints require admin authentication
- **Change Tracking**: Full audit trail of who changed what
- **Export Logging**: Track when data was exported
- **Review System**: Prevent changes from being missed

## 🔮 Future Enhancements

### Potential Additions:
- **Email Notifications**: Send alerts for critical changes
- **API Integration**: Direct sync with external systems
- **Mobile App**: Admin notifications on mobile devices
- **Reporting**: Monthly change reports and analytics

### Integration Options:
- **Accentronix API**: Direct sync without CSV export
- **Camera System API**: Automatic vehicle registration updates
- **WhatsApp Alerts**: Instant notifications for admins

## 📞 Support Information

### For Issues:
1. Check backend logs for error messages
2. Verify database table exists (`user_changes`)
3. Confirm admin authentication is working
4. Test API endpoints with admin credentials

### Maintenance:
- Database table auto-creates on startup
- No manual maintenance required
- Archive old changes periodically for performance

---

## 🎉 Benefits

✅ **Never Miss Changes**: Automatic tracking of all critical updates  
✅ **Real-time Notifications**: Know immediately when residents update info  
✅ **Easy Exports**: One-click CSV downloads for external systems  
✅ **Audit Trail**: Complete history of all changes  
✅ **Time Saving**: No more manual checking for updates  
✅ **Error Prevention**: Ensure external systems stay synchronized  

The system ensures your Accentronix gate system and camera identification system always have the latest resident information!
