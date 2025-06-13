#!/bin/bash
# AI Terraform Agent Setup Script
# This script sets up the complete environment for the Terraform Agent

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
        log_error "Python 3.8 or higher is required. Found: $python_version"
        exit 1
    fi
    log_success "Python $python_version found"
    
    # Check pip
    if ! command_exists pip3; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    log_success "pip3 found"
    
    # Check git
    if ! command_exists git; then
        log_error "git is required but not installed"
        exit 1
    fi
    log_success "git found"
    
    # Check Docker (optional)
    if command_exists docker; then
        log_success "Docker found"
        DOCKER_AVAILABLE=true
    else
        log_warning "Docker not found. Docker deployment will not be available"
        DOCKER_AVAILABLE=false
    fi
    
    # Check Terraform (optional but recommended)
    if command_exists terraform; then
        terraform_version=$(terraform version -json | python3 -c "import sys, json; print(json.load(sys.stdin)['terraform_version'])" 2>/dev/null || echo "unknown")
        log_success "Terraform $terraform_version found"
        TERRAFORM_AVAILABLE=true
    else
        log_warning "Terraform not found. Will install during setup"
        TERRAFORM_AVAILABLE=false
    fi
}

# Install Terraform
install_terraform() {
    if [[ "$TERRAFORM_AVAILABLE" == "true" ]]; then
        log_info "Terraform already installed, skipping..."
        return
    fi
    
    log_info "Installing Terraform..."
    
    # Detect OS
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        arm64|aarch64) ARCH="arm64" ;;
        *) log_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    TERRAFORM_VERSION="1.6.4"
    TERRAFORM_URL="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${OS}_${ARCH}.zip"
    
    # Download and install
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    log_info "Downloading Terraform from $TERRAFORM_URL"
    curl -fsSL "$TERRAFORM_URL" -o terraform.zip
    
    unzip -q terraform.zip
    
    # Install to /usr/local/bin if possible, otherwise to ~/.local/bin
    if [[ -w "/usr/local/bin" ]]; then
        sudo mv terraform /usr/local/bin/
        INSTALL_PATH="/usr/local/bin"
    else
        mkdir -p "$HOME/.local/bin"
        mv terraform "$HOME/.local/bin/"
        INSTALL_PATH="$HOME/.local/bin"
        
        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            log_info "Added $HOME/.local/bin to PATH in ~/.bashrc"
        fi
    fi
    
    cd - >/dev/null
    rm -rf "$TEMP_DIR"
    
    log_success "Terraform installed to $INSTALL_PATH"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Install CLI dependencies
    log_info "Installing CLI dependencies..."
    pip install rich httpx
    
    log_success "Python environment setup complete"
}

# Setup environment variables
configure_environment() {
    log_info "Configuring environment..."
    
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        
        log_warning "Please edit .env file with your configuration:"
        log_warning "  - GITHUB_TOKEN: Your GitHub Personal Access Token"
        log_warning "  - GITHUB_OWNER: Your GitHub username/organization"
        log_warning "  - GCP_PROJECT_ID: Your Google Cloud Project ID"
        
        read -p "Would you like to edit .env now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    else
        log_info ".env file already exists"
    fi
    
    # Source environment variables
    if [[ -f ".env" ]]; then
        set -a  # Automatically export all variables
        source .env
        set +a
    fi
}

# Setup GitHub repository
setup_github_repo() {
    if [[ -z "$GITHUB_TOKEN" ]] || [[ -z "$GITHUB_OWNER" ]]; then
        log_warning "GitHub configuration missing. Skipping repository setup."
        return
    fi
    
    REPO_NAME="${GITHUB_REPO:-terraform-infrastructure}"
    
    log_info "Checking GitHub repository: $GITHUB_OWNER/$REPO_NAME"
    
    # Check if repository exists
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$GITHUB_OWNER/$REPO_NAME")
    
    if [[ "$HTTP_STATUS" == "404" ]]; then
        log_info "Repository doesn't exist. Creating..."
        
        REPO_DATA=$(cat <<EOF
{
  "name": "$REPO_NAME",
  "description": "Infrastructure as Code managed by AI Terraform Agent",
  "private": false,
  "auto_init": true,
  "gitignore_template": "Terraform"
}
EOF
)
        
        curl -s -X POST \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$REPO_DATA" \
            "https://api.github.com/user/repos" > /dev/null
        
        if [[ $? -eq 0 ]]; then
            log_success "GitHub repository created: https://github.com/$GITHUB_OWNER/$REPO_NAME"
        else
            log_error "Failed to create GitHub repository"
        fi
    elif [[ "$HTTP_STATUS" == "200" ]]; then
        log_success "GitHub repository exists: https://github.com/$GITHUB_OWNER/$REPO_NAME"
    else
        log_error "Error checking GitHub repository (HTTP $HTTP_STATUS)"
    fi
}

