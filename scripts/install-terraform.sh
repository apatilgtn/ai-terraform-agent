
#!/bin/bash
# scripts/install-terraform.sh
# Install Terraform on various operating systems

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

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $ARCH in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *) error "Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Default Terraform version
TERRAFORM_VERSION="${TERRAFORM_VERSION:-1.6.4}"

log "Installing Terraform $TERRAFORM_VERSION for $OS/$ARCH"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download URL
TERRAFORM_URL="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${OS}_${ARCH}.zip"

log "Downloading from: $TERRAFORM_URL"
curl -fsSL "$TERRAFORM_URL" -o terraform.zip

# Verify download
if [[ ! -f terraform.zip ]]; then
    error "Failed to download Terraform"
    exit 1
fi

# Extract
log "Extracting Terraform..."
unzip -q terraform.zip

# Install
if [[ -w "/usr/local/bin" ]]; then
    log "Installing to /usr/local/bin (system-wide)"
    sudo mv terraform /usr/local/bin/
    INSTALL_PATH="/usr/local/bin/terraform"
else
    log "Installing to ~/.local/bin (user-local)"
    mkdir -p "$HOME/.local/bin"
    mv terraform "$HOME/.local/bin/"
    INSTALL_PATH="$HOME/.local/bin/terraform"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        warn "Added $HOME/.local/bin to PATH in ~/.bashrc"
        warn "Run 'source ~/.bashrc' or restart your shell"
    fi
fi

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"

# Verify installation
if command -v terraform >/dev/null 2>&1; then
    INSTALLED_VERSION=$(terraform version -json | python3 -c "import sys, json; print(json.load(sys.stdin)['terraform_version'])" 2>/dev/null || terraform version | head -n1 | awk '{print $2}' | sed 's/v//')
    log "Successfully installed Terraform $INSTALLED_VERSION at $INSTALL_PATH"
else
    error "Installation failed - terraform command not found"
    exit 1
fi
