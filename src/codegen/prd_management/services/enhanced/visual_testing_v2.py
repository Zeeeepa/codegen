"""
Enhanced Visual Testing Service with Cypress + Storybook + Percy/Chromatic
Industry-standard visual testing implementation
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from ....sdk.client import CodegenClient
from ...core.prd_template import PRDTemplate


@dataclass
class CypressConfig:
    base_url: str = "http://localhost:3000"
    viewport_width: int = 1280
    viewport_height: int = 720
    video: bool = True
    screenshot_on_run_failure: bool = True


@dataclass
class StorybookConfig:
    port: int = 6006
    static_dir: str = "storybook-static"
    config_dir: str = ".storybook"


@dataclass
class VisualRegressionConfig:
    provider: str = "percy"  # percy, chromatic, applitools
    project_token: str = ""
    threshold: float = 0.1


@dataclass
class EnhancedVisualTestingConfig:
    cypress: CypressConfig
    storybook: StorybookConfig
    visual_regression: VisualRegressionConfig


@dataclass
class ChromaticResult:
    success: bool
    stories_tested: int
    changes_detected: int
    review_url: str
    duration: int
    details: str


@dataclass
class TestRunnerResult:
    success: bool
    tests_run: int
    tests_failed: int
    duration: int
    details: str


@dataclass
class StorybookTestResult:
    type: str = "storybook"
    status: str = "pending"
    chromatic: Optional[ChromaticResult] = None
    test_runner: Optional[TestRunnerResult] = None
    stories: List[str] = None
    duration: int = 0


@dataclass
class CypressTestResult:
    type: str = "cypress"
    status: str = "pending"
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    duration: int = 0
    videos: List[str] = None
    screenshots: List[str] = None
    reports: Dict[str, str] = None
    details: str = ""


@dataclass
class VisualRegressionResult:
    type: str = "visual_regression"
    status: str = "pending"
    snapshots_taken: int = 0
    changes_detected: int = 0
    review_url: str = ""
    duration: int = 0
    details: str = ""


@dataclass
class AccessibilityTestResult:
    type: str = "accessibility"
    status: str = "pending"
    violations_found: int = 0
    wcag_level: str = "AA"
    compliance_score: int = 0
    duration: int = 0
    details: str = ""


@dataclass
class TestSummary:
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    duration: int = 0


@dataclass
class EnhancedVisualTestResult:
    prd_id: str
    timestamp: str
    results: Dict[str, Any]
    summary: TestSummary


class EnhancedVisualTestingService:
    """
    Enhanced Visual Testing Service using industry-standard tools:
    - Cypress for E2E testing
    - Storybook for component testing
    - Percy/Chromatic for visual regression
    - axe-core for accessibility testing
    """
    
    def __init__(self, codegen_client: CodegenClient, config: EnhancedVisualTestingConfig):
        self.codegen_client = codegen_client
        self.cypress_config = config.cypress
        self.storybook_config = config.storybook
        self.visual_regression_config = config.visual_regression
    
    async def run_comprehensive_visual_tests(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> EnhancedVisualTestResult:
        """Run comprehensive visual testing suite"""
        
        test_suite = EnhancedVisualTestResult(
            prd_id=prd.id,
            timestamp=self._get_timestamp(),
            results={
                "storybook": await self.run_storybook_visual_tests(prd, org_id, repo_id),
                "cypress": await self.run_cypress_e2e_tests(prd, org_id, repo_id),
                "visual_regression": await self.run_visual_regression_tests(prd, org_id, repo_id),
                "accessibility": await self.run_accessibility_tests(prd, org_id, repo_id)
            },
            summary=TestSummary()
        )
        
        # Calculate summary
        test_suite.summary = self._calculate_test_summary(test_suite.results)
        
        return test_suite
    
    async def run_storybook_visual_tests(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> StorybookTestResult:
        """Run Storybook component testing with Chromatic"""
        
        # Setup Storybook
        await self._setup_storybook(org_id, repo_id)
        
        # Build Storybook
        await self._build_storybook(org_id, repo_id)
        
        # Run Chromatic visual regression tests
        chromatic_results = await self._run_chromatic_tests(org_id, repo_id)
        
        # Run Storybook test runner
        test_runner_results = await self._run_storybook_test_runner(org_id, repo_id)
        
        return StorybookTestResult(
            type="storybook",
            status="passed" if chromatic_results.success and test_runner_results.success else "failed",
            chromatic=chromatic_results,
            test_runner=test_runner_results,
            stories=await self._get_storybook_stories(org_id, repo_id),
            duration=chromatic_results.duration + test_runner_results.duration
        )
    
    async def _setup_storybook(self, org_id: int, repo_id: int) -> None:
        """Setup Storybook with all necessary addons"""
        
        setup_prompt = """
