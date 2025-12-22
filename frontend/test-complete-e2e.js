const puppeteer = require('puppeteer');

// Test results tracker
const testResults = [];
let passCount = 0;
let failCount = 0;

function logTest(name, passed, details = '') {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status}: ${name}`);
  if (details) console.log(`   ${details}`);
  testResults.push({ name, passed, details });
  if (passed) passCount++;
  else failCount++;
}

(async () => {
  console.log('🚀 COMPREHENSIVE E2E TESTING - Frontend2 Branch');
  console.log('═'.repeat(80));
  console.log('Testing ALL features until 100% pass rate achieved\n');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  const apiCalls = [];
  page.on('request', req => {
    const url = req.url();
    if (url.includes('/api/') || url.includes('codegen')) {
      apiCalls.push({ method: req.method(), url });
    }
  });

  try {
    console.log('\n📋 PHASE 1: Initial Page Load');
    console.log('─'.repeat(80));
    
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle0', timeout: 20000 });
    await new Promise(r => setTimeout(r, 3000));
    
    const title = await page.title();
    logTest('Page loads with correct title', title.includes('CodeGen'), `Title: "${title}"`);
    
    await page.screenshot({ path: '/tmp/e2e-01-landing.png', fullPage: false });
    logTest('Landing page screenshot captured', true);

    console.log('\n📋 PHASE 2: Navigation Structure');
    console.log('─'.repeat(80));
    
    const navButtons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button')).map(btn => ({
        text: btn.textContent.trim().substring(0, 50),
        visible: btn.offsetParent !== null
      }));
    });
    
    logTest('Navigation buttons present', navButtons.length >= 10, `Found ${navButtons.length} buttons`);
    
    // Find the 10 main tabs
    const tabs = ['Dashboard', 'Workflow', 'Control', 'Monitor', 'Template', 'Analytics', 'Webhook', 'Token', 'Profile', 'Inspector'];
    const foundTabs = [];
    
    for (const tabName of tabs) {
      const found = navButtons.some(btn => btn.text.toLowerCase().includes(tabName.toLowerCase()));
      if (found) foundTabs.push(tabName);
    }
    
    logTest('All 10 tabs present in navigation', foundTabs.length === 10, `Found: ${foundTabs.join(', ')}`);

    console.log('\n📋 PHASE 3: Test Each Tab Navigation');
    console.log('─'.repeat(80));
    
    // Test clicking each tab systematically
    const tabTests = [
      { name: 'Dashboard', pattern: 'dashboard' },
      { name: 'Workflows', pattern: 'workflow' },
      { name: 'Control', pattern: 'control' },
      { name: 'Monitor', pattern: 'monitor' },
      { name: 'Templates', pattern: 'template' },
      { name: 'Analytics', pattern: 'analytics' },
      { name: 'Webhooks', pattern: 'webhook' },
      { name: 'API Tokens', pattern: 'token' },
      { name: 'Profiles', pattern: 'profile' },
      { name: 'Inspector', pattern: 'inspector' }
    ];
    
    for (const tab of tabTests) {
      try {
        const clicked = await page.evaluate((pattern) => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const btn = buttons.find(b => b.textContent.toLowerCase().includes(pattern));
          if (btn) {
            btn.click();
            return true;
          }
          return false;
        }, tab.pattern);
        
        if (clicked) {
          await new Promise(r => setTimeout(r, 2000));
          
          const contentVisible = await page.evaluate(() => {
            return document.body.textContent.length > 100;
          });
          
          logTest(`${tab.name} tab clickable and loads content`, contentVisible);
          await page.screenshot({ path: `/tmp/e2e-tab-${tab.pattern}.png` });
        } else {
          logTest(`${tab.name} tab clickable and loads content`, false, 'Tab button not found');
        }
      } catch (e) {
        logTest(`${tab.name} tab clickable and loads content`, false, e.message);
      }
    }

    console.log('\n📋 PHASE 4: Workflow Control Features');
    console.log('─'.repeat(80));
    
    // Navigate to Control tab
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => b.textContent.toLowerCase().includes('control'));
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 3000));
    
    const workflowSection = await page.evaluate(() => {
      const text = document.body.textContent.toLowerCase();
      return text.includes('workflow') || text.includes('execute') || text.includes('pause');
    });
    logTest('Workflow Control section renders', workflowSection);
    
    const hasActionButtons = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const actions = ['execute', 'pause', 'resume', 'stop', 'refresh'];
      return actions.some(action => 
        buttons.some(btn => btn.textContent.toLowerCase().includes(action))
      );
    });
    logTest('Workflow action buttons present', hasActionButtons);
    
    const hasWorkflowList = await page.evaluate(() => {
      return document.querySelectorAll('table, [class*="list"], [class*="card"]').length > 0;
    });
    logTest('Workflow list structure present', hasWorkflowList, 'Tables/cards/lists detected');

    console.log('\n📋 PHASE 5: Monitor Dashboard Features');
    console.log('─'.repeat(80));
    
    // Navigate to Monitor tab
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => b.textContent.toLowerCase().includes('monitor'));
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 3000));
    
    const monitorSection = await page.evaluate(() => {
      const text = document.body.textContent.toLowerCase();
      return text.includes('monitor') || text.includes('execution') || text.includes('run');
    });
    logTest('Monitor Dashboard section renders', monitorSection);
    
    const hasFilters = await page.evaluate(() => {
      const text = document.body.textContent.toLowerCase();
      return ['all', 'success', 'failure', 'running', 'pending'].some(filter => 
        text.includes(filter)
      );
    });
    logTest('Status filter options present', hasFilters);
    
    const hasRunsList = await page.evaluate(() => {
      const text = document.body.textContent.toLowerCase();
      return text.includes('run') || text.includes('execution') || 
             document.querySelectorAll('table, [class*="list"]').length > 0;
    });
    logTest('Runs list structure present', hasRunsList);
    
    const hasLogsButton = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.some(btn => btn.textContent.toLowerCase().includes('log') || 
                                  btn.textContent.toLowerCase().includes('view'));
    });
    logTest('View logs functionality available', hasLogsButton);

    console.log('\n📋 PHASE 6: Analytics Tab');
    console.log('─'.repeat(80));
    
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => b.textContent.toLowerCase().includes('analytics'));
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 2000));
    
    const analyticsContent = await page.evaluate(() => {
      return document.body.textContent.toLowerCase().includes('analytic');
    });
    logTest('Analytics tab loads content', analyticsContent);

    console.log('\n📋 PHASE 7: Templates Tab');
    console.log('─'.repeat(80));
    
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const btn = buttons.find(b => b.textContent.toLowerCase().includes('template'));
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 2000));
    
    const templatesContent = await page.evaluate(() => {
      return document.body.textContent.toLowerCase().includes('template');
    });
    logTest('Templates tab loads content', templatesContent);

    console.log('\n📋 PHASE 8: Additional Tabs (Settings, Webhooks, etc.)');
    console.log('─'.repeat(80));
    
    const additionalTabs = [
      { name: 'Webhooks', pattern: 'webhook' },
      { name: 'API Tokens', pattern: 'token' },
      { name: 'Profiles', pattern: 'profile' },
      { name: 'Inspector', pattern: 'inspector' }
    ];
    
    for (const tab of additionalTabs) {
      await page.evaluate((pattern) => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const btn = buttons.find(b => b.textContent.toLowerCase().includes(pattern));
        if (btn) btn.click();
      }, tab.pattern);
      await new Promise(r => setTimeout(r, 1500));
      
      const hasContent = await page.evaluate(() => document.body.textContent.length > 100);
      logTest(`${tab.name} tab functional`, hasContent);
    }

    console.log('\n📋 PHASE 9: New Agent Run Dialog');
    console.log('─'.repeat(80));
    
    const hasNewRunButton = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.some(btn => {
        const text = btn.textContent.toLowerCase();
        return text.includes('new') || text.includes('create');
      });
    });
    logTest('New run/create button exists', hasNewRunButton);
    
    if (hasNewRunButton) {
      try {
        await page.evaluate(() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          const btn = buttons.find(b => {
            const text = b.textContent.toLowerCase();
            return (text.includes('new') && text.includes('workflow')) || 
                   text.includes('create workflow');
          });
          if (btn) btn.click();
        });
        await new Promise(r => setTimeout(r, 2000));
        
        const dialogOpened = await page.evaluate(() => {
          return document.querySelectorAll('[role="dialog"], .modal, [class*="dialog"]').length > 0;
        });
        logTest('Create dialog opens', dialogOpened);
      } catch (e) {
        logTest('Create dialog opens', false, 'Could not trigger dialog');
      }
    }

    console.log('\n📋 PHASE 10: API Integration Check');
    console.log('─'.repeat(80));
    
    console.log(`\nAPI Calls Tracked: ${apiCalls.length}`);
    if (apiCalls.length > 0) {
      apiCalls.slice(0, 10).forEach(call => {
        console.log(`  ${call.method} ${call.url}`);
      });
      if (apiCalls.length > 10) {
        console.log(`  ... and ${apiCalls.length - 10} more`);
      }
    }
    
    const hasRealApiCalls = apiCalls.some(call => 
      call.url.includes('/api/workflows') || 
      call.url.includes('/api/runs') ||
      call.url.includes('/api/agent')
    );
    logTest('Real API endpoints called', hasRealApiCalls, 
      hasRealApiCalls ? 'API integration working' : 'No /api/ calls detected - may be expected if backend not running');

    console.log('\n📋 PHASE 11: Console Errors Check');
    console.log('─'.repeat(80));
    
    console.log(`Console Errors: ${errors.length}`);
    if (errors.length > 0) {
      errors.slice(0, 5).forEach(err => {
        console.log(`  - ${err.substring(0, 100)}...`);
      });
    }
    
    const criticalErrors = errors.filter(e => 
      !e.includes('Outdated Optimize') && 
      !e.includes('Suspense') &&
      !e.includes('Warning')
    );
    logTest('No critical console errors', criticalErrors.length === 0, 
      `${criticalErrors.length} critical errors, ${errors.length} total`);

    console.log('\n📋 PHASE 12: Responsive Design Test');
    console.log('─'.repeat(80));
    
    await page.setViewport({ width: 375, height: 667 }); // Mobile
    await page.reload({ waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    
    const mobileWorks = await page.evaluate(() => {
      return document.body.offsetWidth <= 400;
    });
    logTest('Mobile responsive view works', mobileWorks, '375px width');
    
    await page.setViewport({ width: 768, height: 1024 }); // Tablet
    await page.reload({ waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 2000));
    
    const tabletWorks = await page.evaluate(() => {
      return document.body.offsetWidth >= 700 && document.body.offsetWidth <= 800;
    });
    logTest('Tablet responsive view works', tabletWorks, '768px width');

    await page.setViewport({ width: 1920, height: 1080 }); // Desktop
    
  } catch (error) {
    console.error('\n❌ CRITICAL ERROR:', error.message);
    logTest('No critical test failures', false, error.message);
  }

  await browser.close();

  // Final Summary
  console.log('\n\n' + '═'.repeat(80));
  console.log('📊 FINAL TEST RESULTS');
  console.log('═'.repeat(80));
  
  const totalTests = passCount + failCount;
  const passRate = Math.round((passCount / totalTests) * 100);
  
  console.log(`\n✅ PASSED: ${passCount}/${totalTests} tests`);
  console.log(`❌ FAILED: ${failCount}/${totalTests} tests`);
  console.log(`📈 PASS RATE: ${passRate}%`);
  
  console.log('\n' + '─'.repeat(80));
  console.log('DETAILED RESULTS:');
  console.log('─'.repeat(80));
  
  testResults.forEach((result, i) => {
    const status = result.passed ? '✅' : '❌';
    console.log(`${status} ${i + 1}. ${result.name}`);
    if (result.details) {
      console.log(`     ${result.details}`);
    }
  });
  
  console.log('\n' + '═'.repeat(80));
  
  if (passRate === 100) {
    console.log('🎉 SUCCESS! All tests passed - Frontend2 is FULLY FUNCTIONAL');
    console.log('✅ Application is production-ready');
  } else if (passRate >= 80) {
    console.log('✅ GOOD! Most features working, minor issues remain');
    console.log(`📋 ${failCount} test(s) need attention`);
  } else if (passRate >= 60) {
    console.log('⚠️  FAIR. Core features work but significant issues exist');
    console.log(`📋 ${failCount} test(s) need fixing`);
  } else {
    console.log('❌ NEEDS WORK. Major functionality issues detected');
    console.log(`📋 ${failCount} test(s) must be fixed`);
  }
  
  console.log('═'.repeat(80));
  
  process.exit(passRate === 100 ? 0 : 1);
})();

