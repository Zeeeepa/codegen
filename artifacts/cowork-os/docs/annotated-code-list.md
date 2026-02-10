# CoWork-OS Code Files — macOS footprint map ([V]=macOS-specific usage, [X]=none)

- [X] build/entitlements.mac.plist
- [X] src/electron/activity/ActivityRepository.ts
- [X] src/electron/agent/__tests__/agent-result-summary-and-memory-retention.test.ts
- [X] src/electron/agent/__tests__/auto-commenter-skill.test.ts
- [X] src/electron/agent/__tests__/context-manager-compaction.test.ts
- [X] src/electron/agent/__tests__/conversation-snapshot.test.ts
- [X] src/electron/agent/__tests__/custom-skill-loader.test.ts
- [X] src/electron/agent/__tests__/daemon-transient-retry.test.ts
- [X] src/electron/agent/__tests__/executor-canvas-fallback.test.ts
- [X] src/electron/agent/__tests__/executor-step-failures.test.ts
- [X] src/electron/agent/__tests__/executor-transient-error.test.ts
- [X] src/electron/agent/__tests__/executor-workspace-classification.test.ts
- [X] src/electron/agent/__tests__/executor-workspace-preflight-ack.test.ts
- [X] src/electron/agent/__tests__/memory-kit-skill.test.ts
- [X] src/electron/agent/__tests__/pi-provider.test.ts
- [X] src/electron/agent/__tests__/queue-manager.test.ts
- [V] src/electron/agent/__tests__/skill-eligibility.test.ts
- [X] src/electron/agent/__tests__/skill-registry.test.ts
- [X] src/electron/agent/__tests__/termination-reason-context.test.ts
- [X] src/electron/agent/browser/browser-service.ts
- [X] src/electron/agent/context-manager.ts
- [X] src/electron/agent/custom-skill-loader.ts
- [X] src/electron/agent/daemon.ts
- [V] src/electron/agent/executor.ts
- [X] src/electron/agent/llm/__tests__/azure-openai-provider.test.ts
- [X] src/electron/agent/llm/__tests__/provider-factory-custom-config.test.ts
- [X] src/electron/agent/llm/__tests__/provider-factory-model-selection.test.ts
- [X] src/electron/agent/llm/anthropic-compatible-provider.ts
- [X] src/electron/agent/llm/anthropic-provider.ts
- [X] src/electron/agent/llm/azure-openai-provider.ts
- [X] src/electron/agent/llm/bedrock-provider.ts
- [X] src/electron/agent/llm/gemini-provider.ts
- [X] src/electron/agent/llm/github-copilot-provider.ts
- [X] src/electron/agent/llm/groq-provider.ts
- [X] src/electron/agent/llm/index.ts
- [X] src/electron/agent/llm/kimi-provider.ts
- [X] src/electron/agent/llm/ollama-provider.ts
- [X] src/electron/agent/llm/openai-compatible-provider.ts
- [X] src/electron/agent/llm/openai-compatible.ts
- [X] src/electron/agent/llm/openai-oauth.ts
- [X] src/electron/agent/llm/openai-provider.ts
- [X] src/electron/agent/llm/openrouter-provider.ts
- [X] src/electron/agent/llm/pi-provider.ts
- [X] src/electron/agent/llm/pricing.ts
- [X] src/electron/agent/llm/provider-factory.ts
- [X] src/electron/agent/llm/types.ts
- [X] src/electron/agent/llm/xai-provider.ts
- [X] src/electron/agent/queue-manager.ts
- [X] src/electron/agent/sandbox/docker-sandbox.ts
- [V] src/electron/agent/sandbox/macos-sandbox.ts
- [V] src/electron/agent/sandbox/runner.ts
- [V] src/electron/agent/sandbox/sandbox-factory.ts
- [X] src/electron/agent/sandbox/security-utils.ts
- [X] src/electron/agent/search/__tests__/provider-factory.test.ts
- [X] src/electron/agent/search/brave-provider.ts
- [X] src/electron/agent/search/google-provider.ts
- [X] src/electron/agent/search/index.ts
- [X] src/electron/agent/search/provider-factory.ts
- [X] src/electron/agent/search/serpapi-provider.ts
- [X] src/electron/agent/search/tavily-provider.ts
- [X] src/electron/agent/search/types.ts
- [X] src/electron/agent/security/index.ts
- [X] src/electron/agent/security/input-sanitizer.ts
- [X] src/electron/agent/security/output-filter.ts
- [X] src/electron/agent/skill-eligibility.ts
- [X] src/electron/agent/skill-registry.ts
- [X] src/electron/agent/skills/__tests__/image-generator-selection.test.ts
- [X] src/electron/agent/skills/__tests__/spreadsheet.test.ts
- [X] src/electron/agent/skills/document.ts
- [X] src/electron/agent/skills/image-generator.ts
- [X] src/electron/agent/skills/organizer.ts
- [X] src/electron/agent/skills/presentation.ts
- [X] src/electron/agent/skills/spreadsheet.ts
- [X] src/electron/agent/tools/__tests__/builtin-settings.test.ts
- [X] src/electron/agent/tools/__tests__/child-task-control.test.ts
- [X] src/electron/agent/tools/__tests__/edit-tools.test.ts
- [X] src/electron/agent/tools/__tests__/glob-tools.test.ts
- [X] src/electron/agent/tools/__tests__/google-workspace-error-boundary.test.ts
- [X] src/electron/agent/tools/__tests__/grep-tools.test.ts
- [X] src/electron/agent/tools/__tests__/integration-approval.test.ts
- [X] src/electron/agent/tools/__tests__/monty-tools.test.ts
- [X] src/electron/agent/tools/__tests__/personality-tools.test.ts
- [X] src/electron/agent/tools/__tests__/read-files.test.ts
- [X] src/electron/agent/tools/__tests__/search-tools.test.ts
- [X] src/electron/agent/tools/__tests__/shell-tools.test.ts
- [X] src/electron/agent/tools/__tests__/spawn-agent.test.ts
- [X] src/electron/agent/tools/__tests__/tool-restrictions.test.ts
- [X] src/electron/agent/tools/__tests__/use-skill.test.ts
- [X] src/electron/agent/tools/__tests__/visual-tools.test.ts
- [X] src/electron/agent/tools/__tests__/voice-call-tools.test.ts
- [X] src/electron/agent/tools/__tests__/web-fetch-tools.test.ts
- [X] src/electron/agent/tools/box-tools.ts
- [X] src/electron/agent/tools/browser-tools.ts
- [X] src/electron/agent/tools/builtin-settings.ts
- [X] src/electron/agent/tools/canvas-tools.ts
- [X] src/electron/agent/tools/channel-tools.ts
- [X] src/electron/agent/tools/cron-tools.ts
- [X] src/electron/agent/tools/dropbox-tools.ts
- [X] src/electron/agent/tools/edit-tools.ts
- [X] src/electron/agent/tools/email-imap-tools.ts
- [X] src/electron/agent/tools/file-tools.ts
- [X] src/electron/agent/tools/glob-tools.ts
- [X] src/electron/agent/tools/gmail-tools.ts
- [X] src/electron/agent/tools/google-calendar-tools.ts
- [X] src/electron/agent/tools/google-drive-tools.ts
- [X] src/electron/agent/tools/grep-tools.ts
- [X] src/electron/agent/tools/image-tools.ts
- [X] src/electron/agent/tools/mention-tools.ts
- [X] src/electron/agent/tools/monty-tools.ts
- [X] src/electron/agent/tools/node-tools.ts
- [X] src/electron/agent/tools/notion-tools.ts
- [X] src/electron/agent/tools/onedrive-tools.ts
- [X] src/electron/agent/tools/read-files.ts
- [V] src/electron/agent/tools/registry.ts
- [X] src/electron/agent/tools/search-tools.ts
- [X] src/electron/agent/tools/sharepoint-tools.ts
- [X] src/electron/agent/tools/shell-tools.ts
- [X] src/electron/agent/tools/skill-tools.ts
- [V] src/electron/agent/tools/system-tools.ts
- [X] src/electron/agent/tools/vision-tools.ts
- [X] src/electron/agent/tools/visual-tools.ts
- [X] src/electron/agent/tools/voice-call-tools.ts
- [X] src/electron/agent/tools/web-fetch-tools.ts
- [X] src/electron/agent/tools/x-tools.ts
- [X] src/electron/agents/AgentRoleRepository.ts
- [X] src/electron/agents/AgentTeamItemRepository.ts
- [X] src/electron/agents/AgentTeamMemberRepository.ts
- [X] src/electron/agents/AgentTeamOrchestrator.ts
- [X] src/electron/agents/AgentTeamRepository.ts
- [X] src/electron/agents/AgentTeamRunRepository.ts
- [X] src/electron/agents/CrossSignalService.ts
- [X] src/electron/agents/FeedbackService.ts
- [X] src/electron/agents/HeartbeatService.ts
- [X] src/electron/agents/MentionRepository.ts
- [X] src/electron/agents/TaskSubscriptionRepository.ts
- [X] src/electron/agents/WorkingStateRepository.ts
- [X] src/electron/agents/__tests__/AgentRoleRepository.test.ts
- [X] src/electron/agents/__tests__/AgentTeamOrchestrator.test.ts
- [X] src/electron/agents/__tests__/AgentTeamRepositories.test.ts
- [X] src/electron/agents/__tests__/HeartbeatService.test.ts
- [X] src/electron/agents/__tests__/MentionRepository.test.ts
- [X] src/electron/agents/__tests__/TaskSubscriptionRepository.test.ts
- [X] src/electron/agents/__tests__/WorkingStateRepository.test.ts
- [X] src/electron/agents/agent-dispatch.ts
- [X] src/electron/agents/mentions.ts
- [X] src/electron/canvas/canvas-manager.ts
- [X] src/electron/canvas/canvas-preload.ts
- [X] src/electron/canvas/canvas-protocol.ts
- [X] src/electron/canvas/canvas-store.ts
- [X] src/electron/canvas/index.ts
- [X] src/electron/control-plane/__tests__/client-edge-cases.test.ts
- [X] src/electron/control-plane/__tests__/client.test.ts
- [X] src/electron/control-plane/__tests__/node-manager.test.ts
- [X] src/electron/control-plane/__tests__/protocol-edge-cases.test.ts
- [X] src/electron/control-plane/__tests__/protocol.test.ts
- [X] src/electron/control-plane/__tests__/remote-client.test.ts
- [X] src/electron/control-plane/__tests__/server.test.ts
- [X] src/electron/control-plane/__tests__/settings.test.ts
- [X] src/electron/control-plane/__tests__/ssh-tunnel.test.ts
- [X] src/electron/control-plane/client.ts
- [X] src/electron/control-plane/handlers.ts
- [X] src/electron/control-plane/index.ts
- [X] src/electron/control-plane/node-manager.ts
- [X] src/electron/control-plane/protocol.ts
- [X] src/electron/control-plane/remote-client.ts
- [X] src/electron/control-plane/server.ts
- [X] src/electron/control-plane/settings.ts
- [X] src/electron/control-plane/ssh-tunnel.ts
- [X] src/electron/cron/__tests__/schedule.test.ts
- [X] src/electron/cron/__tests__/service.test.ts
- [X] src/electron/cron/__tests__/store.test.ts
- [X] src/electron/cron/__tests__/types.test.ts
- [X] src/electron/cron/index.ts
- [X] src/electron/cron/schedule.ts
- [X] src/electron/cron/service.ts
- [X] src/electron/cron/store.ts
- [X] src/electron/cron/types.ts
- [X] src/electron/cron/webhook.ts
- [X] src/electron/database/SecureSettingsRepository.ts
- [X] src/electron/database/TaskLabelRepository.ts
- [X] src/electron/database/__tests__/MemoryRepository.search.test.ts
- [V] src/electron/database/__tests__/SecureSettingsRepository.test.ts
- [X] src/electron/database/__tests__/TaskLabelRepository.test.ts
- [X] src/electron/database/__tests__/channel-user-repository.test.ts
- [X] src/electron/database/__tests__/repositories-agent.test.ts
- [X] src/electron/database/repositories.ts
- [X] src/electron/database/schema.ts
- [X] src/electron/extensions/__tests__/loader.test.ts
- [X] src/electron/extensions/index.ts
- [X] src/electron/extensions/loader.ts
- [X] src/electron/extensions/registry.ts
- [V] src/electron/extensions/types.ts
- [X] src/electron/gateway/__tests__/bluebubbles.test.ts
- [X] src/electron/gateway/__tests__/context-policy.test.ts
- [X] src/electron/gateway/__tests__/email.test.ts
- [X] src/electron/gateway/__tests__/gateway-cleanup.test.ts
- [X] src/electron/gateway/__tests__/gateway-daemon-listeners.test.ts
- [X] src/electron/gateway/__tests__/gateway-followups-persistence.test.ts
- [X] src/electron/gateway/__tests__/google-chat.test.ts
- [X] src/electron/gateway/__tests__/line.test.ts
- [X] src/electron/gateway/__tests__/matrix-direct-rooms.test.ts
- [X] src/electron/gateway/__tests__/matrix.test.ts
- [X] src/electron/gateway/__tests__/mattermost.test.ts
- [X] src/electron/gateway/__tests__/router-rules.test.ts
- [X] src/electron/gateway/__tests__/router-task-updates-log.test.ts
- [X] src/electron/gateway/__tests__/security-pending.test.ts
- [X] src/electron/gateway/__tests__/signal.test.ts
- [X] src/electron/gateway/__tests__/slack-isgroup.test.ts
- [X] src/electron/gateway/__tests__/teams.test.ts
- [X] src/electron/gateway/__tests__/tunnel.test.ts
- [X] src/electron/gateway/__tests__/twitch.test.ts
- [X] src/electron/gateway/__tests__/whatsapp-config.test.ts
- [V] src/electron/gateway/channel-registry.ts
- [X] src/electron/gateway/channels/bluebubbles-client.ts
- [X] src/electron/gateway/channels/bluebubbles.ts
- [X] src/electron/gateway/channels/discord.ts
- [X] src/electron/gateway/channels/email-client.ts
- [X] src/electron/gateway/channels/email.ts
- [X] src/electron/gateway/channels/google-chat.ts
- [X] src/electron/gateway/channels/imessage-client.ts
- [X] src/electron/gateway/channels/imessage.ts
- [X] src/electron/gateway/channels/index.ts
- [X] src/electron/gateway/channels/line-client.ts
- [X] src/electron/gateway/channels/line.ts
- [X] src/electron/gateway/channels/matrix-client.ts
- [X] src/electron/gateway/channels/matrix.ts
- [X] src/electron/gateway/channels/mattermost-client.ts
- [X] src/electron/gateway/channels/mattermost.ts
- [X] src/electron/gateway/channels/signal-client.ts
- [X] src/electron/gateway/channels/signal.ts
- [X] src/electron/gateway/channels/slack.ts
- [X] src/electron/gateway/channels/teams.ts
- [X] src/electron/gateway/channels/telegram.ts
- [X] src/electron/gateway/channels/twitch-client.ts
- [X] src/electron/gateway/channels/twitch.ts
- [X] src/electron/gateway/channels/types.ts
- [X] src/electron/gateway/channels/whatsapp.ts
- [X] src/electron/gateway/chat-transcript.ts
- [X] src/electron/gateway/context-policy.ts
- [X] src/electron/gateway/index.ts
- [X] src/electron/gateway/infrastructure.test.ts
- [X] src/electron/gateway/infrastructure.ts
- [X] src/electron/gateway/router-rules.ts
- [X] src/electron/gateway/router.ts
- [X] src/electron/gateway/security.ts
- [X] src/electron/gateway/session.ts
- [X] src/electron/gateway/tunnel.ts
- [X] src/electron/guardrails/guardrail-manager.ts
- [X] src/electron/hooks/__tests__/mappings.test.ts
- [X] src/electron/hooks/__tests__/server.test.ts
- [X] src/electron/hooks/__tests__/settings.test.ts
- [X] src/electron/hooks/__tests__/types.test.ts
- [X] src/electron/hooks/gmail-watcher.ts
- [X] src/electron/hooks/index.ts
- [X] src/electron/hooks/mappings.ts
- [X] src/electron/hooks/server.ts
- [X] src/electron/hooks/settings.ts
- [X] src/electron/hooks/types.ts
- [X] src/electron/ipc/canvas-handlers.ts
- [X] src/electron/ipc/handlers.ts
- [X] src/electron/ipc/mission-control-handlers.ts
- [V] src/electron/main.ts
- [X] src/electron/mcp/__tests__/MCPClientManager.test.ts
- [X] src/electron/mcp/__tests__/settings.test.ts
- [X] src/electron/mcp/client/MCPClientManager.ts
- [X] src/electron/mcp/client/MCPServerConnection.ts
- [X] src/electron/mcp/client/transports/SSETransport.ts
- [X] src/electron/mcp/client/transports/StdioTransport.ts
- [X] src/electron/mcp/client/transports/WebSocketTransport.ts
- [X] src/electron/mcp/host/MCPHostServer.ts
- [X] src/electron/mcp/host/ToolAdapter.ts
- [X] src/electron/mcp/oauth/connector-oauth.ts
- [X] src/electron/mcp/registry/MCPRegistryManager.ts
- [X] src/electron/mcp/settings.ts
- [X] src/electron/mcp/types.ts
- [X] src/electron/memory/ChatGPTImporter.ts
- [X] src/electron/memory/MarkdownMemoryIndexService.ts
- [X] src/electron/memory/MemoryService.ts
- [X] src/electron/memory/WorkspaceKitContext.ts
- [X] src/electron/memory/__tests__/MarkdownMemoryIndexService.test.ts
- [X] src/electron/memory/__tests__/MemoryService.test.ts
- [X] src/electron/memory/__tests__/WorkspaceKitContext.test.ts
- [X] src/electron/memory/__tests__/local-embedding.test.ts
- [X] src/electron/memory/local-embedding.ts
- [X] src/electron/notifications/index.ts
- [X] src/electron/notifications/service.ts
- [X] src/electron/notifications/store.ts
- [V] src/electron/preload.ts
- [X] src/electron/reports/AgentPerformanceReviewService.ts
- [X] src/electron/reports/StandupReportService.ts
- [X] src/electron/reports/__tests__/StandupReportService.test.ts
- [X] src/electron/reports/__tests__/task-export.test.ts
- [X] src/electron/reports/task-export.ts
- [X] src/electron/sandbox/monty-engine.ts
- [X] src/electron/security/__tests__/monty-tool-policy.test.ts
- [X] src/electron/security/concurrency.ts
- [X] src/electron/security/index.ts
- [X] src/electron/security/monty-tool-policy.ts
- [X] src/electron/security/policy-manager.ts
- [X] src/electron/security/project-access.ts
- [X] src/electron/settings/__tests__/personality-manager.test.ts
- [X] src/electron/settings/appearance-manager.ts
- [X] src/electron/settings/box-manager.ts
- [X] src/electron/settings/dropbox-manager.ts
- [X] src/electron/settings/google-workspace-manager.ts
- [X] src/electron/settings/memory-features-manager.ts
- [X] src/electron/settings/notion-manager.ts
- [X] src/electron/settings/onedrive-manager.ts
- [X] src/electron/settings/personality-manager.ts
- [X] src/electron/settings/sharepoint-manager.ts
- [X] src/electron/settings/x-manager.ts
- [X] src/electron/tailscale/__tests__/exposure.test.ts
- [X] src/electron/tailscale/__tests__/settings.test.ts
- [V] src/electron/tailscale/__tests__/tailscale.test.ts
- [X] src/electron/tailscale/exposure.ts
- [X] src/electron/tailscale/index.ts
- [X] src/electron/tailscale/settings.ts
- [X] src/electron/tailscale/tailscale.ts
- [V] src/electron/tray/QuickInputWindow.ts
- [V] src/electron/tray/TrayManager.ts
- [X] src/electron/tray/index.ts
- [X] src/electron/updater/index.ts
- [X] src/electron/updater/update-manager.ts
- [X] src/electron/utils/box-api.ts
- [X] src/electron/utils/dropbox-api.ts
- [X] src/electron/utils/env-migration.ts
- [X] src/electron/utils/gmail-api.ts
- [X] src/electron/utils/google-calendar-api.ts
- [X] src/electron/utils/google-workspace-api.ts
- [X] src/electron/utils/google-workspace-auth.ts
- [X] src/electron/utils/google-workspace-oauth.ts
- [X] src/electron/utils/json-utils.ts
- [X] src/electron/utils/notion-api.ts
- [X] src/electron/utils/onedrive-api.ts
- [X] src/electron/utils/process.ts
- [X] src/electron/utils/rate-limiter.ts
- [X] src/electron/utils/sharepoint-api.ts
- [X] src/electron/utils/validation.ts
- [X] src/electron/utils/x-cli.ts
- [X] src/electron/voice/VoiceService.ts
- [X] src/electron/voice/__tests__/VoiceService.test.ts
- [X] src/electron/voice/__tests__/voice-settings-manager.test.ts
- [X] src/electron/voice/index.ts
- [X] src/electron/voice/voice-settings-manager.ts
- [X] src/renderer/App.tsx
- [X] src/renderer/__tests__/sidebar-tree.test.ts
- [X] src/renderer/components/ActivityFeed.tsx
- [X] src/renderer/components/ActivityFeedItem.tsx
- [X] src/renderer/components/AgentPerformanceReviewViewer.tsx
- [X] src/renderer/components/AgentRoleCard.tsx
- [X] src/renderer/components/AgentRoleEditor.tsx
- [X] src/renderer/components/AgentSquadSettings.tsx
- [X] src/renderer/components/AgentTeamsPanel.tsx
- [X] src/renderer/components/AgentWorkingStatePanel.tsx
- [X] src/renderer/components/AppearanceSettings.tsx
- [X] src/renderer/components/ApprovalDialog.tsx
- [X] src/renderer/components/BlueBubblesSettings.tsx
- [X] src/renderer/components/BoxSettings.tsx
- [X] src/renderer/components/BrowserView.tsx
- [X] src/renderer/components/BuiltinToolsSettings.tsx
- [X] src/renderer/components/CanvasPreview.tsx
- [X] src/renderer/components/ChatGPTImportWizard.tsx
- [X] src/renderer/components/CommandOutput.tsx
- [X] src/renderer/components/ConnectorEnvModal.tsx
- [X] src/renderer/components/ConnectorSetupModal.tsx
- [X] src/renderer/components/ConnectorsSettings.tsx
- [X] src/renderer/components/ContextPolicySettings.tsx
- [X] src/renderer/components/ControlPlaneSettings.tsx
- [X] src/renderer/components/DisclaimerModal.tsx
- [X] src/renderer/components/DiscordSettings.tsx
- [X] src/renderer/components/DropboxSettings.tsx
- [X] src/renderer/components/EmailSettings.tsx
- [X] src/renderer/components/ExtensionsSettings.tsx
- [X] src/renderer/components/FileViewer.tsx
- [X] src/renderer/components/GoogleChatSettings.tsx
- [X] src/renderer/components/GoogleWorkspaceSettings.tsx
- [X] src/renderer/components/GuardrailSettings.tsx
- [X] src/renderer/components/HooksSettings.tsx
- [X] src/renderer/components/ImessageSettings.tsx
- [X] src/renderer/components/InlineImagePreview.tsx
- [X] src/renderer/components/LineIcons.tsx
- [X] src/renderer/components/LineSettings.tsx
- [X] src/renderer/components/MCPRegistryBrowser.tsx
- [X] src/renderer/components/MCPSettings.tsx
- [X] src/renderer/components/MainContent.tsx
- [X] src/renderer/components/MatrixSettings.tsx
- [X] src/renderer/components/MattermostSettings.tsx
- [X] src/renderer/components/MemoryHubSettings.tsx
- [X] src/renderer/components/MemorySettings.tsx
- [X] src/renderer/components/MentionBadge.tsx
- [X] src/renderer/components/MentionInput.tsx
- [X] src/renderer/components/MentionList.tsx
- [X] src/renderer/components/MissionControlPanel.tsx
- [X] src/renderer/components/NodesSettings.tsx
- [X] src/renderer/components/NotificationPanel.tsx
- [X] src/renderer/components/NotionSettings.tsx
- [X] src/renderer/components/Onboarding/AwakeningOrb.tsx
- [X] src/renderer/components/Onboarding/Onboarding.tsx
- [X] src/renderer/components/Onboarding/TypewriterText.tsx
- [X] src/renderer/components/Onboarding/index.ts
- [X] src/renderer/components/OnboardingModal.tsx
- [X] src/renderer/components/OneDriveSettings.tsx
- [X] src/renderer/components/PairingCodeDisplay.tsx
- [X] src/renderer/components/PersonalitySettings.tsx
- [X] src/renderer/components/QueueSettings.tsx
- [X] src/renderer/components/QuickTaskFAB.tsx
- [X] src/renderer/components/RightPanel.tsx
- [X] src/renderer/components/ScheduledTasksSettings.tsx
- [X] src/renderer/components/SearchSettings.tsx
- [X] src/renderer/components/Settings.tsx
- [X] src/renderer/components/SharePointSettings.tsx
- [X] src/renderer/components/Sidebar.tsx
- [X] src/renderer/components/SignalSettings.tsx
- [X] src/renderer/components/SkillHubBrowser.tsx
- [X] src/renderer/components/SkillParameterModal.tsx
- [X] src/renderer/components/SkillsSettings.tsx
- [X] src/renderer/components/SlackSettings.tsx
- [X] src/renderer/components/StandupReportViewer.tsx
- [X] src/renderer/components/TaskBoard.tsx
- [X] src/renderer/components/TaskBoardCard.tsx
- [X] src/renderer/components/TaskBoardColumn.tsx
- [X] src/renderer/components/TaskLabelManager.tsx
- [X] src/renderer/components/TaskQueuePanel.tsx
- [X] src/renderer/components/TaskQuickActions.tsx
- [X] src/renderer/components/TaskTimeline.tsx
- [X] src/renderer/components/TaskView.tsx
- [X] src/renderer/components/TeamsSettings.tsx
- [X] src/renderer/components/TelegramSettings.tsx
- [X] src/renderer/components/ThemeIcon.tsx
- [X] src/renderer/components/Toast.tsx
- [X] src/renderer/components/TraySettings.tsx
- [X] src/renderer/components/TwitchSettings.tsx
- [X] src/renderer/components/UpdateSettings.tsx
- [X] src/renderer/components/VoiceIndicator.tsx
- [X] src/renderer/components/VoiceSettings.tsx
- [X] src/renderer/components/WhatsAppSettings.tsx
- [X] src/renderer/components/WorkingStateEditor.tsx
- [X] src/renderer/components/WorkingStateHistory.tsx
- [X] src/renderer/components/WorkspaceSelector.tsx
- [X] src/renderer/components/XSettings.tsx
- [X] src/renderer/global.d.ts
- [X] src/renderer/hooks/useAgentContext.ts
- [X] src/renderer/hooks/useOnboardingFlow.ts
- [X] src/renderer/hooks/useVoiceInput.ts
- [X] src/renderer/main.tsx
- [X] src/renderer/utils/agentMessages.ts
- [X] src/renderer/utils/voice-directives.ts
- [X] src/shared/__tests__/agent-preferences.test.ts
- [X] src/shared/__tests__/personality-types.test.ts
- [X] src/shared/agent-preferences.ts
- [X] src/shared/channelMessages.ts
- [X] src/shared/llm-provider-catalog.ts
- [X] src/shared/plan-utils.ts
- [V] src/shared/types.ts

