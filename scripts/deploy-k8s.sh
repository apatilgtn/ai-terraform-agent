
#!/bin/bash
# scripts/deploy-k8s.sh
# Deploy AI Terraform Agent to Kubernetes

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
    echo -e "${BLUE}[K8S]${NC} $1"
}

# Check prerequisites
if ! command -v kubectl >/dev/null 2>&1; then
    error "kubectl is required but not installed"
    exit 1
fi

# Check cluster connection
if ! kubectl cluster-info >/dev/null 2>&1; then
    error "Cannot connect to Kubernetes cluster"
    exit 1
fi

# Configuration
NAMESPACE="terraform-agent"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REPLICAS="${REPLICAS:-2}"

log "Deploying AI Terraform Agent to Kubernetes"
info "Namespace: $NAMESPACE"
info "Image Tag: $IMAGE_TAG"
info "Replicas: $REPLICAS"

# Check if secrets exist
if ! kubectl get secret terraform-agent-secrets -n "$NAMESPACE" >/dev/null 2>&1; then
    warn "Secrets not found. Creating from environment variables..."
    
    # Check required environment variables
    required_vars=("GITHUB_TOKEN" "GITHUB_OWNER" "GCP_PROJECT_ID")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "$var environment variable is required"
            exit 1
        fi
    done
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secret
    kubectl create secret generic terraform-agent-secrets \
        --namespace="$NAMESPACE" \
        --from-literal=GITHUB_TOKEN="$GITHUB_TOKEN" \
        --from-literal=GITHUB_OWNER="$GITHUB_OWNER" \
        --from-literal=GCP_PROJECT_ID="$GCP_PROJECT_ID" \
        --from-literal=GITHUB_REPO="${GITHUB_REPO:-terraform-infrastructure}"
fi

# Apply Kubernetes manifests
log "Applying Kubernetes manifests..."

# Apply in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/role.yaml
kubectl apply -f k8s/rolebinding.yaml

# Update image tag in deployment
if [[ "$IMAGE_TAG" != "latest" ]]; then
    sed "s|:latest|:$IMAGE_TAG|g" k8s/deployment.yaml | kubectl apply -f -
else
    kubectl apply -f k8s/deployment.yaml
fi

kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml

# Optional: Apply ingress if configured
if [[ -f k8s/ingress.yaml ]] && [[ -n "$DOMAIN" ]]; then
    log "Applying ingress configuration..."
    sed "s/terraform-agent.yourdomain.com/$DOMAIN/g" k8s/ingress.yaml | kubectl apply -f -
fi

# Wait for deployment
log "Waiting for deployment to be ready..."
kubectl rollout status deployment/terraform-agent -n "$NAMESPACE" --timeout=300s

# Show status
log "Deployment status:"
kubectl get pods -n "$NAMESPACE" -l app=terraform-agent

# Get service information
SERVICE_TYPE=$(kubectl get service terraform-agent-service -n "$NAMESPACE" -o jsonpath='{.spec.type}')
if [[ "$SERVICE_TYPE" == "LoadBalancer" ]]; then
    log "Getting LoadBalancer IP..."
    EXTERNAL_IP=$(kubectl get service terraform-agent-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [[ -n "$EXTERNAL_IP" ]]; then
        info "Service available at: http://$EXTERNAL_IP"
    else
        warn "LoadBalancer IP not yet assigned"
    fi
else
    info "Service type: $SERVICE_TYPE"
    info "Port forward with: kubectl port-forward -n $NAMESPACE service/terraform-agent-service 8000:80"
fi

# Show logs
log "Recent logs:"
kubectl logs -n "$NAMESPACE" -l app=terraform-agent --tail=10

log "🎉 Deployment completed successfully!"
info "Check status: kubectl get pods -n $NAMESPACE"
info "View logs: kubectl logs -n $NAMESPACE -l app=terraform-agent -f"
info "Port forward: kubectl port-forward -n $NAMESPACE service/terraform-agent-service 8000:80"
