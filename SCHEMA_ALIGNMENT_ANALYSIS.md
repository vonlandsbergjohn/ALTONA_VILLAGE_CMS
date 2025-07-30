# Database Schema Alignment Analysis
# Transition Request Data → Production Database Migration

## 🔍 SCHEMA MISMATCH ANALYSIS

### **Current Production Database Schema:**

#### **Residents Table:**
```sql
- first_name (String(100), NOT NULL)
- last_name (String(100), NOT NULL) 
- phone_number (String(20))
- emergency_contact_name (String(255))
- emergency_contact_number (String(20))
- id_number (String(50), NOT NULL)
- erf_number (String(50), NOT NULL)
- street_number (String(10), NOT NULL)
- street_name (String(100), NOT NULL)
- full_address (String(255), NOT NULL)
- intercom_code (String(20))
- moving_in_date (Date)
- moving_out_date (Date)
```

#### **Owners Table:**
```sql
- first_name (String(100), NOT NULL)
- last_name (String(100), NOT NULL)
- phone_number (String(20))
- id_number (String(50), NOT NULL)
- erf_number (String(50), NOT NULL)
- street_number (String(10), NOT NULL) 
- street_name (String(100), NOT NULL)
- full_address (String(255), NOT NULL)
- intercom_code (String(20))
- title_deed_number (String(100))
- acquisition_date (Date)
- postal_street_number (String(10))
- postal_street_name (String(100))
- postal_suburb (String(100))
- postal_city (String(100))
- postal_code (String(10))
- postal_province (String(50))
- full_postal_address (String(500))
- emergency_contact_name (String(255))
- emergency_contact_number (String(20))
```

#### **Vehicles Table:**
```sql
- registration_number (String(50), UNIQUE, NOT NULL)
- make (String(100))
- model (String(100))
- color (String(50))
- resident_id (FK) OR owner_id (FK)
```

### **Current Transition Request Schema:**

#### **New Occupant Fields:**
```sql
- new_occupant_first_name (String) ✅ MATCHES
- new_occupant_last_name (String) ✅ MATCHES  
- new_occupant_phone (String) ✅ MATCHES
- new_occupant_email (String) ❌ MISSING IN PRODUCTION
- new_occupant_id_number (String) ✅ MATCHES
- new_occupant_adults (Integer) ❌ NOT NEEDED FOR MIGRATION
- new_occupant_children (Integer) ❌ NOT NEEDED FOR MIGRATION
- new_occupant_pets (Integer) ❌ NOT NEEDED FOR MIGRATION
```

#### **TransitionVehicle Fields:**
```sql
- vehicle_make (String(100)) ✅ MATCHES 'make'
- vehicle_model (String(100)) ✅ MATCHES 'model'  
- license_plate (String(50)) ✅ MATCHES 'registration_number'
- ❌ MISSING: color (String(50))
```

---

## ⚠️ **CRITICAL GAPS IDENTIFIED:**

### **1. Missing Required Fields for Users/Residents/Owners:**
```sql
❌ street_number - Required for address
❌ street_name - Required for address  
❌ full_address - Required for display
❌ intercom_code - Required for access
❌ emergency_contact_name - Required for safety
❌ emergency_contact_number - Required for safety
```

### **2. Missing Vehicle Fields:**
```sql
❌ color - Required field in Vehicle table
```

### **3. Missing Owner-Specific Fields:**
```sql
❌ title_deed_number - For property ownership
❌ acquisition_date - For ownership tracking
❌ postal_address components - For non-resident owners
```

### **4. Address Structure Mismatch:**
- **Production**: Separate street_number + street_name + full_address
- **Transition**: Single address approach (if any)

---

## 🛠️ **REQUIRED MIGRATION UPDATES:**

### **Phase 1: Database Schema Updates**
Add missing fields to `user_transition_requests` table:

```sql
-- Address components
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_street_number VARCHAR(10);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_street_name VARCHAR(100);  
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_full_address VARCHAR(255);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_intercom_code VARCHAR(20);

-- Emergency contacts  
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_emergency_contact_name VARCHAR(255);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_emergency_contact_number VARCHAR(20);

-- Owner-specific fields
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_title_deed_number VARCHAR(100);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_acquisition_date DATE;

-- Postal address (for non-resident owners)
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_postal_street_number VARCHAR(10);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_postal_street_name VARCHAR(100);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_postal_suburb VARCHAR(100);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_postal_city VARCHAR(100);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_postal_code VARCHAR(10);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_postal_province VARCHAR(50);
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_full_postal_address VARCHAR(500);

-- Move-in date
ALTER TABLE user_transition_requests ADD COLUMN new_occupant_moving_in_date DATE;
```

```sql
-- Vehicle color field
ALTER TABLE transition_vehicles ADD COLUMN vehicle_color VARCHAR(50);
```

### **Phase 2: Frontend Form Updates**
Update `UserTransitionRequest.jsx` to include:

#### **New Occupant Address Section:**
- Street Number (required)
- Street Name (required)  
- Intercom Code
- Moving In Date

#### **New Occupant Emergency Contact Section:**
- Emergency Contact Name (required)
- Emergency Contact Phone (required)

#### **Owner-Specific Section:** (if new_occupant_type = 'new_owner')
- Title Deed Number
- Acquisition Date
- Postal Address (full form)

#### **Vehicle Form Updates:**
- Add Color field to vehicle entries

### **Phase 3: Migration Logic Implementation**
Create `execute_transition_completion()` function that:

1. **Validates all required fields present**
2. **Creates new User account**
3. **Creates new Resident/Owner record** 
4. **Creates new Vehicle records**
5. **Updates Property ownership**
6. **Transfers intercom codes**
7. **Archives old user data**
8. **Marks transition as completed**

---

## 🎯 **MIGRATION WORKFLOW:**

```
1. Admin reviews transition request
2. All required new occupant data collected
3. Admin clicks "Complete Transition" 
4. System validates schema compatibility  
5. Creates new user/resident/owner records
6. Transfers vehicle registrations
7. Updates property ownership
8. Archives outgoing user
9. Activates new user account
10. Sends welcome email to new occupant
```

---

## ✅ **VALIDATION CHECKLIST:**

Before transition completion, system must verify:

- [ ] New occupant first_name + last_name
- [ ] New occupant id_number  
- [ ] New occupant phone_number
- [ ] New occupant street_number + street_name
- [ ] New occupant emergency contacts
- [ ] All vehicles have make + model + license_plate + color
- [ ] Owner transactions have title_deed_number
- [ ] Address components can build full_address
- [ ] No duplicate id_numbers in system
- [ ] No duplicate vehicle registrations

---

This approach ensures **seamless data migration** where transition request data perfectly matches production database requirements, enabling smooth user replacement when "Completed" status is triggered.
