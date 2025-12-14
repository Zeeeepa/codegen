import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { PrismaClient } from '@prisma/client';

// Routes
import profileRoutes from './api/routes/profiles';
import templateRoutes from './api/routes/templates';
import mcpToolRoutes from './api/routes/mcpTools';
import taskTemplateRoutes from './api/routes/taskTemplates';
import sandboxRoutes from './api/routes/sandboxes';
import contextRoutes from './api/routes/context';

const app: Express = express();
const port = process.env.PORT || 3001;

// Initialize Prisma
export const prisma = new PrismaClient();

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req: Request, res: Response, next: NextFunction) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.path}`);
  next();
});

// Health check
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/profiles', profileRoutes);
app.use('/api/templates', templateRoutes);
app.use('/api/mcp-tools', mcpToolRoutes);
app.use('/api/task-templates', taskTemplateRoutes);
app.use('/api/sandboxes', sandboxRoutes);
app.use('/api/context', contextRoutes);

// 404 handler
app.use((_req: Request, res: Response) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: 'Internal server error', 
    message: process.env.NODE_ENV === 'development' ? err.message : undefined 
  });
});

// Start server
async function main() {
  try {
    // Connect to database
    await prisma.$connect();
    console.log('✅ Database connected');

    // Start server
    app.listen(port, () => {
      console.log(`🚀 Server running on http://localhost:${port}`);
      console.log(`📚 API available at http://localhost:${port}/api`);
      console.log(`🏥 Health check: http://localhost:${port}/health`);
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, shutting down gracefully...');
  await prisma.$disconnect();
  process.exit(0);
});

main();

