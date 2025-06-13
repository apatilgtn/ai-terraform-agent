# 🔐 GCP Authentication Setup Guide

Complete guide to setting up Google Cloud Platform authentication for the AI Terraform Agent.

## 🚨 **Common Error**

If you see this error when running `terraform plan`:

```
Error: Attempted to load application default credentials since neither `credentials` nor `access_token` was set in the provider block. No credentials loaded. To use your gcloud credentials, run 'gcloud auth application-default login'
```

**Don't worry!** This guide will fix it step by step.

## 🎯 **Quick Fix (5 Minutes)**

If you just want to get started quickly:

```bash
# 1. Install gcloud CLI
brew install google-cloud-sdk

# 2. Login to your Google account
gcloud auth login

# 3. Set up application default credentials
gcloud auth application-default login

# 4. Set your project (replace with your actual project ID)
gcloud config set project your-gcp-project-id

# 5. Test it works
gcloud compute zones list --limit=1
```

## 📋 **Prerequisites**

- ✅ Google Cloud Platform account
- ✅ GCP project with billing enabled
- ✅ gcloud CLI installed
- ✅ Appropriate permissions (Editor or specific IAM roles)

## 🛠️ **Setup Methods**

### **Method 1: gcloud CLI (Recommended for Development)**

#### **Step 1: Install gcloud CLI**

**macOS:**
```bash
# Using Homebrew
brew install google-cloud-sdk

# Or download installer
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Linux:**
```bash
# Download and install
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
```powershell
# Download from: https://cloud.google.com/sdk/docs/install
# Run the installer
```

#### **Step 2: Authenticate with Google Cloud**

```bash
# 1. Login to your Google account
gcloud auth login

# 2. Set up application default credentials (for Terraform)
gcloud auth application-default login

# 3. List your projects
gcloud projects list

# 4. Set your project
gcloud config set project YOUR_PROJECT_ID

# 5. Verify authentication
gcloud auth list
```

#### **Step 3: Enable Required APIs**

```bash
# Enable necessary APIs for Terraform
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable serviceusage.googleapis.com
```

#### **Step 4: Verify Setup**

```bash
# Test API access
gcloud compute instances list
gcloud storage buckets list

# Check current configuration
gcloud config list
```

### **Method 2: Service Account (Recommended for Production)**

#### **Step 1: Create Service Account**

**Via gcloud CLI:**
```bash
# 1. Create service account
gcloud iam service-accounts create terraform-agent \
    --display-name="AI Terraform Agent" \
    --description="Service account for AI Terraform Agent automation"

# 2. Get service account email
SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:AI Terraform Agent" \
    --format="value(email)")

echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
```

**Via Google Cloud Console:**
1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Name: `terraform-agent`
4. Description: `AI Terraform Agent Service Account`
5. Click "Create and Continue"

#### **Step 2: Grant Permissions**

```bash
# Grant necessary roles to service account
PROJECT_ID=$(gcloud config get-value project)

# Compute Admin (for VMs)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/compute.admin"

# Storage Admin (for buckets)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

# Service Account User
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser"

# Resource Manager (for project-level operations)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/resourcemanager.projectIamAdmin"
```

#### **Step 3: Create and Download Key**

```bash
# Create key file
mkdir -p ~/.config/gcloud

gcloud iam service-accounts keys create ~/.config/gcloud/terraform-agent-key.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/terraform-agent-key.json"

# Add to shell profile
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/terraform-agent-key.json"' >> ~/.zshrc
```

#### **Step 4: Test Service Account**

```bash
# Test authentication
gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"

# Test API access
gcloud compute zones list --limit=1
```

## 🔧 **Configuration Files**

### **Update .env File**

```bash
# Edit your .env file
nano .env

# Add these values:
GCP_PROJECT_ID=your-actual-project-id
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourusername/.config/gcloud/terraform-agent-key.json

# Optional: Specify default region/zone
GCP_REGION=us-central1
GCP_ZONE=us-central1-a
```

### **Update Generated Terraform Files**

Edit `provider.tf` to use your actual project:

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "your-actual-project-id"  # Replace with your project ID
  region  = "us-central1"
  zone    = "us-central1-a"
  
  # Optional: Explicitly set credentials
  # credentials = file("~/.config/gcloud/terraform-agent-key.json")
}
```

Edit `terraform.tfvars`:

```hcl
# terraform.tfvars
project_id  = "your-actual-project-id"
region      = "us-central1"
environment = "dev"
```

## 🧪 **Testing Your Setup**

### **Verification Script**

Create a verification script to test your setup:

```bash
cat > verify-gcp-setup.sh << 'EOF'
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
```

Run the verification:

```bash
./verify-gcp-setup.sh
```

### **Manual Testing**

```bash
# 1. Test gcloud authentication
gcloud auth list

# 2. Test project access
gcloud projects describe $(gcloud config get-value project)

# 3. Test API access
gcloud compute zones list --limit=5
gcloud storage buckets list

