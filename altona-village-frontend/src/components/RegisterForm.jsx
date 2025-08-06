import { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '@/lib/auth.jsx';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Home, CheckCircle, MapPin, Search } from 'lucide-react';
import EnhancedAltonaVillageMap from './EnhancedAltonaVillageMap';
import { useAddressAutoFill } from '@/hooks/useAddressAutoFill.jsx';

const RegisterForm = ({ onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    emergency_contact_name: '',
    emergency_contact_number: '',
    id_number: '',
    erf_number: '',
    street_number: '',
    street_name: '',
    is_owner: false,
    is_resident: false, // NEW
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showMap, setShowMap] = useState(false);

  const { register } = useAuth();
  const { lookupAddress, loading: erfLoading, error: erfError, clearError } = useAddressAutoFill();
  const erfInputRef = useRef(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Handle ERF autofill (isolated from form state)
  const performErfLookup = useCallback(async (erfNumber) => {
    if (erfNumber && erfNumber.trim().length >= 2) {
      try {
        const addressData = await lookupAddress(erfNumber);
        if (addressData) {
          // Auto-fill the address fields
          setFormData(prev => ({
            ...prev,
            street_number: addressData.street_number || '',
            street_name: addressData.street_name || ''
          }));
          // Clear any previous errors since we found data
          setError('');
        }
      } catch (error) {
        console.log('ERF lookup failed:', error);
      }
    }
  }, [lookupAddress]);

  // Handle ERF input change and trigger lookup
  const handleErfChange = useCallback((e) => {
    const value = e.target.value;
    // Update form data immediately
    setFormData(prev => ({
      ...prev,
      erf_number: value
    }));
    // Clear any lookup errors
    clearError();
  }, [clearError]);

  // Handle ERF lookup on blur (when user finishes typing)
  const handleErfBlur = useCallback((e) => {
    const erfNumber = e.target.value.trim();
    if (erfNumber && erfNumber.length >= 1) {
      performErfLookup(erfNumber);
    }
  }, [performErfLookup]);

  // Handle ERF lookup on Enter key
  const handleErfKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const erfNumber = e.target.value.trim();
      if (erfNumber && erfNumber.length >= 1) {
        performErfLookup(erfNumber);
      }
    }
  }, [performErfLookup]);

  const handleMapErfSelect = (erfNumber, streetAddress) => {
    // Parse street address to get street number and name
    const addressParts = streetAddress.trim().split(' ');
    const streetNumber = addressParts[0];
    const streetName = addressParts.slice(1).join(' ');
    
    setFormData(prev => ({
      ...prev,
      erf_number: erfNumber,
      street_number: streetNumber,
      street_name: streetName
    }));
    setShowMap(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Get current ERF value directly from input
    const currentErfValue = erfInputRef.current?.value || '';

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    // Combine street_number and street_name into address for backend compatibility
    const { confirmPassword, street_number, street_name, ...submitData } = formData;
    const combinedAddress = `${street_number} ${street_name}`.trim();
    
    if (!combinedAddress) {
      setError('Please enter both street number and street name');
      setLoading(false);
      return;
    }
    
    const finalSubmitData = {
      ...submitData,
      erf_number: currentErfValue,
      address: combinedAddress
    };

    const result = await register(finalSubmitData);

    if (result.success) {
      setSuccess(true);
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="h-6 w-6 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-green-600">Registration Submitted!</CardTitle>
            <CardDescription>
              Your application is now pending admin approval.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-gray-600 mb-4">
              <strong>What happens next:</strong><br/>
              • Your application will be reviewed by estate management<br/>
              • You will receive an email notification once approved<br/>
              • Please check your email regularly for updates
            </p>
            <div className="bg-blue-50 p-3 rounded-lg mb-4">
              <p className="text-xs text-blue-700">
                <strong>Note:</strong> The approval process typically takes 1-2 business days. 
                If you have any questions, please contact the estate office directly.
              </p>
            </div>
            <Button onClick={onSwitchToLogin} className="w-full">
              Back to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Home className="h-6 w-6 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold">Join Altona Village</CardTitle>
          <CardDescription>
            Register for your community portal account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name">First Name</Label>
                <Input
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  placeholder="John"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name">Last Name</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Doe"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="id_number">ID Number</Label>
              <Input
                id="id_number"
                name="id_number"
                value={formData.id_number}
                onChange={handleChange}
                placeholder="Enter your ID number"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="erf_number">Erf Number</Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    ref={erfInputRef}
                    id="erf_number"
                    name="erf_number"
                    value={formData.erf_number}
                    onChange={handleErfChange}
                    onBlur={handleErfBlur}
                    onKeyDown={handleErfKeyDown}
                    placeholder="e.g. 27627 (Press Enter or click away to populate address)"
                    autoComplete="off"
                    required
                    disabled={erfLoading}
                  />
                  {erfLoading && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    </div>
                  )}
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowMap(true)}
                  className="flex items-center gap-1 px-3 whitespace-nowrap"
                >
                  <MapPin className="w-4 h-4" />
                  Find on Map
                </Button>
              </div>
              <div className="text-xs text-gray-500 space-y-1">
                <p>Enter your ERF number, then press Enter or click away to populate address fields</p>
                <p>Or click "Find on Map" to locate your property on the Altona Village map</p>
                <p className="text-blue-600">💡 Try: 27627, 27626, 12345, or other valid ERF numbers</p>
              </div>
              {erfError && (
                <p className="text-xs text-amber-600">
                  Address lookup failed - please enter address manually
                </p>
              )}
              {!erfError && formData.street_number && formData.street_name && (
                <p className="text-xs text-green-600">
                  ✓ Address auto-populated from ERF {formData.erf_number}
                </p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="street_number">Street Number</Label>
                <Input
                  id="street_number"
                  name="street_number"
                  value={formData.street_number}
                  onChange={handleChange}
                  placeholder="e.g. 10"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="street_name">Street Name</Label>
                <Input
                  id="street_name"
                  name="street_name"
                  value={formData.street_name}
                  onChange={handleChange}
                  placeholder="e.g. Main Street"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="john.doe@example.com"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone_number">Phone Number</Label>
              <Input
                id="phone_number"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="+27 123 456 7890"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter password"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm password"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergency_contact_name">Emergency Contact Name</Label>
              <Input
                id="emergency_contact_name"
                name="emergency_contact_name"
                value={formData.emergency_contact_name}
                onChange={handleChange}
                placeholder="Emergency contact person"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergency_contact_number">Emergency Contact Number</Label>
              <Input
                id="emergency_contact_number"
                name="emergency_contact_number"
                value={formData.emergency_contact_number}
                onChange={handleChange}
                placeholder="+27 123 456 7890"
              />
            </div>

            {/* NEW CHECKBOXES */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_resident"
                name="is_resident"
                checked={formData.is_resident}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_resident: checked }))}
              />
              <Label htmlFor="is_resident" className="text-sm">
                Will you be a resident here?
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_owner"
                name="is_owner"
                checked={formData.is_owner}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_owner: checked }))}
              />
              <Label htmlFor="is_owner" className="text-sm">
                Are you the registered owner?
              </Label>
            </div>
            {/* END NEW CHECKBOXES */}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Register
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <button
                onClick={onSwitchToLogin}
                className="text-blue-600 hover:underline font-medium"
              >
                Sign in here
              </button>
            </p>
          </div>
        </CardContent>
      </Card>
      
      {/* Enhanced Altona Village Map Modal with PDF Support */}
      {showMap && (
        <EnhancedAltonaVillageMap
          onErfSelect={handleMapErfSelect}
          selectedErf={formData.erf_number}
          onClose={() => setShowMap(false)}
        />
      )}
    </div>
  );
};

export default RegisterForm;