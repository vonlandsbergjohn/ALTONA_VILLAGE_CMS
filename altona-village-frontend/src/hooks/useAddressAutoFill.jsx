import { useState, useCallback, useRef } from 'react';

// Custom hook for ERF address auto-fill functionality
export const useAddressAutoFill = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const lookupAddress = useCallback(async (erfNumber) => {
    if (!erfNumber || erfNumber.trim() === '') {
      return null;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/public/erf-lookup/${erfNumber.trim()}`);
      const data = await response.json();

      if (response.ok && data.success) {
        return {
          street_number: data.data.street_number,
          street_name: data.data.street_name,
          full_address: data.data.full_address,
          suburb: data.data.suburb,
          postal_code: data.data.postal_code
        };
      } else {
        // Don't set error for 404 - just means no mapping found
        if (response.status !== 404) {
          setError(data.error || 'Failed to lookup address');
        }
        return null;
      }
    } catch (error) {
      setError('Network error during address lookup');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError('');
  }, []);

  return {
    lookupAddress,
    loading,
    error,
    clearError
  };
};

// Utility function to auto-fill address fields
export const autoFillAddressFields = (addressData, setFieldValue) => {
  if (!addressData) return;

  // Set individual fields
  if (addressData.street_number) {
    setFieldValue('street_number', addressData.street_number);
  }
  if (addressData.street_name) {
    setFieldValue('street_name', addressData.street_name);
  }
  if (addressData.full_address) {
    setFieldValue('full_address', addressData.full_address);
  }
  if (addressData.suburb) {
    setFieldValue('suburb', addressData.suburb);
  }
  if (addressData.postal_code) {
    setFieldValue('postal_code', addressData.postal_code);
  }
};

// Component for ERF input with auto-fill functionality
export const ErfInputWithAutoFill = ({ 
  value, 
  onChange, 
  onAddressFound, 
  disabled = false,
  placeholder = "Enter ERF number",
  className = "",
  ...props 
}) => {
  const { lookupAddress, loading } = useAddressAutoFill();
  const timeoutRef = useRef(null);

  const handleErfChange = (e) => {
    const erfNumber = e.target.value;
    onChange(erfNumber);
    
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    // Set new timeout for lookup (debounced)
    if (erfNumber && erfNumber.trim().length >= 3) {
      timeoutRef.current = setTimeout(async () => {
        const addressData = await lookupAddress(erfNumber);
        if (addressData && onAddressFound) {
          onAddressFound(addressData);
        }
      }, 500); // 500ms delay to allow user to finish typing
    }
  };

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={handleErfChange}
        disabled={disabled || loading}
        placeholder={placeholder}
        className={`${className} ${loading ? 'opacity-50' : ''}`}
        {...props}
      />
      {loading && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent"></div>
        </div>
      )}
    </div>
  );
};
