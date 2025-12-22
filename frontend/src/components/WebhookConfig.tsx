/**
 * WebhookConfig Component
 * Manages webhook endpoints for real-time workflow notifications
 */

import { useState, useEffect } from 'react';
import {
  Webhook as WebhookIcon,
  Plus,
  Trash2,
  Check,
  X,
  AlertCircle,
  Link as LinkIcon,
  Settings,
  Play,
  Pause,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { databaseApi } from '@/services/databaseApi';
import type { Webhook, WebhookEvent, CreateWebhookRequest } from '@/types/database';

// ============================================================================
// Constants
// ============================================================================

const AVAILABLE_EVENTS: { value: WebhookEvent; label: string; description: string }[] = [
  { value: 'workflow:created', label: 'Workflow Created', description: 'Triggered when a new workflow is created' },
  { value: 'workflow:updated', label: 'Workflow Updated', description: 'Triggered when a workflow is modified' },
  { value: 'workflow:deleted', label: 'Workflow Deleted', description: 'Triggered when a workflow is removed' },
  { value: 'execution:started', label: 'Execution Started', description: 'Triggered when an execution begins' },
  { value: 'execution:completed', label: 'Execution Completed', description: 'Triggered when an execution succeeds' },
  { value: 'execution:failed', label: 'Execution Failed', description: 'Triggered when an execution fails' },
  { value: 'execution:updated', label: 'Execution Updated', description: 'Triggered when execution status changes' },
];

// ============================================================================
// Types
// ============================================================================

interface WebhookFormData {
  url: string;
  events: WebhookEvent[];
  headers: Record<string, string>;
  workflow_id?: string;
}

// ============================================================================
// Component
// ============================================================================

export default function WebhookConfig() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [testingWebhook, setTestingWebhook] = useState<string | null>(null);
  const [formData, setFormData] = useState<WebhookFormData>({
    url: '',
    events: [],
    headers: {},
  });
  const [newHeaderKey, setNewHeaderKey] = useState('');
  const [newHeaderValue, setNewHeaderValue] = useState('');

  // Load webhooks on mount
  useEffect(() => {
    loadWebhooks();
  }, []);

  // ============================================================================
  // API Operations
  // ============================================================================

  async function loadWebhooks() {
    try {
      setLoading(true);
      const response = await databaseApi.webhooks.list({
        page: 1,
        limit: 100,
        sort_by: 'created_at',
        sort_order: 'desc',
      });
      setWebhooks(response.data);
    } catch (error: any) {
      console.error('Failed to load webhooks:', error);
      toast.error(error.message || 'Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  }

  async function createWebhook() {
    if (!formData.url || formData.events.length === 0) {
      toast.error('Please provide a URL and at least one event');
      return;
    }

    // Validate URL
    try {
      new URL(formData.url);
    } catch {
      toast.error('Please provide a valid URL');
      return;
    }

    try {
      const request: CreateWebhookRequest = {
        url: formData.url,
        events: formData.events,
        headers: Object.keys(formData.headers).length > 0 ? formData.headers : undefined,
        workflow_id: formData.workflow_id || undefined,
        is_active: true,
      };

      await databaseApi.webhooks.create(request);
      await loadWebhooks();
      
      // Reset form
      setFormData({
        url: '',
        events: [],
        headers: {},
      });
      setShowCreateForm(false);
      
      toast.success('Webhook created successfully');
    } catch (error: any) {
      console.error('Failed to create webhook:', error);
      toast.error(error.message || 'Failed to create webhook');
    }
  }

  async function toggleWebhook(id: string, currentStatus: boolean) {
    try {
      await databaseApi.webhooks.update(id, {
        is_active: !currentStatus,
      });
      await loadWebhooks();
      toast.success(`Webhook ${currentStatus ? 'disabled' : 'enabled'}`);
    } catch (error: any) {
      console.error('Failed to toggle webhook:', error);
      toast.error(error.message || 'Failed to toggle webhook');
    }
  }

  async function testWebhook(id: string) {
    setTestingWebhook(id);
    try {
      const result = await databaseApi.webhooks.test(id);
      if (result.success) {
        toast.success('Webhook test successful!');
      } else {
        toast.error(`Webhook test failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      console.error('Failed to test webhook:', error);
      toast.error(error.message || 'Failed to test webhook');
    } finally {
      setTestingWebhook(null);
    }
  }

  async function deleteWebhook(id: string) {
    if (!confirm('Are you sure you want to delete this webhook?')) {
      return;
    }

    try {
      await databaseApi.webhooks.delete(id);
      await loadWebhooks();
      toast.success('Webhook deleted successfully');
    } catch (error: any) {
      console.error('Failed to delete webhook:', error);
      toast.error(error.message || 'Failed to delete webhook');
    }
  }

  // ============================================================================
  // UI Helpers
  // ============================================================================

  function toggleEventSelection(event: WebhookEvent) {
    setFormData(prev => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter(e => e !== event)
        : [...prev.events, event],
    }));
  }

  function addHeader() {
    if (!newHeaderKey || !newHeaderValue) {
      toast.error('Please provide both header name and value');
      return;
    }

    setFormData(prev => ({
      ...prev,
      headers: {
        ...prev.headers,
        [newHeaderKey]: newHeaderValue,
      },
    }));

    setNewHeaderKey('');
    setNewHeaderValue('');
  }

  function removeHeader(key: string) {
    setFormData(prev => {
      const { [key]: removed, ...rest } = prev.headers;
      return { ...prev, headers: rest };
    });
  }

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Webhooks</h2>
          <p className="text-sm text-gray-600">
            Configure webhooks for real-time workflow notifications
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Webhook
        </button>
      </div>

      {/* Create Webhook Form */}
      {showCreateForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Create New Webhook</h3>
          
          <div className="space-y-4">
            {/* Webhook URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Webhook URL
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://your-server.com/webhook"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                The endpoint that will receive webhook events
              </p>
            </div>

            {/* Events */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Events to Subscribe
              </label>
              <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3">
                {AVAILABLE_EVENTS.map((event) => (
                  <label
                    key={event.value}
                    className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={formData.events.includes(event.value)}
                      onChange={() => toggleEventSelection(event.value)}
                      className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm text-gray-900">{event.label}</div>
                      <div className="text-xs text-gray-600">{event.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Custom Headers */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Headers (Optional)
              </label>
              
              {/* Existing Headers */}
              {Object.entries(formData.headers).length > 0 && (
                <div className="space-y-1 mb-2">
                  {Object.entries(formData.headers).map(([key, value]) => (
                    <div
                      key={key}
                      className="flex items-center gap-2 bg-gray-50 rounded px-3 py-2"
                    >
                      <code className="flex-1 text-sm font-mono text-gray-700">
                        {key}: {value}
                      </code>
                      <button
                        onClick={() => removeHeader(key)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add New Header */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newHeaderKey}
                  onChange={(e) => setNewHeaderKey(e.target.value)}
                  placeholder="Header name (e.g., Authorization)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
                <input
                  type="text"
                  value={newHeaderValue}
                  onChange={(e) => setNewHeaderValue(e.target.value)}
                  placeholder="Header value"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
                <button
                  onClick={addHeader}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Add
                </button>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={createWebhook}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Webhook
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setFormData({ url: '', events: [], headers: {} });
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Webhooks List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center py-8 text-gray-500">
            Loading webhooks...
          </div>
        ) : webhooks.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
            <WebhookIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No webhooks configured</p>
            <p className="text-sm text-gray-500 mt-1">
              Create your first webhook to receive real-time notifications
            </p>
          </div>
        ) : (
          webhooks.map((webhook) => (
            <div
              key={webhook.id}
              className={`bg-white border rounded-lg p-4 ${
                webhook.is_active ? 'border-gray-200' : 'border-gray-300 bg-gray-50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* URL */}
                  <div className="flex items-center gap-2 mb-2">
                    <LinkIcon className="w-4 h-4 text-gray-500" />
                    <code className="text-sm font-mono text-gray-900 break-all">
                      {webhook.url}
                    </code>
                    {!webhook.is_active && (
                      <span className="px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
                        Disabled
                      </span>
                    )}
                  </div>

                  {/* Events */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {webhook.events.map((event) => (
                      <span
                        key={event}
                        className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                      >
                        {event}
                      </span>
                    ))}
                  </div>

                  {/* Headers */}
                  {webhook.headers && Object.keys(webhook.headers).length > 0 && (
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Settings className="w-3 h-3" />
                      {Object.keys(webhook.headers).length} custom header(s)
                    </div>
                  )}

                  {/* Metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                    <span>Created {new Date(webhook.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-1">
                  <button
                    onClick={() => testWebhook(webhook.id)}
                    disabled={!webhook.is_active || testingWebhook === webhook.id}
                    className="p-2 text-green-600 hover:bg-green-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Test webhook"
                  >
                    {testingWebhook === webhook.id ? (
                      <div className="w-4 h-4 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Check className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => toggleWebhook(webhook.id, webhook.is_active)}
                    className={`p-2 rounded transition-colors ${
                      webhook.is_active
                        ? 'text-orange-600 hover:bg-orange-50'
                        : 'text-green-600 hover:bg-green-50'
                    }`}
                    title={webhook.is_active ? 'Disable webhook' : 'Enable webhook'}
                  >
                    {webhook.is_active ? (
                      <Pause className="w-4 h-4" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => deleteWebhook(webhook.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete webhook"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-blue-900 mb-1">Webhook Payload Format</h4>
            <p className="text-sm text-blue-700 mb-2">
              Webhooks will receive a POST request with the following JSON payload:
            </p>
            <pre className="text-xs bg-white border border-blue-300 rounded p-2 overflow-x-auto">
{`{
  "event": "execution:completed",
  "timestamp": "2024-12-14T19:30:00Z",
  "data": {
    "id": "uuid",
    "workflow_id": "uuid",
    "status": "completed",
    "results": {...}
  }
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

