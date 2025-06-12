// ... existing imports ...

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Task {
  id: string;
  prompt: string;
  status: TaskStatus;
  result?: string;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface CodegenConfig {
  orgId: string;
  token: string;
  isConnected: boolean;
}

export interface Message {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'error';
  taskId?: string;
  status?: TaskStatus;
  createdAt: Date;
}

export interface Thread {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
}

export interface BackendTaskResponse {
  id: string;
  organization_id: string;
  status: string;
  created_at: string;
  result?: string;
  error?: string;
  web_url?: string;
}

export interface BackendTaskStatusResponse {
  id: string;
  organization_id: string;
  status: string;
  created_at: string;
  result?: string;
  error?: string;
  web_url?: string;
}
