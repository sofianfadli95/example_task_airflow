# Makefile for ML Pipeline Development

# Variables
IMAGE_NAME = ml-pipeline
TAG = local
DEV_TAG = dev
FULL_IMAGE = $(IMAGE_NAME):$(TAG)
DEV_IMAGE = $(IMAGE_NAME):$(DEV_TAG)

# Default target
.PHONY: help
help:
	@echo "ML Pipeline Development Commands"
	@echo "================================"
	@echo ""
	@echo "Building:"
	@echo "  build       - Build production Docker image"
	@echo "  build-dev   - Build development Docker image"
	@echo "  build-all   - Build both production and development images"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run automated build and test script"
	@echo "  test-train  - Test training script only"
	@echo "  test-predict- Test prediction script only"
	@echo "  test-validate- Test validation scripts"
	@echo ""
	@echo "Development:"
	@echo "  dev         - Start development container"
	@echo "  jupyter     - Start Jupyter notebook server"
	@echo "  shell       - Start interactive shell in container"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       - Clean up test files and containers"
	@echo "  clean-all   - Clean everything including images"
	@echo "  format      - Format Python code"
	@echo "  lint        - Run code linting"
	@echo ""
	@echo "Deployment:"
	@echo "  tag         - Tag image for registry"
	@echo "  push        - Push to container registry"
	@echo ""

# Building targets
.PHONY: build
build:
	@echo "🔨 Building production Docker image..."
	docker build -t $(FULL_IMAGE) ml_pipeline/

.PHONY: build-dev
build-dev:
	@echo "🔨 Building development Docker image..."
	docker build -f ml_pipeline/Dockerfile.dev -t $(DEV_IMAGE) ml_pipeline/

.PHONY: build-all
build-all: build build-dev

# Testing targets
.PHONY: test
test:
	@echo "🧪 Running automated build and test..."
	./build-local.sh

.PHONY: test-train
test-train: build
	@echo "🏋️  Testing training script..."
	@mkdir -p test_models
	docker run --rm \
		-v $(PWD)/test_models:/app/models \
		$(FULL_IMAGE) \
		python train.py --model-output-path /app/models

.PHONY: test-predict
test-predict: build test-train
	@echo "🔮 Testing prediction script..."
	@mkdir -p test_predictions
	docker run --rm \
		-v $(PWD)/test_models:/app/models \
		-v $(PWD)/test_predictions:/app/predictions \
		$(FULL_IMAGE) \
		python predict.py --model-path /app/models/latest_model.pkl --output-path /app/predictions

.PHONY: test-validate
test-validate: build test-train test-predict
	@echo "✅ Testing validation scripts..."
	docker run --rm \
		-v $(PWD)/test_models:/app/models \
		-v $(PWD)/test_predictions:/app/predictions \
		$(FULL_IMAGE) \
		python validate.py validate-model --models-dir /app/models
	docker run --rm \
		-v $(PWD)/test_models:/app/models \
		-v $(PWD)/test_predictions:/app/predictions \
		$(FULL_IMAGE) \
		python validate.py validate-predictions --predictions-dir /app/predictions

# Development targets
.PHONY: dev
dev: build-dev
	@echo "🚀 Starting development container..."
	@mkdir -p data models predictions
	docker run -it --rm \
		-v $(PWD)/ml_pipeline:/app \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/models:/app/models \
		-v $(PWD)/predictions:/app/predictions \
		-p 8888:8888 \
		$(DEV_IMAGE)

.PHONY: jupyter
jupyter: build-dev
	@echo "📊 Starting Jupyter notebook server..."
	@mkdir -p data models predictions
	docker run -it --rm \
		-v $(PWD)/ml_pipeline:/app \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/models:/app/models \
		-v $(PWD)/predictions:/app/predictions \
		-p 8888:8888 \
		$(DEV_IMAGE) \
		jupyter

.PHONY: shell
shell: build
	@echo "🐚 Starting interactive shell..."
	@mkdir -p data models predictions
	docker run -it --rm \
		-v $(PWD)/ml_pipeline:/app \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/models:/app/models \
		-v $(PWD)/predictions:/app/predictions \
		$(FULL_IMAGE) bash

# Maintenance targets
.PHONY: clean
clean:
	@echo "🧹 Cleaning up test files..."
	-rm -rf test_data test_models test_predictions
	-docker container prune -f
	@echo "✅ Cleanup completed"

.PHONY: clean-all
clean-all: clean
	@echo "🧹 Cleaning up everything..."
	-docker image rm $(FULL_IMAGE) $(DEV_IMAGE) 2>/dev/null || true
	-docker system prune -f
	@echo "✅ Full cleanup completed"

.PHONY: format
format: build-dev
	@echo "🎨 Formatting Python code..."
	docker run --rm \
		-v $(PWD)/ml_pipeline:/app \
		$(DEV_IMAGE) format

.PHONY: lint
lint: build-dev
	@echo "🔍 Running code linting..."
	docker run --rm \
		-v $(PWD)/ml_pipeline:/app \
		$(DEV_IMAGE) lint

# Deployment targets
.PHONY: tag
tag: build
	@echo "🏷️  Tagging image for registry..."
	@read -p "Enter registry URL (e.g., ghcr.io/username/repo): " registry; \
	read -p "Enter tag (default: latest): " tag; \
	tag=$${tag:-latest}; \
	docker tag $(FULL_IMAGE) $$registry/ml-pipeline:$$tag; \
	echo "Tagged as $$registry/ml-pipeline:$$tag"

.PHONY: push
push:
	@echo "📤 Pushing to container registry..."
	@echo "Please ensure you're logged in to your container registry first"
	@read -p "Enter full image name to push: " image; \
	docker push $$image

# Kubernetes targets
.PHONY: k8s-setup
k8s-setup:
	@echo "☸️  Setting up Kubernetes resources..."
	./setup-k8s.sh

.PHONY: k8s-clean
k8s-clean:
	@echo "🧹 Cleaning up Kubernetes resources..."
	-kubectl delete namespace airflow
	@echo "✅ Kubernetes cleanup completed"

# Quick development workflow
.PHONY: dev-workflow
dev-workflow: build test
	@echo "🎉 Development workflow completed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "1. If tests pass, commit your changes:"
	@echo "   git add . && git commit -m 'Updated ML pipeline'"
	@echo ""
	@echo "2. Push to trigger GitHub Actions:"
	@echo "   git push origin main"
	@echo ""
	@echo "3. Or manually tag and push:"
	@echo "   make tag"
	@echo "   make push"
