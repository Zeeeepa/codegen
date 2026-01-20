#!/bin/bash
# Web2API Installation Verification Script

echo "================================================"
echo "Web2API Installation Verification"
echo "================================================"
echo ""

PASS=0
FAIL=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_pass() {
    echo -e "${GREEN}✓ PASS${NC} - $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗ FAIL${NC} - $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠ WARN${NC} - $1"
}

# 1. Check file structure
echo "1. Checking file structure..."
echo ""

FILES=(
    "backend/web2api/README.md"
    "backend/web2api/QUICK_START.md"
    "backend/web2api/IMPLEMENTATION_STATUS.md"
    "backend/web2api/setup.sh"
    "backend/web2api/autoqa-ai-testing/src/autoqa/__init__.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/adapters/__init__.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/adapters/owl/__init__.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/adapters/owl/browser_adapter.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/api/server.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/auth/__init__.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/auth/credential_store.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/auth/session_manager.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/discovery/__init__.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/discovery/auth_detector.py"
    "backend/web2api/autoqa-ai-testing/src/autoqa/storage/database.py"
    "backend/web2api/autoqa-ai-testing/tests/test_web2api_e2e.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File exists: $file"
    else
        check_fail "File missing: $file"
    fi
done

echo ""
echo "2. Checking Python imports..."
echo ""

cd backend/web2api/autoqa-ai-testing

# Test imports
IMPORTS=(
    "from autoqa.adapters.owl import OwlBrowserAdapter"
    "from autoqa.auth.credential_store import CredentialStore"
    "from autoqa.auth.session_manager import SessionManager"
    "from autoqa.discovery.auth_detector import AuthDetector"
    "from autoqa.storage.database import DatabaseManager, ServiceModel"
)

for import_cmd in "${IMPORTS[@]}"; do
    if python3 -c "$import_cmd" 2>/dev/null; then
        check_pass "Import: $import_cmd"
    else
        check_fail "Import failed: $import_cmd"
    fi
done

echo ""
echo "3. Checking database models..."
echo ""

python3 << 'EOF'
from autoqa.storage.database import Base, ServiceModel, ServiceSessionModel, OperationModel, StreamModel, ArtifactModel

models = [
    ("ServiceModel", ServiceModel),
    ("ServiceSessionModel", ServiceSessionModel),
    ("OperationModel", OperationModel),
    ("StreamModel", StreamModel),
    ("ArtifactModel", ArtifactModel),
]

for name, model in models:
    try:
        # Check if model has __tablename__
        if hasattr(model, '__tablename__'):
            print(f"✓ PASS - Model {name} has table: {model.__tablename__}")
        else:
            print(f"✗ FAIL - Model {name} missing __tablename__")
    except Exception as e:
        print(f"✗ FAIL - Model {name} error: {e}")
EOF

echo ""
echo "4. Checking API endpoints..."
echo ""

python3 << 'EOF'
from autoqa.api.server import app
from fastapi import FastAPI

routes = []
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        for method in route.methods:
            routes.append(f"{method} {route.path}")

expected_routes = [
    "POST /api/services",
    "GET /api/services",
    "GET /api/services/{service_id}",
    "POST /api/services/{service_id}/discover",
    "POST /v1/chat/completions",
    "GET /v1/models",
    "GET /health",
]

for expected in expected_routes:
    found = False
    for route in routes:
        if expected in route:
            print(f"✓ PASS - Endpoint: {expected}")
            found = True
            break
    if not found:
        print(f"✗ FAIL - Endpoint not found: {expected}")
EOF

echo ""
echo "5. Checking dependencies..."
echo ""

# Check critical dependencies
DEPS=(
    "fastapi"
    "sqlalchemy"
    "cryptography"
    "structlog"
    "pydantic"
)

for dep in "${DEPS[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        check_pass "Dependency installed: $dep"
    else
        check_fail "Dependency missing: $dep"
    fi
done

echo ""
echo "6. Checking Owl-Browser SDK availability..."
echo ""

if python3 -c "from owl_browser import Browser" 2>/dev/null; then
    check_pass "Owl-Browser SDK installed"
else
    check_warn "Owl-Browser SDK not installed (optional for development)"
fi

echo ""
echo "7. Checking environment setup..."
echo ""

cd ../..

if [ -f "autoqa-ai-testing/.env" ]; then
    check_pass ".env file exists"
else
    check_warn ".env file not found (run setup.sh)"
fi

if [ -x "setup.sh" ]; then
    check_pass "setup.sh is executable"
else
    check_fail "setup.sh not executable"
fi

echo ""
echo "================================================"
echo "Verification Complete"
echo "================================================"
echo ""
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: cd backend/web2api && ./setup.sh"
    echo "2. Update .env with your credentials"
    echo "3. Start server: cd autoqa-ai-testing && python -m autoqa.api.server"
    echo "4. Run tests: python tests/test_web2api_e2e.py"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Please review the failures above and ensure all files are present."
    exit 1
fi
