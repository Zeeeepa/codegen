# Complete Example: PRD → Implementation Flow

This document shows a **complete end-to-end example** of using the Iris-enhanced frontend to implement a feature.

---

## 🎯 Example Feature: User Profile Settings Page

### Step 1: Create PRD

```markdown
# PRD: User Profile Settings Page

## Overview
Allow users to view and edit their profile information including name, email, avatar, and preferences.

## Requirements

### Functional
- Display current user profile data
- Allow editing: name, email, bio, avatar upload
- Validate inputs (email format, name length)
- Save changes with confirmation
- Cancel button reverts changes
- Show loading state during save
- Display success/error messages

### Non-Functional
- Mobile-responsive design
- Accessible (WCAG AA)
- Save within 2 seconds
- Profile picture < 5MB

## Design
- Use existing design system (Tailwind + lucide-react icons)
- Form layout: 2-column on desktop, 1-column on mobile
- Avatar: Circular, 128px diameter
- Buttons: Primary (Save), Secondary (Cancel)

## Technical
- TypeScript + React
- Zustand for state
- API endpoint: PATCH /api/v1/profile
- Form validation with Zod
```

---

### Step 2: Select Repository

In the frontend UI:
1. Navigate to "PRD to Implementation" tab
2. Select repository from dropdown: `your-org/your-repo`
3. Paste PRD into editor
4. Click **"Implement"** button

---

### Step 3: Watch Agent Chain Execute

#### **Agent 1: Developer** (5 minutes)

**Task sent to Codegen API**:
```
Implement the following feature based on the PRD:

[PRD content here]

Requirements:
- Follow all specifications in the PRD
- Write clean, maintainable code
- Include inline comments for complex logic
- Follow project conventions and patterns
```

**Context sent**:
```json
{
  "prd": "[Full PRD text]",
  "templates": {
    "codingStandards": "Follow TypeScript best practices",
    "testingRequirements": "Include unit tests for all functions"
  },
  "metadata": {
    "repository": "your-org/your-repo",
    "chainId": "chain-1702564800000"
  }
}
```

**Agent creates**:
- `src/components/ProfileSettings.tsx` - Main component
- `src/services/profileApi.ts` - API client
- `src/schemas/profile.ts` - Zod validation
- `tests/unit/ProfileSettings.test.tsx` - Unit tests

**Agent output** (stored in `context.previousResult`):
```
Implementation complete. Created ProfileSettings component with:
- Form validation using Zod
- Avatar upload with preview
- Save/Cancel functionality
- Loading states and error handling
- Mobile-responsive layout
- 12 unit tests (100% coverage)

Files created:
- src/components/ProfileSettings.tsx (287 lines)
- src/services/profileApi.ts (45 lines)
- src/schemas/profile.ts (28 lines)
- tests/unit/ProfileSettings.test.tsx (156 lines)
```

**Frontend polls status every 2s**:
```typescript
// Poll loop
const status = await getAgentRunStatus(orgId, token, agentRunId);
if (status === "completed") {
  // Status changed! Proceed to next agent
}
```

---

#### **Agent 2: Visual Testing** (3 minutes)

**Task sent**:
```
Review the implemented feature for visual quality and UX:

Previous implementation result:
[Developer agent output]

Check for:
- UI consistency with design system
- Responsive behavior on mobile/tablet/desktop
- Accessibility (WCAG AA compliance)
- User experience flow
- Visual bugs or glitches
```

**Context sent**:
```json
{
  "prd": "[Full PRD]",
  "previousResult": "[Developer output]",
  "templates": {
    "designSystem": "Use Tailwind CSS with our custom theme",
    "accessibilityChecklist": "ARIA labels, keyboard navigation, screen reader support"
  }
}
```

