import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingSpinner = ({ size = 'default', className = '' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  };

  return (
    <Loader2 className={`animate-spin ${sizeClasses[size]} ${className}`} />
  );
};

export const LoadingCard = ({ title = 'Loading...', description = 'Please wait while we fetch your data' }) => (
  <div className="flex flex-col items-center justify-center py-12 px-6">
    <LoadingSpinner size="lg" className="text-blue-600 mb-4" />
    <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
    <p className="text-sm text-gray-500 text-center max-w-sm">{description}</p>
  </div>
);

export const LoadingPage = ({ 
  title = 'Loading Application...', 
  description = 'Please wait while we set everything up for you' 
}) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <LoadingSpinner size="xl" className="text-blue-600 mb-6 mx-auto" />
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>
      <p className="text-gray-600 max-w-md mx-auto">{description}</p>
    </div>
  </div>
);

export const InlineLoading = ({ text = 'Loading...', className = '' }) => (
  <div className={`flex items-center space-x-2 ${className}`}>
    <LoadingSpinner size="sm" />
    <span className="text-sm text-gray-600">{text}</span>
  </div>
);

export default LoadingSpinner;
