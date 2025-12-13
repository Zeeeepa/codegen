import React, { useState } from 'react';
import { X, Save, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { useStore } from '../store';
import toast from 'react-hot-toast';

interface SettingsProps {
  onClose: () => void;
}

export default function Settings({ onClose }: SettingsProps) {
  const { apiToken, organizationId, setApiToken, setOrganizationId } = useStore();
  
  const [token, setToken] = useState(apiToken || '');
  const [orgId, setOrgId] = useState(organizationId || '');
  const [showToken, setShowToken] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');

  const validateToken = async () => {
    if (!token || !orgId) {
      toast.error('Please enter both API token and organization ID');
      return false;
    }

    // Basic format validation
    if (!token.startsWith('sk-')) {
      toast.error('Invalid token format. Token should start with "sk-"');
      return false;
    }

    setIsValidating(true);
    setValidationStatus('idle');

    try {
      // Test API connection
      const response = await fetch(`https://api.codegen.com/v1/organizations/${orgId}/agent/run`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok || response.status === 404) {
        // 404 is ok - means endpoint exists but no runs yet
        setValidationStatus('valid');
        toast.success('✅ API credentials validated successfully!');
        return true;
      } else if (response.status === 401) {
        setValidationStatus('invalid');
        toast.error('❌ Invalid API token or organization ID');
        return false;
      } else {
        throw new Error(`Unexpected status: ${response.status}`);
      }
    } catch (error: any) {
      setValidationStatus('invalid');
      toast.error(`❌ Validation failed: ${error.message}`);
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = async () => {
    const isValid = await validateToken();
    
    if (isValid) {
      setApiToken(token);
      setOrganizationId(orgId);
      toast.success('✅ Settings saved!');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-white">Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Close settings"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* API Configuration Section */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">API Configuration</h3>
            
            {/* Organization ID */}
            <div className="mb-4">
              <label htmlFor="orgId" className="block text-sm font-medium text-gray-300 mb-2">
                Organization ID
              </label>
              <input
                id="orgId"
                type="text"
                value={orgId}
                onChange={(e) => setOrgId(e.target.value)}
                placeholder="e.g., 323"
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <p className="mt-1 text-xs text-gray-400">
                Your CodeGen organization ID
              </p>
            </div>

            {/* API Token */}
            <div className="mb-4">
              <label htmlFor="apiToken" className="block text-sm font-medium text-gray-300 mb-2">
                API Token
              </label>
              <div className="relative">
                <input
                  id="apiToken"
                  type={showToken ? 'text' : 'password'}
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="sk-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  className="w-full px-4 py-2 pr-12 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                  aria-label={showToken ? 'Hide token' : 'Show token'}
                >
                  {showToken ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-400">
                Your CodeGen API token (starts with "sk-")
              </p>
            </div>

            {/* Validation Status */}
            {validationStatus !== 'idle' && (
              <div className={`flex items-center gap-2 p-3 rounded-lg ${
                validationStatus === 'valid' 
                  ? 'bg-green-900 bg-opacity-30 text-green-400'
                  : 'bg-red-900 bg-opacity-30 text-red-400'
              }`}>
                {validationStatus === 'valid' ? (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    <span className="text-sm">API credentials validated successfully</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-5 h-5" />
                    <span className="text-sm">Invalid credentials. Please check and try again.</span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Help Section */}
          <div className="bg-gray-700 bg-opacity-50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-white mb-2">How to get your API credentials:</h4>
            <ol className="text-sm text-gray-300 space-y-1 list-decimal list-inside">
              <li>Go to <a href="https://codegen.com/settings" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300">codegen.com/settings</a></li>
              <li>Copy your Organization ID</li>
              <li>Generate or copy your API token</li>
              <li>Paste both values above</li>
            </ol>
          </div>

          {/* Security Notice */}
          <div className="bg-yellow-900 bg-opacity-20 border border-yellow-700 rounded-lg p-4">
            <div className="flex gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-gray-300">
                <p className="font-semibold text-yellow-500 mb-1">Security Notice</p>
                <p>Your API credentials are stored locally in your browser's localStorage. They are not sent to any third-party servers except CodeGen's API.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isValidating || !token || !orgId}
            className="flex items-center gap-2 px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            <Save className="w-4 h-4" />
            {isValidating ? 'Validating...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}

