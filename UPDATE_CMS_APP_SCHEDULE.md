# Altona Village CMS - User Lifecycle Management Implementation Plan

**Date:** July 29, 2025  
**Based on:** Completed stakeholder discussion document  
**Status:** Ready for implementation

---

## 📋 EXECUTIVE SUMMARY

Based on your detailed responses, here's what we'll implement:

### **Core Principles:**
- **Admin-controlled system** with user self-service request forms
- **Minimal data retention** - archive immediately except property transfer dates
- **Strong automation preference** but manual admin approval required
- **User dashboard forms** for move-out/sale requests
- **No automatic status triggers** - all changes require admin action

---

## 🔄 STATUS MANAGEMENT SYSTEM

### **Status Definitions & Triggers:**

#### **`active`**
- **Triggers:** Admin approval of new registrations, admin reactivation
- **No automatic triggers**

#### **`inactive`** 
- **Triggers:** Admin action after user move-out/sale request
- **Sub-categories to track:** Moved out, Sold property, Deceased, Banned, Other
- **Data retention:** Archive immediately (delete all data)

#### **`transferred`**
- **Triggers:** Admin action for internal estate moves/role changes
- **Data retention:** Keep property transfer dates only

#### **`pending_transfer`**
- **Triggers:** Admin sets after receiving user form request
- **Access:** Full access maintained
- **Duration:** No auto-revert, admin controls cancellation/completion
- **Notice period:** 30 days typical

---

## 📊 DATA RETENTION POLICY

### **Tenant Only:**
- **Retention:** **NONE** - Delete all data immediately upon move-out
- **Security:** Immediate access revocation

### **Owner Only:**
- **Retention:** **Property transfer dates only**
- **Purpose:** Track ownership history for each ERF
- **Contact info:** Keep for property history inquiries

### **Owner-Resident:**
- **Scenario A (keeps ownership):** Handle as Owner Only
- **Scenario B (sells property):** Handle as Tenant (delete all data)
- **Transfer emergency contacts:** From resident to owner record if staying

---

## 🚀 USER SELF-SERVICE FEATURES

### **Dashboard Forms Required:**

#### **1. Move-Out Request Form (Tenants)**
- Integrated with existing ticket system
- Triggers admin notification
- User can cancel via same form system

#### **2. Property Sale Request Form (Owners)**
- Similar to move-out form
- Triggers pending_transfer status
- Admin approval workflow

#### **3. Status Change Request Form**
- Owner-resident → Owner only
- Tenant → Owner (property purchase)
- Admin approval required

---

## 🛠️ TECHNICAL IMPLEMENTATION PRIORITIES

### **Phase 1: Core System (High Priority)**
1. **User dashboard forms** for move-out/sale requests
2. **Admin status management** panel
3. **Property transfer tracking** (dates only)
4. **User status workflow** with admin controls

### **Phase 2: Enhanced Features**
1. **Bulk operations** for admin
2. **Transition reporting** capabilities
3. **Email automation** (welcome/farewell emails)
4. **Property history tracking** per ERF

### **Phase 3: Integration**
1. **Email template system** for notifications
2. **Audit trail reporting**
3. **Property transfer reports**

---

## 📧 COMMUNICATION SYSTEM

### **Automated Emails:**
- **Welcome emails:** Already exists for new users
- **Farewell emails:** Admin option to send upon move-out/sale
- **Form notifications:** To admin when users submit requests

### **No Communication Needed:**
- Emergency contact transitions (not handled)
- Vehicle access control (handled by separate camera system)

---

## 🏠 PROPERTY MANAGEMENT APPROACH

### **What We Track:**
- **Property transfer dates** from owner to owner
- **ERF numbers and basic address info**
- **Utility meter numbers** (water/electricity)
- **Current active user** per property

### **What We Don't Track:**
- **Title deed numbers** or legal documents
- **Emergency contact transitions**
- **Vehicle ownership transfers** (vehicles belong to people, not properties)
- **Extended historical data**

---

## 🔐 ACCESS CONTROL PHILOSOPHY

### **During Pending Transfer:**
- **Full access maintained** until admin completes transition
- **New registrations allowed** with approval
- **No automatic access changes**

### **Upon Status Change:**
- **Admin controls all access changes**
- **No grace periods** - immediate when admin processes
- **Vehicle registrations handled like other profile updates**

---

## 🎯 KEY SUCCESS METRICS

### **Frequency Expectations:**
- **~20 transitions per year** across all types
- **Most common:** Scenarios 1-4 (never property subdivision)

### **Automation Goals:**
- **User-initiated requests** via dashboard forms
- **Admin approval workflows** for all status changes
- **Bulk operation capabilities** for efficiency
- **Reporting on transition patterns**

---

## 🚨 CRITICAL REQUIREMENTS

### **Must Haves:**
1. **No automatic status triggers** - admin control mandatory
2. **User dashboard forms** integrated with ticket system
3. **Immediate data archival** except property transfer dates
4. **Admin can extend/cancel pending status**
5. **Property transfer date tracking** for ownership history

### **Nice to Haves:**
1. **Bulk operations** for multiple property transitions
2. **Transition reporting** and analytics
3. **Automated farewell emails** with admin control

---

## 📝 NEXT IMPLEMENTATION STEPS

### **Week 1-2: Database Design**
- Create property_transfers table
- Add status tracking fields
- Design user request forms data structure

### **Week 3-4: User Dashboard**
- Build move-out/sale request forms
- Integrate with existing ticket system
- Test user workflow

### **Week 5-6: Admin Panel**
- Status management interface
- Bulk operations capability
- Property transfer tracking

### **Week 7-8: Integration & Testing**
- Email notifications
- Reporting features
- End-to-end testing

---

**This implementation plan reflects your specific needs for admin control, minimal data retention, and user self-service request capabilities. Ready to proceed?**