Set up Storybook for component visual testing:

1. Install Storybook and dependencies:
   npx storybook@latest init --yes
   npm install --save-dev @storybook/test-runner
   npm install --save-dev @storybook/addon-a11y
   npm install --save-dev @storybook/addon-viewport
   npm install --save-dev @storybook/addon-docs
   npm install --save-dev chromatic

2. Configure .storybook/main.js:
   export default {
     stories: ['../src/**/*.stories.@(js|jsx|ts|tsx|mdx)'],
     addons: [
       '@storybook/addon-essentials',
       '@storybook/addon-a11y',
       '@storybook/addon-viewport',
       '@storybook/addon-docs'
     ],
     framework: {
       name: '@storybook/react-vite',
       options: {}
     },
     docs: {
       autodocs: 'tag'
     }
   };

3. Create .storybook/preview.js:
   export const parameters = {
     actions: { argTypesRegex: '^on[A-Z].*' },
     controls: {
       matchers: {
         color: /(background|color)$/i,
         date: /Date$/,
       },
     },
     a11y: {
       element: '#root',
       config: {},
       options: {},
       manual: true,
     },
     viewport: {
       viewports: {
         mobile: { name: 'Mobile', styles: { width: '375px', height: '667px' } },
         tablet: { name: 'Tablet', styles: { width: '768px', height: '1024px' } },
         desktop: { name: 'Desktop', styles: { width: '1024px', height: '768px' } }
       }
     }
   };

4. Create component stories for all UI components found in the codebase
5. Configure visual regression testing with Chromatic
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=setup_prompt,
            repo_id=repo_id
        )
        
        await self._poll_completion(org_id, agent_run.id)
    
    async def _build_storybook(self, org_id: int, repo_id: int) -> None:
        """Build Storybook for testing"""
        
        build_prompt = """
Build Storybook for testing:

1. Build static Storybook:
   npm run build-storybook

2. Verify build output in storybook-static/
3. Start Storybook server for testing:
   npm run storybook -- --ci --port 6006 &

4. Wait for Storybook to be ready on http://localhost:6006
5. Verify all stories load without errors
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=build_prompt,
            repo_id=repo_id
        )
        
        await self._poll_completion(org_id, agent_run.id)
    
    async def _run_chromatic_tests(self, org_id: int, repo_id: int) -> ChromaticResult:
        """Run Chromatic visual regression tests"""
        
        chromatic_prompt = f"""
Run Chromatic visual regression tests:

1. Set up Chromatic project token (use environment variable)
2. Run Chromatic tests:
   npx chromatic --project-token=${{CHROMATIC_PROJECT_TOKEN}} --exit-zero-on-changes

3. Capture results:
   - Number of stories tested
   - Visual changes detected
   - Baseline comparisons
   - Review URLs

4. Generate report with:
   - Changed components
   - New components
   - Regression details
   - Review links

