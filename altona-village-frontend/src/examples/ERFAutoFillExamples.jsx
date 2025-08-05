/**
 * Demo: How to integrate ERF auto-fill functionality in any form
 * 
 * This file shows examples of how to use the ERF address auto-fill system
 * that we just implemented throughout the application.
 */

// Example 1: Using the useAddressAutoFill hook in a React component
import React, { useState } from 'react';
import { useAddressAutoFill } from '@/lib/useAddressAutoFill';

const RegistrationFormExample = () => {
  const [formData, setFormData] = useState({
    erfNumber: '',
    streetNumber: '',
    streetName: ''
  });

  // Use the auto-fill hook
  const { loading, error, lookupAddress } = useAddressAutoFill();

  const handleErfChange = async (e) => {
    const erfNumber = e.target.value;
    setFormData(prev => ({ ...prev, erfNumber }));

    // Auto-fill when ERF number is entered (at least 3 digits)
    if (erfNumber.length >= 3) {
      const addressData = await lookupAddress(erfNumber);
      if (addressData) {
        setFormData(prev => ({
          ...prev,
          streetNumber: addressData.street_number || '',
          streetName: addressData.street_name || ''
        }));
      }
    }
  };

  return (
    <form>
      <div>
        <label>ERF Number:</label>
        <input
          type="text"
          value={formData.erfNumber}
          onChange={handleErfChange}
          placeholder="Enter ERF number..."
        />
        {loading && <span>Looking up address...</span>}
        {error && <span className="error">{error}</span>}
      </div>

      <div>
        <label>Street Number:</label>
        <input
          type="text"
          value={formData.streetNumber}
          onChange={(e) => setFormData(prev => ({ ...prev, streetNumber: e.target.value }))}
        />
      </div>

      <div>
        <label>Street Name:</label>
        <input
          type="text"
          value={formData.streetName}
          onChange={(e) => setFormData(prev => ({ ...prev, streetName: e.target.value }))}
        />
      </div>
    </form>
  );
};

// Example 2: Using the ErfInputWithAutoFill component (even simpler)
import { ErfInputWithAutoFill } from '@/lib/useAddressAutoFill';

const SimpleFormExample = () => {
  const [formData, setFormData] = useState({
    erfNumber: '',
    streetNumber: '',
    streetName: ''
  });

  const handleAddressAutoFill = (addressData) => {
    setFormData(prev => ({
      ...prev,
      streetNumber: addressData.street_number || '',
      streetName: addressData.street_name || ''
    }));
  };

  return (
    <form>
      <ErfInputWithAutoFill
        value={formData.erfNumber}
        onChange={(value) => setFormData(prev => ({ ...prev, erfNumber: value }))}
        onAddressFound={handleAddressAutoFill}
        placeholder="Enter ERF number for auto-fill..."
        className="form-input"
      />

      <input
        type="text"
        value={formData.streetNumber}
        onChange={(e) => setFormData(prev => ({ ...prev, streetNumber: e.target.value }))}
        placeholder="Street Number (auto-filled)"
      />

      <input
        type="text"
        value={formData.streetName}
        onChange={(e) => setFormData(prev => ({ ...prev, streetName: e.target.value }))}
        placeholder="Street Name (auto-filled)"
      />
    </form>
  );
};

// Example 3: Using the utility function directly for manual control
import { autoFillAddressFields } from '@/lib/useAddressAutoFill';

const ManualControlExample = () => {
  const handleErfBlur = async (erfNumber) => {
    if (erfNumber) {
      const success = await autoFillAddressFields(erfNumber, {
        streetNumberField: document.getElementById('street-number'),
        streetNameField: document.getElementById('street-name'),
        onSuccess: (data) => console.log('Address found:', data),
        onError: (error) => console.log('Error:', error)
      });
      
      if (success) {
        console.log('Address auto-filled successfully');
      }
    }
  };

  return (
    <form>
      <input
        type="text"
        onBlur={(e) => handleErfBlur(e.target.value)}
        placeholder="ERF Number"
      />
      <input id="street-number" placeholder="Street Number" />
      <input id="street-name" placeholder="Street Name" />
    </form>
  );
};

export {
  RegistrationFormExample,
  SimpleFormExample,
  ManualControlExample
};
