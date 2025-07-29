# Altona Village CMS - User Lifecycle Management Discussion Document

**Date:** July 29, 2025  
**Topic:** User Invitation, Creation, and Transition Management System  
**Purpose:** Planning comprehensive user lifecycle management for property transitions

---

## 🏘️ UNDERSTANDING THE USER LIFECYCLE SCENARIOS

### Common Transitions in Estate Management:

1. **Tenant moves out → New tenant moves in** (same ERF)
2. **Owner sells → New owner buys** (property ownership transfer)
3. **Owner becomes owner-resident** (moves into their own property)
4. **Owner-resident becomes just owner** (moves out, keeps ownership)
5. **Property gets subdivided/consolidated** (ERF changes)

**YOUR INPUT NEEDED:**
- Which of these scenarios are most common in your estate?
- Are there other transition scenarios we should consider?
- How frequently do these transitions occur?

---

## 💡 SUGGESTED SYSTEM ARCHITECTURE

### 1. User Status Management
Instead of deleting users, use status-based approach:
- `active` - Currently using the property
- `inactive` - No longer using the property but data preserved
- `transferred` - Moved to another property/role
- `pending_transfer` - In process of transition

**YOUR INPUT NEEDED:**
- Do these status categories cover all scenarios?
- Should we add additional status types?
- How long should users remain in each status? (See detailed breakdown below for each user group)

### 2. Property-User Relationship Tracking
- **Current User** (active relationship)
- **Historical Users** (maintain audit trail)
- **Effective dates** (from/to dates for each relationship)

**YOUR INPUT NEEDED:**
- Is this relationship structure sufficient?
- Do you need to track multiple relationships simultaneously?
- What date information is most important for your records?

### 3. Invitation & Transfer System
```
Admin Dashboard Features:
├── Invite New User (email invitation)
├── Transfer Property (from old → new user)
├── Deactivate User (preserve data)
├── Reactivate User (if they return)
└── Merge User Data (combine accounts if needed)
```

**YOUR INPUT NEEDED:**
- What other admin features would be helpful?
- Should there be bulk operation capabilities?
- Do you need reporting features for transitions?

---

## 🔄 PROPOSED WORKFLOW EXAMPLE

### Scenario: Tenant Moving Out, New Tenant Moving In

1. **Admin receives notice** → Clicks "Transfer Property"
2. **System creates invitation** → Sends email to new tenant
3. **New tenant registers** → System links them to ERF
4. **Admin confirms transfer** → Old tenant becomes `inactive`, new tenant becomes `active`
5. **Data preservation** → Old tenant's history preserved, vehicles/access transferred

**YOUR INPUT NEEDED:**
- Is this workflow realistic for your office procedures?
- What steps are missing or unnecessary?
- How much automation vs manual control do you prefer?

---

## 🏠 USER GROUP STATUS MANAGEMENT - DETAILED BREAKDOWN

### **TENANT ONLY** - Data Management When They Move Out

**Scenario:** Tenant moves out of ERF 123

**Status Transition:** `active` → `inactive`

**Data Management Questions:**
- How long should tenant data remain in `inactive` status before archiving/deletion?
- Should we keep their vehicle registrations for reference?
- What about their emergency contact information?
- How long should we preserve their intercom code history?

**Considerations:**
- Tenants have **no ownership stake** - once they leave, relationship is severed
- May need data for **deposit returns, damage claims, reference checks**
- **Security concern:** Old intercom codes should be deactivated quickly
- **Vehicle access:** Should be removed immediately for security

**YOUR INPUT FOR TENANT DATA RETENTION:**
[Please specify how long to keep inactive tenant data and what information to preserve/delete]

---

### **OWNER ONLY** - Data Management When They Sell Property

**Scenario:** Owner sells ERF 456 to new owner

**Status Transition:** `active` → `transferred` (if staying in estate) OR `inactive` (if leaving estate)

**Data Management Questions:**
- How long should former owner data remain accessible for property transfer records?
- Should we keep their contact information for warranty/property history inquiries?
- What about their emergency contacts and family information?
- How do we handle their title deed numbers and legal documents?

**Considerations:**
- Owners have **legal/financial history** with the property
- New owners may need **contact information for property-related questions**
- **Legal documents:** May need to be preserved for longer periods
- **Financial records:** May be needed for tax, insurance, or legal purposes

**YOUR INPUT FOR OWNER DATA RETENTION:**
[Please specify how long to keep former owner data and what information must be preserved for legal/property reasons]

---

### **OWNER-RESIDENT** - Two Different Scenarios

#### **Scenario A: Owner-Resident moves out but KEEPS property (becomes Owner Only)**

**Status Transition:** 
- **Resident record:** `active` → `inactive` 
- **Owner record:** Remains `active`

**Data Management Questions:**
- How long should the inactive resident data be kept?
- Should emergency contacts transfer from resident record to owner record?
- What about daily access needs (intercom, gate access) - should these be modified?
- Should vehicle registrations be updated to reflect non-resident status?

**Considerations:**
- Still has **ownership rights and responsibilities**
- May need **different access levels** (owner access vs resident access)
- **Emergency contacts:** May change since they don't live there anymore
- **Communication preferences:** May want property updates but not daily resident info

#### **Scenario B: Owner-Resident sells property (loses both roles)**

**Status Transition:** 
- **Both resident and owner records:** `active` → `transferred` OR `inactive`

