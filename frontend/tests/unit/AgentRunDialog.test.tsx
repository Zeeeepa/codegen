/**
 * Unit Tests for AgentRunDialog Component
 * Tests validation, filtering, error handling, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AgentRunDialog from '../../src/components/AgentRunDialog';
import * as codegenApi from '../../src/services/codegenApi';

// Mock the codegenApi module
vi.mock('../../src/services/codegenApi', () => ({
  listRepositories: vi.fn(),
  createAgentRun: vi.fn(),
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('AgentRunDialog', () => {
  const mockRepositories = [
    {
      id: 1,
      name: 'test-repo-1',
      full_name: 'org/test-repo-1',
      archived: false,
      organization_id: 123,
    },
    {
      id: 2,
      name: 'test-repo-2',
      full_name: 'org/test-repo-2',
      archived: false,
      organization_id: 123,
    },
    {
      id: 3,
      name: 'archived-repo',
      full_name: 'org/archived-repo',
      archived: true,
      organization_id: 123,
    },
  ];

  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementation
    (codegenApi.listRepositories as any).mockResolvedValue({
      items: mockRepositories,
      total: mockRepositories.length,
      page: 1,
      size: 50,
      pages: 1,
    });

    (codegenApi.createAgentRun as any).mockResolvedValue({
      agentRunId: 'test-run-id-123',
      status: 'ACTIVE',
      createdAt: Date.now(),
    });
  });

  describe('Rendering', () => {
    it('should not render when closed', () => {
      render(
        <AgentRunDialog
          isOpen={false}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      expect(screen.queryByText('Create Agent Run')).not.toBeInTheDocument();
    });

    it('should render when open', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Create Agent Run')).toBeInTheDocument();
      });
    });

    it('should display character counter', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/0 \/ 5000 characters/)).toBeInTheDocument();
      });
    });
  });

  describe('Validation', () => {
    it('should show error for empty task', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Create Agent Run')).toBeInTheDocument();
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1]; // Get the button, not the header
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Task description is required')).toBeInTheDocument();
      });
    });

    it('should show error for task too short', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, { target: { value: 'short' } });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Task description is too short \(minimum 10 characters\)/)
        ).toBeInTheDocument();
      });
    });

    it('should show error for task too long', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      const longText = 'a'.repeat(5001);
      fireEvent.change(textarea, { target: { value: longText } });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Task description is too long \(maximum 5000 characters\)/)
        ).toBeInTheDocument();
      });
    });

    it('should show error for task without letters', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, { target: { value: '12345678901' } });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Task description must contain at least one letter/)
        ).toBeInTheDocument();
      });
    });

    it('should update character count as user types', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, { target: { value: 'Test task description' } });

      await waitFor(() => {
        expect(screen.getByText(/21 \/ 5000 characters/)).toBeInTheDocument();
      });
    });

    it('should clear validation error when user starts typing', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Create Agent Run')).toBeInTheDocument();
      });

      // Trigger validation error
      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Task description is required')).toBeInTheDocument();
      });

      // Start typing
      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, { target: { value: 'Valid task description' } });

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText('Task description is required')).not.toBeInTheDocument();
      });
    });
  });

  describe('Agent Run Creation', () => {
    it('should create agent run with valid task', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Add error handling to authentication module' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(codegenApi.createAgentRun).toHaveBeenCalledWith(
          undefined,
          undefined,
          expect.objectContaining({
            task: 'Add error handling to authentication module',
            model: 'Sonnet 4.5',
          })
        );
      });

      expect(mockOnSuccess).toHaveBeenCalledWith('test-run-id-123');
    });

    it('should create agent run with repository selection', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(codegenApi.listRepositories).toHaveBeenCalled();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Add error handling to authentication module' },
      });

      const repoSelect = screen.getByLabelText(/Repository/);
      fireEvent.change(repoSelect, { target: { value: '1' } });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(codegenApi.createAgentRun).toHaveBeenCalledWith(
          undefined,
          undefined,
          expect.objectContaining({
            task: 'Add error handling to authentication module',
            repo_id: 1,
            model: 'Sonnet 4.5',
          })
        );
      });
    });

    it('should create agent run without repository', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Create comprehensive README file' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(codegenApi.createAgentRun).toHaveBeenCalledWith(
          undefined,
          undefined,
          expect.objectContaining({
            task: 'Create comprehensive README file',
            repo_id: undefined,
            model: 'Sonnet 4.5',
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      (codegenApi.createAgentRun as any).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Valid task description for testing' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });

      expect(mockOnSuccess).not.toHaveBeenCalled();
    });

    it('should show specific error for 403 Forbidden', async () => {
      (codegenApi.createAgentRun as any).mockRejectedValue({
        response: { status: 403 },
        message: 'Forbidden',
      });

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Valid task description for testing' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/You don't have access to this repository/)
        ).toBeInTheDocument();
      });
    });

    it('should show specific error for 404 Not Found', async () => {
      (codegenApi.createAgentRun as any).mockRejectedValue({
        response: { status: 404 },
        message: 'Not Found',
      });

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Valid task description for testing' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Repository not found/)
        ).toBeInTheDocument();
      });
    });

    it('should show specific error for 429 Rate Limit', async () => {
      (codegenApi.createAgentRun as any).mockRejectedValue({
        response: { status: 429 },
        message: 'Too Many Requests',
      });

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Valid task description for testing' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Rate limit exceeded/)
        ).toBeInTheDocument();
      });
    });

    it('should handle repository loading error', async () => {
      (codegenApi.listRepositories as any).mockRejectedValue(
        new Error('Failed to load repositories')
      );

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load repositories/)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading state when creating agent run', async () => {
      // Make the API call take longer
      (codegenApi.createAgentRun as any).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  agentRunId: 'test-run-id',
                  status: 'ACTIVE',
                  createdAt: Date.now(),
                }),
              100
            )
          )
      );

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        const textarea = screen.getByPlaceholderText(/Describe what you want/);
        expect(textarea).toBeInTheDocument();
      });

      const textarea = screen.getByPlaceholderText(/Describe what you want/);
      fireEvent.change(textarea, {
        target: { value: 'Valid task description for testing' },
      });

      const submitButton = screen.getAllByText('Create Agent Run')[1];
      fireEvent.click(submitButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText('Creating...')).toBeInTheDocument();
      });
    });

    it('should show loading state when fetching repositories', () => {
      (codegenApi.listRepositories as any).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  items: mockRepositories,
                  total: mockRepositories.length,
                  page: 1,
                  size: 50,
                  pages: 1,
                }),
              100
            )
          )
      );

      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      expect(screen.getByText(/Loading repositories/)).toBeInTheDocument();
    });
  });

  describe('Dialog Interaction', () => {
    it('should close dialog when cancel button is clicked', async () => {
      render(
        <AgentRunDialog
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument();
      });

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});

