
#!/bin/bash
# scripts/create-github-repo.sh
# Create GitHub repository for Terraform files

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[GITHUB]${NC} $1"
}

# Check if GitHub CLI is installed
if ! command -v gh >/dev/null 2>&1; then
    error "GitHub CLI (gh) is required but not installed"
    info "Install it from: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status >/dev/null 2>&1; then
    error "Please authenticate with GitHub CLI first"
    info "Run: gh auth login"
    exit 1
fi

# Get repository details
REPO_NAME="${GITHUB_REPO:-terraform-infrastructure}"
REPO_DESCRIPTION="Infrastructure as Code managed by AI Terraform Agent"

log "Creating GitHub repository: $REPO_NAME"

# Create repository
gh repo create "$REPO_NAME" \
    --description "$REPO_DESCRIPTION" \
    --public \
    --gitignore "Terraform" \
    --license "MIT"

# Clone the repository
log "Cloning repository..."
gh repo clone "$REPO_NAME"
cd "$REPO_NAME"

# Create initial structure
log "Setting up repository structure..."

mkdir -p {environments/{dev,staging,prod},modules,docs}

# Create README
cat > README.md << 'EOF'
# Infrastructure as Code

This repository contains Terraform configurations managed by the AI Terraform Agent.

## Structure
- `environments/` - Environment-specific configurations
- `modules/` - Reusable Terraform modules
- `docs/` - Documentation

## Usage
Configurations in this repository are automatically generated and managed by the AI Terraform Agent.

## Generated Resources
This repository will contain automatically generated Terraform configurations for:
- Google Cloud Platform resources
- AWS resources (future)
- Azure resources (future)

---
*This repository is managed by AI Terraform Agent*
EOF

# Create .gitignore if not exists
if [[ ! -f .gitignore ]]; then
    cat > .gitignore << 'EOF'
# Terraform
*.tfstate
*.tfstate.*
*.tfvars
.terraform/
.terraform.lock.hcl
terraform.tfplan

# Sensitive files
*.pem
*.key
service-account.json
EOF
fi

# Create branch protection workflow
mkdir -p .github/workflows
cat > .github/workflows/terraform-validate.yml << 'EOF'
name: Terraform Validate

on:
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.6.4
    
    - name: Terraform Format
      run: terraform fmt -check -recursive
    
    - name: Terraform Init
      run: |
        find . -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do
          echo "Initializing $dir"
          cd "$dir"
          terraform init -backend=false
          cd - > /dev/null
        done
    
    - name: Terraform Validate
      run: |
        find . -name "*.tf" -exec dirname {} \; | sort -u | while read dir; do
          echo "Validating $dir"
          cd "$dir"
          terraform validate
          cd - > /dev/null
        done
EOF

# Commit and push
log "Creating initial commit..."
git add .
git commit -m "🎉 Initial repository setup by AI Terraform Agent"
git push origin main

# Set up branch protection
log "Setting up branch protection..."
gh api repos/:owner/:repo/branches/main/protection \
    --method PUT \
    --field required_status_checks='{"strict":true,"contexts":["validate"]}' \
    --field enforce_admins=true \
    --field required_pull_request_reviews='{"required_approving_review_count":1}' \
    --field restrictions=null || warn "Could not set branch protection (check permissions)"

log "✅ GitHub repository setup completed!"
info "Repository URL: $(gh repo view --json url -q .url)"
info "Configure your .env file with:"
echo "GITHUB_OWNER=$(gh api user --jq .login)"
echo "GITHUB_REPO=$REPO_NAME"
