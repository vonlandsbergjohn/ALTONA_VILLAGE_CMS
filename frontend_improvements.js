/* 
IMPROVED REGISTRATION FORM STRUCTURE
For better address handling and gate access sorting

This shows how the frontend registration form should be updated
to use the new separated address fields
*/

// Example React component structure for improved registration

const ImprovedRegistrationForm = () => {
  const [formData, setFormData] = useState({
    // User account info
    email: '',
    password: '',
    confirmPassword: '',
    
    // Personal info (separated names)
    firstName: '',
    lastName: '',
    phoneNumber: '',
    idNumber: '',
    
    // Address info (separated components) 
    erfNumber: '',
    streetNumber: '',          // NEW: Separate field for number
    streetName: '',            // NEW: Separate field for street name
    // fullAddress auto-generated from above
    
    // Emergency contact
    emergencyContactName: '',
    emergencyContactNumber: '',
    
    // Registration type
    isResident: false,
    isOwner: false,
    
    // Owner-specific fields (only if isOwner = true)
    titleDeedNumber: '',
    acquisitionDate: '',
    
    // Postal address for non-resident owners (only if isOwner = true && isResident = false)
    postalStreetNumber: '',
    postalStreetName: '',
    postalSuburb: '',
    postalCity: '',
    postalCode: '',
    postalProvince: ''
  });

  return (
    <form className="improved-registration-form">
      {/* Account Information */}
      <section className="form-section">
        <h3>Account Information</h3>
        <input
          type="email"
          placeholder="Email Address"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
        />
      </section>

      {/* Personal Information */}
      <section className="form-section">
        <h3>Personal Information</h3>
        <div className="name-fields">
          <input
            type="text"
            placeholder="First Name"
            value={formData.firstName}
            onChange={(e) => setFormData({...formData, firstName: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="Last Name" 
            value={formData.lastName}
            onChange={(e) => setFormData({...formData, lastName: e.target.value})}
            required
          />
        </div>
        <input
          type="tel"
          placeholder="Phone Number"
          value={formData.phoneNumber}
          onChange={(e) => setFormData({...formData, phoneNumber: e.target.value})}
        />
        <input
          type="text"
          placeholder="ID Number"
          value={formData.idNumber}
          onChange={(e) => setFormData({...formData, idNumber: e.target.value})}
          required
        />
      </section>

      {/* Property Address - IMPROVED STRUCTURE */}
      <section className="form-section">
        <h3>Property Address in Altona Village</h3>
        <div className="address-fields">
          <input
            type="text"
            placeholder="ERF Number (e.g., ERF001)"
            value={formData.erfNumber}
            onChange={(e) => setFormData({...formData, erfNumber: e.target.value})}
            required
          />
          <div className="street-address">
            <input
              type="text"
              placeholder="Street Number (e.g., 33)"
              value={formData.streetNumber}
              onChange={(e) => setFormData({...formData, streetNumber: e.target.value})}
              className="street-number"
              required
            />
            <input
              type="text"
              placeholder="Street Name (e.g., Yellowwood Crescent)"
              value={formData.streetName}
              onChange={(e) => setFormData({...formData, streetName: e.target.value})}
              className="street-name"
              required
            />
          </div>
          <div className="address-preview">
            <strong>Full Address Preview:</strong> 
            {formData.streetNumber && formData.streetName ? 
              `${formData.streetNumber} ${formData.streetName}, Altona Village, Worcester` : 
              'Will be generated automatically'
            }
          </div>
        </div>
      </section>

      {/* Registration Type */}
      <section className="form-section">
        <h3>Registration Type</h3>
        <div className="registration-type">
          <label>
            <input
              type="checkbox"
              checked={formData.isResident}
              onChange={(e) => setFormData({...formData, isResident: e.target.checked})}
            />
            I am a <strong>Resident</strong> (I live on this property)
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.isOwner}
              onChange={(e) => setFormData({...formData, isOwner: e.target.checked})}
            />
            I am an <strong>Owner</strong> (I own this property)
          </label>
        </div>
      </section>

      {/* Owner-Specific Fields */}
      {formData.isOwner && (
        <section className="form-section">
          <h3>Owner Information</h3>
          <input
            type="text"
            placeholder="Title Deed Number"
            value={formData.titleDeedNumber}
            onChange={(e) => setFormData({...formData, titleDeedNumber: e.target.value})}
          />
          <input
            type="date"
            placeholder="Property Acquisition Date"
            value={formData.acquisitionDate}
            onChange={(e) => setFormData({...formData, acquisitionDate: e.target.value})}
          />
        </section>
      )}

      {/* Postal Address for Non-Resident Owners */}
      {formData.isOwner && !formData.isResident && (
        <section className="form-section">
          <h3>Postal Address (for correspondence)</h3>
          <div className="postal-address">
            <div className="street-address">
              <input
                type="text"
                placeholder="Street Number"
                value={formData.postalStreetNumber}
                onChange={(e) => setFormData({...formData, postalStreetNumber: e.target.value})}
                className="street-number"
              />
              <input
                type="text"
                placeholder="Street Name"
                value={formData.postalStreetName}
                onChange={(e) => setFormData({...formData, postalStreetName: e.target.value})}
                className="street-name"
              />
            </div>
            <input
              type="text"
              placeholder="Suburb"
              value={formData.postalSuburb}
              onChange={(e) => setFormData({...formData, postalSuburb: e.target.value})}
            />
            <input
              type="text"
              placeholder="City"
              value={formData.postalCity}
              onChange={(e) => setFormData({...formData, postalCity: e.target.value})}
            />
            <div className="code-province">
              <input
                type="text"
                placeholder="Postal Code"
                value={formData.postalCode}
                onChange={(e) => setFormData({...formData, postalCode: e.target.value})}
                className="postal-code"
              />
              <select
                value={formData.postalProvince}
                onChange={(e) => setFormData({...formData, postalProvince: e.target.value})}
                className="province"
              >
                <option value="">Select Province</option>
                <option value="Western Cape">Western Cape</option>
                <option value="Gauteng">Gauteng</option>
                <option value="KwaZulu-Natal">KwaZulu-Natal</option>
                {/* Add other provinces */}
              </select>
            </div>
          </div>
        </section>
      )}

      {/* Emergency Contact */}
      <section className="form-section">
        <h3>Emergency Contact</h3>
        <input
          type="text"
          placeholder="Emergency Contact Name"
          value={formData.emergencyContactName}
          onChange={(e) => setFormData({...formData, emergencyContactName: e.target.value})}
        />
        <input
          type="tel"
          placeholder="Emergency Contact Number"
          value={formData.emergencyContactNumber}
          onChange={(e) => setFormData({...formData, emergencyContactNumber: e.target.value})}
        />
      </section>

      <button type="submit" className="submit-button">
        Register
      </button>
    </form>
  );
};

/* 
CSS STYLES FOR IMPROVED FORM
*/
.improved-registration-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.form-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.form-section h3 {
  margin-bottom: 15px;
  color: #2c3e50;
  border-bottom: 2px solid #3498db;
  padding-bottom: 5px;
}

.name-fields, .address-fields, .street-address, .code-province {
  display: flex;
  gap: 10px;
}

.street-number {
  flex: 0 0 100px;
}

.street-name {
  flex: 1;
}

.postal-code {
  flex: 0 0 120px;
}

.province {
  flex: 1;
}

.address-preview {
  margin-top: 10px;
  padding: 10px;
  background: #e8f4f8;
  border-radius: 4px;
  font-style: italic;
}

.registration-type {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.registration-type label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.submit-button {
  width: 100%;
  padding: 15px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.3s;
}

.submit-button:hover {
  background: #219a52;
}

/* 
BENEFITS OF THIS IMPROVED STRUCTURE:

1. ✅ Separated street numbers and names for proper sorting
2. ✅ No more address format confusion
3. ✅ Automatic full address generation
4. ✅ Separate postal addresses for non-resident owners
5. ✅ Clear registration type selection
6. ✅ Better data consistency
7. ✅ Perfect for gate access register sorting
8. ✅ Easy Excel export with proper columns
9. ✅ Mobile-responsive design
10. ✅ User-friendly interface with clear sections
*/
