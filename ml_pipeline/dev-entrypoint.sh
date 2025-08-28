#!/bin/bash

# Development entrypoint script
# Provides helpful utilities for development

echo "🚀 ML Pipeline Development Environment"
echo "======================================"
echo ""
echo "Available commands:"
echo "  train     - Run training pipeline"
echo "  predict   - Run prediction pipeline"
echo "  validate  - Run validation scripts"
echo "  test      - Run all tests"
echo "  jupyter   - Start Jupyter notebook server"
echo "  format    - Format code with black"
echo "  lint      - Run code linting"
echo ""
echo "Example usage:"
echo "  python train.py --help"
echo "  python predict.py --help"
echo "  python validate.py --help"
echo ""
echo "Development files are mounted at /app"
echo "Data files: /app/data"
echo "Models: /app/models"
echo "Predictions: /app/predictions"
echo ""

# Function to run training
train() {
    echo "🏋️  Starting training pipeline..."
    python train.py --model-output-path /app/models "$@"
}

# Function to run prediction
predict() {
    echo "🔮 Starting prediction pipeline..."
    python predict.py --model-path /app/models/latest_model.pkl --output-path /app/predictions "$@"
}

# Function to run validation
validate() {
    echo "✅ Running validation..."
    if [ -z "$1" ]; then
        echo "Usage: validate [validate-model|validate-predictions|cleanup]"
        return 1
    fi
    python validate.py "$@"
}

# Function to run tests
test() {
    echo "🧪 Running tests..."
    # Add test commands here when you have tests
    echo "No tests defined yet. Add pytest tests in /app/tests/"
}

# Function to start Jupyter
jupyter() {
    echo "📊 Starting Jupyter notebook server..."
    mkdir -p /app/notebooks
    jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/app/notebooks
}

# Function to format code
format() {
    echo "🎨 Formatting code with black..."
    black /app/*.py
}

# Function to lint code
lint() {
    echo "🔍 Linting code..."
    flake8 /app/*.py
    pylint /app/*.py || true
}

# Export functions
export -f train predict validate test jupyter format lint

# Execute command if provided
if [ $# -gt 0 ]; then
    case "$1" in
        train)
            shift
            train "$@"
            ;;
        predict)
            shift
            predict "$@"
            ;;
        validate)
            shift
            validate "$@"
            ;;
        test)
            shift
            test "$@"
            ;;
        jupyter)
            jupyter
            ;;
        format)
            format
            ;;
        lint)
            lint
            ;;
        *)
            exec "$@"
            ;;
    esac
else
    # Start interactive bash session
    exec bash
fi
