// Custom Cypress commands for the PRD Management System

// PRD Management Commands
Cypress.Commands.add('createPRD', (prdData) => {
  cy.visit('/prd/new');
  cy.get('[data-testid="prd-title-input"]').type(prdData.title);
  cy.get('[data-testid="prd-goal-textarea"]').type(prdData.goal);
  cy.get('[data-testid="prd-what-textarea"]').type(prdData.what);
  
  // Add success criteria
  prdData.successCriteria.forEach((criteria, index) => {
    if (index > 0) {
      cy.get('[data-testid="add-success-criteria-button"]').click();
    }
    cy.get(`[data-testid="success-criteria-input-${index}"]`).type(criteria);
  });
  
  cy.get('[data-testid="create-prd-button"]').click();
  cy.url().should('include', '/prd/');
});

Cypress.Commands.add('selectProject', (orgId, repoId) => {
  cy.get(`[data-testid="org-card-${orgId}"]`).click();
  cy.get(`[data-testid="repo-card-${repoId}"]`).click();
  cy.get('[data-testid="project-selected"]').should('be.visible');
});

Cypress.Commands.add('generatePRDWithProMode', (prompt, options = {}) => {
  cy.get('[data-testid="user-prompt-textarea"]').type(prompt);
  
  if (options.numGenerations) {
    cy.get('[data-testid="num-generations-input"]').clear().type(options.numGenerations.toString());
  }
  
  if (options.temperature) {
    cy.get('[data-testid="temperature-slider"]').invoke('val', options.temperature).trigger('input');
  }
  
  cy.get('[data-testid="generate-prd-button"]').click();
  cy.get('[data-testid="pro-mode-progress"]', { timeout: 60000 }).should('be.visible');
  cy.get('[data-testid="prd-generated"]', { timeout: 300000 }).should('be.visible');
});

Cypress.Commands.add('viewPRD', (prdId) => {
  cy.visit(`/prd/${prdId}`);
  cy.get('[data-testid="prd-viewer"]').should('be.visible');
});

Cypress.Commands.add('implementPRD', (prdId) => {
  cy.visit(`/prd/${prdId}`);
  cy.get('[data-testid="implement-prd-button"]').click();
  cy.get('[data-testid="implementation-progress"]', { timeout: 60000 }).should('be.visible');
});

Cypress.Commands.add('waitForImplementation', (timeout = 600000) => {
  cy.get('[data-testid="implementation-complete"]', { timeout }).should('be.visible');
  cy.get('[data-testid="implementation-status"]').should('contain', 'completed');
});

// Testing Commands
Cypress.Commands.add('runVisualTests', (prdId) => {
  cy.visit(`/prd/${prdId}/testing`);
  cy.get('[data-testid="run-visual-tests-button"]').click();
  cy.get('[data-testid="visual-tests-running"]', { timeout: 30000 }).should('be.visible');
  cy.get('[data-testid="visual-tests-complete"]', { timeout: 300000 }).should('be.visible');
});

Cypress.Commands.add('runPerformanceTests', (prdId) => {
  cy.visit(`/prd/${prdId}/testing`);
  cy.get('[data-testid="run-performance-tests-button"]').click();
  cy.get('[data-testid="performance-tests-complete"]', { timeout: 180000 }).should('be.visible');
});

Cypress.Commands.add('runSecurityTests', (prdId) => {
  cy.visit(`/prd/${prdId}/testing`);
  cy.get('[data-testid="run-security-tests-button"]').click();
  cy.get('[data-testid="security-tests-complete"]', { timeout: 300000 }).should('be.visible');
});

// Deployment Commands
Cypress.Commands.add('deployPRD', (prdId, deploymentConfig) => {
  cy.visit(`/prd/${prdId}/deployment`);
  
  cy.get('[data-testid="deployment-environment-select"]').select(deploymentConfig.environment);
  cy.get('[data-testid="deployment-platform-select"]').select(deploymentConfig.platform);
  
  if (deploymentConfig.domain) {
    cy.get('[data-testid="deployment-domain-input"]').type(deploymentConfig.domain);
  }
  
  cy.get('[data-testid="deploy-button"]').click();
  cy.get('[data-testid="deployment-progress"]', { timeout: 60000 }).should('be.visible');
  cy.get('[data-testid="deployment-complete"]', { timeout: 600000 }).should('be.visible');
});

