/**
 * GraphQL Schema Definition
 * Aggregates Codegen API endpoints into optimized GraphQL queries
 */

import { gql } from 'graphql-tag';

export const typeDefs = gql`
  scalar DateTime
  scalar JSON

  # Core Types
  type User {
    id: ID!
    email: String!
    name: String
    avatarUrl: String
    createdAt: DateTime!
    updatedAt: DateTime!
  }

  type Organization {
    id: ID!
    name: String!
    slug: String!
    avatarUrl: String
    createdAt: DateTime!
    updatedAt: DateTime!
    users: [User!]!
    repositories: [Repository!]!
    agentRuns(
      page: Int = 1
      pageSize: Int = 10
      sourceType: String
      status: String
    ): AgentRunConnection!
  }

  type Repository {
    id: ID!
    name: String!
    fullName: String!
    description: String
    private: Boolean!
    htmlUrl: String!
    cloneUrl: String!
    defaultBranch: String!
    language: String
    createdAt: DateTime!
    updatedAt: DateTime!
    organizationId: ID!
    checkSuiteSettings: CheckSuiteSettings
  }

  type CheckSuiteSettings {
    repositoryId: ID!
    enabled: Boolean!
    autoFixEnabled: Boolean!
    prReviewEnabled: Boolean!
    createdAt: DateTime!
    updatedAt: DateTime!
  }

  # Agent Run Types
  enum AgentRunStatus {
    PENDING
    RUNNING
    COMPLETE
    FAILED
    STOPPED
    CANCELLED
  }

  enum AgentRunSourceType {
    API
    SLACK
    GITHUB
    LINEAR
    CLI
  }

  type AgentRun {
    id: ID!
    organizationId: ID!
    userId: ID!
    status: AgentRunStatus!
    sourceType: AgentRunSourceType!
    prompt: String!
    summary: String
    result: String
    model: String
    repoId: ID
    createdAt: DateTime!
    updatedAt: DateTime!
    completedAt: DateTime
    webUrl: String
    errorMessage: String
    progressPercentage: Int
    githubPullRequests: [GitHubPullRequest!]!
    logs(skip: Int = 0, limit: Int = 50): AgentRunLogConnection!
    repository: Repository
    user: User!
  }

  type AgentRunConnection {
    items: [AgentRun!]!
    total: Int!
    page: Int!
    pageSize: Int!
    pages: Int!
  }

  # Agent Run Logs
  enum LogMessageType {
    ACTION
    PLAN_EVALUATION
    FINAL_ANSWER
    ERROR
    USER_MESSAGE
    USER_GITHUB_ISSUE_COMMENT
    INITIAL_PR_GENERATION
    DETECT_PR_ERRORS
    FIX_PR_ERRORS
    PR_CREATION_FAILED
    PR_EVALUATION
    COMMIT_EVALUATION
    AGENT_RUN_LINK
  }

  type AgentRunLog {
    agentRunId: ID!
    createdAt: DateTime!
    messageType: LogMessageType!
    thought: String
    toolName: String
    toolInput: JSON
    toolOutput: JSON
    observation: JSON
  }

  type AgentRunLogConnection {
    items: [AgentRunLog!]!
    total: Int!
    page: Int!
    size: Int!
    pages: Int!
  }

  # Pull Request Types
  enum PullRequestState {
    OPEN
    CLOSED
    MERGED
  }

  type GitHubPullRequest {
    id: ID!
    number: Int!
    title: String!
    body: String
    state: PullRequestState!
    url: String!
    htmlUrl: String!
    headBranchName: String!
    baseBranchName: String!
    createdAt: DateTime!
    updatedAt: DateTime!
    mergedAt: DateTime
    author: GitHubUser
  }

  type GitHubUser {
    login: String!
    avatarUrl: String
  }

  # Integration Types
  enum IntegrationType {
    GITHUB
    SLACK
    LINEAR
    JIRA
    CLICKUP
    MONDAY
    SENTRY
    CIRCLECI
  }

  type Integration {
    id: ID!
    name: String!
    type: IntegrationType!
    enabled: Boolean!
    configuration: JSON!
    createdAt: DateTime!
    updatedAt: DateTime!
  }

  # Project Types (for visual workflow management)
  enum ProjectStatus {
    ACTIVE
    PAUSED
    COMPLETED
    ARCHIVED
  }

  type Project {
    id: ID!
    name: String!
    description: String
    organizationId: ID!
    repositoryIds: [ID!]!
    workflowTemplateId: ID
    status: ProjectStatus!
    createdAt: DateTime!
    updatedAt: DateTime!
    starred: Boolean!
    tags: [String!]!
    repositories: [Repository!]!
    workflows: [Workflow!]!
  }

  # Workflow Types
  enum WorkflowStatus {
    DRAFT
    ACTIVE
    PAUSED
    COMPLETED
  }

  enum WorkflowNodeType {
    AGENT
    CONDITION
    INTEGRATION
    MANUAL
  }

  type WorkflowNode {
    id: ID!
    type: WorkflowNodeType!
    position: Position!
    data: WorkflowNodeData!
  }

  type Position {
    x: Float!
    y: Float!
  }

  type WorkflowNodeData {
    label: String!
    description: String
    config: JSON!
  }

  type WorkflowEdge {
    id: ID!
    source: ID!
    target: ID!
    type: String
    data: WorkflowEdgeData
  }

  type WorkflowEdgeData {
    condition: String
    label: String
  }

  type Workflow {
    id: ID!
    name: String!
    description: String
    projectId: ID!
    nodes: [WorkflowNode!]!
    edges: [WorkflowEdge!]!
    status: WorkflowStatus!
    createdAt: DateTime!
    updatedAt: DateTime!
    version: Int!
    project: Project!
  }

  # Dashboard Analytics
  type DashboardStats {
    activeAgents: Int!
    totalWorkflows: Int!
    totalProjects: Int!
    successRate: Float!
    recentActivity: [ActivityItem!]!
  }

  type ActivityItem {
    id: ID!
    type: String!
    title: String!
    status: String!
    timestamp: DateTime!
    metadata: JSON
  }

  # Input Types
  input CreateAgentRunInput {
    prompt: String!
    model: String
    repoId: ID
    organizationId: ID
  }

  input CreateProjectInput {
    name: String!
    description: String
    organizationId: ID!
    repositoryIds: [ID!]!
    workflowTemplateId: ID
    status: ProjectStatus = ACTIVE
    tags: [String!] = []
  }

  input CreateWorkflowInput {
    name: String!
    description: String
    projectId: ID!
    nodes: [WorkflowNodeInput!]!
    edges: [WorkflowEdgeInput!]!
    status: WorkflowStatus = DRAFT
  }

  input WorkflowNodeInput {
    id: ID!
    type: WorkflowNodeType!
    position: PositionInput!
    data: WorkflowNodeDataInput!
  }

  input PositionInput {
    x: Float!
    y: Float!
  }

  input WorkflowNodeDataInput {
    label: String!
    description: String
    config: JSON!
  }

  input WorkflowEdgeInput {
    id: ID!
    source: ID!
    target: ID!
    type: String
    data: WorkflowEdgeDataInput
  }

  input WorkflowEdgeDataInput {
    condition: String
    label: String
  }

  input UpdateWorkflowInput {
    id: ID!
    name: String
    description: String
    nodes: [WorkflowNodeInput!]
    edges: [WorkflowEdgeInput!]
    status: WorkflowStatus
  }

  # Root Types
  type Query {
    # User & Organization
    me: User
    organizations: [Organization!]!
    organization(id: ID!): Organization

    # Agent Runs
    agentRuns(
      organizationId: ID!
      page: Int = 1
      pageSize: Int = 10
      sourceType: String
      status: String
      userId: ID
    ): AgentRunConnection!
    
    agentRun(organizationId: ID!, id: ID!): AgentRun
    
    agentRunLogs(
      organizationId: ID!
      agentRunId: ID!
      skip: Int = 0
      limit: Int = 50
    ): AgentRunLogConnection!

    # Repositories
    repositories(organizationId: ID!): [Repository!]!
    repository(organizationId: ID!, id: ID!): Repository

    # Integrations
    integrations(organizationId: ID!): [Integration!]!

    # Projects & Workflows
    projects(organizationId: ID!): [Project!]!
    project(id: ID!): Project
    workflows(projectId: ID!): [Workflow!]!
    workflow(id: ID!): Workflow

    # Dashboard
    dashboardStats(organizationId: ID!): DashboardStats!

    # Search
    search(
      organizationId: ID!
      query: String!
      types: [String!] = ["agent_runs", "projects", "workflows"]
      limit: Int = 20
    ): [SearchResult!]!
  }

  type Mutation {
    # Agent Runs
    createAgentRun(input: CreateAgentRunInput!): AgentRun!
    resumeAgentRun(organizationId: ID!, agentRunId: ID!): AgentRun!

    # Projects
    createProject(input: CreateProjectInput!): Project!
    updateProject(id: ID!, input: CreateProjectInput!): Project!
    deleteProject(id: ID!): Boolean!
    toggleProjectStar(id: ID!): Project!

    # Workflows
    createWorkflow(input: CreateWorkflowInput!): Workflow!
    updateWorkflow(input: UpdateWorkflowInput!): Workflow!
    deleteWorkflow(id: ID!): Boolean!
  }

  type Subscription {
    # Real-time updates
    agentRunUpdates(organizationId: ID!): AgentRun!
    workflowUpdates(projectId: ID!): Workflow!
    systemNotifications(organizationId: ID!): SystemNotification!
  }

  # Search Results
  union SearchResult = AgentRun | Project | Workflow

  # System Notifications
  type SystemNotification {
    id: ID!
    type: String!
    title: String!
    message: String!
    timestamp: DateTime!
    read: Boolean!
    metadata: JSON
  }
`;

export default typeDefs;
