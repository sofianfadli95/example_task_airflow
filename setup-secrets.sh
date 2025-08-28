#!/bin/bash

# Setup script for Kubernetes secrets
# Run this after setting up your basic Kubernetes resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace airflow &> /dev/null; then
    print_error "Airflow namespace not found. Run ./setup-k8s.sh first"
    exit 1
fi

print_info "Setting up Kubernetes secrets..."

# Check if this is a public or private repository
echo ""
echo "Is your GitHub repository and container registry private? (y/N)"
read -r IS_PRIVATE

if [[ $IS_PRIVATE =~ ^[Yy]$ ]]; then
    print_info "Setting up container registry secret for private repository..."
    
    echo "Enter your GitHub username:"
    read -r GITHUB_USERNAME
    
    echo "Enter your GitHub Personal Access Token (with packages:read permission):"
    read -s GITHUB_TOKEN
    
    echo "Enter your email address:"
    read -r GITHUB_EMAIL
    
    # Create container registry secret
    kubectl create secret docker-registry ghcr-secret \
        --docker-server=ghcr.io \
        --docker-username="$GITHUB_USERNAME" \
        --docker-password="$GITHUB_TOKEN" \
        --docker-email="$GITHUB_EMAIL" \
        --namespace=airflow \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_info "✅ Container registry secret created"
else
    print_info "Using public repository - no registry secret needed"
    # Remove imagePullSecrets from service account if it exists
    kubectl patch serviceaccount airflow -n airflow --type='json' -p='[{"op": "remove", "path": "/imagePullSecrets"}]' 2>/dev/null || true
fi

# Create any additional secrets if needed
print_info "Setting up additional secrets..."

# Example: Create a secret for external API keys (if your ML pipeline needs them)
# kubectl create secret generic ml-api-keys \
#     --from-literal=api-key="your-api-key" \
#     --namespace=airflow

print_info "Verifying secrets..."
kubectl get secrets -n airflow

print_info "✅ Secrets setup completed!"

echo ""
print_info "Next steps:"
echo "1. Import Airflow variables: airflow variables import airflow-variables.json"
echo "2. Or set them manually in Airflow UI"
echo "3. Deploy your DAG and test the pipeline"