// Reporting Commands
Cypress.Commands.add('viewReport', (reportId) => {
  cy.visit(`/reports/${reportId}`);
  cy.get('[data-testid="comprehensive-report"]').should('be.visible');
});

Cypress.Commands.add('downloadReport', (reportId, format = 'pdf') => {
  cy.visit(`/reports/${reportId}`);
  cy.get(`[data-testid="download-report-${format}"]`).click();
  cy.readFile(`cypress/downloads/report-${reportId}.${format}`).should('exist');
});

// Utility Commands
Cypress.Commands.add('waitForWebSocket', () => {
  cy.window().its('websocket').should('exist');
  cy.window().its('websocket.readyState').should('equal', 1); // WebSocket.OPEN
});

Cypress.Commands.add('mockCodegenAPI', (responses = {}) => {
  cy.intercept('POST', '/api/v1/organizations/*/agent/run', responses.createAgentRun || { fixture: 'agent-run-created.json' });
  cy.intercept('GET', '/api/v1/organizations/*/agent/run/*', responses.getAgentRun || { fixture: 'agent-run-completed.json' });
  cy.intercept('GET', '/api/v1/organizations', responses.getOrganizations || { fixture: 'organizations.json' });
  cy.intercept('GET', '/api/v1/organizations/*/repos', responses.getRepositories || { fixture: 'repositories.json' });
});

Cypress.Commands.add('verifyPRDStructure', (prd) => {
  cy.get('[data-testid="prd-title"]').should('contain', prd.title);
  cy.get('[data-testid="prd-goal"]').should('contain', prd.goal);
  cy.get('[data-testid="prd-what"]').should('contain', prd.what);
  
  prd.successCriteria.forEach((criteria, index) => {
    cy.get(`[data-testid="success-criteria-${index}"]`).should('contain', criteria);
  });
});

Cypress.Commands.add('verifyImplementationResults', (expectedResults) => {
  cy.get('[data-testid="implementation-status"]').should('contain', expectedResults.status);
  cy.get('[data-testid="tasks-completed"]').should('contain', expectedResults.tasksCompleted);
  cy.get('[data-testid="total-tasks"]').should('contain', expectedResults.totalTasks);
  
  if (expectedResults.prUrl) {
    cy.get('[data-testid="pr-link"]').should('have.attr', 'href', expectedResults.prUrl);
  }
});

Cypress.Commands.add('verifyTestResults', (testType, expectedResults) => {
  cy.get(`[data-testid="${testType}-test-status"]`).should('contain', expectedResults.status);
  
  if (expectedResults.testsRun) {
    cy.get(`[data-testid="${testType}-tests-run"]`).should('contain', expectedResults.testsRun);
  }
  
  if (expectedResults.testsPassed) {
    cy.get(`[data-testid="${testType}-tests-passed"]`).should('contain', expectedResults.testsPassed);
  }
  
  if (expectedResults.testsFailed) {
    cy.get(`[data-testid="${testType}-tests-failed"]`).should('contain', expectedResults.testsFailed);
  }
});

// Error handling commands
Cypress.Commands.add('handleRetryMechanism', (operationType) => {
  cy.get(`[data-testid="${operationType}-retry-indicator"]`).should('be.visible');
  cy.get(`[data-testid="${operationType}-retry-complete"]`, { timeout: 180000 }).should('be.visible');
});

Cypress.Commands.add('verifyErrorRecovery', (errorType) => {
  cy.get(`[data-testid="error-${errorType}"]`).should('be.visible');
  cy.get(`[data-testid="recovery-${errorType}"]`).should('be.visible');
  cy.get(`[data-testid="recovery-success-${errorType}"]`, { timeout: 120000 }).should('be.visible');
});

