# Agent Profiles System - Complete Guide

## Overview

The Agent Profiles system allows you to define specialized instructions, rules, and quality criteria for each agent in your workflow using simple markdown files. This enables clear, consistent guidance for agents across different stages of your autonomous development process.

## Quick Start

### 1. Create Default Profiles

```python
from codegen.agent_profiles import AgentProfileManager

# Create profile manager
manager = AgentProfileManager()

# Generate default profile templates
manager.create_default_profiles("./profiles")
```

This creates 7 default profiles in markdown format:
- `research_profile.md` - Discovery and research specialist
- `analysis_profile.md` - Technical feasibility analyst
- `implementation_profile.md` - Senior software engineer
- `test_profile.md` - Quality assurance engineer
- `fix_profile.md` - Bug fix specialist
- `benchmark_profile.md` - Performance engineer
- `integration_profile.md` - Integration decision maker

### 2. Load Profiles

```python
# Load all profiles from directory
profiles = manager.load_profiles("./profiles")

print(f"Loaded {len(profiles)} profiles")
# Output: Loaded 7 profiles
```

### 3. Use Profiles with Infinity Loop

```python
from codegen.infinity_loop import InfinityLoopOrchestrator

# Create orchestrator with profiles
orch = InfinityLoopOrchestrator(
    api_key="your-api-key",
    org_id=323,
    profiles=profiles  # Assign loaded profiles
)

# Run loop - agents will use profile instructions
execution = await orch.run_loop("Improve database performance")
```

### 4. Use Profiles with Individual Agents

```python
from codegen.infinity_loop import ResearchAgent

# Get specific profile
research_profile = profiles["research"]

# Create agent with profile
agent = ResearchAgent(
    api_key="your-api-key", 
    org_id=323,
    profile=research_profile
)

# Execute - profile instructions auto-injected
result = await agent.research("Find best caching libraries")
```

## Profile Structure

Each profile is a markdown file with standardized sections:

```markdown
# Profile: profile_name

## Role
Description of the agent's specialized role and purpose

## Instructions
Detailed step-by-step instructions for the agent's tasks:
1. First step with description
2. Second step with details
3. Third step with guidance
...

## Rules
- Rule 1: Specific constraint or requirement
- Rule 2: Another important rule
- Rule 3: Quality standard
...

## Output Format
Expected output structure, can include:
- Markdown template
- JSON schema
- Specific sections required
...

## Quality Criteria
- Criterion 1: How success is measured
- Criterion 2: Quality standard
- Criterion 3: Validation check
...
```

## Default Profiles Included

### 1. Research Profile

**Role**: Discovery and Research Specialist

**Key Focus**:
- Analyze current state and identify bottlenecks
- Discover state-of-the-art solutions
- Benchmark competition
- Prioritize by impact and feasibility

**Rules** (6):
- Always cite sources with links
- Include quantitative metrics
- Compare at least 3 alternatives
- Consider technical and business impact
- Identify risks and trade-offs
- Keep recommendations actionable

**Output**: Research report with executive summary, analysis, solutions, and recommendations

### 2. Analysis Profile

**Role**: Technical Feasibility Analyst

**Key Focus**:
- Validate technical compatibility
- Estimate development effort
- Identify risks and dependencies
- Design implementation strategy

**Rules** (6):
- Validate against existing tech stack
- Provide realistic time estimates
- Identify external dependencies
- Consider rollback strategy
- Assess monitoring requirements
- Flag security/compliance issues

**Output**: Feasibility analysis with technical assessment, effort estimation, risks, and go/no-go recommendation

### 3. Implementation Profile

**Role**: Senior Software Engineer

**Key Focus**:
- Generate clean, maintainable code
- Write comprehensive tests
- Add thorough documentation
- Implement error handling
- Follow best practices

**Rules** (9):
- Follow existing code style
- Write self-documenting code
- Include comprehensive error handling
- Aim for 80%+ test coverage
- Document all public APIs
- Use type hints/annotations
- Consider edge cases
- No hardcoded values
- Security first (validate inputs, sanitize outputs)

**Output**: Implementation with code, tests, documentation, and usage examples

### 4. Test Profile

**Role**: Quality Assurance Engineer

**Key Focus**:
- Functional testing (all features)
- Performance testing (response times, resources)
- Security testing (vulnerabilities)
- Edge case testing (boundaries, errors)
- Integration testing (dependencies)

