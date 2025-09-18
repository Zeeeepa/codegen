/**
 * Jest Test Setup
 * 
 * Global test configuration and utilities for the CI/CD lifecycle system tests
 */

// Mock console methods to reduce noise in tests
const originalConsole = { ...console };

beforeAll(() => {
  // Mock console methods but keep error and warn for debugging
  console.log = jest.fn();
  console.info = jest.fn();
  console.debug = jest.fn();
  // Keep console.error and console.warn for debugging
});

afterAll(() => {
  // Restore console methods
  Object.assign(console, originalConsole);
});

// Global test timeout
jest.setTimeout(30000);

// Mock timers for consistent testing
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
  jest.clearAllMocks();
});

// Global test utilities
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeWithinRange(floor: number, ceiling: number): R;
    }
  }
}

// Custom matchers
expect.extend({
  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
});

// Mock WebSocket for testing
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    // Echo back for testing
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data }));
      }
    }, 0);
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock IndexedDB
const indexedDBMock = {
  open: jest.fn(),
  deleteDatabase: jest.fn(),
};

// Apply mocks to global
Object.defineProperty(global, 'WebSocket', {
  value: MockWebSocket,
  writable: true,
});

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

Object.defineProperty(global, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
});

Object.defineProperty(global, 'indexedDB', {
  value: indexedDBMock,
  writable: true,
});

// Mock performance API
Object.defineProperty(global, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByName: jest.fn(() => []),
    getEntriesByType: jest.fn(() => []),
  },
  writable: true,
});

// Test data factories
export const createMockProject = (overrides = {}) => ({
  id: 'project_123',
  timestamp: Date.now(),
  version: 1,
  projectId: 'project_123',
  name: 'Test Project',
  status: 'active',
  repository: {
    url: 'https://github.com/test/repo',
    branch: 'main',
    commit: 'abc123',
    lastUpdate: Date.now(),
    provider: 'github',
    private: false,
  },
  codebaseState: {
    languages: [],
    files: 0,
    linesOfCode: 0,
    complexity: { cyclomatic: 0, cognitive: 0, maintainability: 0, technical_debt: 0 },
    coverage: { lines: 0, functions: 0, branches: 0, statements: 0 },
    quality: { bugs: 0, vulnerabilities: 0, code_smells: 0, duplications: 0, rating: 'A' },
    lastAnalysis: Date.now(),
  },
  dependencies: {
    nodes: [],
    edges: [],
    cycles: [],
    outdated: [],
  },
  healthMetrics: {
    score: 100,
    trends: [],
    alerts: [],
    recommendations: [],
  },
  activeAgents: [],
  pipelines: [],
  errors: [],
  ...overrides,
});

export const createMockAgent = (overrides = {}) => ({
  id: 'agent_123',
  timestamp: Date.now(),
  version: 1,
  agentId: 'agent_123',
  runId: 'run_123',
  projectId: 'project_123',
  status: 'created',
  type: 'CODEGEN_CLAUDE',
  configuration: {
    prompt: 'Test prompt',
    tools: [],
    integrations: [],
    environment: {},
    timeout: 300,
    retries: 3,
  },
  execution: {
    startTime: Date.now(),
    progress: 0,
    currentStep: 'initializing',
    steps: [],
    resources: { cpu: 0, memory: 0, disk: 0, network: 0 },
  },
  traces: [],
  performance: {
    executionTime: 0,
    toolUsage: [],
    successRate: 0,
    errorRate: 0,
    efficiency: 0,
  },
  context: {
    projectContext: '',
    codebaseContext: '',
    conversationHistory: [],
    knowledgeBase: [],
    preferences: {},
  },
  ...overrides,
});

export const createMockPipeline = (overrides = {}) => ({
  id: 'pipeline_123',
  timestamp: Date.now(),
  version: 1,
  pipelineId: 'pipeline_123',
  projectId: 'project_123',
  name: 'Test Pipeline',
  status: 'draft',
  stages: [],
  configuration: {
    triggers: [],
    variables: {},
    notifications: [],
    approvals: [],
  },
  execution: {
    runId: 'run_123',
    trigger: { type: 'manual', conditions: {} },
    startTime: Date.now(),
    progress: 0,
    currentStage: '',
    artifacts: [],
    logs: [],
  },
  metrics: {
    totalRuns: 0,
    successRate: 0,
    averageDuration: 0,
    failureReasons: [],
    trends: [],
  },
  dependencies: [],
  ...overrides,
});

// Test utilities
export const waitFor = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export const flushPromises = (): Promise<void> => {
  return new Promise(resolve => setImmediate(resolve));
};

export const mockAsyncFunction = <T>(returnValue: T, delay = 0): jest.MockedFunction<() => Promise<T>> => {
  return jest.fn().mockImplementation(() => 
    new Promise(resolve => setTimeout(() => resolve(returnValue), delay))
  );
};

// Cleanup helpers
export const cleanupMocks = (): void => {
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
  
  sessionStorageMock.getItem.mockClear();
  sessionStorageMock.setItem.mockClear();
  sessionStorageMock.removeItem.mockClear();
  sessionStorageMock.clear.mockClear();
  
  indexedDBMock.open.mockClear();
  indexedDBMock.deleteDatabase.mockClear();
};

// Export mocks for use in tests
export {
  MockWebSocket,
  localStorageMock,
  sessionStorageMock,
  indexedDBMock,
};

