# CodeGen Server - Agentic Profiles Backend

Backend TypeScript server for the CodeGen Agentic Profiles System, providing REST APIs for dynamic template management, profile configuration, MCP tool integration, and multi-sandbox orchestration.

## Features

- **Profile Management**: Full CRUD for agentic profiles with role assignment, tools, skills, and templates
- **Dynamic Templates**: Database-backed template system (replacing static chainTemplates.ts)
- **MCP Tool Catalog**: Browse, configure, and deploy MCP tools with step-by-step instructions
- **Task Templates**: Pre-settable workflow configurations
- **Sandbox Manager**: Multi-sandbox context isolation and deployment configuration
- **Context Application Engine**: Merge profiles + templates + variables into executable agent contexts

## Tech Stack

- **Runtime**: Node.js 18+ with TypeScript
- **Framework**: Express.js
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **ORM**: Prisma
- **Validation**: Zod
- **Testing**: Vitest

## Quick Start

```bash
# Install dependencies
npm install

# Setup database
cp .env.example .env
npx prisma generate
npx prisma migrate dev --name init

# Seed initial data (MCP tools, etc.)
npm run db:seed

# Start development server
npm run dev
```

Server runs on `http://localhost:3001`

## API Endpoints

### Profiles
- `GET /api/profiles` - List all profiles
- `GET /api/profiles/:id` - Get profile by ID
- `POST /api/profiles` - Create profile
- `PUT /api/profiles/:id` - Update profile
- `DELETE /api/profiles/:id` - Delete profile
- `GET /api/profiles/active/current` - Get active profile
- `POST /api/profiles/:id/activate` - Set active profile

### Templates
- `GET /api/templates` - List all templates
- `POST /api/templates` - Create template
- `POST /api/templates/import` - Import from external source (e.g., davila7/claude-code-templates)

### MCP Tools
- `GET /api/mcp-tools` - List MCP tool catalog
- `GET /api/mcp-tools/:id` - Get tool with deployment instructions

### Context Application
- `POST /api/context/apply` - Generate agent run payload from profile + template + variables

## Database Schema

See `prisma/schema.prisma` for complete schema. Key models:
- **Profile**: Core profile configuration
- **Template**: Dynamic templates with variables
- **McpTool**: MCP tool catalog with deployment instructions
- **TaskTemplate**: Pre-configured workflows
- **Sandbox**: Sandbox configuration per profile
- Junction tables for many-to-many relationships

## Development

```bash
# Type checking
npm run typecheck

# Linting
npm run lint

# Tests
npm test

# Build
npm run build

# Prisma Studio (DB GUI)
npm run prisma:studio
```

## Environment Variables

```env
DATABASE_URL=file:./dev.db
PORT=3001
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000
API_KEY=optional-api-key-for-single-user-mode
```

## Deployment

Ready for deployment to:
- Docker/Docker Compose
- Kubernetes
- Serverless platforms (with PostgreSQL)
- Traditional VPS/cloud servers

## Next Steps

1. Implement template CRUD routes
2. Add template importer for davila7/claude-code-templates
3. Seed MCP tool catalog
4. Build context application engine
5. Add E2E tests with Playwright

## License

MIT

