# NPM Package Analysis: scordi-extension

## Package Overview

**Package Name:** `scordi-extension`  
**Display Name:** SaaS Admin Control Manager  
**Version:** 1.19.29  
**NPM URL:** https://www.npmjs.com/package/scordi-extension  
**Registry URL:** https://registry.npmjs.org/scordi-extension  
**Package Size:** 525.3 kB (unpacked: 2.0 MB)  
**Total Files:** 148  
**License:** Not specified in package.json  
**Private:** false (publicly available)

---

## Package Description

**scordi-extension** (also known as 8G Extension / SaaS Admin Control Manager) is a Chrome extension and browser SDK designed for stable data collection and automation from web pages. The package provides:

1. **Chrome Extension**: Complete MV3 (Manifest V3) extension with content scripts, background service worker, and popup UI
2. **Browser SDK**: JavaScript/TypeScript SDK for web pages to communicate with the extension via messaging
3. **Workflow System**: Declarative workflow execution engine for browser automation
4. **Block System**: Modular execution blocks for DOM manipulation, data extraction, and automation

The README is primarily in Korean (한국어), indicating the target audience is Korean-speaking developers or users working with Korean SaaS platforms.

---

## Package.json Analysis

### Entry Points

```json
{
  "main": "./dist/sdk/index.cjs",
  "module": "./dist/sdk/index.js",
  "types": "./dist/sdk/index.d.ts"
}
```

### Exports Configuration

The package provides multiple export paths:

1. **Main SDK Export** (`"."`):
   - TypeScript types: `./dist/sdk/index.d.ts`
   - ESM import: `./dist/sdk/index.js`
   - CommonJS require: `./dist/sdk/index.cjs`

2. **Blocks Export** (`"./blocks"`):
   - Provides access to individual workflow blocks
   - Types available at `./dist/blocks/index.d.ts`

### Key Dependencies

#### Production Dependencies

**AI/LLM Integration:**
- `@langchain/anthropic@^1.0.0` - Anthropic Claude integration
- `@langchain/core@^1.0.1` - LangChain core functionality
- `@langchain/openai@^1.0.0` - OpenAI integration
- `langchain@^1.0.1` - LangChain framework

**Data Processing:**
- `xlsx@^0.18.5` - Excel file manipulation
- `jsonata@^2.1.0` - JSON query and transformation
- `zod@^3.25.76` - Schema validation

**React (UI):**
- `react@^19.2.0` - Latest React version
- `react-dom@^19.2.0` - React DOM renderer

**Validation & Transformation:**
- `class-transformer@^0.5.1` - Class-based object transformation
- `class-validator@^0.14.2` - Decorator-based validation

**Error Tracking:**
- `@sentry/browser@^10.29.0` - Browser error monitoring

#### Development Dependencies

**Build Tools:**
- `vite@^6.0.0` - Build tool
- `@crxjs/vite-plugin@^2.0.3` - Chrome extension support for Vite
- `@vitejs/plugin-react@^4.7.0` - React plugin for Vite
- `vite-plugin-zip-pack@^1.2.4` - Zip packaging

**Testing:**
- `vitest@^3.2.4` - Test framework
- `@vitest/ui@^3.2.4` - Test UI
- `@testing-library/dom@^10.4.1` - DOM testing utilities
- `@testing-library/jest-dom@^6.8.0` - Jest DOM matchers
- `jsdom@^27.0.0` - DOM implementation

**TypeScript & Linting:**
- `typescript@~5.8.3` - TypeScript compiler
- `eslint@^9.36.0` - Linter
- `prettier@^3.6.2` - Code formatter
- Various TypeScript and ESLint plugins

**Release Management:**
- `shipjs@^0.27.0` - Release automation

### Scripts

