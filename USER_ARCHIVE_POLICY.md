# Altona Village CMS - User Archive and Deletion Policy

## 📋 OVERVIEW

The User Archive and Deletion System manages the lifecycle of inactive users in the Altona Village CMS, ensuring data privacy compliance while maintaining necessary records for legal and operational purposes.

## 🎯 ARCHIVE POLICIES BY USER TYPE

### 1. **TENANT ONLY**
- **Trigger**: Completed transition request with `new_occupant_type = 'terminated'`
- **Action**: **IMMEDIATE DELETION**
- **Retention**: **NONE**
- **Rationale**: Tenants have no ownership stake; relationship is completely severed upon moveout

**Data Processing:**
- ✅ **DELETED**: Personal information, vehicles, access codes, emergency contacts, complaints
- ❌ **PRESERVED**: Nothing (complete deletion)

### 2. **OWNER ONLY** 
- **Trigger**: Property sold, transition completed
- **Action**: **LIMITED RETENTION ARCHIVE**
- **Retention**: **2 years** (configurable)
- **Rationale**: New owners may need contact for property history inquiries

**Data Processing:**
- ✅ **PRESERVED**: Property ownership dates, ERF association, title deed information
- ❌ **DELETED**: Personal details, emergency contacts, vehicles, access codes, postal addresses

### 3. **OWNER-RESIDENT** (Two Scenarios)

#### Scenario A: Moved out but KEPT property
- **Action**: **ARCHIVE RESIDENT, KEEP OWNER ACTIVE**
- **Retention**: Resident data 30 days, Owner data remains active
- **Rationale**: Still has ownership rights but no daily access needs

**Data Processing:**
- ✅ **PRESERVED**: Property ownership, title deed info
- 🔄 **MODIFIED**: Vehicle access changed to "owner-only", emergency contacts updated
- ❌ **ARCHIVED**: Resident personal info, daily access codes

#### Scenario B: Sold property (lost both roles)
- **Action**: **IMMEDIATE DELETION**
- **Retention**: **NONE**
- **Rationale**: Complete relationship termination

**Data Processing:**
- ❌ **DELETED**: All resident and owner data, vehicles, access codes

## 🔧 SYSTEM COMPONENTS

### 1. **user_archive_deletion_system.py**
Core archive engine that handles:
- Analysis of inactive users
- Automated data classification
- Execution of archive/deletion policies
- Archive record creation
- Data retention management

### 2. **archive_management_interface.py**
Interactive management tool for administrators:
- Manual user archive review
- Specific user archival
- Archive record viewing
- Old archive cleanup

### 3. **automated_archive_scheduler.py**
Automated processing system:
- Scheduled archive processing
- Configurable policies
- Audit logging
- Archive reporting

## 📊 BUSINESS RULES

### Automatic Processing Criteria
- **Tenant Only**: Auto-archive after 7-day grace period
- **Owner Only**: Auto-archive immediately after property transfer
- **Owner-Resident**: Requires review of specific scenario

### Manual Review Required
- **Complex ownership arrangements**
- **Disputed transitions**
- **Users with active complaints**
- **System configuration requires manual approval**

## 🗃️ ARCHIVE DATA STRUCTURE

Archives are stored in the `user_archives` table with:
```sql
- archive_id: Unique identifier
- user_id: Original user reference
- archived_at: Timestamp
- archived_by: Admin who performed action
- archive_reason: Justification
- user_type: Classification for retention policy
- retention_policy: Applied policy
- archive_data: Complete JSON backup of original data
```

## ⚙️ CONFIGURATION

### Archive Settings (`archive_config.json`)
```json
{
    "auto_archive_enabled": true,
    "tenant_grace_period_days": 7,
    "owner_retention_years": 2,
    "require_manual_approval": false,
    "notification_email": "admin@altonavillage.co.za"
}
```

### Logging
- **File**: `user_archive_log.txt`
- **Format**: Timestamp, level, message
- **Retention**: 1 year (manual cleanup)

## 🔒 SECURITY AND COMPLIANCE

### Data Privacy
- **POPIA Compliance**: Personal data deleted when no longer needed
- **Audit Trail**: Complete record of all archive actions
- **Access Control**: Only authorized administrators can perform archival
- **Encryption**: Archive data stored securely in database

### Legal Requirements
- **Property Records**: Maintained as required by property law
- **Financial Records**: Preserved per financial regulations
- **Audit Requirements**: Full traceability of all actions

## 🚀 OPERATIONAL PROCEDURES

### Daily Operations
1. **Automated Processing**: Run scheduler daily
2. **Review Reports**: Check for manual review items
3. **Monitor Logs**: Verify successful operations

### Weekly Operations
1. **Archive Report**: Generate comprehensive report
2. **Manual Reviews**: Process items requiring admin approval
3. **System Health**: Verify archive system functionality

### Monthly Operations
1. **Policy Review**: Assess archive effectiveness
2. **Cleanup**: Remove old archive records per retention policy
3. **Backup Verification**: Ensure archive data integrity

## 📋 USAGE EXAMPLES

### 1. Analyze Current Inactive Users
```bash
python user_archive_deletion_system.py
```

### 2. Interactive Management
```bash
python archive_management_interface.py
```

### 3. Automated Processing
```bash
python automated_archive_scheduler.py
```

### 4. Generate Report Only
```bash
python automated_archive_scheduler.py
# Select option 2
```

## 🔧 EMERGENCY PROCEDURES

### Data Recovery
- Archive records contain complete original data
- Can be restored within retention period
- Requires admin approval and justification

### System Failure
- Archives stored in database for persistence
- Logs provide complete audit trail
- Manual procedures documented for emergency processing

## 📞 SUPPORT AND MAINTENANCE

### Regular Maintenance
- **Database Optimization**: Monthly index rebuilding
- **Log Rotation**: Monthly log file archival
- **System Updates**: Quarterly review of policies

### Troubleshooting
- Check logs for error details
- Verify database connectivity
- Ensure proper permissions
- Review configuration settings

## 📈 REPORTING AND METRICS

### Standard Reports
- **Monthly Archive Summary**: Users processed, policies applied
- **Retention Analysis**: Data volume, storage usage
- **Compliance Report**: Privacy and legal adherence

### Key Metrics
- **Processing Time**: Average time per user archive
- **Success Rate**: Percentage of successful archives
- **Manual Review Rate**: Percentage requiring human intervention
- **Storage Efficiency**: Archive compression and optimization

---

**Document Version**: 1.0
**Last Updated**: August 6, 2025
**Next Review**: November 6, 2025
