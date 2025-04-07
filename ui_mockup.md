# PR Review Bot UI Mockup

## Overview

This document presents a UI mockup for the PR Review Bot dashboard, designed to provide better visibility into the bot's operations, clear error states, and actionable feedback for users.

## Dashboard Layout

```
+----------------------------------------------------------------------+
|                         PR REVIEW BOT DASHBOARD                       |
+----------------------------------------------------------------------+
| [Status: Running ✅] | [Repositories: 7] | [Last Check: 2 mins ago]  |
+----------------------------------------------------------------------+
|                                                                      |
|  +------------------------+  +----------------------------------+    |
|  |   RECENT ACTIVITY      |  |   REPOSITORY HEALTH              |    |
|  +------------------------+  +----------------------------------+    |
|  | • PR #123 created      |  | ✅ codegen: Healthy              |    |
|  | • PR #120 reviewed     |  | ✅ bolt-chat: Healthy            |    |
|  | • PR #118 merged       |  | ⚠️ agentgen: 2 errors            |    |
|  | • Branch monitor error |  | ✅ langgraph-slackbot: Healthy   |    |
|  | • PR #115 reviewed     |  | ⚠️ mcp-index: 1 warning          |    |
|  +------------------------+  +----------------------------------+    |
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   ACTIVE BRANCHES                                                ||
|  +------------------------------------------------------------------+|
|  | REPOSITORY | BRANCH                | STATUS        | ACTIONS     ||
|  |------------|----------------------|---------------|-------------||
|  | codegen    | feature/new-ui       | PR #123 Open  | [View PR]   ||
|  | agentgen   | fix/datetime-issue   | PR #45 Open   | [View PR]   ||
|  | bolt-chat  | gen/33d8dcdc-9a6b... | ❌ No commits | [Details]   ||
|  | mcp-index  | feature/search       | PR #67 Merged | [View PR]   ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   ERROR LOG                                                      ||
|  +------------------------------------------------------------------+|
|  | ❌ Error processing branch gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365 |
|  | in Zeeeepa/codegen: No commits between main and branch           ||
|  | [Expand Details] [Retry] [Dismiss]                               ||
|  |                                                                  ||
|  | ⚠️ Warning: Can't compare offset-naive and offset-aware datetimes ||
|  | in Zeeeepa/agentgen when processing PR #42                       ||
|  | [Expand Details] [Fix Automatically] [Dismiss]                   ||
|  +------------------------------------------------------------------+|
|                                                                      |
+----------------------------------------------------------------------+
|  [Settings]  [Run Manual Check]  [Generate Report]  [View Logs]      |
+----------------------------------------------------------------------+
```

## Error Details Modal

When a user clicks on [Details] or [Expand Details] for an error:

```
+----------------------------------------------------------------------+
|                         ERROR DETAILS                                 |
+----------------------------------------------------------------------+
| ❌ Error processing branch gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365   |
| in Zeeeepa/codegen                                                   |
+----------------------------------------------------------------------+
|                                                                      |
| Error Type: GitHub Validation Error                                  |
| Status Code: 422                                                     |
|                                                                      |
| Message: Validation Failed: No commits between main and              |
| gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365                            |
|                                                                      |
| Timestamp: 2025-04-07 12:00:54,356                                   |
|                                                                      |
| Stacktrace:                                                          |
| Traceback (most recent call last):                                   |
|   File "/home/l/codegen/pr_review_bot/pr_review_bot/monitors/branch_m|
|   onitor.py", line 208, in process_new_branch                        |
|     pr = self.github_client.create_pull_request(                     |
|         repo=repo,                                                   |
|     ...                                                              |
|                                                                      |
| Recommended Action:                                                  |
| This branch has no commits compared to the main branch. Consider:    |
| - Adding commits to this branch before creating a PR                 |
| - Deleting this branch if it's no longer needed                      |
| - Checking if this branch was created by mistake                     |
|                                                                      |
+----------------------------------------------------------------------+
|  [Ignore Branch]  [Delete Branch]  [Retry Later]  [Close]            |
+----------------------------------------------------------------------+
```

## Repository Details View

When a user clicks on a repository name:

```
+----------------------------------------------------------------------+
|                         REPOSITORY: CODEGEN                           |
+----------------------------------------------------------------------+
| [Status: Monitored ✅] | [Branches: 12] | [Open PRs: 3]              |
+----------------------------------------------------------------------+
|                                                                      |
|  +------------------------+  +----------------------------------+    |
|  |   BRANCH ACTIVITY      |  |   PR STATISTICS                  |    |
|  +------------------------+  +----------------------------------+    |
|  | • 2 new branches today |  | • 3 open PRs                     |    |
|  | • 1 PR created today   |  | • 5 merged in last 7 days        |    |
|  | • 2 PRs merged today   |  | • Avg review time: 4.2 hours     |    |
|  +------------------------+  +----------------------------------+    |
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   ACTIVE BRANCHES                                                ||
|  +------------------------------------------------------------------+|
|  | BRANCH                | CREATED       | STATUS        | ACTIONS  ||
|  |----------------------|---------------|---------------|----------||
|  | feature/new-ui       | 2 hours ago   | PR #123 Open  | [View]   ||
|  | fix/auth-issue       | 1 day ago     | PR #120 Open  | [View]   ||
|  | gen/33d8dcdc-9a6b... | 3 hours ago   | ❌ No commits | [Details]||
|  | feature/analytics    | 5 days ago    | PR #115 Merged| [View]   ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   RECENT ERRORS                                                  ||
|  +------------------------------------------------------------------+|
|  | ❌ Error processing branch gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365 |
|  | No commits between main and branch                               ||
|  | 2025-04-07 12:00:54                                              ||
|  | [Expand Details] [Retry] [Dismiss]                               ||
|  +------------------------------------------------------------------+|
|                                                                      |
+----------------------------------------------------------------------+
|  [Run Manual Check]  [Generate Report]  [View All Branches]          |
+----------------------------------------------------------------------+
```

