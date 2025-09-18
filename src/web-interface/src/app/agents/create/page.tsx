'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import useAppStore from '@/store/app-store';
import DashboardLayout from '@/components/layout/DashboardLayout';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ArrowLeft, Send, AlertCircle } from 'lucide-react';

const createAgentRunSchema = z.object({
  prompt: z.string().min(10, 'Prompt must be at least 10 characters long'),
  model: z.string().optional(),
  repoId: z.string().optional(),
});

type CreateAgentRunFormData = z.infer<typeof createAgentRunSchema>;

export default function CreateAgentRunPage() {
  const router = useRouter();
  const { createAgentRun, auth } = useAppStore();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch
  } = useForm<CreateAgentRunFormData>({
    resolver: zodResolver(createAgentRunSchema),
    defaultValues: {
      model: 'claude-3-5-sonnet-20241022',
    }
  });

  const promptValue = watch('prompt', '');

  useEffect(() => {
    if (!auth.isAuthenticated) {
      router.push('/login');
    }
  }, [auth.isAuthenticated, router]);

  const onSubmit = async (data: CreateAgentRunFormData) => {
    try {
      setError(null);
      setIsSubmitting(true);
      
      const agentRun = await createAgentRun(
        data.prompt,
        data.model || undefined,
        data.repoId ? parseInt(data.repoId, 10) : undefined
      );
      
      router.push(`/agents/${agentRun.id}`);
    } catch (err) {
      console.error('Failed to create agent run:', err);
      setError('Failed to create agent run. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBack = () => {
    router.push('/agents');
  };

  const availableModels = [
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (Latest)' },
    { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
  ];

  const examplePrompts = [
    "Fix the authentication bug in the user login flow",
    "Refactor the database connection logic to use connection pooling",
    "Add comprehensive unit tests for the API endpoints",
    "Update the documentation with the latest API changes",
    "Optimize the SQL queries in the user service",
    "Implement error handling for the payment processing module",
  ];

  if (!auth.isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <button
              onClick={handleBack}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Agent Runs
            </button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Create Agent Run</h1>
          <p className="text-gray-600 mt-1">
            Create a new AI agent task to automate your development workflow
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="bg-white shadow-sm rounded-lg p-6">
                {/* Prompt */}
                <div className="mb-6">
                  <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                    Task Description *
                  </label>
                  <textarea
                    {...register('prompt')}
                    rows={6}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Describe the task you want the AI agent to perform. Be specific about what you want to achieve."
                  />
                  <div className="mt-1 flex items-center justify-between">
                    {errors.prompt ? (
                      <p className="text-sm text-red-600">{errors.prompt.message}</p>
                    ) : (
                      <p className="text-sm text-gray-500">
                        Be specific about what you want the agent to do
                      </p>
                    )}
                    <p className="text-sm text-gray-500">
                      {promptValue.length} characters
                    </p>
                  </div>
                </div>

                {/* Model Selection */}
                <div className="mb-6">
                  <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-2">
                    AI Model
                  </label>
                  <select
                    {...register('model')}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  >
                    {availableModels.map(model => (
                      <option key={model.value} value={model.value}>
                        {model.label}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-sm text-gray-500">
                    Claude 3.5 Sonnet is recommended for most development tasks
                  </p>
                </div>

                {/* Repository ID (Optional) */}
                <div className="mb-6">
                  <label htmlFor="repoId" className="block text-sm font-medium text-gray-700 mb-2">
                    Repository ID (Optional)
                  </label>
                  <input
                    {...register('repoId')}
                    type="number"
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter repository ID if task is repo-specific"
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Leave empty if the task is not specific to a repository
                  </p>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="mb-6 rounded-md bg-red-50 p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <AlertCircle className="h-5 w-5 text-red-400" />
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">Error</h3>
                        <div className="mt-2 text-sm text-red-700">
                          <p>{error}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? (
                      <LoadingSpinner size="sm" color="secondary" className="mr-2" />
                    ) : (
                      <Send className="w-4 h-4 mr-2" />
                    )}
                    Create Agent Run
                  </button>
                </div>
              </div>
            </form>
          </div>

          {/* Sidebar with Examples and Tips */}
          <div className="space-y-6">
            {/* Example Prompts */}
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Example Prompts</h3>
              <div className="space-y-3">
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => {
                      // This would populate the form with the example prompt
                      const form = document.querySelector('textarea[name="prompt"]') as HTMLTextAreaElement;
                      if (form) {
                        form.value = prompt;
                        form.dispatchEvent(new Event('input', { bubbles: true }));
                      }
                    }}
                    className="block w-full text-left p-3 rounded-md border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors duration-150"
                  >
                    <p className="text-sm text-gray-700">{prompt}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Tips */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-blue-900 mb-4">Tips for Better Results</h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li>• Be specific about what you want to achieve</li>
                <li>• Include context about your codebase when relevant</li>
                <li>• Mention any constraints or requirements</li>
                <li>• Specify the programming language or framework</li>
                <li>• Include error messages if fixing bugs</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}