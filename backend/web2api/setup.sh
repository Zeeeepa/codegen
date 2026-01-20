#!/bin/bash
# Web2API Quick Setup Script

set -e

echo "================================================"
echo "Web2API Quick Setup"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $PYTHON_VERSION"

# Check if PostgreSQL is running
echo ""
echo "📋 Checking PostgreSQL..."
if pg_isready -q 2>/dev/null; then
    echo -e "   ${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "   ${RED}✗ PostgreSQL is not running${NC}"
    echo "   Please start PostgreSQL: sudo service postgresql start"
    exit 1
fi

# Create database if not exists
echo ""
echo "📋 Setting up database..."
if psql -lqt | cut -d \| -f 1 | grep -qw web2api; then
    echo -e "   ${YELLOW}⚠ Database 'web2api' already exists${NC}"
else
    createdb web2api
    echo -e "   ${GREEN}✓ Created database 'web2api'${NC}"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
cd backend/web2api/autoqa-ai-testing
pip install -e . -q
echo -e "   ${GREEN}✓ Dependencies installed${NC}"

# Generate encryption key
echo ""
echo "🔑 Generating encryption key..."
ENCRYPTION_KEY=$(python3 -c "from autoqa.auth.credential_store import CredentialStore; print(CredentialStore.generate_key())")
echo "   Generated key: ${ENCRYPTION_KEY:0:20}..."

# Create .env file
echo ""
echo "📝 Creating .env file..."
cat > .env << EOF
# Web2API Configuration
CREDENTIAL_ENCRYPTION_KEY=$ENCRYPTION_KEY
DATABASE_URL=postgresql+asyncpg://web2api:web2api@localhost:5432/web2api
OWL_BROWSER_URL=http://localhost:8080
OWL_BROWSER_TOKEN=your-token-here
WEB2API_PORT=8000
EOF

echo -e "   ${GREEN}✓ Created .env file${NC}"

# Initialize database
echo ""
echo "🗄️  Initializing database tables..."
python3 -c "import asyncio; from autoqa.storage.database import DatabaseManager; asyncio.run(DatabaseManager().create_tables())" 2>/dev/null
echo -e "   ${GREEN}✓ Database tables created${NC}"

# Check Owl-Browser connection
echo ""
echo "🦉 Checking Owl-Browser connection..."
if [ -n "$OWL_BROWSER_TOKEN" ] && [ "$OWL_BROWSER_TOKEN" != "your-token-here" ]; then
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Owl-Browser is connected${NC}"
    else
        echo -e "   ${YELLOW}⚠ Cannot connect to Owl-Browser at $OWL_BROWSER_URL${NC}"
        echo "   Please ensure Owl-Browser server is running"
    fi
else
    echo -e "   ${YELLOW}⚠ OWL_BROWSER_TOKEN not set in .env${NC}"
    echo "   Update .env with your Owl-Browser token"
fi

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Update your credentials in .env:"
echo "   - OWL_BROWSER_TOKEN (required)"
echo ""
echo "2. Start the API server:"
echo "   cd backend/web2api/autoqa-ai-testing"
echo "   python -m autoqa.api.server"
echo ""
echo "3. In another terminal, run tests:"
echo "   export K2THINK_EMAIL='your-email@example.com'"
echo "   export K2THINK_PASSWORD='your-password'"
echo "   python tests/test_web2api_e2e.py"
echo ""
echo "4. Or test manually:"
echo "   curl -X POST http://localhost:8000/api/services \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\": \"k2think\", \"url\": \"https://k2think.ai\", \"credentials\": {...}}'"
echo ""
echo "For more information, see backend/web2api/README.md"
echo ""
