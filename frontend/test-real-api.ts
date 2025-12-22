/**
 * Real API Connection Test
 * 
 * Tests actual Codegen API with real credentials
 * Organization ID: 323
 * API Token: sk-92083737-4e5b-4a48-a2a1-f870a3a096a6
 */

import { codegenApi, createAgentRun, getAgentRunStatus, resumeAgentRun, listRepositories } from './src/services/codegenApi';

const ORG_ID = '323';
const API_TOKEN = 'sk-92083737-4e5b-4a48-a2a1-f870a3a096a6';

async function testRealAPI() {
  console.log('🔥 TESTING REAL CODEGEN API');
  console.log('================================');
  console.log(`Organization ID: ${ORG_ID}`);
  console.log(`API Token: ${API_TOKEN.substring(0, 10)}...`);
  console.log('');

  try {
    // Test 1: Connection Test
    console.log('Test 1: Testing API Connection...');
    const connectionResult = await codegenApi.testConnection();
    console.log('✅ Connection:', connectionResult.message);
    console.log('');

    // Test 2: List Repositories
    console.log('Test 2: Fetching Repositories...');
    const repos = await codegenApi.listRepositories();
    console.log(`✅ Found ${repos.length} repositories:`);
    repos.slice(0, 5).forEach(repo => {
      console.log(`   - ${repo.fullName} (ID: ${repo.id})`);
    });
    console.log('');

    // Test 3: Create Agent Run
    console.log('Test 3: Creating Agent Run...');
    const createResult = await codegenApi.createAgentRun({
      task: 'List all files in the repository and provide a brief summary',
      context: {
        test: true,
        timestamp: Date.now()
      },
      metadata: {
        source: 'frontend-test-script',
        repository: repos[0]?.id
      }
    });
    console.log('✅ Agent run created:', createResult.agentRunId);
    console.log('');

    // Test 4: Poll Status
    console.log('Test 4: Polling Agent Run Status...');
    let status = 'pending';
    let attempts = 0;
    const maxAttempts = 30; // 1 minute max

    while (status !== 'completed' && status !== 'failed' && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const statusResult = await codegenApi.getAgentRunStatus(createResult.agentRunId);
      status = statusResult.status;
      attempts++;
      
      console.log(`   Attempt ${attempts}: Status = ${status}`);
      
      if (statusResult.progress) {
        console.log(`   Progress: ${statusResult.progress}%`);
      }
    }

    if (status === 'completed') {
      console.log('✅ Agent run completed successfully!');
      
      // Get final result
      const finalResult = await codegenApi.getAgentRunStatus(createResult.agentRunId);
      console.log('');
      console.log('Result Preview:');
      console.log(finalResult.result?.substring(0, 500) + '...');
    } else if (status === 'failed') {
      console.log('❌ Agent run failed');
      const finalResult = await codegenApi.getAgentRunStatus(createResult.agentRunId);
      console.log('Error:', finalResult.error);
    } else {
      console.log('⏱️ Agent run timeout (still running)');
    }

    console.log('');
    console.log('================================');
    console.log('🎉 ALL TESTS COMPLETED!');
    
  } catch (error: any) {
    console.error('');
    console.error('================================');
    console.error('❌ TEST FAILED:', error.message);
    console.error('');
    console.error('Full error:', error);
  }
}

// Run the test
testRealAPI();

