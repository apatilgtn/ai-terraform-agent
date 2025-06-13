
docs/DEPLOYMENT.md
Deployment Guide
Prerequisites

Docker or Kubernetes cluster
GitHub Personal Access Token
Google Cloud Project with enabled APIs

Environment Variables
bashGITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=terraform-infrastructure
GCP_PROJECT_ID=your_gcp_project_id
Deployment Options
1. Docker Deployment
bash# Build and run
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f terraform-agent
2. Kubernetes Deployment
bash# Create namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n terraform-agent
3. Local Development
bash# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload
Configuration
GitHub Setup

Create Personal Access Token with repo permissions
Create or use existing repository for Terraform files
Configure environment variables

GCP Setup

Create GCP project
Enable required APIs:

Compute Engine API
Cloud Storage API
Cloud Resource Manager API


Setup authentication:
bashgcloud auth application-default login


Monitoring

Health endpoint: GET /health
Logs: Available via Docker/Kubernetes logging
Metrics: Prometheus-compatible (future enhancement)
