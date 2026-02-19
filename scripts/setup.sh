#!/bin/bash
echo "=== DataBridge Pipeline Setup ==="
echo ""

# Check Python
python3 --version || { echo "Python 3.11+ required"; exit 1; }

# Check Node
node --version || { echo "Node.js 20+ required"; exit 1; }

# Check Redis
redis-cli ping 2>/dev/null || echo "WARNING: Redis not running. Install: sudo apt install redis-server && sudo systemctl start redis"

# Create Python virtual env
echo "Creating Python virtual environment..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Copy env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env — EDIT THIS FILE with your database, LDAP, and ShotGrid credentials"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your PostgreSQL, LDAP, ShotGrid credentials"
echo "  2. Create database: psql -c 'CREATE DATABASE databridge_db;'"
echo "  3. Run migrations: cd backend && source .venv/bin/activate && alembic upgrade head"
echo "  4. Build frontend: cd frontend && npm run build"
echo "  5. Start app: bash scripts/start.sh"
