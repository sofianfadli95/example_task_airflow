# Local Development Guide

This guide explains how to build, test, and develop the ML pipeline Docker images locally before pushing to the repository.

## 🚀 Quick Start

### Option 1: Automated Build and Test

```bash
# Build and test everything automatically
./build-local.sh
```

This script will:
1. Build the Docker image locally
2. Test all ML pipeline components
3. Verify file generation
4. Show test results

### Option 2: Manual Step-by-Step

```bash
# 1. Build the production image
cd ml_pipeline
docker build -t ml-pipeline:local .

# 2. Build the development image (optional)
docker build -f Dockerfile.dev -t ml-pipeline:dev .

# 3. Create test directories
mkdir -p test_data test_models test_predictions

# 4. Test training
docker run --rm \
  -v $(pwd)/../test_models:/app/models \
  ml-pipeline:local \
  python train.py --model-output-path /app/models

# 5. Test prediction
docker run --rm \
  -v $(pwd)/../test_models:/app/models \
  -v $(pwd)/../test_predictions:/app/predictions \
  ml-pipeline:local \
  python predict.py --model-path /app/models/latest_model.pkl --output-path /app/predictions
```

## 🛠️ Development Workflow

### 1. Development Container

Use the development container for interactive development:

```bash
# Start development container
docker run -it --rm \
  -v $(pwd)/ml_pipeline:/app \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/predictions:/app/predictions \
  -p 8888:8888 \
  ml-pipeline:dev

# Inside the container, you can use:
train --help                    # Run training
predict --help                  # Run prediction
validate validate-model         # Validate model
jupyter                         # Start Jupyter notebook
format                          # Format code
lint                           # Lint code
```

### 2. Code Changes and Testing

When you make changes to your Python scripts:

```bash
# 1. Edit your code in ml_pipeline/
# 2. Rebuild the image
docker build -t ml-pipeline:local ml_pipeline/

# 3. Test your changes
./build-local.sh

# 4. If tests pass, commit and push
git add .
git commit -m "Updated ML pipeline"
git push origin main
```

### 3. Testing with Different Data

```bash
# Prepare your own training data
cp your_data.csv data/training_data.csv

# Test with your data
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  ml-pipeline:local \
  python train.py --data-path /app/data/training_data.csv --model-output-path /app/models
```

## 🧪 Testing Strategies

### 1. Unit Testing

Create test files in `ml_pipeline/tests/`:

```bash
# Run tests in development container
docker run --rm \
  -v $(pwd)/ml_pipeline:/app \
  ml-pipeline:dev \
  pytest /app/tests/
```

### 2. Integration Testing

Test the complete pipeline:

```bash
# Full pipeline test
./build-local.sh

# Or manually:
docker run --rm \
  -v $(pwd)/test_models:/app/models \
  -v $(pwd)/test_predictions:/app/predictions \
  ml-pipeline:local \
  bash -c "
    python train.py --model-output-path /app/models && \
    python predict.py --model-path /app/models/latest_model.pkl --output-path /app/predictions && \
    python validate.py validate-model --models-dir /app/models && \
    python validate.py validate-predictions --predictions-dir /app/predictions
  "
```

### 3. Performance Testing

Test with larger datasets:

```bash
# Generate larger test dataset
docker run --rm \
  -v $(pwd)/test_data:/app/data \
  ml-pipeline:local \
  python -c "
from sklearn.datasets import make_classification
import pandas as pd
X, y = make_classification(n_samples=10000, n_features=50, random_state=42)
df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(50)])
df['target'] = y
df.to_csv('/app/data/large_dataset.csv', index=False)
print('Large dataset created')
"

# Test with large dataset
docker run --rm \
  -v $(pwd)/test_data:/app/data \
  -v $(pwd)/test_models:/app/models \
  ml-pipeline:local \
  python train.py --data-path /app/data/large_dataset.csv --model-output-path /app/models
```

## 🔍 Debugging

### 1. Interactive Debugging

```bash
# Start container with bash
docker run -it --rm \
  -v $(pwd)/ml_pipeline:/app \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/predictions:/app/predictions \
  ml-pipeline:local bash

# Inside container:
python -i train.py  # Interactive Python session
```

### 2. Checking Logs

```bash
# Run with verbose logging
docker run --rm \
  -v $(pwd)/models:/app/models \
  -e PYTHONUNBUFFERED=1 \
  ml-pipeline:local \
  python train.py --model-output-path /app/models
```

### 3. Inspecting Generated Files

```bash
# Check model files
ls -la models/
file models/latest_model.pkl

# Check predictions
head predictions/latest_predictions.csv
wc -l predictions/latest_predictions.csv

# Check metrics
cat models/metrics_*.json | jq .
```

## 📊 Jupyter Development

For interactive development with Jupyter:

```bash
# Start Jupyter server
docker run -it --rm \
  -v $(pwd)/ml_pipeline:/app \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/predictions:/app/predictions \
  -p 8888:8888 \
  ml-pipeline:dev jupyter

# Access at http://localhost:8888
```

Create notebooks in the mounted `/app/notebooks` directory.

## 🔄 CI/CD Integration

### Local GitHub Actions Testing

Test your GitHub Actions workflow locally using `act`:

```bash
# Install act (GitHub Actions local runner)
# macOS: brew install act
# Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run the workflow locally
act push -j build-and-push
```

### Pre-commit Hooks

Set up pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        files: ^ml_pipeline/.*\.py$
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        files: ^ml_pipeline/.*\.py$
EOF

# Install the hooks
pre-commit install
```

## 🚀 Deployment Pipeline

### 1. Local → GitHub → Registry

```bash
# 1. Develop and test locally
./build-local.sh

# 2. Push to GitHub (triggers Actions)
git push origin main

# 3. GitHub Actions builds and pushes to registry
# 4. Update Airflow variable with new image tag
```

### 2. Manual Registry Push

```bash
# Tag for registry
docker tag ml-pipeline:local ghcr.io/yourusername/yourrepo/ml-pipeline:v1.0.0

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u yourusername --password-stdin

# Push to registry
docker push ghcr.io/yourusername/yourrepo/ml-pipeline:v1.0.0
```

## 🐛 Common Issues and Solutions

### Issue 1: Permission Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER models/ predictions/ data/

# Or run with user mapping
docker run --rm \
  -u $(id -u):$(id -g) \
  -v $(pwd)/models:/app/models \
  ml-pipeline:local \
  python train.py --model-output-path /app/models
```

### Issue 2: Out of Memory

```bash
# Limit container memory
docker run --rm \
  --memory=2g \
  --memory-swap=4g \
  -v $(pwd)/models:/app/models \
  ml-pipeline:local \
  python train.py --model-output-path /app/models
```

### Issue 3: Slow Build Times

```bash
# Use build cache
docker build --cache-from ml-pipeline:local -t ml-pipeline:local ml_pipeline/

# Or use BuildKit
DOCKER_BUILDKIT=1 docker build -t ml-pipeline:local ml_pipeline/
```

## 📝 Best Practices

1. **Always test locally** before pushing to GitHub
2. **Use the automated build script** for consistency
3. **Keep test data small** for faster iteration
4. **Version your images** with meaningful tags
5. **Clean up test files** regularly to save disk space
6. **Use development container** for interactive work
7. **Monitor resource usage** during local testing

## 🔗 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Docker Guidelines](https://docs.python.org/3/using/cmdline.html)
- [Airflow Docker Guide](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
