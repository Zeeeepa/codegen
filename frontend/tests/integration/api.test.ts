import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createAgentRun, getAgentRunStatus, resumeAgentRun } from '../../src/services/api';
import axios from 'axios';

vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('createAgentRun', () => {
    it('should create agent run with correct API call', async () => {
      const mockResponse = {
        data: {
          id: 'run-123',
          organization_id: 'org-456',
          status: 'pending',
          created_at: '2024-01-01T00:00:00Z',
          web_url: 'https://codegen.com/runs/123',
        },
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const result = await createAgentRun(
        'org-456',
        'api-key-789',
        'Test prompt'
      );

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'https://api.codegen.com/v1/organizations/org-456/agent/run',
        { prompt: 'Test prompt' },
        {
          headers: {
            Authorization: 'Bearer api-key-789',
            'Content-Type': 'application/json',
          },
        }
      );

      expect(result).toEqual(mockResponse.data);
    });

    it('should handle API errors gracefully', async () => {
      mockedAxios.post.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        createAgentRun('org-456', 'api-key-789', 'Test prompt')
      ).rejects.toThrow('Network error');
    });

    it('should handle 401 unauthorized errors', async () => {
      const error = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' },
        },
      };

      mockedAxios.post.mockRejectedValueOnce(error);

      await expect(
        createAgentRun('org-456', 'invalid-key', 'Test prompt')
      ).rejects.toThrow();
    });
  });

  describe('getAgentRunStatus', () => {
    it('should fetch agent run status correctly', async () => {
      const mockResponse = {
        data: {
          id: 'run-123',
          status: 'completed',
          result: 'Task completed successfully',
          summary: 'Implementation complete',
          github_pull_requests: [
            {
              number: 42,
              url: 'https://github.com/org/repo/pull/42',
              title: 'feat: Add new feature',
            },
          ],
        },
      };

      mockedAxios.get.mockResolvedValueOnce(mockResponse);

      const result = await getAgentRunStatus(
        'org-456',
        'api-key-789',
        'run-123'
      );

      expect(mockedAxios.get).toHaveBeenCalledWith(
        'https://api.codegen.com/v1/organizations/org-456/agent/run/run-123',
        {
          headers: {
            Authorization: 'Bearer api-key-789',
          },
        }
      );

      expect(result.status).toBe('completed');
      expect(result.github_pull_requests).toHaveLength(1);
    });

    it('should handle run not found errors', async () => {
      const error = {
        response: {
          status: 404,
          data: { error: 'Run not found' },
        },
      };

      mockedAxios.get.mockRejectedValueOnce(error);

      await expect(
        getAgentRunStatus('org-456', 'api-key-789', 'invalid-run-id')
      ).rejects.toThrow();
    });
  });

  describe('resumeAgentRun', () => {
    it('should resume agent run with additional instructions', async () => {
      const mockResponse = {
        data: {
          id: 'run-123',
          status: 'running',
          updated_at: '2024-01-01T00:05:00Z',
        },
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const result = await resumeAgentRun(
        'org-456',
        'api-key-789',
        'run-123',
        'Continue with implementation'
      );

      expect(mockedAxios.post).toHaveBeenCalledWith(
        'https://api.codegen.com/v1/organizations/org-456/agent/run/resume',
        {
          run_id: 'run-123',
          prompt: 'Continue with implementation',
        },
        {
          headers: {
            Authorization: 'Bearer api-key-789',
            'Content-Type': 'application/json',
          },
        }
      );

      expect(result.status).toBe('running');
    });
  });

  describe('API Response Validation', () => {
    it('should validate agent run response structure', async () => {
      const mockResponse = {
        data: {
          id: 'run-123',
          organization_id: 'org-456',
          status: 'pending',
          created_at: '2024-01-01T00:00:00Z',
          web_url: 'https://codegen.com/runs/123',
          result: null,
          summary: null,
          source_type: 'api',
          github_pull_requests: [],
          metadata: {},
        },
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse);

      const result = await createAgentRun(
        'org-456',
        'api-key-789',
        'Test prompt'
      );

      // Verify all required fields are present
      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('organization_id');
      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('created_at');
      expect(result).toHaveProperty('web_url');
      expect(result).toHaveProperty('github_pull_requests');
    });
  });

  describe('API Error Handling', () => {
    it('should handle rate limiting errors', async () => {
      const error = {
        response: {
          status: 429,
          data: { error: 'Rate limit exceeded' },
        },
      };

      mockedAxios.post.mockRejectedValueOnce(error);

      await expect(
        createAgentRun('org-456', 'api-key-789', 'Test prompt')
      ).rejects.toThrow();
    });

    it('should handle server errors', async () => {
      const error = {
        response: {
          status: 500,
          data: { error: 'Internal server error' },
        },
      };

      mockedAxios.post.mockRejectedValueOnce(error);

      await expect(
        createAgentRun('org-456', 'api-key-789', 'Test prompt')
      ).rejects.toThrow();
    });
  });
});

