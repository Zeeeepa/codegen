const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

class CodegenAPIClient {
  constructor() {
    this.baseURL = 'https://api.codegen.com/v1';
    this.token = process.env.CODEGEN_TOKEN;
    this.orgId = process.env.ORG_ID;

    if (!this.token) {
      throw new Error('CODEGEN_TOKEN environment variable is required');
    }

    if (!this.orgId) {
      throw new Error('ORG_ID environment variable is required');
    }

    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        'X-Organization-ID': this.orgId
      },
      timeout: 30000 // 30 seconds
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const { status, data } = error.response;
          throw new Error(`API Error ${status}: ${data.message || data.error || 'Unknown error'}`);
        } else if (error.request) {
          throw new Error('Network error: Unable to reach Codegen API');
        } else {
          throw new Error(`Request error: ${error.message}`);
        }
      }
    );
  }

  async makeRequest(method, endpoint, data = null, params = {}) {
    try {
      const config = {
        method,
        url: endpoint,
        params,
        headers: {
          'X-Request-ID': uuidv4()
        }
      };

      if (data && (method === 'post' || method === 'put' || method === 'patch')) {
        config.data = data;
      }

      const response = await this.client.request(config);
      return response.data;
    } catch (error) {
      console.error(`API ${method.toUpperCase()} ${endpoint} failed:`, error.message);
      throw error;
    }
  }

  // Helper methods for common HTTP operations
  async get(endpoint, params = {}) {
    return this.makeRequest('get', endpoint, null, params);
  }

  async post(endpoint, data = {}) {
    return this.makeRequest('post', endpoint, data);
  }

  async put(endpoint, data = {}) {
    return this.makeRequest('put', endpoint, data);
  }

  async delete(endpoint) {
    return this.makeRequest('delete', endpoint);
  }
}

module.exports = new CodegenAPIClient();