```json
{
  "dev": "vite",
  "build": "vite build --config vite.sdk.config.ts && tsc -p tsconfig.sdk.json",
  "build:extension": "pnpm run build && tsc -b && vite build --config vite.config.ts",
  "preview": "vite preview",
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:run": "vitest run",
  "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
  "lint:fix": "eslint . --ext ts,tsx --fix",
  "format": "prettier --write .",
  "format:check": "prettier --check .",
  "clean": "rm -rf dist/ node_modules/.cache/ *.tsbuildinfo",
  "typecheck": "tsc --noEmit",
  "release": "shipjs prepare"
}
```

**Key Observations:**
- Separate build configurations for SDK and extension
- Testing with Vitest (modern Vite-based test framework)
- Code quality enforced via ESLint and Prettier
- TypeScript strict checking available

---

## Directory Structure

```
package/
├── README.md (12.6 kB) - Korean documentation
├── package.json (2.7 kB)
└── dist/ (2.0 MB total, 148 files)
    ├── assets/ - Bundled JavaScript modules
    │   ├── client-CU6jEEQX.js (185.7 kB)
    │   ├── index.ts-DKCgmjXI.js (794.1 kB) - Largest bundle
    │   ├── types-8qZlocUF.js (192.7 kB)
    │   └── ... (11 files total)
    │
    ├── blocks/ - Workflow block definitions (TypeScript declarations)
    │   ├── index.d.ts - Main blocks export (55.9 kB)
    │   ├── types.d.ts - Block type definitions
    │   ├── AiParseDataBlock.d.ts - AI-powered data parsing
    │   ├── EventClickBlock.d.ts - Click automation
    │   ├── GetTextBlock.d.ts - Text extraction
    │   ├── WaitForConditionBlock.d.ts - Conditional waiting
    │   └── ... (25 block types total)
    │
    ├── content/ - Content script utilities
    │   └── elements/ - Element selector/finder utilities
    │       ├── finders/ - Selector implementations
    │       │   ├── CssSelector.d.ts
    │       │   ├── XPathFinder.d.ts
    │       │   ├── ShadowDOMSelector.d.ts
    │       │   └── ...
    │       └── utils/ - Selector generation utilities
    │
    ├── locales/ - Internationalization support
    │   └── index.d.ts (1.7 kB)
    │
    ├── sdk/ - Main SDK (browser-side client)
    │   ├── index.js (344.4 kB) - ESM bundle
    │   ├── index.cjs (217.9 kB) - CommonJS bundle
    │   ├── index.d.ts (695 B) - Main type export
    │   ├── types.d.ts (17.1 kB) - SDK type definitions
    │   ├── EightGClient.d.ts - Main client class
    │   ├── errors.d.ts - Error definitions
    │   └── logo.png (6.9 kB)
    │
    ├── types/ - Internal message type definitions
    │   ├── external-messages.d.ts - Web page ↔ Extension messages
    │   ├── internal-messages.d.ts - Extension internal messages
    │   └── index.d.ts
    │
    ├── utils/ - Utility functions
    │   ├── locale-detector.d.ts
    │   └── translation-resolver.d.ts
    │
    ├── workflow/ - Workflow execution context
    │   └── context/ - Execution context management
    │       ├── execution-context/ - Main execution state
    │       ├── loop-context/ - Loop iteration context
    │       ├── step-context/ - Step-level context
    │       └── var-context/ - Variable context
    │
    ├── manifest.json - Chrome extension manifest
    ├── logo.png - Extension icon
    ├── service-worker-loader.js - Background service worker loader
    └── src/
        └── popup/
            └── index.html - Extension popup UI
```

### File Count Statistics

- **Total Files**: 148
- **TypeScript Definitions**: 63 `.d.ts` files
- **Source Maps**: Multiple `.d.ts.map` files for debugging
- **JavaScript Bundles**: 11 asset files (1.5+ MB)
- **SDK Bundles**: 2 formats (ESM + CommonJS)

---

## Key Files and Purposes

### 1. SDK Entry Point (`dist/sdk/index.d.ts`)

Exports the main client and types:

```typescript
export * from './EightGClient';
export * from './types';
export * from './errors';
```

