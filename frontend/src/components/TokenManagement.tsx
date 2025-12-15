/**
 * TokenManagement Component
 * Manages API keys with scopes, expiration, and revocation
 */

import { useState, useEffect } from 'react';
import { 
  Key, 
  Copy, 
  Eye, 
  EyeOff, 
  Plus, 
  Trash2, 
  AlertCircle, 
  CheckCircle2,
  Clock,
  Shield,
  XCircle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { databaseApi } from '@/services/databaseApi';
import type { ApiKey, ApiKeyScope, CreateApiKeyRequest } from '@/types/database';

// ============================================================================
// Types
// ============================================================================

interface TokenFormData {
  name: string;
  scopes: ApiKeyScope[];
  expires_at?: string;
}

// ============================================================================
// Constants
// ============================================================================

const AVAILABLE_SCOPES: { value: ApiKeyScope; label: string; description: string }[] = [
  { value: 'workflows:read', label: 'Workflows Read', description: 'View workflows' },
  { value: 'workflows:write', label: 'Workflows Write', description: 'Create and edit workflows' },
  { value: 'executions:read', label: 'Executions Read', description: 'View execution history' },
  { value: 'executions:write', label: 'Executions Write', description: 'Start and manage executions' },
  { value: 'templates:read', label: 'Templates Read', description: 'Browse templates' },
  { value: 'templates:write', label: 'Templates Write', description: 'Create and edit templates' },
  { value: 'profiles:read', label: 'Profiles Read', description: 'View profiles' },
  { value: 'profiles:write', label: 'Profiles Write', description: 'Create and edit profiles' },
  { value: 'webhooks:read', label: 'Webhooks Read', description: 'View webhooks' },
  { value: 'webhooks:write', label: 'Webhooks Write', description: 'Create and edit webhooks' },
  { value: 'admin', label: 'Admin', description: 'Full access to all resources' },
];

// ============================================================================
// Component
// ============================================================================

export default function TokenManagement() {
  const [tokens, setTokens] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<TokenFormData>({
    name: '',
    scopes: [],
  });
  const [newlyCreatedToken, setNewlyCreatedToken] = useState<string | null>(null);
  const [visibleTokens, setVisibleTokens] = useState<Set<string>>(new Set());

  // Load tokens on mount
  useEffect(() => {
    loadTokens();
  }, []);

  // ============================================================================
  // API Operations
  // ============================================================================

  async function loadTokens() {
    try {
      setLoading(true);
      const response = await databaseApi.apiKeys.list({
        page: 1,
        limit: 100,
        sort_by: 'created_at',
        sort_order: 'desc',
      });
      setTokens(response.data);
    } catch (error: any) {
      console.error('Failed to load tokens:', error);
      toast.error(error.message || 'Failed to load API tokens');
    } finally {
      setLoading(false);
    }
  }

  async function createToken() {
    if (!formData.name || formData.scopes.length === 0) {
      toast.error('Please provide a name and at least one scope');
      return;
    }

    try {
      const request: CreateApiKeyRequest = {
        name: formData.name,
        scopes: formData.scopes,
        expires_at: formData.expires_at || undefined,
      };

      const response = await databaseApi.apiKeys.create(request);
      
      // Show the plaintext key (only time it's visible)
      setNewlyCreatedToken(response.plaintext_key);
      
      // Refresh tokens list
      await loadTokens();
      
      // Reset form
      setFormData({ name: '', scopes: [] });
      
      toast.success('API token created successfully');
    } catch (error: any) {
      console.error('Failed to create token:', error);
      toast.error(error.message || 'Failed to create API token');
    }
  }

  async function revokeToken(id: string) {
    if (!confirm('Are you sure you want to revoke this token? This action cannot be undone.')) {
      return;
    }

    try {
      await databaseApi.apiKeys.revoke(id);
      await loadTokens();
      toast.success('Token revoked successfully');
    } catch (error: any) {
      console.error('Failed to revoke token:', error);
      toast.error(error.message || 'Failed to revoke token');
    }
  }

  async function deleteToken(id: string) {
    if (!confirm('Are you sure you want to delete this token? This action cannot be undone.')) {
      return;
    }

    try {
      await databaseApi.apiKeys.delete(id);
      await loadTokens();
      toast.success('Token deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete token:', error);
      toast.error(error.message || 'Failed to delete token');
    }
  }

  // ============================================================================
  // UI Helpers
  // ============================================================================

  function toggleScopeSelection(scope: ApiKeyScope) {
    setFormData(prev => ({
      ...prev,
      scopes: prev.scopes.includes(scope)
        ? prev.scopes.filter(s => s !== scope)
        : [...prev.scopes, scope],
    }));
  }

  function toggleTokenVisibility(id: string) {
    setVisibleTokens(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  }

  function maskToken(hash: string): string {
    if (hash.length <= 8) return '••••••••';
    return `${hash.substring(0, 4)}...${hash.substring(hash.length - 4)}`;
  }

  function isTokenExpired(expiresAt?: string): boolean {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  }

  function isTokenExpiringSoon(expiresAt?: string): boolean {
    if (!expiresAt) return false;
    const expiryDate = new Date(expiresAt);
    const daysUntilExpiry = (expiryDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry > 0 && daysUntilExpiry < 7;
  }

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">API Tokens</h2>
          <p className="text-sm text-gray-600">
            Manage API keys for programmatic access to your workflows
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Token
        </button>
      </div>

      {/* Newly Created Token Display */}
      {newlyCreatedToken && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-green-900 mb-2">
                Token Created Successfully
              </h3>
              <p className="text-sm text-green-700 mb-3">
                Make sure to copy your token now. You won't be able to see it again!
              </p>
              <div className="flex items-center gap-2 bg-white border border-green-300 rounded px-3 py-2">
                <code className="flex-1 text-sm font-mono text-gray-900">
                  {newlyCreatedToken}
                </code>
                <button
                  onClick={() => copyToClipboard(newlyCreatedToken)}
                  className="p-1 hover:bg-green-100 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4 text-green-600" />
                </button>
              </div>
              <button
                onClick={() => setNewlyCreatedToken(null)}
                className="mt-3 text-sm text-green-700 hover:text-green-900"
              >
                I've copied my token
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Token Form */}
      {showCreateForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Create New API Token</h3>
          
          <div className="space-y-4">
            {/* Token Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Token Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Production API Token"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Expiration Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expiration Date (Optional)
              </label>
              <input
                type="datetime-local"
                value={formData.expires_at || ''}
                onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Scopes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Permissions (Scopes)
              </label>
              <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3">
                {AVAILABLE_SCOPES.map((scope) => (
                  <label
                    key={scope.value}
                    className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formData.scopes.includes(scope.value)}
                      onChange={() => toggleScopeSelection(scope.value)}
                      className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm text-gray-900">{scope.label}</div>
                      <div className="text-xs text-gray-600">{scope.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={createToken}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Token
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setFormData({ name: '', scopes: [] });
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tokens List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8 text-gray-500">
            Loading tokens...
          </div>
        ) : tokens.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <Key className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No API tokens yet</p>
            <p className="text-sm text-gray-500 mt-1">
              Create your first token to get started
            </p>
          </div>
        ) : (
          tokens.map((token) => {
            const isExpired = isTokenExpired(token.expires_at);
            const isExpiringSoon = isTokenExpiringSoon(token.expires_at);
            const isVisible = visibleTokens.has(token.id);

            return (
              <div
                key={token.id}
                className={`bg-white border rounded-lg p-4 ${
                  isExpired ? 'border-red-300 bg-red-50' : 
                  !token.is_active ? 'border-gray-300 bg-gray-50' :
                  isExpiringSoon ? 'border-yellow-300 bg-yellow-50' :
                  'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Token Name and Status */}
                    <div className="flex items-center gap-2 mb-2">
                      <Key className="w-4 h-4 text-gray-500" />
                      <h4 className="font-semibold text-gray-900">{token.name}</h4>
                      {!token.is_active && (
                        <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
                          Revoked
                        </span>
                      )}
                      {isExpired && (
                        <span className="px-2 py-0.5 bg-red-200 text-red-700 text-xs rounded flex items-center gap-1">
                          <XCircle className="w-3 h-3" />
                          Expired
                        </span>
                      )}
                      {isExpiringSoon && !isExpired && (
                        <span className="px-2 py-0.5 bg-yellow-200 text-yellow-700 text-xs rounded flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          Expiring Soon
                        </span>
                      )}
                    </div>

                    {/* Token Hash */}
                    <div className="flex items-center gap-2 mb-2">
                      <code className="text-sm font-mono text-gray-600">
                        {isVisible ? token.key_hash : maskToken(token.key_hash)}
                      </code>
                      <button
                        onClick={() => toggleTokenVisibility(token.id)}
                        className="p-1 hover:bg-gray-100 rounded transition-colors"
                        title={isVisible ? 'Hide' : 'Show'}
                      >
                        {isVisible ? (
                          <EyeOff className="w-4 h-4 text-gray-500" />
                        ) : (
                          <Eye className="w-4 h-4 text-gray-500" />
                        )}
                      </button>
                      <button
                        onClick={() => copyToClipboard(token.key_hash)}
                        className="p-1 hover:bg-gray-100 rounded transition-colors"
                        title="Copy to clipboard"
                      >
                        <Copy className="w-4 h-4 text-gray-500" />
                      </button>
                    </div>

                    {/* Scopes */}
                    <div className="flex flex-wrap gap-1 mb-2">
                      {token.scopes.map((scope) => (
                        <span
                          key={scope}
                          className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded flex items-center gap-1"
                        >
                          <Shield className="w-3 h-3" />
                          {scope}
                        </span>
                      ))}
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>Created {new Date(token.created_at).toLocaleDateString()}</span>
                      {token.expires_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Expires {new Date(token.expires_at).toLocaleDateString()}
                        </span>
                      )}
                      {token.last_used_at && (
                        <span>Last used {new Date(token.last_used_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-1">
                    {token.is_active && !isExpired && (
                      <button
                        onClick={() => revokeToken(token.id)}
                        className="p-2 text-orange-600 hover:bg-orange-50 rounded transition-colors"
                        title="Revoke token"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteToken(token.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete token"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