**Agent output**:
```
Visual Testing Report:

✅ Passed:
- Design system compliance (Tailwind classes correct)
- Responsive at 375px, 768px, 1920px
- ARIA labels present on all inputs
- Keyboard navigation functional
- Color contrast ratios meet WCAG AA

⚠️ Warnings:
- Avatar preview could use skeleton loader
- Form could benefit from autofocus on name field

❌ No critical issues

Recommendation: Add skeleton loader for better perceived performance

Approval Status: APPROVED_WITH_WARNINGS
```

---

#### **Agent 3: Validator** (4 minutes)

**Task sent**:
```
Test the feature with real-life scenarios and edge cases:

Previous results:
Implementation: [Developer output]
Visual testing: [Visual testing output]

Test scenarios:
- Normal use cases
- Edge cases (empty data, large datasets, special characters)
- Error handling (network failures, validation errors)
- Performance under load

Report any issues found.
```

**Agent tests**:
- ✅ Normal profile update
- ✅ Empty bio (should be allowed)
- ✅ Invalid email format (rejected correctly)
- ✅ Name with special characters (handled)
- ✅ Avatar > 5MB (rejected correctly)
- ✅ Network timeout (error shown)
- ✅ Concurrent updates (last write wins)

**Agent output**:
```
Validation Report:

✅ All test scenarios passed

Test Results:
- Normal use: ✓
- Edge cases: ✓ (7/7 passed)
- Error handling: ✓
- Performance: ✓ (save in 1.2s avg)

No errors detected. Feature ready for PR.
```

---

#### **Agent 4: Debugging** (SKIPPED)

**Condition check**:
```typescript
condition: (ctx) => !!ctx.previousError
```

Since `previousError` is `undefined`, this agent is **skipped automatically**.

---

#### **Agent 5: PR Agent** (2 minutes)

**Task sent**:
```
Create a pull request for this feature:

Feature summary: [PRD title]
Implementation details: [Developer output]
Testing results: [Validator output]

PR should include:
- Clear title and description
- Summary of changes
- Testing evidence
- Screenshots/demos if applicable
- Link to relevant issues
```

**Agent creates PR**:
```
Title: feat: Add user profile settings page

Description:
## What Changed
- Added ProfileSettings component with full CRUD
- Implemented avatar upload with 5MB limit
- Added form validation with Zod
- Created 12 unit tests (100% coverage)

## Why
Implements user story #123: Allow users to edit profile

## Testing
✅ Unit tests: 12/12 passing
✅ Visual testing: Approved with minor warnings
✅ Validation testing: All scenarios passed
✅ Responsive: Mobile, tablet, desktop
✅ Accessible: WCAG AA compliant

## Screenshots
[Avatar upload demo]
[Mobile responsive layout]

PR #456 created: https://github.com/your-org/your-repo/pull/456
```

---

#### **Agent 6: Commit Agent** (1 minute)

**Task sent**:
```
Commit all changes with proper commit messages:

Follow conventional commits format:
- feat: new feature
- fix: bug fix
- refactor: code refactoring
- test: test updates
- docs: documentation

Commit message should be descriptive and reference the PR.
```

**Agent creates commits**:
```
feat: add ProfileSettings component

- Implement profile editing form
- Add avatar upload functionality
- Include Zod validation
- Add unit tests

Related to PR #456
```

---

#### **Agent 7: Reflection** (2 minutes)

**Task sent**:
```
Perform a self-review of the entire implementation:

Review areas:
- Code quality and maintainability
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations

Provide honest assessment and improvement suggestions.
```

**Agent output**:
```
Reflection Report:

Code Quality: ⭐⭐⭐⭐⭐
- Clean TypeScript code
- Proper component composition
- Good separation of concerns

Test Coverage: ⭐⭐⭐⭐⭐
- 100% coverage on core logic
- Edge cases well tested
- Integration tests would be beneficial

Documentation: ⭐⭐⭐⭐☆
- Inline comments clear
- README updated
- Could add JSDoc for public APIs

Performance: ⭐⭐⭐⭐☆
- Fast initial render
- Form optimistic updates
- Avatar upload could be optimized (use compression)

Security: ⭐⭐⭐⭐⭐
- File upload validated server-side
- XSS prevention in place
- CSRF token included

Improvement Suggestions:
1. Add image compression before upload
2. Consider lazy loading for settings tabs
3. Add JSDoc comments for component props
```