**Data Management Questions:**
- How long should both records be preserved?
- Should we maintain the link between their resident and owner histories?
- What information needs to be available for the new owner-resident?
- How do we handle the complete relationship termination?

**Considerations:**
- **Most complex transition** - losing both ownership and residency
- **Property history:** New owners may need their contact info for questions
- **Legal requirements:** May need to preserve records for longer due to ownership component
- **Complete access termination:** All systems (resident AND owner) need updating

**YOUR INPUT FOR OWNER-RESIDENT DATA RETENTION:**
[Please specify different retention periods and policies for Scenario A (keeps ownership) vs Scenario B (sells property)]

---

## ❓ KEY DISCUSSION QUESTIONS

### 1. Data Retention Policy by User Group
**Question:** How long should we keep user data for each group after they become inactive?

**User Group Specific Considerations:**

**TENANT ONLY:**
- Typical retention: 6 months to 2 years
- Reasons: Deposit disputes, reference checks, damage claims
- Security: Immediate access revocation needed

**OWNER ONLY:**
- Typical retention: 5-10 years or indefinitely
- Reasons: Property history, legal documents, warranty issues
- Legal: May have statutory requirements for financial records

**OWNER-RESIDENT:**
- Scenario A (keeps ownership): Resident data 2-3 years, Owner data indefinitely
- Scenario B (sells property): Combined records 5-10 years
- Complexity: Need to maintain relationship between both roles

**YOUR ANSWER:**
[Please specify retention periods for each user group and explain your reasoning]

### 2. Vehicle Transfer Management
**Question:** Should vehicles automatically transfer to new users?

**Considerations:**
- Vehicles might belong to the person, not the property
- Some vehicles might transfer with tenancy agreements
- New users might have different vehicles

**YOUR ANSWER:**
[Please provide your approach to vehicle transitions]

### 3. Access Control Timing
**Question:** Should old users immediately lose access or have a grace period?

**Options:**
- Immediate deactivation upon transfer
- Grace period (1 week, 1 month) for transition
- Admin-controlled deactivation timing
- Different timing for owners vs tenants

**YOUR ANSWER:**
[Please specify your preferred access control approach]

### 4. Communication and Notifications
**Question:** Should both old and new users be notified of transfers?

**Considerations:**
- Privacy concerns
- Transparency in the process
- Legal notification requirements
- Admin notification preferences

**YOUR ANSWER:**
[Please outline your communication preferences]

### 5. Emergency Contact Transitions
**Question:** How do we handle emergency contact transitions?

**Scenarios:**
- Emergency contacts might be property-specific
- Some contacts might transfer with the person
- New users need time to update emergency contacts

**YOUR ANSWER:**
[Please describe how emergency contacts should be handled]

### 6. Current Manual Process
**Question:** How do you currently handle these transitions manually?

**Please describe:**
- What paperwork/forms are involved?
- Who initiates the process?
- What information needs to be transferred?
- What are the biggest pain points?

**YOUR ANSWER:**
[Please provide detailed description of current process]

### 7. Legal and Compliance Requirements
**Question:** Are there any legal/compliance requirements for data retention in your jurisdiction?

**Considerations:**
- POPI Act compliance (South Africa)
- Property management regulations
- Financial record keeping requirements
- Insurance and liability considerations

**YOUR ANSWER:**
[Please outline any legal requirements we must consider]

### 8. User-Initiated Processes
**Question:** Should users be able to initiate their own "moving out" process?

**Considerations:**
- User convenience and self-service
- Admin control and verification needs
- Potential for misuse or errors
- Integration with existing procedures

**YOUR ANSWER:**
[Please indicate if users should have self-service options]

---

## 🛠️ TECHNICAL IMPLEMENTATION PLANNING

### Database Changes Needed:
- Add `effective_from` and `effective_to` dates to user-property relationships
- Create `property_transfers` table to track all transitions
- Enhance user status field with more granular options
- Add invitation tracking system

### New API Endpoints Required:
- `/admin/invite-user` - Send invitation emails
- `/admin/transfer-property` - Handle property transfers  
- `/admin/user-history/{erf}` - View all users for a property
- `/admin/deactivate-user` - Safely deactivate users
- `/admin/user-transitions` - View all transitions and pending actions

### Admin Dashboard Enhancements:
- Property Management section
- User Lifecycle Management panel
- Transition history and audit logs
- Bulk operation capabilities
- Notification and communication center

**YOUR INPUT NEEDED:**
- What technical features are highest priority?
- Are there integration requirements with other systems?
- What reporting capabilities do you need?

---

## 📋 NEXT STEPS

Based on your responses to this discussion document, we will:

1. **Design the database schema** for user lifecycle management
2. **Create the invitation system** with email templates
3. **Build the property transfer workflow** with admin controls
4. **Implement status management** with appropriate transitions
5. **Develop reporting and audit capabilities**
6. **Create user documentation** and training materials

**YOUR FINAL THOUGHTS:**
[Please add any additional considerations, concerns, or requirements not covered above]

---

## 📝 INSTRUCTIONS FOR COMPLETION

1. **Copy this content** into a Word document
2. **Fill in your answers** under each "YOUR ANSWER:" section
3. **Add any additional notes** or requirements you think of
4. **Save and share** the completed document for review
5. **We'll use your input** to design the implementation plan

**Contact:** Available for follow-up discussion and clarification on any points.

---

**Document Version:** 1.0  
**Last Updated:** July 29, 2025  
**Status:** Awaiting stakeholder input
