/**
 * Jest Test Setup
 *
 * Global test configuration and utilities for the CI/CD lifecycle system tests
 */
declare global {
    namespace jest {
        interface Matchers<R> {
            toBeWithinRange(floor: number, ceiling: number): R;
        }
    }
}
declare class MockWebSocket {
    url: string;
    static CONNECTING: number;
    static OPEN: number;
    static CLOSING: number;
    static CLOSED: number;
    readyState: number;
    onopen: ((event: Event) => void) | null;
    onclose: ((event: CloseEvent) => void) | null;
    onmessage: ((event: MessageEvent) => void) | null;
    onerror: ((event: Event) => void) | null;
    constructor(url: string);
    send(data: string): void;
    close(): void;
}
declare const localStorageMock: {
    getItem: jest.Mock<any, any, any>;
    setItem: jest.Mock<any, any, any>;
    removeItem: jest.Mock<any, any, any>;
    clear: jest.Mock<any, any, any>;
};
declare const sessionStorageMock: {
    getItem: jest.Mock<any, any, any>;
    setItem: jest.Mock<any, any, any>;
    removeItem: jest.Mock<any, any, any>;
    clear: jest.Mock<any, any, any>;
};
declare const indexedDBMock: {
    open: jest.Mock<any, any, any>;
    deleteDatabase: jest.Mock<any, any, any>;
};
export declare const createMockProject: (overrides?: {}) => {
    id: string;
    timestamp: number;
    version: number;
    projectId: string;
    name: string;
    status: string;
    repository: {
        url: string;
        branch: string;
        commit: string;
        lastUpdate: number;
        provider: string;
        private: boolean;
    };
    codebaseState: {
        languages: never[];
        files: number;
        linesOfCode: number;
        complexity: {
            cyclomatic: number;
            cognitive: number;
            maintainability: number;
            technical_debt: number;
        };
        coverage: {
            lines: number;
            functions: number;
            branches: number;
            statements: number;
        };
        quality: {
            bugs: number;
            vulnerabilities: number;
            code_smells: number;
            duplications: number;
            rating: string;
        };
        lastAnalysis: number;
    };
    dependencies: {
        nodes: never[];
        edges: never[];
        cycles: never[];
        outdated: never[];
    };
    healthMetrics: {
        score: number;
        trends: never[];
        alerts: never[];
        recommendations: never[];
    };
    activeAgents: never[];
    pipelines: never[];
    errors: never[];
};
export declare const createMockAgent: (overrides?: {}) => {
    id: string;
    timestamp: number;
    version: number;
    agentId: string;
    runId: string;
    projectId: string;
    status: string;
    type: string;
    configuration: {
        prompt: string;
        tools: never[];
        integrations: never[];
        environment: {};
        timeout: number;
        retries: number;
    };
    execution: {
        startTime: number;
        progress: number;
        currentStep: string;
        steps: never[];
        resources: {
            cpu: number;
            memory: number;
            disk: number;
            network: number;
        };
    };
    traces: never[];
    performance: {
        executionTime: number;
        toolUsage: never[];
        successRate: number;
        errorRate: number;
        efficiency: number;
    };
    context: {
        projectContext: string;
        codebaseContext: string;
        conversationHistory: never[];
        knowledgeBase: never[];
        preferences: {};
    };
};
export declare const createMockPipeline: (overrides?: {}) => {
    id: string;
    timestamp: number;
    version: number;
    pipelineId: string;
    projectId: string;
    name: string;
    status: string;
    stages: never[];
    configuration: {
        triggers: never[];
        variables: {};
        notifications: never[];
        approvals: never[];
    };
    execution: {
        runId: string;
        trigger: {
            type: string;
            conditions: {};
        };
        startTime: number;
        progress: number;
        currentStage: string;
        artifacts: never[];
        logs: never[];
    };
    metrics: {
        totalRuns: number;
        successRate: number;
        averageDuration: number;
        failureReasons: never[];
        trends: never[];
    };
    dependencies: never[];
};
export declare const waitFor: (ms: number) => Promise<void>;
export declare const flushPromises: () => Promise<void>;
export declare const mockAsyncFunction: <T>(returnValue: T, delay?: number) => jest.MockedFunction<() => Promise<T>>;
export declare const cleanupMocks: () => void;
export { MockWebSocket, localStorageMock, sessionStorageMock, indexedDBMock, };
//# sourceMappingURL=setup.d.ts.map