---

#### **Agent 8: Validation** (2 minutes)

**Task sent**:
```
Final validation before marking as complete:

Checklist:
- ✓ All requirements from PRD implemented
- ✓ Tests passing
- ✓ Code reviewed
- ✓ Documentation updated
- ✓ PR created and linked
- ✓ No critical issues

Provide final approval or list blocking issues.
```

**Agent output**:
```
Final Validation Report:

Checklist Status:
✅ All PRD requirements implemented
✅ Unit tests: 12/12 passing
✅ Visual testing: Approved
✅ Validation testing: All scenarios passed
✅ Code review: Self-reviewed, high quality
✅ Documentation: README and inline comments
✅ PR #456: Created and linked
✅ No critical issues

🎉 FINAL APPROVAL GRANTED

Feature is production-ready. Recommend merge after human review of PR #456.

Summary:
- Implementation time: ~15 minutes (agent time)
- Quality score: 94/100
- Test coverage: 100%
- Performance: Excellent
- Security: Excellent

Outstanding minor improvements (non-blocking):
1. Add image compression (Performance +5%)
2. Add JSDoc comments (Documentation +5%)
```

---

## Step 4: View Results

### In the Frontend UI

The user sees:

```
✅ Feature Implementation Complete!

Execution Summary:
- Total time: 19 minutes
- Agents: 7/8 executed (1 skipped)
- Status: SUCCESS

Results:
✅ Developer Agent (5m 23s)
✅ Visual Testing Agent (3m 12s)
✅ Validator Agent (4m 08s)
⏭️ Debugging Agent (skipped - no errors)
✅ PR Agent (2m 03s)
✅ Commit Agent (1m 15s)
✅ Reflection Agent (2m 34s)
✅ Validation Agent (1m 56s)

Next Steps:
1. Review PR #456: https://github.com/your-org/your-repo/pull/456
2. Merge PR when approved
3. Deploy to staging
```

---

## 🎉 Success!

The feature is **fully implemented**, **tested**, **documented**, and **PR created** - all in **~20 minutes** with **zero manual intervention**.

The user just:
1. ✍️ Wrote PRD
2. 🖱️ Clicked "Implement"
3. ☕ Grabbed coffee
4. ✅ Reviewed PR

The agents did:
- Code implementation
- Visual testing
- Validation testing
- Error fixing (if needed)
- PR creation
- Commits
- Self-review
- Final approval

---

## 🔑 Key Insights

### Why This Works

1. **Simple Pattern**: Poll → Wait → Resume
   - No complex orchestration
   - Just REST API calls
   - Easy to debug

2. **Context Passing**: Each agent gets previous results
   - `previousResult` = output of last agent
   - `previousError` = errors detected
   - `templates` = standards and guidelines

3. **Conditional Execution**: Debugging agent only runs if errors
   - Smart branching
   - No wasted work

4. **Real-Time Monitoring**: User sees progress live
   - State updates every 2s
   - Clear status indicators
   - Detailed logs

5. **Production-Ready**: All quality gates covered
   - Testing (unit, visual, validation)
   - Code review (reflection agent)
   - Documentation
   - PR creation

---

## 📈 Performance Metrics

From this example:

| Metric | Value |
|--------|-------|
| **Total Time** | 19 minutes |
| **Manual Work** | 2 minutes (write PRD) |
| **Automated Work** | 17 minutes (agents) |
| **Time Saved** | 2-3 hours (vs. manual) |
| **Quality Score** | 94/100 |
| **Test Coverage** | 100% |
| **Bugs Found** | 0 |

**ROI**: 6-9x time savings with higher quality!

---

**This is the power of agent chaining! 🚀**