# 4. Test Terraform
cd /path/to/your/terraform/files
terraform init
terraform plan
```

## 🚨 **Troubleshooting**

### **Error: "gcloud: command not found"**

**Solution:**
```bash
# macOS
brew install google-cloud-sdk

# Or add to PATH
export PATH=$PATH:$HOME/google-cloud-sdk/bin
```

### **Error: "User does not have permission to access project"**

**Solution:**
```bash
# Check your permissions
gcloud projects get-iam-policy $(gcloud config get-value project)

# Contact project admin to grant you Editor or specific roles:
# - Compute Admin
# - Storage Admin
# - Service Account User
```

### **Error: "API has not been used in project before"**

**Solution:**
```bash
# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

### **Error: "This API method requires billing to be enabled"**

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to Billing
3. Link a billing account to your project
4. Enable billing for the project

### **Error: "Invalid authentication credentials"**

**Solution:**
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Or refresh token
gcloud auth application-default print-access-token
```

### **Error: "terraform plan" still fails**

**Solution:**
```bash
# 1. Clear Terraform cache
rm -rf .terraform*

# 2. Re-initialize
terraform init

# 3. Check provider.tf has correct project ID
cat provider.tf

# 4. Verify credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS
gcloud auth list
```

## 🔐 **Security Best Practices**

### **For Development:**
- ✅ Use `gcloud auth application-default login`
- ✅ Use personal Google account
- ✅ Enable 2FA on your Google account
- ❌ Don't share your personal credentials

### **For Production:**
- ✅ Use service accounts
- ✅ Principle of least privilege (minimal required roles)
- ✅ Rotate service account keys regularly
- ✅ Store keys securely (encrypted, not in version control)
- ❌ Don't use overly permissive roles like Owner/Editor

### **Key Management:**
```bash
# Secure key file permissions
chmod 600 ~/.config/gcloud/terraform-agent-key.json

# Add to .gitignore
echo "*.json" >> .gitignore
echo ".env" >> .gitignore

# Use environment variables instead of hardcoded paths
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/terraform-agent-key.json"
```

## 🌍 **Multi-Environment Setup**

### **Development Environment**
```bash
# Development service account
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/dev-terraform-key.json"
export GCP_PROJECT_ID="my-project-dev"
```

### **Production Environment**
```bash
# Production service account
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/prod-terraform-key.json"
export GCP_PROJECT_ID="my-project-prod"
```

### **Environment Switcher Script**
```bash
cat > switch-gcp-env.sh << 'EOF'
#!/bin/bash

case $1 in
  dev)
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/dev-terraform-key.json"
    export GCP_PROJECT_ID="my-project-dev"
    echo "✅ Switched to DEV environment"
    ;;
  prod)
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/prod-terraform-key.json"
    export GCP_PROJECT_ID="my-project-prod"
    echo "✅ Switched to PROD environment"
    ;;
  *)
    echo "Usage: $0 {dev|prod}"
    exit 1
    ;;
esac

gcloud config set project $GCP_PROJECT_ID
echo "Current project: $(gcloud config get-value project)"
EOF

chmod +x switch-gcp-env.sh

# Usage
source switch-gcp-env.sh dev
```

## 🎯 **Quick Reference**

### **Essential Commands**
```bash
# Authentication
gcloud auth login
gcloud auth application-default login

# Project management
gcloud projects list
gcloud config set project PROJECT_ID

# API management
gcloud services enable compute.googleapis.com
gcloud services list --enabled

# Service accounts
gcloud iam service-accounts list
gcloud iam service-accounts keys create KEY_FILE --iam-account=EMAIL

# Testing
gcloud compute zones list
gcloud storage buckets list
```

### **Environment Variables**
```bash
# Required
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
export GCP_PROJECT_ID="your-project-id"

# Optional
export GCP_REGION="us-central1"
export GCP_ZONE="us-central1-a"
```

### **Files to Check**
- `~/.config/gcloud/application_default_credentials.json` (ADC)
- `~/.config/gcloud/terraform-agent-key.json` (Service Account)
- `.env` (Project configuration)
- `provider.tf` (Terraform provider config)

## 🎉 **Success Indicators**

You'll know everything is working when:

✅ `gcloud auth list` shows an active account  
✅ `gcloud config get-value project` returns your project ID  
✅ `gcloud compute zones list` returns zone data  
✅ `terraform init` completes without errors  
✅ `terraform plan` shows planned changes (not authentication errors)  
✅ Your AI Terraform Agent generates working configurations  

---

## 📞 **Need Help?**

If you're still having issues:

1. **Run the verification script** to identify the specific problem
2. **Check the troubleshooting section** for common solutions
3. **Review GCP Console** for project permissions and billing
4. **Verify API enablement** in the GCP Console
5. **Check our main README** for additional configuration steps

Remember: The most common issue is simply forgetting to run `gcloud auth application-default login` after installing gcloud CLI! 🔑

---

*Happy Infrastructure Coding with Google Cloud Platform! 🚀*
