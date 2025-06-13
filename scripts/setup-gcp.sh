
#!/bin/bash
# scripts/setup-gcp.sh  
# Setup Google Cloud Platform for Terraform Agent

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud >/dev/null 2>&1; then
    error "gcloud CLI is required but not installed"
    info "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
if [[ -z "$GCP_PROJECT_ID" ]]; then
    echo "Enter your GCP Project ID:"
    read -p "Project ID: " GCP_PROJECT_ID
fi

if [[ -z "$GCP_PROJECT_ID" ]]; then
    error "GCP Project ID is required"
    exit 1
fi

log "Setting up GCP project: $GCP_PROJECT_ID"

# Set project
gcloud config set project "$GCP_PROJECT_ID"

# Enable required APIs
log "Enabling required APIs..."
APIS=(
    "compute.googleapis.com"
    "storage.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "iam.googleapis.com"
    "serviceusage.googleapis.com"
)

for api in "${APIS[@]}"; do
    log "Enabling $api..."
    gcloud services enable "$api" --project="$GCP_PROJECT_ID"
done

# Create service account for Terraform
SERVICE_ACCOUNT="terraform-agent-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

log "Creating service account: $SERVICE_ACCOUNT"
gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
    --display-name="Terraform Agent Service Account" \
    --description="Service account for AI Terraform Agent" \
    --project="$GCP_PROJECT_ID" || true

# Grant necessary roles
log "Granting IAM roles..."
ROLES=(
    "roles/compute.admin"
    "roles/storage.admin"
    "roles/iam.serviceAccountUser"
    "roles/resourcemanager.projectIamAdmin"
)

for role in "${ROLES[@]}"; do
    log "Granting $role..."
    gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role"
done

# Create and download service account key
KEY_FILE="$HOME/.config/gcloud/terraform-agent-key.json"
mkdir -p "$(dirname "$KEY_FILE")"

log "Creating service account key..."
gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SERVICE_ACCOUNT_EMAIL" \
    --project="$GCP_PROJECT_ID"

# Set environment variable
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_FILE\"" >> "$HOME/.bashrc"
export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"

# Test authentication
log "Testing authentication..."
gcloud auth application-default print-access-token > /dev/null

log "✅ GCP setup completed successfully!"
info "Service account key saved to: $KEY_FILE"
info "Environment variable added to ~/.bashrc"
info "Run 'source ~/.bashrc' to load the environment variable"

# Optional: Create state bucket
read -p "Create a GCS bucket for Terraform state? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    BUCKET_NAME="${GCP_PROJECT_ID}-terraform-state"
    log "Creating state bucket: $BUCKET_NAME"
    
    gsutil mb -p "$GCP_PROJECT_ID" -l "us-central1" "gs://$BUCKET_NAME" || true
    gsutil versioning set on "gs://$BUCKET_NAME"
    
    info "Terraform state bucket created: gs://$BUCKET_NAME" 
    info "Add this to your provider.tf backend configuration:"
    echo '  backend "gcs" {'
    echo "    bucket = \"$BUCKET_NAME\""
    echo '    prefix = "terraform/state"'
    echo '  }'
fi