5. Output results in JSON format for parsing
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=chromatic_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        
        return ChromaticResult(
            success=not ("error" in result.get("output", "").lower()),
            stories_tested=self._extract_number(result.get("output", ""), r"(\d+) stories tested") or 0,
            changes_detected=self._extract_number(result.get("output", ""), r"(\d+) changes detected") or 0,
            review_url=self._extract_url(result.get("output", "")) or "",
            duration=result.get("duration", 0),
            details=result.get("output", "")
        )
    
    async def _run_storybook_test_runner(self, org_id: int, repo_id: int) -> TestRunnerResult:
        """Run Storybook test runner for interaction testing"""
        
        test_runner_prompt = """
Run Storybook test runner for interaction testing:

1. Start test runner:
   npm run test-storybook -- --watchAll=false

2. Run tests for all stories:
   - Smoke tests (stories render without errors)
   - Interaction tests (user interactions work)
   - Accessibility tests (a11y violations)

3. Generate test report with:
   - Test results per story
   - Failed tests details
   - Coverage information
   - Performance metrics

4. Output results in structured format
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=test_runner_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        
        return TestRunnerResult(
            success="passed" in result.get("output", "").lower(),
            tests_run=self._extract_number(result.get("output", ""), r"(\d+) tests? passed") or 0,
            tests_failed=self._extract_number(result.get("output", ""), r"(\d+) tests? failed") or 0,
            duration=result.get("duration", 0),
            details=result.get("output", "")
        )
    
    async def run_cypress_e2e_tests(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> CypressTestResult:
        """Run Cypress E2E tests"""
        
        # Setup Cypress
        await self._setup_cypress(org_id, repo_id)
        
        # Generate test specs from PRD
        await self._generate_cypress_specs(prd, org_id, repo_id)
        
        # Run Cypress tests
        cypress_results = await self._execute_cypress_tests(org_id, repo_id)
        
        return cypress_results
    
    async def _setup_cypress(self, org_id: int, repo_id: int) -> None:
        """Setup Cypress for E2E testing"""
        
        setup_prompt = f"""
Set up Cypress for E2E testing:

1. Install Cypress and dependencies:
   npm install --save-dev cypress
   npm install --save-dev @cypress/code-coverage
   npm install --save-dev cypress-axe
   npm install --save-dev @percy/cypress

2. Initialize Cypress:
   npx cypress install

3. Configure cypress.config.js:
   import {{ defineConfig }} from 'cypress'
   
   export default defineConfig({{
     e2e: {{
       baseUrl: '{self.cypress_config.base_url}',
       supportFile: 'cypress/support/e2e.js',
       specPattern: 'cypress/e2e/**/*.cy.{{js,jsx,ts,tsx}}',
       video: {str(self.cypress_config.video).lower()},
       screenshotOnRunFailure: {str(self.cypress_config.screenshot_on_run_failure).lower()},
       viewportWidth: {self.cypress_config.viewport_width},
       viewportHeight: {self.cypress_config.viewport_height},
       setupNodeEvents(on, config) {{
         require('@cypress/code-coverage/task')(on, config)
         return config
       }}
     }}
   }})

4. Set up cypress/support/e2e.js:
   import '@cypress/code-coverage/support'
   import 'cypress-axe'
   import '@percy/cypress'

