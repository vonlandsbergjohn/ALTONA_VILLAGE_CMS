import { useState } from 'react';
import { useAuth } from '@/lib/auth.jsx';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Home, CheckCircle } from 'lucide-react';

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
    address: '',
    is_owner: false,
    is_resident: false, // NEW
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const { register } = useAuth();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    const { confirmPassword, ...submitData } = formData;
    const result = await register(submitData);

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
              <Input
                id="erf_number"
                name="erf_number"
                value={formData.erf_number}
                onChange={handleChange}
                placeholder="e.g. 123"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Address in Altona Village</Label>
              <Input
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="e.g. 10 Main Street"
                required
              />
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
    </div>
  );
};

export default RegisterForm;