# Setup GCP authentication
setup_gcp_auth() {
    if [[ -z "$GCP_PROJECT_ID" ]]; then
        log_warning "GCP_PROJECT_ID not set. Skipping GCP setup."
        return
    fi
    
    log_info "Setting up GCP authentication..."
    
    # Check if gcloud is installed
    if ! command_exists gcloud; then
        log_warning "gcloud CLI not found. Please install Google Cloud SDK manually."
        log_info "Visit: https://cloud.google.com/sdk/docs/install"
        return
    fi
    
    # Check if already authenticated
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [[ "$CURRENT_PROJECT" == "$GCP_PROJECT_ID" ]]; then
        log_success "Already authenticated with GCP project: $GCP_PROJECT_ID"
    else
        log_info "Please authenticate with GCP and set project:"
        echo "  gcloud auth login"
        echo "  gcloud config set project $GCP_PROJECT_ID"
        echo "  gcloud auth application-default login"
    fi
    
    # Enable required APIs
    log_info "Enabling required GCP APIs..."
    gcloud services enable compute.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
    gcloud services enable storage.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
    gcloud services enable cloudresourcemanager.googleapis.com --project="$GCP_PROJECT_ID" 2>/dev/null || true
}

# Create startup scripts
create_scripts() {
    log_info "Creating startup scripts..."
    
    # Create start script
    cat > start.sh << 'EOF'
#!/bin/bash
# Start the AI Terraform Agent

# Activate virtual environment
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# Load environment variables
if [[ -f ".env" ]]; then
    set -a
    source .env
    set +a
fi

# Start the server
echo "Starting AI Terraform Agent..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF
    
    chmod +x start.sh
    
    # Create CLI wrapper script
    cat > terraform-cli << 'EOF'
#!/bin/bash
# CLI wrapper for AI Terraform Agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment
if [[ -d "$SCRIPT_DIR/venv" ]]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run CLI
python3 "$SCRIPT_DIR/cli.py" "$@"
EOF
    
    chmod +x terraform-cli
    
    # Create systemd service file (optional)
    cat > terraform-agent.service << EOF
[Unit]
Description=AI Terraform Agent
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$(pwd)/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    log_success "Startup scripts created:"
    log_info "  - start.sh: Start the server"
    log_info "  - terraform-cli: CLI tool"
    log_info "  - terraform-agent.service: Systemd service file"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run pytest
    if python3 -m pytest tests/ -v; then
        log_success "All tests passed!"
    else
        log_warning "Some tests failed. Check the output above."
    fi
}

# Docker setup
setup_docker() {
    if [[ "$DOCKER_AVAILABLE" != "true" ]]; then
        log_info "Docker not available, skipping Docker setup"
        return
    fi
    
    log_info "Setting up Docker environment..."
    
    # Build Docker image
    log_info "Building Docker image..."
    docker build -t terraform-agent:latest .
    
    log_success "Docker image built successfully"
    log_info "To run with Docker: docker-compose up -d"
}

# Main setup function
main() {
    log_info "🚀 Starting AI Terraform Agent Setup"
    echo
    
    # Check requirements first
    check_requirements
    echo
    
    # Install Terraform if needed
    install_terraform
    echo
    
    # Setup Python environment
    setup_python_env
    echo
    
    # Configure environment
    configure_environment
    echo
    
    # Setup GitHub repository
    setup_github_repo
    echo
    
    # Setup GCP authentication
    setup_gcp_auth
    echo
    
    # Create startup scripts
    create_scripts
    echo
    
    # Run tests
    if [[ "${RUN_TESTS:-true}" == "true" ]]; then
        run_tests
        echo
    fi
    
    # Setup Docker if available
    if [[ "${SETUP_DOCKER:-true}" == "true" ]]; then
        setup_docker
        echo
    fi
    
    # Final instructions
    log_success "🎉 Setup complete!"
    echo
    log_info "Next steps:"
    log_info "1. Review and update your .env file with proper credentials"
    log_info "2. Start the server: ./start.sh"
    log_info "3. Test the CLI: ./terraform-cli health"
    log_info "4. Generate your first Terraform: ./terraform-cli generate 'Create a small VM'"
    echo
    log_info "Documentation and examples:"
    log_info "- Server API: http://localhost:8000/docs"
    log_info "- CLI help: ./terraform-cli --help"
    log_info "- Interactive mode: ./terraform-cli interactive"
    echo
    log_info "Happy Infrastructure Coding! 🏗️"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            RUN_TESTS=false
            shift
            ;;
        --skip-docker)
            SETUP_DOCKER=false
            shift
            ;;
        --help|-h)
            echo "AI Terraform Agent Setup Script"
            echo
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --skip-tests    Skip running tests"
            echo "  --skip-docker   Skip Docker setup"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main setup
main
