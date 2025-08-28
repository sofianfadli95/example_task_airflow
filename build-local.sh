#!/bin/bash

# Local Docker Build Script for ML Pipeline
# This script builds and tests the ML pipeline Docker image locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
IMAGE_NAME="ml-pipeline"
TAG="local"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_info "Building ML Pipeline Docker image locally..."
echo "Image: ${FULL_IMAGE_NAME}"
echo ""

# Step 1: Build the Docker image
print_step "1. Building Docker image..."
cd ml_pipeline
if docker build --no-cache -f Dockerfile.dev -t ${FULL_IMAGE_NAME} .; then
    print_info "✅ Docker image built successfully"
else
    print_error "❌ Failed to build Docker image"
    exit 1
fi

cd ..

# Step 2: Create test directories
print_step "2. Setting up test directories..."
mkdir -p test_data test_models test_predictions

# Step 3: Test training script
print_step "3. Testing training script..."
if docker run --rm \
    -v $(pwd)/test_models:/app/models \
    -v $(pwd)/test_data:/app/data \
    ${FULL_IMAGE_NAME} \
    python train.py --model-output-path /app/models; then
    print_info "✅ Training script executed successfully"
else
    print_error "❌ Training script failed"
    exit 1
fi

# Step 4: Verify model was created
print_step "4. Verifying model creation..."
if [ -f "test_models/latest_model.pkl" ]; then
    print_info "✅ Model file created successfully"
else
    print_error "❌ Model file not found"
    exit 1
fi

# Step 5: Test prediction script
print_step "5. Testing prediction script..."
if docker run --rm \
    -v $(pwd)/test_models:/app/models \
    -v $(pwd)/test_predictions:/app/predictions \
    ${FULL_IMAGE_NAME} \
    python predict.py --model-path /app/models/latest_model.pkl --output-path /app/predictions; then
    print_info "✅ Prediction script executed successfully"
else
    print_error "❌ Prediction script failed"
    exit 1
fi

# Step 6: Verify predictions were created
print_step "6. Verifying predictions creation..."
if [ -f "test_predictions/latest_predictions.csv" ]; then
    print_info "✅ Predictions file created successfully"
else
    print_error "❌ Predictions file not found"
    exit 1
fi

# Step 7: Test validation script
print_step "7. Testing validation script..."
if docker run --rm \
    -v $(pwd)/test_models:/app/models \
    -v $(pwd)/test_predictions:/app/predictions \
    ${FULL_IMAGE_NAME} \
    python validate.py validate-model --models-dir /app/models; then
    print_info "✅ Model validation script executed successfully"
else
    print_error "❌ Model validation script failed"
    exit 1
fi

if docker run --rm \
    -v $(pwd)/test_models:/app/models \
    -v $(pwd)/test_predictions:/app/predictions \
    ${FULL_IMAGE_NAME} \
    python validate.py validate-predictions --predictions-dir /app/predictions; then
    print_info "✅ Predictions validation script executed successfully"
else
    print_error "❌ Predictions validation script failed"
    exit 1
fi

# Step 8: Test cleanup script
print_step "8. Testing cleanup script..."
if docker run --rm \
    -v $(pwd)/test_models:/app/models \
    -v $(pwd)/test_predictions:/app/predictions \
    ${FULL_IMAGE_NAME} \
    python validate.py cleanup --models-dir /app/models --predictions-dir /app/predictions --keep-count 5; then
    print_info "✅ Cleanup script executed successfully"
else
    print_error "❌ Cleanup script failed"
    exit 1
fi

# Step 9: Show image info
print_step "9. Image information..."
echo ""
docker images ${FULL_IMAGE_NAME}
echo ""
docker inspect ${FULL_IMAGE_NAME} --format='{{.Config.Env}}' | tr ' ' '\n' | grep -E '^[A-Z]'

# Step 10: Show test results
print_step "10. Test results summary..."
echo ""
print_info "Generated files:"
echo "Models directory:"
ls -la test_models/ 2>/dev/null || echo "  (empty)"
echo ""
echo "Predictions directory:"
ls -la test_predictions/ 2>/dev/null || echo "  (empty)"
echo ""

# Step 11: Interactive test option
print_step "11. Interactive testing (optional)"
echo ""
print_info "You can now test the image interactively:"
echo "docker run -it --rm \\"
echo "  -v \$(pwd)/test_models:/app/models \\"
echo "  -v \$(pwd)/test_predictions:/app/predictions \\"
echo "  -v \$(pwd)/test_data:/app/data \\"
echo "  ${FULL_IMAGE_NAME} bash"
echo ""

# Step 12: Cleanup option
read -p "Do you want to clean up test directories? (y/N): " cleanup_choice
if [[ $cleanup_choice =~ ^[Yy]$ ]]; then
    print_step "12. Cleaning up test directories..."
    rm -rf test_data test_models test_predictions
    print_info "✅ Test directories cleaned up"
else
    print_info "Test directories kept for inspection"
fi

print_info "🎉 Local build and testing completed successfully!"
echo ""
print_info "Next steps:"
echo "1. If everything looks good, push your code to trigger GitHub Actions"
echo "2. Or manually tag and push the image:"
echo "   docker tag ${FULL_IMAGE_NAME} ghcr.io/yourusername/yourrepo/ml-pipeline:latest"
echo "   docker push ghcr.io/yourusername/yourrepo/ml-pipeline:latest"
echo ""
print_info "To use this local image in Airflow, update the ml_pipeline_image variable to:"
echo "   ${FULL_IMAGE_NAME}"
