
#!/bin/bash
# scripts/validate-terraform.sh
# Validate generated Terraform configurations

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

# Check if Terraform is installed
if ! command -v terraform >/dev/null 2>&1; then
    error "Terraform is required but not installed"
    exit 1
fi

# Directory to validate
TERRAFORM_DIR="${1:-terraform_output}"

if [[ ! -d "$TERRAFORM_DIR" ]]; then
    error "Directory $TERRAFORM_DIR does not exist"
    exit 1
fi

log "Validating Terraform configuration in: $TERRAFORM_DIR"

cd "$TERRAFORM_DIR"

# Format check
log "Checking Terraform format..."
if terraform fmt -check -diff; then
    log "✅ Format check passed"
else
    warn "Format issues found. Run 'terraform fmt' to fix."
fi

# Initialize
log "Initializing Terraform..."
if terraform init -backend=false; then
    log "✅ Initialization successful"
else
    error "❌ Initialization failed"
    exit 1
fi

# Validate
log "Validating configuration..."
if terraform validate; then
    log "✅ Validation successful"
else
    error "❌ Validation failed"
    exit 1
fi

# Plan (if possible)
log "Creating execution plan..."
if terraform plan -out=tfplan > plan.out 2>&1; then
    log "✅ Plan created successfully"
    
    # Show plan summary
    echo
    log "Plan Summary:"
    grep -E "(Plan:|No changes)" plan.out || true
    
    # Check for potential issues
    if grep -q "Error:" plan.out; then
        warn "Potential issues found in plan:"
        grep "Error:" plan.out
    fi
else
    warn "⚠️  Plan creation failed (this may be expected without proper credentials)"
    if [[ -f plan.out ]]; then
        log "Plan output:"
        cat plan.out
    fi
fi

# Security scan
log "Running security checks..."
if command -v tfsec >/dev/null 2>&1; then
    tfsec . || warn "Security issues found"
else
    warn "tfsec not installed - skipping security scan"
fi

# Cost estimation
if command -v infracost >/dev/null 2>&1; then
    log "Estimating costs..."
    infracost breakdown --path . || warn "Cost estimation failed"
else
    warn "infracost not installed - skipping cost estimation"
fi

log "🎉 Terraform validation completed!"