5. Create custom commands for common interactions
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=setup_prompt,
            repo_id=repo_id
        )
        
        await self._poll_completion(org_id, agent_run.id)
    
    async def _generate_cypress_specs(self, prd: PRDTemplate, org_id: int, repo_id: int) -> None:
        """Generate Cypress test specifications based on PRD requirements"""
        
        spec_generation_prompt = f"""
Generate Cypress test specifications based on PRD requirements:

PRD Goal: {prd.goal}
PRD What: {prd.what}
Success Criteria: {', '.join(prd.success_criteria)}

Create comprehensive E2E tests covering:

1. User Journey Tests:
   - Happy path scenarios
   - Error handling flows
   - Edge cases

2. Visual Regression Tests:
   - Key page screenshots with Percy
   - Component visual states
   - Responsive design validation

3. Accessibility Tests:
   - WCAG compliance with cypress-axe
   - Keyboard navigation
   - Screen reader compatibility

4. Performance Tests:
   - Page load times
   - Core Web Vitals
   - Resource loading

Generate test files in cypress/e2e/ directory with descriptive names.
Use Page Object Model pattern for maintainability.
Include data-testid attributes for reliable element selection.

Example test structure:
describe('User Authentication', () => {{
  beforeEach(() => {{
    cy.visit('/login')
  }})
  
  it('should login successfully with valid credentials', () => {{
    cy.get('[data-testid="email-input"]').type('user@example.com')
    cy.get('[data-testid="password-input"]').type('password123')
    cy.get('[data-testid="login-button"]').click()
    cy.url().should('include', '/dashboard')
    cy.percySnapshot('Dashboard after login')
  }})
  
  it('should be accessible', () => {{
    cy.injectAxe()
    cy.checkA11y()
  }})
}})
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=spec_generation_prompt,
            repo_id=repo_id
        )
        
        await self._poll_completion(org_id, agent_run.id)
    
    async def _execute_cypress_tests(self, org_id: int, repo_id: int) -> CypressTestResult:
        """Execute Cypress E2E tests"""
        
        execution_prompt = """
Execute Cypress E2E tests:

1. Start the application:
   npm start &
   
2. Wait for application to be ready on http://localhost:3000

3. Run Cypress tests:
   npx cypress run --browser chrome --headless --reporter mochawesome

4. Generate reports:
   - JUnit XML reports
   - Mochawesome HTML reports
   - Coverage reports
   - Video recordings
   - Screenshots of failures

5. Collect results:
   - Total tests run
   - Passed/failed counts
   - Test duration
   - Failure details
   - Performance metrics

