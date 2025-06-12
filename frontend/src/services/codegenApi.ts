import { Task, TaskStatus, BackendTaskResponse, BackendTaskStatusResponse } from '../types';

class CodegenAPI {
  private orgId: string = '';
  private token: string = '';
  private baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8887/api/v1';

  configure(orgId: string, token: string) {
    this.orgId = orgId;
    this.token = token;
  }

  isConfigured(): boolean {
    return Boolean(this.orgId && this.token);
  }

  async testConnection(): Promise<boolean> {
    if (!this.isConfigured()) return false;
    
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Org-ID': this.orgId,
          'X-Token': this.token
        }
      });
      
      return response.ok;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }

  async runAgent(prompt: string, streaming: boolean = true): Promise<Task> {
    if (!this.isConfigured()) {
      throw new Error('API not configured. Please set org_id and token.');
    }

    try {
      if (streaming) {
        return this.runAgentStreaming(prompt);
      } else {
        return this.runAgentSync(prompt);
      }
    } catch (error) {
      console.error('Failed to run agent:', error);
      throw error;
    }
  }

  private async runAgentSync(prompt: string): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/run-task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Org-ID': this.orgId,
        'X-Token': this.token
      },
      body: JSON.stringify({
        prompt: prompt,
        stream: false
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API request failed with status ${response.status}`);
    }

    const data: BackendTaskResponse = await response.json();
    
    const task: Task = {
      id: data.id,
      prompt,
      status: this.mapStatus(data.status),
      result: data.result,
      error: data.error,
      createdAt: new Date(data.created_at),
      updatedAt: new Date()
    };

    this.storeTask(task);
    return task;
  }

  private async runAgentStreaming(prompt: string): Promise<Task> {
    const taskId = this.generateTaskId();
    
    const task: Task = {
      id: taskId,
      prompt,
      status: 'pending',
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.storeTask(task);

    // Start streaming request
    const response = await fetch(`${this.baseUrl}/run-task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Org-ID': this.orgId,
        'X-Token': this.token
      },
      body: JSON.stringify({
        prompt: prompt,
        stream: true
      })
    });

    if (!response.ok) {
      throw new Error(`Streaming request failed with status ${response.status}`);
    }

    // Handle streaming response
    this.handleStreamingResponse(response, taskId);
    
    return task;
  }

  private async handleStreamingResponse(response: Response, taskId: string) {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let lastUpdate = Date.now();
    const UPDATE_THROTTLE = 100; // Throttle updates to 100ms

    if (!reader) {
      throw new Error('No response body reader available');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last line in the buffer if it's incomplete
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') {
              // Final update for completed task
              const storedTask = this.getStoredTask(taskId);
              if (storedTask) {
                const finalTask: Task = {
                  ...storedTask,
                  status: 'completed',
                  updatedAt: new Date()
                };
                this.storeTask(finalTask);
                window.dispatchEvent(new CustomEvent('taskUpdate', { 
                  detail: { taskId, task: finalTask } 
                }));
              }
              return;
            }
            
            try {
              const parsed: BackendTaskResponse = JSON.parse(data);
              
              // Update stored task
              const storedTask = this.getStoredTask(taskId);
              if (storedTask) {
                const updatedTask: Task = {
                  ...storedTask,
                  status: this.mapStatus(parsed.status),
                  result: parsed.result,
                  error: parsed.error,
                  updatedAt: new Date()
                };
                
                // Store task and trigger update (with throttling)
                this.storeTask(updatedTask);
                const now = Date.now();
                if (now - lastUpdate >= UPDATE_THROTTLE) {
                  window.dispatchEvent(new CustomEvent('taskUpdate', { 
                    detail: { taskId, task: updatedTask } 
                  }));
                  lastUpdate = now;
                }
              }
            } catch (e) {
              console.error('Failed to parse streaming data:', e, data);
            }
          }
        }
      }

      // Process any remaining data in the buffer
      if (buffer.length > 0) {
        const lines = buffer.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') {
              // Final update for completed task
              const storedTask = this.getStoredTask(taskId);
              if (storedTask) {
                const finalTask: Task = {
                  ...storedTask,
                  status: 'completed',
                  updatedAt: new Date()
                };
                this.storeTask(finalTask);
                window.dispatchEvent(new CustomEvent('taskUpdate', { 
                  detail: { taskId, task: finalTask } 
                }));
              }
              return;
            }
            
            try {
              const parsed: BackendTaskResponse = JSON.parse(data);
              const storedTask = this.getStoredTask(taskId);
              if (storedTask) {
                const updatedTask: Task = {
                  ...storedTask,
                  status: this.mapStatus(parsed.status),
                  result: parsed.result,
                  error: parsed.error,
                  updatedAt: new Date()
                };
                
                this.storeTask(updatedTask);
                window.dispatchEvent(new CustomEvent('taskUpdate', { 
                  detail: { taskId, task: updatedTask } 
                }));
              }
            } catch (e) {
              console.error('Failed to parse streaming data:', e, data);
            }
          }
        }
      }

      // Ensure we have a final state
      const finalStoredTask = this.getStoredTask(taskId);
      if (finalStoredTask && finalStoredTask.status !== 'completed' && finalStoredTask.status !== 'failed') {
        // Try to get the final status from the server
        try {
          const response = await fetch(`${this.baseUrl}/task/${taskId}/status`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'X-Org-ID': this.orgId,
              'X-Token': this.token
            }
          });

          if (response.ok) {
            const data: BackendTaskStatusResponse = await response.json();
            const finalTask: Task = {
              ...finalStoredTask,
              status: this.mapStatus(data.status),
              result: data.result,
              error: data.error,
              updatedAt: new Date()
            };
            this.storeTask(finalTask);
            window.dispatchEvent(new CustomEvent('taskUpdate', { 
              detail: { taskId, task: finalTask } 
            }));
            return;
          }
        } catch (error) {
          console.error('Failed to get final task status:', error);
        }

        // If we couldn't get the status from the server, mark as completed
        const finalTask: Task = {
          ...finalStoredTask,
          status: 'completed',
          updatedAt: new Date()
        };
        this.storeTask(finalTask);
        window.dispatchEvent(new CustomEvent('taskUpdate', { 
          detail: { taskId, task: finalTask } 
        }));
      }
    } finally {
      reader.releaseLock();
    }
  }

  async getTaskStatus(taskId: string): Promise<Task | null> {
    if (!this.isConfigured()) {
      return this.getStoredTask(taskId);
    }

    try {
      const response = await fetch(`${this.baseUrl}/task/${taskId}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Org-ID': this.orgId,
          'X-Token': this.token
        }
      });

      if (!response.ok) {
        // If we get a 500 error, the task might be completed but the server is having issues
        // Use the stored task if we have it
        const storedTask = this.getStoredTask(taskId);
        if (storedTask && response.status === 500) {
          const finalTask: Task = {
            ...storedTask,
            status: 'completed',
            updatedAt: new Date()
          };
          this.storeTask(finalTask);
          return finalTask;
        }
        console.error(`Failed to get task status: ${response.status}`);
        return this.getStoredTask(taskId);
      }

      const data: BackendTaskStatusResponse = await response.json();
      
      const storedTask = this.getStoredTask(taskId);
      const task: Task = {
        id: data.id,
        prompt: storedTask?.prompt || '',
        status: this.mapStatus(data.status),
        result: data.result,
        error: data.error,
        createdAt: storedTask?.createdAt || new Date(data.created_at),
        updatedAt: new Date()
      };

      this.storeTask(task);
      return task;
    } catch (error) {
      console.error('Failed to get task status:', error);
      // If we have a stored task, return it with completed status
      const storedTask = this.getStoredTask(taskId);
      if (storedTask) {
        const finalTask: Task = {
          ...storedTask,
          status: 'completed',
          updatedAt: new Date()
        };
        this.storeTask(finalTask);
        return finalTask;
      }
      return null;
    }
  }

  private mapStatus(apiStatus: string): TaskStatus {
    switch (apiStatus.toLowerCase()) {
      case 'pending':
      case 'queued':
        return 'pending';
      case 'running':
      case 'active':
      case 'in_progress':
      case 'executing':
        return 'running';
      case 'completed':
      case 'complete':
      case 'success':
      case 'done':
        return 'completed';
      case 'failed':
      case 'error':
      case 'cancelled':
        return 'failed';
      default:
        return 'pending';
    }
  }

  private generateTaskId(): string {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getStoredTask(taskId: string): Task | null {
    try {
      const storedTasks = JSON.parse(localStorage.getItem('codegen_tasks') || '{}');
      const stored = storedTasks[taskId];
      if (stored) {
        return {
          ...stored,
          createdAt: new Date(stored.createdAt),
          updatedAt: new Date(stored.updatedAt)
        };
      }
      return null;
    } catch (error) {
      console.error('Failed to get stored task:', error);
      return null;
    }
  }

  storeTask(task: Task) {
    try {
      const storedTasks = JSON.parse(localStorage.getItem('codegen_tasks') || '{}');
      storedTasks[task.id] = {
        ...task,
        createdAt: task.createdAt.toISOString(),
        updatedAt: task.updatedAt.toISOString()
      };
      localStorage.setItem('codegen_tasks', JSON.stringify(storedTasks));
    } catch (error) {
      console.error('Failed to store task:', error);
    }
  }

  cleanup() {
    // No polling intervals to clean up since we use streaming
  }
}

export const codegenAPI = new CodegenAPI();
