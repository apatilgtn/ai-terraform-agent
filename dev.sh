# dev.sh - Development startup script
#!/bin/bash
# dev.sh - Start development environment with all services

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[DEV]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log "🚀 Starting AI Terraform Agent Development Environment"

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
    warn "Docker not found. Starting local development server only."
    export ENVIRONMENT=development
    export LOG_LEVEL=DEBUG
    export RELOAD=true
    ./start.sh
    exit 0
fi

# Start with Docker Compose
log "Starting development services with Docker Compose..."

# Build development image
log "Building development image..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml build

# Start all services
log "Starting all development services..."
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Wait for services to be ready
log "Waiting for services to start..."
sleep 10

# Show service status
log "Development environment started! 🎉"
echo ""
info "Available services:"
info "  📡 API Server:          http://localhost:8000"
info "  📚 API Documentation:   http://localhost:8000/docs"
info "  🔍 Health Check:        http://localhost:8000/health"
info "  🗄️  Database Admin:      http://localhost:8080"
info "  📊 Redis Commander:     http://localhost:8081"
info "  📈 Prometheus:          http://localhost:9090"
info "  📊 Grafana:             http://localhost:3000 (admin/admin)"
info "  📧 Mailhog:             http://localhost:8025"
echo ""
info "Commands:"
info "  📋 View logs:           docker-compose logs -f terraform-agent"
info "  🛑 Stop services:       docker-compose down"
info "  🔄 Restart:             docker-compose restart terraform-agent"
echo ""
log "Happy coding! 🎯"
