#!/bin/bash
# AI Terraform Agent Setup Script - Fixed Version
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

# Fixed version comparison function
version_compare() {
    local version1=$1
    local version2=$2
    
    # Convert versions to comparable format (remove 'v' prefix if present)
    version1=${version1#v}
    version2=${version2#v}
    
    # Use Python to compare versions properly
    python3 -c "
import sys
from packaging import version
v1 = version.parse('$version1')
v2 = version.parse('$version2')
sys.exit(0 if v1 >= v2 else 1)
" 2>/dev/null
}

# Check requirements
check_requirements() {
    log_info "🚀 Starting AI Terraform Agent Setup"
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Get Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Found Python $python_version"
    
    # Check if version is 3.8 or higher using a more reliable method
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "✅ Python $python_version is compatible (3.8+ required)"
    else
        log_error "Python 3.8 or higher is required. Found: $python_version"
        exit 1
    fi
    
    # Check pip
    if ! command_exists pip3 && ! command_exists pip; then
        log_error "pip is required but not installed"
        exit 1
    fi
    log_success "✅ pip found"
    
    # Check git
    if ! command_exists git; then
        log_error "git is required but not installed"
        exit 1
    fi
    log_success "✅ git found"
    
    # Check Docker (optional)
    if command_exists docker; then
        log_success "✅ Docker found"
        DOCKER_AVAILABLE=true
    else
        log_warning "⚠️  Docker not found. Docker deployment will not be available"
        DOCKER_AVAILABLE=false
    fi
    
    # Check Terraform (optional but recommended)
    if command_exists terraform; then
        terraform_version=$(terraform version -json 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['terraform_version'])" 2>/dev/null || terraform version | head -n1 | awk '{print $2}' | sed 's/v//' || echo "unknown")
        log_success "✅ Terraform $terraform_version found"
        TERRAFORM_AVAILABLE=true
    else
        log_warning "⚠️  Terraform not found. Will install during setup"
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
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
            log_info "Added $HOME/.local/bin to PATH in shell config files"
        fi
    fi
    
    cd - >/dev/null
    rm -rf "$TEMP_DIR"
    
    log_success "✅ Terraform installed to $INSTALL_PATH"
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
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    log_success "✅ Python environment setup complete"
}

# Setup environment variables
configure_environment() {
    log_info "Configuring environment..."
    
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        
        log_warning "⚠️  Please edit .env file with your configuration:"
        log_warning "  - GITHUB_TOKEN: Your GitHub Personal Access Token"
        log_warning "  - GITHUB_OWNER: Your GitHub username/organization"
        log_warning "  - GCP_PROJECT_ID: Your Google Cloud Project ID"
        
        read -p "Would you like to edit .env now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        fi
    else
        log_info "✅ .env file already exists"
    fi
}

# Create startup scripts
create_scripts() {
    log_info "Making scripts executable..."
    
    # Make scripts executable
    chmod +x start.sh stop.sh dev.sh terraform-cli 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "✅ Scripts made executable"
}

# Run tests
run_tests() {
    if [[ "${RUN_TESTS:-true}" != "true" ]]; then
        return
    fi
    
    log_info "Running basic tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test basic imports
    python3 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import fastapi
    print('✅ FastAPI imported successfully')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')
    sys.exit(1)

try:
    import uvicorn
    print('✅ Uvicorn imported successfully')
except ImportError as e:
    print(f'❌ Uvicorn import failed: {e}')
    sys.exit(1)

try:
    import httpx
    print('✅ HTTPX imported successfully')
except ImportError as e:
    print(f'❌ HTTPX import failed: {e}')
    sys.exit(1)

print('🎉 All core dependencies working!')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "✅ Basic tests passed!"
    else
        log_warning "⚠️  Some tests failed. Check the output above."
    fi
}

# Main setup function
main() {
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
    
    # Create startup scripts
    create_scripts
    echo
    
    # Run tests
    run_tests
    echo
    
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
    log_success "🏗️  Happy Infrastructure Coding!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            RUN_TESTS=false
            shift
            ;;
        --skip-terraform)
            TERRAFORM_AVAILABLE=true
            shift
            ;;
        --help|-h)
            echo "AI Terraform Agent Setup Script"
            echo
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --skip-tests       Skip running tests"
            echo "  --skip-terraform   Skip Terraform installation"
            echo "  --help, -h         Show this help message"
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