### 2. Main Client (`dist/sdk/EightGClient.d.ts`)

The `EightGClient` class is the primary interface for web pages to interact with the extension:

```typescript
export declare class EightGClient {
  constructor();
  checkExtension(): Promise<boolean>;
  collectWorkflow(options: CollectWorkflowOptions): Promise<WorkflowResult>;
  // Workspace management methods
  getWorkspaces(): Promise<any>;
  getWorkspacePlanAndCycle(): Promise<any>;
  getWorkspaceBillingHistories(): Promise<any>;
  getWorkspaceMembers(): Promise<any>;
}
```

### 3. Types System (`dist/sdk/types.d.ts`)

Core type definitions including:

- `ExecutionContext` - Workflow execution state
- `Workflow` - Workflow definition
- `WorkflowStep` - Individual step configuration
- `Condition` - Conditional logic (JSON and expression-based)
- `Binding` - Data binding configuration
- `RepeatConfig` - Loop/forEach configuration
- `Block` - Workflow block type union

### 4. Blocks System (`dist/blocks/index.d.ts`)

Exports 25 different block types for automation:

**Data Extraction:**
- `GetTextBlock` - Extract text content
- `GetAttributeValueBlock` - Get element attributes
- `GetValueFormsBlock` - Read form values
- `GetElementDataBlock` - Extract complex element data

**DOM Manipulation:**
- `EventClickBlock` - Click elements
- `SetValueFormsBlock` - Set form values
- `ClearValueFormsBlock` - Clear form data
- `SetContentEditableBlock` - Modify editable content
- `PasteValueBlock` - Paste clipboard data

**Navigation & Waiting:**
- `NavigateBlock` - Navigate to URLs
- `WaitBlock` - Simple time delay
- `WaitForConditionBlock` - Conditional waiting (URL, element, cookie, storage, user confirmation)
- `ScrollBlock` - Page scrolling

**Advanced Features:**
- `AiParseDataBlock` - AI-powered data parsing (OpenAI/Anthropic)
- `FetchApiBlock` - External API calls
- `NetworkCatchBlock` - Network request interception
- `ExecuteJavaScriptBlock` - Custom JavaScript execution
- `TransformDataBlock` - Data transformation
- `ExportDataBlock` - Data export
- `SaveAssetsBlock` - Asset collection
- `ApplyLocaleBlock` - Locale/translation application
- `MarkBorderBlock` - Visual element marking
- `KeypressBlock` - Keyboard simulation
- `ThrowErrorBlock` - Error handling

### 5. Chrome Extension Manifest (`dist/manifest.json`)

Manifest V3 configuration:

```json
{
  "manifest_version": 3,
  "name": "SaaS Admin Control Manager",
  "version": "1.19.29",
  "permissions": [
    "tabs",
    "debugger",
    "downloads",
    "clipboardRead",
    "clipboardWrite"
  ],
  "host_permissions": ["<all_urls>"],
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "run_at": "document_start",
      "match_about_blank": true
    }
  ],
  "background": {
    "service_worker": "service-worker-loader.js",
    "type": "module"
  }
}
```

**Key Permissions:**
- Full access to all URLs (`<all_urls>`)
- Debugger protocol access (for CDP operations)
- Download management
- Clipboard access

---

## Code Architecture and Patterns

### 1. Layered Architecture

The extension follows a clean layered architecture:

```
┌──────────────────────────────────────┐
│  Web Page (JavaScript/TypeScript)   │
│  Uses: EightGClient SDK              │
└────────────┬─────────────────────────┘
             │ window.postMessage
             ↓
┌──────────────────────────────────────┐
│  Content Script                       │
│  - MessageKernel                      │
│  - ExternalMessageHandler             │
│  - InternalMessageHandler             │
└────────────┬─────────────────────────┘
             │ chrome.runtime.sendMessage
             ↓
┌──────────────────────────────────────┐
│  Background Service Worker            │
│  - BackgroundManager                  │
│  - TabManager                         │
│  - WorkflowRunner                     │
│  - WorkflowService                    │
└────────────┬─────────────────────────┘
             │
             ↓
┌──────────────────────────────────────┐
│  Block Execution Layer                │
│  - BlockHandler.executeBlock()        │
│  - Individual Block Handlers          │
│  - Element Finders (CSS/XPath)        │
└──────────────────────────────────────┘
```

