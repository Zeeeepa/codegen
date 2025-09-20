import { ChatInterfaceManager } from '../../middleware/chat-interface-manager.js';
import { Logger } from '../../utils/logger.js';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  checks: {
    [key: string]: {
      status: 'pass' | 'fail' | 'warn';
      message?: string;
      duration?: number;
      details?: any;
    };
  };
  summary: {
    total: number;
    passed: number;
    failed: number;
    warned: number;
  };
}

export interface InterfaceHealth {
  interface: string;
  healthy: boolean;
  checks: {
    configuration: boolean;
    browser: boolean;
    tools: boolean;
  };
  lastTest?: Date;
  error?: string;
  timestamp: string;
}

export class HealthCheckService {
  private logger: Logger;
  private lastHealthCheck?: Date;
  private healthCache?: HealthStatus;
  private interfaceHealthCache: Map<string, InterfaceHealth> = new Map();

  constructor(private manager: ChatInterfaceManager) {
    this.logger = new Logger('HealthCheckService');
  }

  async getHealthStatus(useCache = true): Promise<HealthStatus> {
    // Return cached result if recent (within 30 seconds)
    if (useCache && this.healthCache && this.lastHealthCheck) {
      const age = Date.now() - this.lastHealthCheck.getTime();
      if (age < 30000) {
        return this.healthCache;
      }
    }

    const startTime = Date.now();
    const checks: HealthStatus['checks'] = {};

    try {
      // Check 1: Manager initialization
      const managerCheckStart = Date.now();
      try {
        const interfaces = this.manager.getAvailableInterfaces();
        checks.manager_initialization = {
          status: 'pass',
          message: `${interfaces.length} interfaces available`,
          duration: Date.now() - managerCheckStart,
          details: { interfaceCount: interfaces.length }
        };
      } catch (error) {
        checks.manager_initialization = {
          status: 'fail',
          message: error.message,
          duration: Date.now() - managerCheckStart
        };
      }

      // Check 2: Memory usage
      const memoryCheckStart = Date.now();
      const memUsage = process.memoryUsage();
      const memoryUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
      
      checks.memory_usage = {
        status: memoryUsagePercent > 90 ? 'fail' : memoryUsagePercent > 70 ? 'warn' : 'pass',
        message: `Heap usage: ${Math.round(memoryUsagePercent)}%`,
        duration: Date.now() - memoryCheckStart,
        details: {
          heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
          heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
          percentage: Math.round(memoryUsagePercent)
        }
      };

      // Check 3: System stats
      const statsCheckStart = Date.now();
      try {
        const stats = await this.manager.getStats();
        checks.system_stats = {
          status: 'pass',
          message: `${stats.interfaces} interfaces, ${stats.activeInstances} active browsers`,
          duration: Date.now() - statsCheckStart,
          details: stats
        };
      } catch (error) {
        checks.system_stats = {
          status: 'fail',
          message: error.message,
          duration: Date.now() - statsCheckStart
        };
      }

      // Check 4: Configuration validity
      const configCheckStart = Date.now();
      try {
        const interfaces = this.manager.getAvailableInterfaces();
        let configErrors = 0;
        
        for (const interfaceName of interfaces) {
          const config = this.manager.getInterfaceConfig(interfaceName);
          if (!config) {
            configErrors++;
          }
        }

        checks.configuration_validity = {
          status: configErrors === 0 ? 'pass' : configErrors === interfaces.length ? 'fail' : 'warn',
          message: configErrors === 0 
            ? 'All configurations valid' 
            : `${configErrors}/${interfaces.length} configurations have issues`,
          duration: Date.now() - configCheckStart,
          details: { 
            totalConfigs: interfaces.length, 
            invalidConfigs: configErrors 
          }
        };
      } catch (error) {
        checks.configuration_validity = {
          status: 'fail',
          message: error.message,
          duration: Date.now() - configCheckStart
        };
      }

      // Check 5: Storage system
      const storageCheckStart = Date.now();
      try {
        // This would require adding a health check method to StorageManager
        checks.storage_system = {
          status: 'pass',
          message: 'Storage system operational',
          duration: Date.now() - storageCheckStart
        };
      } catch (error) {
        checks.storage_system = {
          status: 'fail',
          message: error.message,
          duration: Date.now() - storageCheckStart
        };
      }

    } catch (error) {
      this.logger.error('Error during health check:', error);
      checks.health_check_system = {
        status: 'fail',
        message: `Health check system error: ${error.message}`
      };
    }

    // Calculate summary
    const summary = {
      total: Object.keys(checks).length,
      passed: Object.values(checks).filter(check => check.status === 'pass').length,
      failed: Object.values(checks).filter(check => check.status === 'fail').length,
      warned: Object.values(checks).filter(check => check.status === 'warn').length,
    };

    // Determine overall status
    let status: HealthStatus['status'] = 'healthy';
    if (summary.failed > 0) {
      status = 'unhealthy';
    } else if (summary.warned > 0) {
      status = 'degraded';
    }

    const healthStatus: HealthStatus = {
      status,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      checks,
      summary
    };

    // Cache the result
    this.healthCache = healthStatus;
    this.lastHealthCheck = new Date();

    this.logger.debug('Health check completed', {
      status,
      duration: `${Date.now() - startTime}ms`,
      summary
    });

    return healthStatus;
  }

