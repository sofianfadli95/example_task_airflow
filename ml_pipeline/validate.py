#!/usr/bin/env python3
"""
Validation scripts for ML Pipeline
These scripts are used by Kubernetes pods for validation tasks.
"""

import os
import sys
import json
import pandas as pd
import pickle
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_model(models_dir="/app/models"):
    """Validate that model training was successful"""
    logger.info(f"Validating model in directory: {models_dir}")
    
    latest_model = os.path.join(models_dir, 'latest_model.pkl')
    
    if not os.path.exists(latest_model):
        logger.error(f"Model file not found: {latest_model}")
        return False
    
    logger.info(f"Model file found: {latest_model}")
    
    # Check if model can be loaded
    try:
        with open(latest_model, 'rb') as f:
            model = pickle.load(f)
        logger.info("Model successfully loaded")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False
    
    # Check for metrics file
    metrics_files = [f for f in os.listdir(models_dir) if f.startswith('metrics_') and f.endswith('.json')]
    if metrics_files:
        latest_metrics = max(metrics_files)
        metrics_path = os.path.join(models_dir, latest_metrics)
        
        logger.info(f"Loading metrics from: {metrics_path}")
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        accuracy = metrics.get('accuracy', 0)
        logger.info(f"Model accuracy: {accuracy:.4f}")
        
        if accuracy < 0.5:  # Minimum acceptable accuracy
            logger.error(f"Model accuracy too low: {accuracy}")
            return False
        
        logger.info("Model validation successful")
        return True
    
    logger.warning("Model file exists but no metrics found")
    return True  # Still consider it valid if model exists


def validate_predictions(predictions_dir="/app/predictions"):
    """Validate prediction results and generate summary"""
    logger.info(f"Validating predictions in directory: {predictions_dir}")
    
    latest_predictions = os.path.join(predictions_dir, 'latest_predictions.csv')
    
    if not os.path.exists(latest_predictions):
        logger.error(f"Predictions file not found: {latest_predictions}")
        return False
    
    logger.info(f"Predictions file found: {latest_predictions}")
    
    try:
        # Load and analyze predictions
        df = pd.read_csv(latest_predictions)
        
        summary = {
            'total_predictions': len(df),
            'unique_classes': df['predicted_class'].nunique(),
            'average_confidence': df['prediction_confidence'].mean(),
            'min_confidence': df['prediction_confidence'].min(),
            'max_confidence': df['prediction_confidence'].max(),
        }
        
        logger.info(f"Prediction summary: {summary}")
        
        if len(df) == 0:
            logger.error("No predictions found in file")
            return False
        
        logger.info("Prediction validation successful")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate predictions: {e}")
        return False


def cleanup_old_files(models_dir="/app/models", predictions_dir="/app/predictions", keep_count=5):
    """Clean up old model and prediction files"""
    logger.info(f"Cleaning up old files, keeping last {keep_count} files")
    
    import glob
    
    # Cleanup model files
    model_files = sorted(glob.glob(os.path.join(models_dir, "*.pkl")), key=os.path.getmtime)
    if len(model_files) > keep_count:
        files_to_remove = model_files[:-keep_count]
        for file_path in files_to_remove:
            if 'latest_model.pkl' not in file_path:  # Don't remove the symlink
                os.remove(file_path)
                logger.info(f"Removed old model file: {file_path}")
    
    # Cleanup prediction files
    prediction_files = sorted(glob.glob(os.path.join(predictions_dir, "predictions_*.csv")), key=os.path.getmtime)
    if len(prediction_files) > keep_count:
        files_to_remove = prediction_files[:-keep_count]
        for file_path in files_to_remove:
            os.remove(file_path)
            logger.info(f"Removed old prediction file: {file_path}")
    
    # Cleanup metrics files
    metrics_files = sorted(glob.glob(os.path.join(models_dir, "metrics_*.json")), key=os.path.getmtime)
    if len(metrics_files) > keep_count:
        files_to_remove = metrics_files[:-keep_count]
        for file_path in files_to_remove:
            os.remove(file_path)
            logger.info(f"Removed old metrics file: {file_path}")
    
    logger.info("Cleanup completed")
    return True


def main():
    parser = argparse.ArgumentParser(description='ML Pipeline Validation Scripts')
    parser.add_argument('action', choices=['validate-model', 'validate-predictions', 'cleanup'],
                       help='Validation action to perform')
    parser.add_argument('--models-dir', type=str, default='/app/models',
                       help='Models directory path')
    parser.add_argument('--predictions-dir', type=str, default='/app/predictions',
                       help='Predictions directory path')
    parser.add_argument('--keep-count', type=int, default=5,
                       help='Number of files to keep during cleanup')
    
    args = parser.parse_args()
    
    success = False
    
    if args.action == 'validate-model':
        success = validate_model(args.models_dir)
    elif args.action == 'validate-predictions':
        success = validate_predictions(args.predictions_dir)
    elif args.action == 'cleanup':
        success = cleanup_old_files(args.models_dir, args.predictions_dir, args.keep_count)
    
    if success:
        logger.info(f"Action '{args.action}' completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Action '{args.action}' failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