### 2. Message-Based Communication

**External Messages** (Web Page ↔ Extension):
- Prefixed with `8G_*`
- Uses `window.postMessage` for cross-context communication
- Request-response pattern with unique request IDs

**Internal Messages** (Content ↔ Background):
- Uses Chrome's `chrome.runtime` messaging API
- Structured message types for different operations

### 3. Workflow Execution Model

Workflows are declarative JSON structures:

```typescript
{
  version: "1.0",
  start: "stepId",
  steps: [
    {
      id: "stepId",
      block: { /* block config */ },
      when?: { /* condition */ },
      next?: "nextStepId",
      switch?: [
        { when: { /* condition */ }, next: "altStepId" }
      ],
      retry?: {
        attempts: number,
        delayMs?: number,
        backoffFactor?: number
      },
      timeoutMs?: number,
      delayAfterMs?: number,
      repeat?: {
        forEach: "path.to.array" | count: number,
        continueOnError?: boolean
      }
    }
  ]
}
```

**Features:**
- Conditional branching (`when`, `switch`)
- Success/failure paths (`onSuccess`, `onFailure`)
- Retry logic with exponential backoff
- Timeout management
- Loop/iteration support (`forEach`, `count`)
- Variable binding and data transformation

### 4. Context Management

The workflow system maintains multiple context layers:

- **ExecutionContext**: Overall workflow state
  - `steps`: Record of all step results
  - `vars`: User-defined variables
  
- **StepContext**: Current step information
  
- **LoopContext** / **ForEachContext**: Iteration state
  - Current index/item
  - Loop metadata

- **VarContext**: Variable resolution and binding

### 5. Block Pattern

All blocks follow a consistent pattern:

```typescript
// 1. Schema validation (Zod)
export const BlockSchema = z.object({
  name: z.literal("block-name"),
  selector: z.string(),
  findBy: z.enum(["cssSelector", "xpath"]),
  option: z.object({
    waitForSelector: z.boolean().optional(),
    waitSelectorTimeout: z.number().optional(),
    multiple: z.boolean().optional()
  }),
  // ... block-specific options
});

// 2. Type definition
export type Block = z.infer<typeof BlockSchema>;

// 3. Validation function
export async function validateBlock(block: Block): Promise<void> {
  BlockSchema.parse(block);
}

// 4. Handler function
export async function handlerBlock(block: Block): Promise<BlockResult<T>> {
  // Implementation
  return { data: result, hasError: false };
}
```

### 6. Element Selection System

Sophisticated element finding with multiple strategies:

**Selectors:**
- `CssSelector`: Standard CSS selectors
- `XPathFinder`: XPath expressions
- `ShadowDOMSelector`: Shadow DOM penetration
- `IframeSelector`: Cross-frame element access

**Features:**
- Wait for element presence (`waitForSelector`)
- Timeout configuration
- Multiple element selection
- Shadow DOM traversal
- Automatic selector generation (`CSSSelectorGenerator`, `XPathGenerator`)

### 7. AI Integration

The `AiParseDataBlock` provides AI-powered data extraction:

```typescript
{
  name: "ai-parse-data",
  sourceData: string | object,  // Raw data to parse
  schema: SchemaDefinition,       // Zod-like schema
  provider: "openai" | "anthropic",
  apiKey: string,
  model?: string,
  temperature?: number
}
```

Uses LangChain for LLM integration, supporting:
- OpenAI models (GPT-3.5, GPT-4)
- Anthropic models (Claude)
- Structured output with schema validation

---

## Entry Points and Exports

### Main SDK Export

