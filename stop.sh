# stop.sh - Server stop script
#!/bin/bash
# stop.sh - Stop the AI Terraform Agent server

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

log "🛑 Stopping AI Terraform Agent"

# Check for PID file
if [[ -f ".server.pid" ]]; then
    PID=$(cat .server.pid)
    if kill -0 "$PID" 2>/dev/null; then
        log "Stopping server process $PID..."
        kill "$PID"
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                log "✅ Server stopped successfully"
                rm -f .server.pid
                exit 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        warn "Process still running, force killing..."
        kill -9 "$PID" 2>/dev/null || true
        rm -f .server.pid
        log "✅ Server force stopped"
    else
        warn "Process $PID not running"
        rm -f .server.pid
    fi
else
    # Try to find and stop uvicorn processes
    PIDS=$(pgrep -f "uvicorn.*main:app" 2>/dev/null || true)
    
    if [[ -n "$PIDS" ]]; then
        log "Found running uvicorn processes: $PIDS"
        echo "$PIDS" | xargs kill
        log "✅ Stopped uvicorn processes"
    else
        warn "No running server found"
    fi
fi

# Stop Docker containers if running
if command -v docker-compose >/dev/null 2>&1; then
    if docker-compose ps -q terraform-agent >/dev/null 2>&1; then
        log "Stopping Docker containers..."
        docker-compose down
        log "✅ Docker containers stopped"
    fi
fi

log "🏁 Shutdown complete"
