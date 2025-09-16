import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    video: true,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    pageLoadTimeout: 30000,
    experimentalStudio: true,
    experimentalWebKitSupport: true,
    setupNodeEvents(on, config) {
      // Code coverage
      require('@cypress/code-coverage/task')(on, config)
      
      // Custom tasks
      on('task', {
        log(message) {
          console.log(message)
          return null
        },
        table(message) {
          console.table(message)
          return null
        }
      })
      
      return config
    },
  },
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
    specPattern: 'src/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/component.js',
  },
  env: {
    coverage: true,
    codeCoverage: {
      exclude: [
        'cypress/**/*.*',
        '**/*.cy.{js,jsx,ts,tsx}',
        '**/*.stories.{js,jsx,ts,tsx}',
        '**/node_modules/**',
      ],
    },
  },
  retries: {
    runMode: 2,
    openMode: 0,
  },
})

