import axios from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:3001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      throw new Error(data.error || `API Error ${status}`);
    } else if (error.request) {
      throw new Error('Network error: Unable to reach API server');
    } else {
      throw new Error(`Request error: ${error.message}`);
    }
  }
);

// Agent Runs API
export const getAgentRuns = async (params = {}) => {
  return api.get('/api/agent-runs', { params });
};

export const getAgentRun = async (runId) => {
  return api.get(`/api/agent-runs/${runId}`);
};

export const createAgentRun = async (data) => {
  return api.post('/api/agent-runs', data);
};

export const resumeAgentRun = async (runId, data) => {
  return api.post(`/api/agent-runs/${runId}/resume`, data);
};

// Setup Commands API
export const generateSetupCommands = async (data) => {
  return api.post('/api/setup-commands/generate', data);
};

// Health check
export const getHealth = async () => {
  return api.get('/api/health');
};

export default api;

