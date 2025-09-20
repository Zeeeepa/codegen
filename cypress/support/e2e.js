// Import commands.js using ES2015 syntax:
import './commands'

// Import code coverage support
import '@cypress/code-coverage/support'

// Import accessibility testing
import 'cypress-axe'

// Import Percy for visual testing
import '@percy/cypress'

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Hide fetch/XHR requests from command log
const app = window.top;
if (!app.document.head.querySelector('[data-hide-command-log-request]')) {
  const style = app.document.createElement('style');
  style.innerHTML = '.command-name-request, .command-name-xhr { display: none }';
  style.setAttribute('data-hide-command-log-request', '');
  app.document.head.appendChild(style);
}

// Global error handling
Cypress.on('uncaught:exception', (err, runnable) => {
  // Returning false here prevents Cypress from failing the test
  // You can customize this based on your needs
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false;
  }
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false;
  }
  return true;
});

// Custom commands for common operations
Cypress.Commands.add('login', (email = 'test@example.com', password = 'password123') => {
  cy.visit('/login');
  cy.get('[data-testid="email-input"]').type(email);
  cy.get('[data-testid="password-input"]').type(password);
  cy.get('[data-testid="login-button"]').click();
  cy.url().should('not.include', '/login');
});

Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

// Accessibility testing helper
Cypress.Commands.add('checkA11y', (context = null, options = null) => {
  cy.injectAxe();
  cy.checkA11y(context, options, (violations) => {
    if (violations.length > 0) {
      cy.task('log', `${violations.length} accessibility violation(s) detected`);
      cy.task('table', violations.map(v => ({
        id: v.id,
        impact: v.impact,
        description: v.description,
        nodes: v.nodes.length
      })));
    }
  });
});

// Visual regression testing helper
Cypress.Commands.add('visualSnapshot', (name, options = {}) => {
  const defaultOptions = {
    widths: [375, 768, 1024, 1440],
    minHeight: 1024,
    ...options
  };
  cy.percySnapshot(name, defaultOptions);
});

// Performance testing helper
Cypress.Commands.add('measurePerformance', (name) => {
  cy.window().then((win) => {
    const perfData = win.performance.getEntriesByType('navigation')[0];
    const metrics = {
      name,
      loadTime: perfData.loadEventEnd - perfData.loadEventStart,
      domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
      firstPaint: win.performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 0,
      firstContentfulPaint: win.performance.getEntriesByType('paint').find(p => p.name === 'first-contentful-paint')?.startTime || 0,
    };
    cy.task('log', `Performance metrics for ${name}:`);
    cy.task('table', metrics);
  });
});

// API testing helper
Cypress.Commands.add('apiRequest', (method, url, body = null, headers = {}) => {
  return cy.request({
    method,
    url,
    body,
    headers: {
      'Content-Type': 'application/json',
      ...headers
    },
    failOnStatusCode: false
  });
});

// Database seeding helper (if needed)
Cypress.Commands.add('seedDatabase', (fixture) => {
  cy.task('seedDb', fixture);
});

// Wait for application to be ready
Cypress.Commands.add('waitForApp', () => {
  cy.get('[data-testid="app-ready"]', { timeout: 30000 }).should('exist');
});

// Custom assertions
Cypress.Commands.add('shouldBeAccessible', { prevSubject: 'element' }, (subject) => {
  cy.wrap(subject).should('be.visible');
  cy.wrap(subject).should('not.have.attr', 'aria-hidden', 'true');
  cy.wrap(subject).should('have.attr', 'tabindex').and('not.equal', '-1');
});

// Mobile testing helpers
Cypress.Commands.add('setMobileViewport', () => {
  cy.viewport(375, 667);
});

Cypress.Commands.add('setTabletViewport', () => {
  cy.viewport(768, 1024);
});

Cypress.Commands.add('setDesktopViewport', () => {
  cy.viewport(1440, 900);
});