```typescript
import { EightGClient } from 'scordi-extension';
// or
import { EightGClient } from '8g-extension'; // alias
```

### Blocks Export

```typescript
import { GetTextBlock, EventClickBlock, /* ... */ } from 'scordi-extension/blocks';
```

### Usage Pattern

```typescript
// 1. Initialize client
const client = new EightGClient();

// 2. Check extension availability
const available = await client.checkExtension();

// 3. Define workflow
const workflow = {
  version: "1.0",
  start: "extract_title",
  steps: [
    {
      id: "extract_title",
      block: {
        name: "get-text",
        selector: "h1.title",
        findBy: "cssSelector",
        option: { waitForSelector: true }
      }
    }
  ]
};

// 4. Execute workflow
const result = await client.collectWorkflow({
  targetUrl: "https://example.com",
  workflow: workflow,
  closeTabAfterCollection: true
});

// 5. Access results
console.log(result.steps.extract_title.result.data);
```

---

## Dependencies Analysis

### Runtime Dependencies (12 total)

**LLM/AI Stack** (4 packages, ~Heavy):
- LangChain ecosystem for AI-powered data parsing
- Supports OpenAI and Anthropic models
- Enables natural language data extraction

**Validation & Schema** (3 packages, ~Light):
- `zod` - Runtime type validation (modern, TypeScript-first)
- `class-transformer` - Object transformation
- `class-validator` - Decorator-based validation

**Data Processing** (2 packages, ~Medium):
- `xlsx` - Excel file generation/parsing
- `jsonata` - JSONPath-like querying

**UI Framework** (2 packages, ~Heavy):
- React 19 (latest version)
- For extension popup interface

**Monitoring** (1 package, ~Medium):
- Sentry browser SDK for error tracking

### Development Dependencies (26 total)

**Build System:**
- Vite 6.0 (modern, fast)
- CRXJS plugin for Chrome extension support
- Vite plugins for React and zip packaging

**Testing:**
- Vitest (Vite-native test runner)
- Testing Library for DOM testing
- jsdom for DOM simulation

**Code Quality:**
- TypeScript 5.8
- ESLint 9 with TypeScript support
- Prettier for formatting
- Multiple linting plugins

**Type Definitions:**
- `@types/chrome` - Chrome extension APIs
- `@types/react` - React types
- `@types/node` - Node.js types

### Dependency Graph Insights

1. **Heavy AI Integration**: LangChain stack adds significant bundle size but enables powerful AI features

2. **Modern Tooling**: Uses latest versions of build tools (Vite 6, React 19, TypeScript 5.8)

3. **Comprehensive Testing**: Full testing setup with Vitest and Testing Library

4. **Type Safety**: Strong TypeScript support with Zod for runtime validation

5. **Production-Ready**: Includes error monitoring (Sentry) and release automation (shipjs)

---

## Notable Features and Patterns

### 1. Dual-Mode Architecture

The package serves two purposes:
- **Chrome Extension**: Full-featured browser extension
- **SDK/Library**: Standalone SDK for programmatic use

### 2. Workflow-as-Code

Declarative workflow definitions enable:
- Version control of automation logic
- Sharing and reuse of workflows
- Dynamic workflow generation
- JSON-based configuration (no code compilation needed)

### 3. Advanced Error Handling

Multi-level error handling:
- Block-level retry with exponential backoff
- Step-level error paths (`onSuccess`, `onFailure`)
- Global error catching
- Sentry integration for production monitoring

### 4. Context-Aware Execution

Workflows maintain rich execution context:
- Access previous step results via `steps.stepId.result.data`
- Variable binding with templates (`{{ vars.myVar }}`)
- Loop iteration context
- Conditional logic based on execution state

### 5. Chrome DevTools Protocol Integration

Uses CDP for advanced automation:
- Programmatic clicking (bypassing event handlers)
- Keyboard input simulation
- Network request interception

### 6. Internationalization Support

Built-in locale support:
- `ApplyLocaleBlock` for translation
- Locale detection utilities
- Translation resolver

