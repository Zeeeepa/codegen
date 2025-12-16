# Controller Dashboard - Frontend

A modern React + TypeScript + Vite web application for managing workflows, monitoring sandboxes, and tracking execution metrics.

## 🚀 Features

- **Workflow Management**: View, toggle, and execute workflows
- **Real-Time Monitoring**: Live updates of sandbox execution status
- **Dashboard Analytics**: Summary statistics and metrics visualization
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Type-Safe**: Full TypeScript implementation
- **Fast Development**: Vite for instant HMR and fast builds

## 🛠️ Tech Stack

- **Framework**: React 18.3.1
- **Language**: TypeScript 5.4.3
- **Build Tool**: Vite 5.2.0
- **Routing**: React Router 6.22.3
- **State Management**: Zustand 4.5.2
- **Data Fetching**: TanStack Query 5.28.4
- **HTTP Client**: Axios 1.6.8
- **Styling**: Tailwind CSS 3.4.1
- **Icons**: Lucide React 0.363.0
- **Date Utilities**: date-fns 3.6.0

## 📦 Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your API URL
# VITE_API_URL=http://localhost:8000
```

## 🏃 Development

```bash
# Start development server (runs on http://localhost:3000)
npm run dev

# Type check
npm run type-check

# Lint code
npm run lint

# Run tests
npm run test
```

## 🏗️ Building for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The build output will be in the `dist/` directory.

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and type definitions
│   │   ├── client.ts     # HTTP client with all API methods
│   │   └── types.ts      # TypeScript interfaces
│   ├── components/       # React components
│   │   ├── Common/       # Reusable UI components
│   │   ├── Dashboard/    # Dashboard-specific components
│   │   ├── Workflows/    # Workflow management components
│   │   └── Sandboxes/    # Sandbox monitoring components
│   ├── hooks/            # Custom React hooks
│   │   ├── useWorkflows.ts
│   │   └── useSandboxes.ts
│   ├── pages/            # Page components
│   │   ├── DashboardPage.tsx
│   │   ├── WorkflowsPage.tsx
│   │   └── SandboxesPage.tsx
│   ├── store/            # Zustand state management
│   │   ├── workflowStore.ts
│   │   └── sandboxStore.ts
│   ├── styles/           # Global styles
│   │   └── index.css
│   ├── utils/            # Utility functions
│   │   ├── formatters.ts
│   │   └── cn.ts
│   ├── App.tsx           # Main application component
│   └── main.tsx          # Application entry point
├── public/               # Static assets
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── README.md             # This file
```

## 🔌 API Integration

The frontend connects to the Controller Dashboard backend API. Ensure the backend is running and accessible at the URL specified in your `.env` file.

### API Endpoints Used

- `GET /api/workflows` - List all workflows
- `POST /api/workflows/{id}/toggle` - Toggle workflow enabled/disabled
- `POST /api/workflows/{id}/execute` - Execute workflow
- `GET /api/sandboxes` - List all sandboxes
- `POST /api/sandboxes/{id}/terminate` - Terminate sandbox
- `GET /api/dashboard/summary` - Get dashboard statistics

## 🎨 Customization

### Colors

The application uses a custom color palette defined in `tailwind.config.js`:

- **Primary Purple**: `rgb(82, 19, 217)` - Main brand color
- **Accent Orange**: `rgb(255, 202, 133)` - Active states
- **Success Green**: `rgb(66, 196, 153)` - Success indicators
- **Error Red**: `rgb(255, 103, 103)` - Error states

### Components

All components are built with Tailwind CSS and are easily customizable. Common components are located in `src/components/Common/`.

## 🧪 Testing

```bash
# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test -- --coverage
```

## 🚢 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

### Docker

```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_AUTH_TOKEN` | Optional auth token | - |

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Ensure tests pass and types check
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues or questions:
- Open an issue on GitHub
- Check the backend documentation
- Review the IRIS frontend gap analysis document

## 🎯 Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Visual workflow editor (React Flow integration)
- [ ] PRD editor with rich text support
- [ ] Project management UI
- [ ] Dark mode support
- [ ] Advanced filtering and search
- [ ] Export functionality (CSV, PDF)
- [ ] User authentication UI
- [ ] Mobile app (React Native)

## ⚡ Performance

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: 90+
- **Bundle Size**: < 500KB (gzipped)

## 🔒 Security

- All API calls use HTTPS in production
- Environment variables for sensitive config
- CORS properly configured
- Input validation on all forms
- XSS protection via React

---

Built with ❤️ using React + TypeScript + Vite

