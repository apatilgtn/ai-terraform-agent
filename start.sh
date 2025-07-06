#!/bin/bash
# start.sh - Start the AI Terraform Agent server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[SERVER]${NC} $1"
}

# Configuration
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
RELOAD="${RELOAD:-false}"

log "🚀 Starting AI Terraform Agent"

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    error "main.py not found. Please run from the project root directory."
    exit 1
fi

# Activate virtual environment if it exists
if [[ -d "venv" ]]; then
    log "Activating virtual environment..."
    source venv/bin/activate
elif [[ -d ".venv" ]]; then
    log "Activating virtual environment..."
    source .venv/bin/activate
else
    warn "No virtual environment found. Using system Python."
fi

# Load environment variables
if [[ -f ".env" ]]; then
    log "Loading environment variables from .env"
    set -a
    source .env
    set +a
else
    warn "No .env file found. Using system environment variables."
fi

# Validate required environment variables
REQUIRED_VARS=("GITHUB_TOKEN" "GITHUB_OWNER" "GCP_PROJECT_ID")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        MISSING_VARS+=("$var")
    fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    warn "Missing recommended environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        warn "  - $var"
    done
    warn "Some features may not work without these variables."
    warn "Set these variables in your .env file or environment for full functionality."
    
    # Set default values for local testing
    if [[ -z "$GITHUB_TOKEN" ]]; then
        export GITHUB_TOKEN="local-testing-token"
    fi
    if [[ -z "$GITHUB_OWNER" ]]; then
        export GITHUB_OWNER="local-testing-owner"
    fi
    if [[ -z "$GCP_PROJECT_ID" ]]; then
        export GCP_PROJECT_ID="local-testing-project"
    fi
fi

# Check if required dependencies are installed
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    error "Required dependencies not found. Please install:"
    error "  pip install -r requirements.txt"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Set up logging
export LOG_FILE="logs/terraform-agent-$(date +%Y%m%d).log"

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "http://localhost:$PORT/health" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    return 1
}

# Start server
info "Configuration:"
info "  Host: $HOST"
info "  Port: $PORT"
info "  Workers: $WORKERS"
info "  Reload: $RELOAD"
info "  Log file: $LOG_FILE"

log "Starting server..."

# Determine uvicorn command based on environment
if [[ "$RELOAD" == "true" ]]; then
    # Development mode with auto-reload
    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level info \
        --access-log \
        --log-config logging.json 2>/dev/null || \
    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level info \
        --access-log &
else
    # Production mode
    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info \
        --access-log \
        --log-config logging.json 2>/dev/null || \
    uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info \
        --access-log &
fi

SERVER_PID=$!

# Wait for server to start
log "Waiting for server to start..."
if health_check; then
    log "✅ Server started successfully!"
    info "Server is running at: http://localhost:$PORT"
    info "API documentation: http://localhost:$PORT/docs"
    info "Health check: http://localhost:$PORT/health"
    info "Process ID: $SERVER_PID"
    
    # Save PID for later use
    echo $SERVER_PID > .server.pid
    
    # Wait for server process
    wait $SERVER_PID
else
    error "❌ Server failed to start within 30 seconds"
    exit 1
fi