### 7. Asset Management

`SaveAssetsBlock` enables:
- Image collection and download
- Resource archiving
- Asset metadata extraction

### 8. Network Interception

`NetworkCatchBlock` provides:
- Request/response capture
- API monitoring
- Data extraction from XHR/Fetch requests

### 9. Security Considerations

**Permissions Used:**
- `debugger` - Required for CDP, but raises security concerns
- `<all_urls>` - Full web access (expected for automation tool)
- Clipboard access - Can read/write clipboard

**Potential Concerns:**
- Broad permissions may trigger security warnings
- Access to sensitive data via content scripts
- Network interception capabilities

**Mitigations:**
- Type-safe message validation
- Zod schema validation
- Error boundary patterns
- Sentry error tracking

---

## Security Considerations

### High-Risk Permissions

1. **`debugger` Permission**:
   - Allows Chrome DevTools Protocol access
   - Can inject code and intercept all page activity
   - Required for advanced automation but poses security risk

2. **`<all_urls>` Host Permission**:
   - Access to all websites
   - Can read and modify any web page
   - Standard for automation tools but very broad

3. **Clipboard Access**:
   - Can read and write clipboard
   - Potential for data exfiltration

### Positive Security Practices

1. **Type Safety**:
   - Zod schema validation for all inputs
   - TypeScript throughout
   - Runtime type checking

2. **Message Validation**:
   - Structured message protocols
   - Request ID verification
   - Origin checking (implied)

3. **Error Isolation**:
   - Try-catch blocks in block handlers
   - Error boundaries
   - Graceful degradation

### Recommendations for Users

1. **Review Permissions**: Understand what access is granted
2. **Audit Workflows**: Review workflow JSON before execution
3. **Monitor Network**: Watch for unexpected API calls
4. **Use Private Keys**: Keep AI API keys secure
5. **Limit Scope**: Use content scripts selectively if possible

---

## Repomix Output Summary

**Total Tokens**: 4,695 tokens  
**Total Characters**: 13,651 characters  
**Files Analyzed**: 2 (README.md, package.json)

**Top Files by Token Count**:
1. README.md - 3,382 tokens (72%)
2. package.json - 935 tokens (19.9%)

**Security Check**: ✓ No suspicious files detected

**Note**: The Repomix analysis only processed 2 files (README and package.json) from the root directory. The actual package contains 148 files in the `dist/` directory with type definitions, compiled JavaScript bundles, and assets.

---

## Package Quality Assessment

### Strengths

✅ **Modern Architecture**:
- Clean separation of concerns
- Modular block system
- Type-safe throughout

✅ **Comprehensive Features**:
- 25+ automation blocks
- AI integration
- Advanced workflow engine

✅ **Developer Experience**:
- Full TypeScript support
- Extensive type definitions (63 .d.ts files)
- Clear API surface

✅ **Production-Ready**:
- Error monitoring (Sentry)
- Release automation (shipjs)
- Testing infrastructure

✅ **Flexibility**:
- Dual-mode (extension + SDK)
- Multiple export formats (ESM + CJS)
- Extensible block system

### Weaknesses

⚠️ **Documentation**:
- Primarily in Korean (limits international adoption)
- No English version in package
- Limited inline code documentation

⚠️ **Bundle Size**:
- 2.0 MB unpacked (quite large)
- Heavy AI dependencies (LangChain stack)
- May impact load times

⚠️ **Security Concerns**:
- Very broad permissions
- CDP access is powerful but risky
- No mention of security audits

⚠️ **Dependency Management**:
- Some very new versions (React 19.2.0)
- May have compatibility issues
- Large dependency tree

### Opportunities

💡 **Internationalization**:
- Add English documentation
- Multi-language support in code
- Translation of block names

💡 **Tree-Shaking**:
- Split block imports for better tree-shaking
- Reduce bundle size
- Optional dependencies

💡 **Security Hardening**:
- Content Security Policy
- Permission minimization
- Security audit documentation