6. Output structured results for parsing
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=execution_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        
        return CypressTestResult(
            type="cypress",
            status="passed" if "All specs passed!" in result.get("output", "") else "failed",
            tests_run=self._extract_number(result.get("output", ""), r"(\d+) tests? passed") or 0,
            tests_passed=self._extract_number(result.get("output", ""), r"(\d+) passed") or 0,
            tests_failed=self._extract_number(result.get("output", ""), r"(\d+) failed") or 0,
            duration=result.get("duration", 0),
            videos=self._extract_video_paths(result.get("output", "")),
            screenshots=self._extract_screenshot_paths(result.get("output", "")),
            reports={
                "junit": "cypress/reports/junit.xml",
                "mochawesome": "cypress/reports/mochawesome.html",
                "coverage": "coverage/lcov-report/index.html"
            },
            details=result.get("output", "")
        )
    
    async def run_visual_regression_tests(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> VisualRegressionResult:
        """Run comprehensive visual regression testing"""
        
        visual_regression_prompt = f"""
Run comprehensive visual regression testing with {self.visual_regression_config.provider}:

1. Set up Percy for visual testing:
   npm install --save-dev @percy/cli @percy/cypress

2. Configure Percy in cypress/support/e2e.js:
   import '@percy/cypress'

3. Add Percy snapshots to Cypress tests:
   cy.percySnapshot('Homepage')
   cy.percySnapshot('Login Form')
   cy.percySnapshot('Dashboard')

4. Run tests with Percy:
   npx percy exec -- cypress run

5. Capture visual differences:
   - Baseline comparisons
   - New screenshots
   - Visual changes detected
   - Review URLs

6. Generate visual regression report with:
   - Changed pages/components
   - Pixel differences
   - Browser compatibility
   - Responsive design validation

7. Output structured results
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=visual_regression_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        
        return VisualRegressionResult(
            type="visual_regression",
            status="passed" if "no visual changes detected" in result.get("output", "").lower() else "failed",
            snapshots_taken=self._extract_number(result.get("output", ""), r"(\d+) snapshots taken") or 0,
            changes_detected=self._extract_number(result.get("output", ""), r"(\d+) visual changes") or 0,
            review_url=self._extract_url(result.get("output", "")) or "",
            duration=result.get("duration", 0),
            details=result.get("output", "")
        )
    
    async def run_accessibility_tests(
        self,
        prd: PRDTemplate,
        org_id: int,
        repo_id: int
    ) -> AccessibilityTestResult:
        """Run comprehensive accessibility testing"""
        
        a11y_prompt = """
Run comprehensive accessibility testing:

1. Set up axe-core for accessibility testing:
   npm install --save-dev cypress-axe

2. Add accessibility tests to Cypress specs:
   cy.injectAxe()
   cy.checkA11y()

3. Run accessibility audit:
   - WCAG 2.1 AA compliance
   - Color contrast validation
   - Keyboard navigation testing
   - Screen reader compatibility
   - Focus management

4. Generate accessibility report:
   - Violations by severity
   - Affected elements
   - Remediation suggestions
   - Compliance score

5. Test with multiple assistive technologies:
   - Screen readers (NVDA, JAWS, VoiceOver)
   - Keyboard-only navigation
   - High contrast mode
   - Zoom levels up to 200%

6. Output structured accessibility results
"""
        
        agent_run = await self.codegen_client.create_agent_run(
            org_id=org_id,
            prompt=a11y_prompt,
            repo_id=repo_id
        )
        
        result = await self._poll_completion(org_id, agent_run.id)
        
        return AccessibilityTestResult(
            type="accessibility",
            status="passed" if "no violations found" in result.get("output", "").lower() else "failed",
            violations_found=self._extract_number(result.get("output", ""), r"(\d+) violations found") or 0,
            wcag_level="AA",
            compliance_score=self._extract_number(result.get("output", ""), r"(\d+)% compliant") or 0,
            duration=result.get("duration", 0),
            details=result.get("output", "")
        )
    
    # Utility methods
    def _calculate_test_summary(self, results: Dict[str, Any]) -> TestSummary:
        """Calculate overall test summary"""
        total_tests = 0
        passed = 0
        failed = 0
        duration = 0
        
        for result in results.values():
            if hasattr(result, 'tests_run') and result.tests_run:
                total_tests += result.tests_run
            if hasattr(result, 'tests_passed') and result.tests_passed:
                passed += result.tests_passed
            if hasattr(result, 'tests_failed') and result.tests_failed:
                failed += result.tests_failed
            if hasattr(result, 'duration') and result.duration:
                duration += result.duration
        
        return TestSummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            duration=duration
        )
    
    def _extract_number(self, text: str, regex: str) -> Optional[int]:
        """Extract number from text using regex"""
        if not text:
            return None
        match = re.search(regex, text)
        return int(match.group(1)) if match else None
    
    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from text"""
        if not text:
            return None
        url_regex = r'https?://[^\s]+'
        match = re.search(url_regex, text)
        return match.group(0) if match else None
    
    def _extract_video_paths(self, text: str) -> List[str]:
        """Extract video file paths from text"""
        if not text:
            return []
        video_regex = r'cypress/videos/[^\s]+\.mp4'
        return re.findall(video_regex, text)
    
    def _extract_screenshot_paths(self, text: str) -> List[str]:
        """Extract screenshot file paths from text"""
        if not text:
            return []
        screenshot_regex = r'cypress/screenshots/[^\s]+\.png'
        return re.findall(screenshot_regex, text)
    
    async def _get_storybook_stories(self, org_id: int, repo_id: int) -> List[str]:
        """Get list of Storybook stories"""
        # Implementation to extract story names from Storybook
        return []
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def _poll_completion(self, org_id: int, agent_run_id: str) -> Dict[str, Any]:
        """Poll for agent run completion"""
        timeout = 600  # 10 minutes
        poll_interval = 10  # 10 seconds
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                agent_run = await self.codegen_client.get_agent_run(org_id, agent_run_id)
                
                if agent_run.status == "COMPLETE":
                    return agent_run.result or {}
                elif agent_run.status == "FAILED":
                    raise Exception(f"Visual testing step failed: {agent_run.error}")
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)
        
        raise Exception("Visual testing step timed out")

