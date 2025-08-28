#!/bin/bash

# Setup script for Kubernetes ML Pipeline
# This script sets up the required Kubernetes resources for the ML pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if we can connect to Kubernetes cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

print_info "Setting up Kubernetes resources for ML Pipeline..."

# Create namespace
print_info "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Create service account and RBAC
print_info "Creating service account and RBAC..."
kubectl apply -f k8s/service-account.yaml

# Create persistent volume claims
print_info "Creating persistent volume claims..."
kubectl apply -f k8s/persistent-volumes.yaml

# Wait for PVCs to be bound
print_info "Waiting for PVCs to be bound..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if kubectl get pvc -n airflow | grep -q "Bound"; then
        print_info "PVCs are bound successfully"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    if [ $counter -eq $timeout ]; then
        print_warning "PVCs are not bound yet. You may need to check your storage class."
    fi
done

# Verify resources
print_info "Verifying created resources..."

echo ""
print_info "Namespace:"
kubectl get namespace airflow

echo ""
print_info "Service Account:"
kubectl get serviceaccount -n airflow

echo ""
print_info "Persistent Volume Claims:"
kubectl get pvc -n airflow

echo ""
print_info "RBAC Resources:"
kubectl get role,rolebinding -n airflow

echo ""
print_info "Setup completed successfully!"
echo ""
print_info "Next steps:"
echo "1. Update your Airflow Variables with the Kubernetes configuration"
echo "2. Build and push your ML pipeline Docker image"
echo "3. Update the ml_pipeline_image variable in Airflow"
echo "4. Enable and run the ml_pipeline DAG"

echo ""
print_info "Airflow Variables to set:"
echo "- ml_pipeline_image: ghcr.io/yourusername/yourrepo/ml-pipeline:latest"
echo "- kubernetes_namespace: airflow"
echo "- service_account: airflow"
echo "- pvc_data: airflow-data-pvc"
echo "- pvc_models: airflow-models-pvc"
echo "- pvc_predictions: airflow-predictions-pvc"