## Settings Page

```
+----------------------------------------------------------------------+
|                         PR REVIEW BOT SETTINGS                        |
+----------------------------------------------------------------------+
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   GENERAL SETTINGS                                               ||
|  +------------------------------------------------------------------+|
|  | Check Interval:      [5] minutes                                 ||
|  | Auto-create PRs:     [✓] Enabled                                 ||
|  | Auto-review PRs:     [✓] Enabled                                 ||
|  | Auto-merge PRs:      [ ] Disabled                                ||
|  | Slack Notifications: [✓] Enabled                                 ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   REPOSITORY SETTINGS                                            ||
|  +------------------------------------------------------------------+|
|  | REPOSITORY          | MONITORED | AUTO-PR | AUTO-REVIEW | NOTIFY ||
|  |--------------------|-----------|---------|------------|--------||
|  | codegen            | [✓]       | [✓]     | [✓]        | [✓]    ||
|  | bolt-chat          | [✓]       | [✓]     | [✓]        | [✓]    ||
|  | agentgen           | [✓]       | [✓]     | [✓]        | [✓]    ||
|  | mcp-index          | [✓]       | [✓]     | [✓]        | [✓]    ||
|  | langgraph-slackbot | [✓]       | [✓]     | [✓]        | [✓]    ||
|  | [+ Add Repository]                                               ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   NOTIFICATION SETTINGS                                          ||
|  +------------------------------------------------------------------+|
|  | Slack Channel:      [#pr-reviews]                                ||
|  | Notify on:                                                       ||
|  | [✓] New branch detected                                          ||
|  | [✓] PR created                                                   ||
|  | [✓] PR reviewed                                                  ||
|  | [✓] PR merged                                                    ||
|  | [✓] Errors                                                       ||
|  +------------------------------------------------------------------+|
|                                                                      |
|  +------------------------------------------------------------------+|
|  |   ERROR HANDLING                                                 ||
|  +------------------------------------------------------------------+|
|  | [✓] Auto-fix timezone comparison issues                          ||
|  | [✓] Skip branches with no commits                                ||
|  | [✓] Retry failed operations (max attempts: [3])                  ||
|  | [✓] Log detailed error information                               ||
|  +------------------------------------------------------------------+|
|                                                                      |
+----------------------------------------------------------------------+
|  [Save Changes]  [Reset to Defaults]  [Test Configuration]           |
+----------------------------------------------------------------------+
```

## Slack Notification Templates

### Error Notification

```
🚨 *PR Review Bot Error*
*Repository:* Zeeeepa/codegen
*Branch:* gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365
*Error:* No commits between main and branch

*Details:*
```
Validation Failed: 422 {"message": "Validation Failed", "errors": [{"resource": "PullRequest", "code": "custom", "message": "No commits between main and gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365"}], "documentation_url": "https://docs.github.com/rest/pulls/pulls#create-a-pull-request", "status": "422"}
```

*Recommended Action:*
This branch has no commits compared to the main branch. Consider adding commits to this branch before creating a PR.

[View Branch](https://github.com/Zeeeepa/codegen/tree/gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365) | [View Dashboard](https://pr-review-bot.example.com/dashboard)
```

### PR Created Notification

```
🎉 *New PR Created*
*Repository:* Zeeeepa/codegen
*PR:* #123 - Add new feature
*Branch:* feature/new-ui
*Created by:* PR Review Bot

The PR has been automatically created from a new branch. Review will begin shortly.

[View PR](https://github.com/Zeeeepa/codegen/pull/123) | [View Dashboard](https://pr-review-bot.example.com/dashboard)
```

## Implementation Notes

1. **Dashboard**
   - Real-time status indicators for bot operation
   - Clear visualization of repository health
   - Actionable error messages with context
   - Quick access to recent activity

2. **Error Handling**
   - Detailed error information with context
   - Recommended actions for common errors
   - Options to retry, ignore, or fix issues
   - Visual indicators for error severity

3. **Repository Views**
   - Branch activity tracking
   - PR statistics and metrics
   - Error history specific to each repository
   - Branch management tools

4. **Settings**
   - Granular control over bot behavior
   - Per-repository configuration
   - Notification preferences
   - Error handling strategies

5. **Notifications**
   - Formatted Slack messages with context
   - Links to relevant resources
   - Clear error descriptions
   - Actionable recommendations

This UI design addresses the specific issues encountered in the logs by:
1. Clearly showing branches with no commits and preventing PR creation attempts
2. Providing visibility into datetime comparison errors
3. Offering automatic fixes for common issues
4. Giving users actionable feedback on how to resolve problems
