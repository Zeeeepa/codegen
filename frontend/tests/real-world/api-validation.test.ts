/**
 * Real-World API Validation Test
 * Tests actual CodeGen API with real credentials
 * Organization ID: 323
 */

import axios from 'axios';

const ORG_ID = '323';
const API_TOKEN = process.env.CODEGEN_TOKEN || 'sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99';
const API_BASE_URL = 'https://api.codegen.com/v1';

interface AgentRunResponse {
  id: string;
  organization_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  web_url: string;
  result?: string;
  summary?: string;
  source_type: string;
  github_pull_requests?: Array<{
    number: number;
    url: string;
    title: string;
  }>;
  metadata?: Record<string, any>;
}

async function testCreateAgentRun(): Promise<AgentRunResponse> {
  console.log('🧪 Testing: Create Agent Run');
  console.log(`📍 Org ID: ${ORG_ID}`);
  console.log(`🔑 Token: ${API_TOKEN.substring(0, 10)}...`);
  
  try {
    const response = await axios.post<AgentRunResponse>(
      `${API_BASE_URL}/organizations/${ORG_ID}/agent/run`,
      {
        prompt: 'Test prompt from visual orchestration platform - analyzing codebase structure',
      },
      {
        headers: {
          Authorization: `Bearer ${API_TOKEN}`,
          'Content-Type': 'application/json',
        },
      }
    );

    console.log('✅ Agent run created successfully!');
    console.log(`   Run ID: ${response.data.id}`);
    console.log(`   Status: ${response.data.status}`);
    console.log(`   Web URL: ${response.data.web_url}`);
    console.log(`   Created: ${response.data.created_at}`);
    
    const requiredFields = ['id', 'organization_id', 'status', 'created_at', 'web_url'];
    const missingFields = requiredFields.filter(field => !(field in response.data));
    
    if (missingFields.length > 0) {
      console.warn(`⚠️  Missing fields: ${missingFields.join(', ')}`);
    } else {
      console.log('✅ All required fields present');
    }

    return response.data;
  } catch (error: any) {
    console.error('❌ Failed to create agent run');
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Error: ${JSON.stringify(error.response.data, null, 2)}`);
    } else {
      console.error(`   Error: ${error.message}`);
    }
    throw error;
  }
}

async function testGetAgentRunStatus(runId: string): Promise<AgentRunResponse> {
  console.log('\n🧪 Testing: Get Agent Run Status');
  console.log(`   Run ID: ${runId}`);
  
  try {
    const response = await axios.get<AgentRunResponse>(
      `${API_BASE_URL}/organizations/${ORG_ID}/agent/run/${runId}`,
      {
        headers: {
          Authorization: `Bearer ${API_TOKEN}`,
        },
      }
    );

    console.log('✅ Successfully retrieved status');
    console.log(`   Status: ${response.data.status}`);
    if (response.data.result) {
      console.log(`   Result: ${response.data.result.substring(0, 100)}...`);
    }
    
    return response.data;
  } catch (error: any) {
    console.error('❌ Failed to get status');
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Error: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    throw error;
  }
}

async function analyzeGaps(): Promise<{ gaps: string[]; gapCount: number }> {
  console.log('\n🔍 ANALYZING GAPS:\n');

  const gaps: string[] = [];
  
  console.log('1. Environment Variables');
  if (!process.env.CODEGEN_TOKEN) {
    gaps.push('❌ API token not in environment');
    console.log('   ❌ CODEGEN_TOKEN not found');
  } else {
    console.log('   ✅ CODEGEN_TOKEN found');
  }

  console.log('\n2. Error Recovery');
  gaps.push('⚠️  No retry logic for failures');
  gaps.push('⚠️  No exponential backoff for 429');
  console.log('   ⚠️  Missing: Automatic retry');
  console.log('   ⚠️  Missing: Exponential backoff');

  console.log('\n3. Visual Editor Integration');
  gaps.push('⚠️  WorkflowCanvas cannot trigger API');
  gaps.push('⚠️  No real-time status updates');
  console.log('   ⚠️  Missing: API integration in canvas');
  console.log('   ⚠️  Missing: WebSocket support');

  console.log('\n4. Context Passing');
  gaps.push('⚠️  Context not tested with real API');
  gaps.push('⚠️  Large context handling unvalidated');
  console.log('   ⚠️  Missing: Real context validation');

  console.log('\n5. Template System');
  gaps.push('⚠️  Templates cannot load to canvas');
  gaps.push('⚠️  No template selector UI');
  console.log('   ⚠️  Missing: Template converter');

  console.log('\n6. State Persistence');
  gaps.push('❌ Workflows not saved');
  gaps.push('❌ No workflow history');
  console.log('   ❌ Missing: Save to backend');
  console.log('   ❌ Missing: Load from state');

  console.log('\n7. Authentication');
  gaps.push('⚠️  Token management not user-friendly');
  gaps.push('⚠️  No org selector');
  console.log('   ⚠️  Missing: Settings page');

  console.log('\n8. Error UI');
  gaps.push('⚠️  API errors not in visual editor');
  gaps.push('⚠️  No toast notifications');
  console.log('   ⚠️  Missing: Error notifications');

  console.log('\n9. Performance');
  gaps.push('⚠️  Large workflows not tested');
  gaps.push('⚠️  No virtualization');
  console.log('   ⚠️  Missing: Performance testing');

  console.log('\n10. Production');
  gaps.push('❌ No Docker config');
  gaps.push('❌ No CI/CD');
  gaps.push('❌ No env config');
  console.log('   ❌ Missing: Dockerfile');
  console.log('   ❌ Missing: GitHub Actions');

  return { gaps, gapCount: gaps.length };
}

async function runTests(): Promise<void> {
  console.log('═══════════════════════════════════════════════════════');
  console.log('🌍 REAL-WORLD API VALIDATION');
  console.log('═══════════════════════════════════════════════════════\n');

  let runId: string | undefined;

  try {
    const createResult = await testCreateAgentRun();
    runId = createResult.id;

    console.log('\n⏳ Waiting 3 seconds...');
    await new Promise(resolve => setTimeout(resolve, 3000));

    if (runId) {
      await testGetAgentRunStatus(runId);
    }

    const { gaps, gapCount } = await analyzeGaps();

    console.log('\n═══════════════════════════════════════════════════════');
    console.log('📊 SUMMARY');
    console.log('═══════════════════════════════════════════════════════');
    console.log(`✅ API Connection: SUCCESS`);
    console.log(`✅ Agent Run: ${runId || 'N/A'}`);
    console.log(`⚠️  Gaps: ${gapCount}`);
    
    const criticalGaps = gaps.filter(g => g.startsWith('❌'));
    const warningGaps = gaps.filter(g => g.startsWith('⚠️'));
    
    console.log(`\n🔴 Critical (${criticalGaps.length}):`);
    criticalGaps.forEach(gap => console.log(`   ${gap}`));
    
    console.log(`\n🟡 Warnings (${warningGaps.length}):`);
    warningGaps.slice(0, 5).forEach(gap => console.log(`   ${gap}`));

    console.log('\n═══════════════════════════════════════════════════════');
    
  } catch (error) {
    console.log('\n═══════════════════════════════════════════════════════');
    console.log('❌ FAILED');
    console.log('═══════════════════════════════════════════════════════');
    throw error;
  }
}

runTests().catch(error => {
  console.error('\n💥 Failed:', error.message);
  process.exit(1);
});