💡 **Community**:
- Open source contribution guide
- Example workflows
- Community block marketplace

---

## Use Cases

Based on the architecture and features, this package is ideal for:

1. **SaaS Platform Automation**:
   - Admin task automation
   - Data collection from SaaS dashboards
   - Workflow automation for repetitive tasks

2. **Web Scraping**:
   - Structured data extraction
   - Multi-page workflows
   - Dynamic content handling

3. **QA/Testing**:
   - End-to-end testing
   - User journey recording
   - Regression testing

4. **Data Migration**:
   - Legacy system data export
   - Format transformation
   - Bulk data operations

5. **Research & Analysis**:
   - Competitive analysis
   - Market research
   - Data aggregation

6. **Monitoring**:
   - Website change detection
   - Performance monitoring
   - Content verification

---

## Comparison with Similar Tools

### vs. Puppeteer/Playwright
- **Advantage**: No Node.js required, runs in browser
- **Disadvantage**: Less control, browser-dependent

### vs. Selenium
- **Advantage**: Declarative workflows, easier to use
- **Disadvantage**: Limited to Chrome, smaller ecosystem

### vs. Zapier/Make
- **Advantage**: More powerful, programmable
- **Disadvantage**: Requires development knowledge

### vs. RPA Tools (UiPath, Automation Anywhere)
- **Advantage**: Open source, free, lightweight
- **Disadvantage**: Web-only, less enterprise features

---

## Conclusion

**scordi-extension** is a sophisticated, production-ready browser automation framework with a unique architecture combining a Chrome extension with a programmatic SDK. Its workflow-based approach and modular block system make it powerful yet accessible for web automation tasks.

### Best For:
- Korean SaaS platforms (based on documentation)
- Teams needing browser automation without external tools
- Developers wanting programmable web scraping
- Organizations requiring AI-enhanced data extraction

### Not Recommended For:
- Projects requiring minimal permissions
- Non-web automation needs
- Teams without Korean language support
- Projects with strict bundle size constraints

### Overall Rating: ⭐⭐⭐⭐ (4/5)

**Strengths**: Modern architecture, comprehensive features, type safety  
**Areas for Improvement**: Documentation, bundle size, internationalization

---

## Additional Resources

- **NPM Package**: https://www.npmjs.com/package/scordi-extension
- **Package Version**: 1.19.29
- **Last Analyzed**: December 27, 2024
- **Analyzer**: Codegen NPM Package Analysis Tool

---

## Appendix: Block Catalog

Complete list of available blocks:

| Block Name | Purpose | Category |
|------------|---------|----------|
| `get-text` | Extract text content | Data Extraction |
| `attribute-value` | Get element attributes | Data Extraction |
| `get-value-form` | Read form values | Data Extraction |
| `get-element-data` | Complex data extraction | Data Extraction |
| `event-click` | Click elements | DOM Manipulation |
| `set-value-form` | Set form values | DOM Manipulation |
| `clear-value-form` | Clear form data | DOM Manipulation |
| `set-content-editable` | Modify editable content | DOM Manipulation |
| `paste-value` | Paste clipboard data | DOM Manipulation |
| `navigate` | Navigate to URLs | Navigation |
| `wait` | Simple delay | Timing |
| `wait-for-condition` | Conditional waiting | Timing |
| `scroll` | Page scrolling | Interaction |
| `keypress` | Keyboard simulation | Interaction |
| `element-exists` | Check element presence | Validation |
| `ai-parse-data` | AI-powered parsing | AI/ML |
| `fetch-api` | External API calls | Integration |
| `network-catch` | Network interception | Integration |
| `execute-javascript` | Custom JavaScript | Advanced |
| `transform-data` | Data transformation | Processing |
| `export-data` | Data export | Processing |
| `save-assets` | Asset collection | Processing |
| `apply-locale` | Localization | Utility |
| `mark-border` | Visual marking | Utility |
| `throw-error` | Error handling | Control Flow |

---

*End of Analysis Report*