**Rules** (8):
- Test happy paths and error paths
- Include boundary value testing
- Test with realistic data volumes
- Verify error messages are helpful
- Check security vulnerabilities (SQL injection, XSS, etc.)
- Measure performance under load
- Test rollback/recovery
- Validate outputs and side effects

**Output**: Test report with summary, functional/performance/security tests, issues found, and pass/fail recommendation

### 5. Fix Profile

**Role**: Bug Fix Specialist

**Key Focus**:
- Root cause analysis
- Impact assessment
- Minimal, targeted fixes
- Validation without side effects
- Prevention strategies

**Rules** (8):
- Reproduce issue first
- Fix root cause, not symptoms
- Keep fixes minimal and focused
- Add regression tests
- Update error messages if needed
- Consider impact on existing functionality
- Validate no new breakage
- Document what and why

**Output**: Bug fix report with root cause, fix description, changes, testing, and prevention strategy

### 6. Benchmark Profile

**Role**: Performance Engineer

**Key Focus**:
- Baseline measurement
- Test under realistic load
- Compare results vs baseline
- Track resource utilization
- Check for regressions

**Rules** (8):
- Use realistic test data
- Measure multiple runs (averages)
- Track improvements AND regressions
- Test different load levels
- Measure CPU, memory, I/O usage
- Check for memory/resource leaks
- Validate caching behavior
- Test scalability

**Output**: Benchmark report with baseline metrics, new metrics, improvement percentages, and accept/reject recommendation

### 7. Integration Profile

**Role**: Integration Decision Maker

**Key Focus**:
- Quality gate review
- Business and technical impact
- Deployment risk assessment
- Documentation verification
- Final go/no-go decision

**Rules** (8):
- All tests must pass (no exceptions)
- Performance must meet/exceed baseline
- Security vulnerabilities resolved
- Documentation complete
- Rollback plan exists
- Breaking changes documented
- Improvement exceeds 5% threshold
- Code follows team conventions

**Output**: Integration decision with quality assessment, impact analysis, risk assessment, and clear decision with reasoning

## Creating Custom Profiles

### Example: Custom "Security Audit" Profile

Create `profiles/security_audit_profile.md`:

```markdown
# Profile: security_audit

## Role
Security Audit Specialist - Identifies security vulnerabilities, assesses risk, and recommends mitigations.

## Instructions
Your task is to perform comprehensive security audit:

1. **Code Analysis**: Review code for common vulnerabilities (OWASP Top 10)
2. **Dependency Check**: Scan dependencies for known CVEs
3. **Configuration Review**: Check security configurations
4. **Access Control**: Verify authentication and authorization
5. **Data Protection**: Validate encryption and sensitive data handling

## Rules
- Check against OWASP Top 10
- Scan all dependencies for CVEs
- Verify input validation and sanitization
- Check for hardcoded secrets
- Assess authentication mechanisms
- Review authorization logic
- Validate encryption usage
- Check for SQL injection vulnerabilities

## Output Format
```
# Security Audit Report: [Component]

## Vulnerabilities Found
### Critical
- Vulnerability 1: [Description with CVE if applicable]
  - Impact: [Description]
  - Remediation: [Steps]

### High
...

## Dependencies
- Package 1: [Version] - [CVEs found]

## Recommendations
1. Immediate actions
2. Short-term fixes
3. Long-term improvements

## Risk Score
Overall: [Critical/High/Medium/Low]
```

## Quality Criteria
- All OWASP Top 10 checked
- Dependency scan completed
- CVEs identified with severity
- Remediation steps provided
- Risk score assigned
- Prioritized action plan
```

### Using Custom Profile

```python
# Load custom profile
manager = AgentProfileManager()
profiles = manager.load_profiles("./profiles")

# Access custom profile
security_profile = profiles["security_audit"]

# Use with agent
from codegen.infinity_loop import InfinityLoopAgent

agent = InfinityLoopAgent(
    api_key="key",
    org_id=323,
    profile=security_profile
)

# Execute with custom instructions
result = await agent.execute("Audit the authentication module")
```

## Advanced Usage

### Profile Inheritance (Manual)

While profiles don't support inheritance directly, you can create specialized versions:

```python
# Load base profile
base = manager.get_profile("research")

# Create specialized profile programmatically
from codegen.agent_profiles import AgentProfile

ml_research = AgentProfile(
    name="ml_research",
    role=base.role + " - Specialized in Machine Learning",
    instructions=base.instructions + "\n\nFocus specifically on ML/AI solutions.",
    rules=base.rules + [
        "Prioritize solutions with proven ML applications",
        "Include model performance metrics",
        "Consider training data requirements"
    ],
    output_format=base.output_format,
    quality_criteria=base.quality_criteria
)
```

