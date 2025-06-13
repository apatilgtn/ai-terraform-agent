#!/bin/bash

echo "🔍 Verifying GCP Authentication Setup..."
echo "======================================"

# Check gcloud installation
if command -v gcloud >/dev/null 2>&1; then
    echo "✅ gcloud CLI installed: $(gcloud version --format='value(Google Cloud SDK)')"
else
    echo "❌ gcloud CLI not found"
    echo "   Install: brew install google-cloud-sdk"
    exit 1
fi

# Check authentication
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -n "$ACTIVE_ACCOUNT" ]; then
    echo "✅ Authenticated as: $ACTIVE_ACCOUNT"
else
    echo "❌ Not authenticated"
    echo "   Run: gcloud auth login"
    exit 1
fi

# Check project
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT" ]; then
    echo "✅ Project set: $PROJECT"
else
    echo "❌ No project set"
    echo "   Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# Check application default credentials
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "✅ Service account key found: $GOOGLE_APPLICATION_CREDENTIALS"
    else
        echo "❌ Service account key file not found: $GOOGLE_APPLICATION_CREDENTIALS"
        exit 1
    fi
else
    # Check if ADC is set up
    ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"
    if [ -f "$ADC_FILE" ]; then
        echo "✅ Application Default Credentials found"
    else
        echo "❌ No Application Default Credentials"
        echo "   Run: gcloud auth application-default login"
        exit 1
    fi
fi

# Test API access
echo "🔍 Testing API access..."

if gcloud compute zones list --limit=1 >/dev/null 2>&1; then
    echo "✅ Compute Engine API accessible"
else
    echo "❌ Compute Engine API not accessible"
    echo "   Enable: gcloud services enable compute.googleapis.com"
    exit 1
fi

if gcloud storage buckets list --limit=1 >/dev/null 2>&1; then
    echo "✅ Cloud Storage API accessible"
else
    echo "❌ Cloud Storage API not accessible"
    echo "   Enable: gcloud services enable storage.googleapis.com"
    exit 1
fi

# Test Terraform
if command -v terraform >/dev/null 2>&1; then
    echo "✅ Terraform installed: $(terraform version | head -n1)"
    
    # Test terraform plan in a temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    cat > provider.tf << EOL
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "$PROJECT"
  region  = "us-central1"
}

data "google_compute_zones" "available" {
  region = "us-central1"
}
EOL
    
    if terraform init >/dev/null 2>&1 && terraform plan >/dev/null 2>&1; then
        echo "✅ Terraform can authenticate with GCP"
    else
        echo "❌ Terraform authentication failed"
        exit 1
    fi
    
    cd - >/dev/null
    rm -rf "$TEMP_DIR"
else
    echo "⚠️  Terraform not found (optional)"
fi

echo ""
echo "🎉 GCP Authentication Setup Complete!"
echo "======================================"
echo "You can now run:"
echo "  terraform init"
echo "  terraform plan"
echo "  terraform apply"
EOF

chmod +x verify-gcp-setup.sh