## Files flagged [V] with context (first 3 matches)

### CoWork-OS/src/electron/agent/__tests__/skill-eligibility.test.ts
> 63:      const result = checker.checkOS([process.platform as 'darwin' | 'linux' | 'win32']);
> 69:      const differentOS = process.platform === 'darwin' ? 'win32' : 'darwin';
> 81:      const result = checker.checkOS(['darwin']);

### CoWork-OS/src/electron/agent/executor.ts
> 93:  /syntax error/i,     // Script syntax errors (AppleScript, shell, etc.)
> 94:  /applescript execution failed/i, // AppleScript errors are input-related

### CoWork-OS/src/electron/agent/sandbox/macos-sandbox.ts
> 52:    if (process.platform !== 'darwin') {

### CoWork-OS/src/electron/agent/sandbox/runner.ts
> 127:    const useSandboxExec = process.platform === 'darwin' && this.sandboxProfile;
> 319:    if (process.platform === 'darwin') {

### CoWork-OS/src/electron/agent/sandbox/sandbox-factory.ts
> 267:  if (process.platform === 'darwin') {
> 295:    if (preferredType === 'macos' && process.platform !== 'darwin') {

### CoWork-OS/src/electron/agent/tools/registry.ts
> 783:- run_applescript: Execute AppleScript on macOS (control apps, automate tasks)
> 992:    if (name === 'run_applescript') return await this.systemTools.runAppleScript(input.script);

### CoWork-OS/src/electron/agent/tools/system-tools.ts
> 229:      if (platform === 'darwin') {
> 402:   * Execute AppleScript code on macOS
> 405:  async runAppleScript(script: string): Promise<{

### CoWork-OS/src/electron/database/__tests__/SecureSettingsRepository.test.ts
> 45:  platform: vi.fn(() => 'darwin'),

### CoWork-OS/src/electron/extensions/types.ts
> 61:    /** Supported platforms (darwin, linux, win32) */
> 226:  /** Platform (darwin, linux, win32) */

### CoWork-OS/src/electron/gateway/channel-registry.ts
> 388:        platforms: ['darwin'],
> 923:        platforms: ['darwin'],

### CoWork-OS/src/electron/main.ts
> 55:// Suppress GPU-related Chromium errors that occur with transparent windows and vibrancy
> 83:  const isMacOS = process.platform === 'darwin';
> 100:    windowConfig.titleBarStyle = 'hiddenInset';

### CoWork-OS/src/electron/preload.ts
> 499:  os?: ('darwin' | 'linux' | 'win32')[];

### CoWork-OS/src/electron/tailscale/__tests__/tailscale.test.ts
> 42:        OS: 'darwin',

### CoWork-OS/src/electron/tray/QuickInputWindow.ts
> 260:      vibrancy: 'under-window',
> 261:      visualEffectState: 'active',

### CoWork-OS/src/electron/tray/TrayManager.ts
> 504:      if (process.platform === 'darwin') {
> 505:        icon.setTemplateImage(true);
> 588:    const extension = process.platform === 'darwin' ? 'png' : 'png';

### CoWork-OS/src/renderer/styles/index.css
> 867:/* Override native vibrancy with solid background in light mode */

### CoWork-OS/src/shared/types.ts
> 2797:  os?: ('darwin' | 'linux' | 'win32')[];  // Must be one of these platforms