### Dynamic Profile Loading

```python
import os

def load_project_profiles(project_name: str):
    """Load profiles for specific project."""
    profile_dir = f"./projects/{project_name}/profiles"
    
    if not os.path.exists(profile_dir):
        # Fall back to defaults
        profile_dir = "./profiles"
    
    manager = AgentProfileManager()
    return manager.load_profiles(profile_dir)

# Use project-specific profiles
profiles = load_project_profiles("backend-api")
```

### Profile Validation

```python
def validate_profile(profile: AgentProfile) -> bool:
    """Validate profile has required components."""
    if not profile.name:
        return False
    if not profile.role:
        return False
    if len(profile.rules) < 3:
        return False
    if len(profile.quality_criteria) < 2:
        return False
    return True

# Validate all loaded profiles
for name, profile in profiles.items():
    if not validate_profile(profile):
        print(f"Warning: Profile {name} may be incomplete")
```

## Best Practices

### 1. Keep Profiles Focused

Each profile should have a single, clear responsibility:
- ✅ Good: "Research Specialist - Discovers solutions"
- ❌ Bad: "Research and Implementation Specialist"

### 2. Define Measurable Quality Criteria

Use specific, measurable criteria:
- ✅ Good: "At least 3 solutions compared", "80%+ test coverage"
- ❌ Bad: "Good research", "Adequate testing"

### 3. Include Examples in Rules

Make rules concrete with examples:
- ✅ Good: "Always cite sources with links: [Source](url)"
- ❌ Bad: "Cite sources"

### 4. Update Profiles Based on Experience

Treat profiles as living documents:
```python
# After a sprint, review and update
# Add new rules that would have prevented issues
# Remove rules that proved unnecessary
# Clarify ambiguous instructions
```

### 5. Version Control Profiles

Store profiles in git alongside code:
```bash
git add profiles/*.md
git commit -m "Update research profile with ML focus"
```

## Integration with Council Orchestrator

Profiles can also be used with the Council Orchestrator for multi-model queries:

```python
from codegen.council_orchestrator import CouncilOrchestrator
from codegen.agent_profiles import AgentProfileManager

# Load profiles
manager = AgentProfileManager()
profiles = manager.load_profiles("./profiles")

# Create council
council = CouncilOrchestrator(token="key", org_id=323)

# Use research profile for all council agents
research_profile = profiles["research"]
query_with_profile = research_profile.format_instructions(
    "Find best DevOps tools"
)

# Execute council query with profile guidance
result = await council.query_council(query_with_profile, num_variations=3)
```

## Troubleshooting

### Profile Not Loading

```python
try:
    profiles = manager.load_profiles("./profiles")
except FileNotFoundError as e:
    print(f"Profile directory not found: {e}")
    # Create default profiles
    manager.create_default_profiles("./profiles")
    profiles = manager.load_profiles("./profiles")
```

### Profile Missing Sections

If a profile is missing sections, ProfileParser uses defaults:
- Missing role → "General purpose agent"
- Missing instructions → "Follow standard best practices"
- Missing rules → ["Follow instructions carefully"]
- Missing output format → "Structured response"
- Missing quality criteria → ["Accurate", "Complete"]

### Viewing Profile Contents

```python
# Inspect loaded profile
profile = profiles["research"]
print(f"Name: {profile.name}")
print(f"Role: {profile.role}")
print(f"Rules: {len(profile.rules)}")
for i, rule in enumerate(profile.rules, 1):
    print(f"  {i}. {rule}")
```

## Performance Considerations

- **Profile Loading**: Profiles are loaded once at initialization
- **Instruction Formatting**: Done per execution (minimal overhead)
- **Memory Usage**: ~1-2KB per profile
- **Recommendation**: Load profiles at application startup, reuse across requests

## Summary

Agent Profiles provide:
- ✅ Clear, consistent agent guidance
- ✅ Reusable instruction templates
- ✅ Quality standards enforcement
- ✅ Easy customization per project
- ✅ Version-controlled agent behavior

Get started:
```bash
# Install package
pip install -e .

# Generate default profiles
python -c "from codegen.agent_profiles import AgentProfileManager; AgentProfileManager().create_default_profiles('./profiles')"

# Use in your code
# See examples above
```