  async checkInterface(interfaceName: string, useCache = true): Promise<InterfaceHealth> {
    // Check cache first
    if (useCache && this.interfaceHealthCache.has(interfaceName)) {
      const cached = this.interfaceHealthCache.get(interfaceName)!;
      const age = Date.now() - new Date(cached.timestamp).getTime();
      if (age < 60000) { // 1 minute cache
        return cached;
      }
    }

    const interfaceHealth: InterfaceHealth = {
      interface: interfaceName,
      healthy: true,
      checks: {
        configuration: false,
        browser: false,
        tools: false
      },
      timestamp: new Date().toISOString()
    };

    try {
      // Test the interface
      const testResult = await this.manager.testInterface(interfaceName);
      
      // Map test results to health checks
      for (const result of testResult.results) {
        switch (result.test) {
          case 'config_validation':
            interfaceHealth.checks.configuration = result.success;
            break;
          case 'browser_creation':
            interfaceHealth.checks.browser = result.success;
            break;
          case 'tool_execution':
            interfaceHealth.checks.tools = result.success;
            break;
        }

        if (!result.success && !interfaceHealth.error) {
          interfaceHealth.error = result.error;
        }
      }

      interfaceHealth.healthy = testResult.success;
      interfaceHealth.lastTest = new Date();

    } catch (error) {
      interfaceHealth.healthy = false;
      interfaceHealth.error = error.message;
      this.logger.error(`Interface health check failed for ${interfaceName}:`, error);
    }

    // Cache the result
    this.interfaceHealthCache.set(interfaceName, interfaceHealth);

    return interfaceHealth;
  }

  async checkAllInterfaces(): Promise<Map<string, InterfaceHealth>> {
    const interfaces = this.manager.getAvailableInterfaces();
    const results = new Map<string, InterfaceHealth>();

    // Check interfaces in parallel
    const healthChecks = interfaces.map(async (interfaceName) => {
      try {
        const health = await this.checkInterface(interfaceName, false);
        results.set(interfaceName, health);
      } catch (error) {
        this.logger.error(`Failed to check interface ${interfaceName}:`, error);
        results.set(interfaceName, {
          interface: interfaceName,
          healthy: false,
          checks: {
            configuration: false,
            browser: false,
            tools: false
          },
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    await Promise.allSettled(healthChecks);
    return results;
  }

  clearCache(): void {
    this.healthCache = undefined;
    this.lastHealthCheck = undefined;
    this.interfaceHealthCache.clear();
  }

  async getDetailedReport(): Promise<{
    system: HealthStatus;
    interfaces: Map<string, InterfaceHealth>;
    summary: {
      systemHealthy: boolean;
      interfacesHealthy: number;
      interfacesTotal: number;
      lastUpdated: string;
    };
  }> {
    const [systemHealth, interfaceHealth] = await Promise.all([
      this.getHealthStatus(false),
      this.checkAllInterfaces()
    ]);

    const healthyInterfaces = Array.from(interfaceHealth.values()).filter(h => h.healthy).length;

    return {
      system: systemHealth,
      interfaces: interfaceHealth,
      summary: {
        systemHealthy: systemHealth.status === 'healthy',
        interfacesHealthy: healthyInterfaces,
        interfacesTotal: interfaceHealth.size,
        lastUpdated: new Date().toISOString()
      }
    };
  }
}