#!/usr/bin/env python3
"""
Machine Learning Prediction Pipeline
Loads a trained model and makes predictions on new data.
"""

import os
import pickle
import pandas as pd
import numpy as np
import logging
import argparse
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLPredictionPipeline:
    def __init__(self, model_path="/app/models/latest_model.pkl", output_path="/app/predictions"):
        self.model_path = model_path
        self.output_path = output_path
        self.model = None
        
        # Ensure output directory exists
        os.makedirs(self.output_path, exist_ok=True)
    
    def load_model(self):
        """Load the trained model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        logger.info(f"Loading model from: {self.model_path}")
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        logger.info("Model loaded successfully")
    
    def load_prediction_data(self, data_path):
        """Load data for prediction"""
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Prediction data file not found: {data_path}")
        
        logger.info(f"Loading prediction data from: {data_path}")
        
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        elif data_path.endswith('.json'):
            df = pd.read_json(data_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or JSON.")
        
        logger.info(f"Loaded {len(df)} samples for prediction")
        return df
    
    def generate_sample_prediction_data(self, n_samples=100):
        """Generate sample data for prediction (for demonstration)"""
        logger.info(f"Generating {n_samples} sample records for prediction")
        
        # Generate random data matching the training features
        np.random.seed(42)
        n_features = 20  # Should match training data
        
        X = np.random.randn(n_samples, n_features)
        feature_names = [f"feature_{i}" for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_names)
        
        return df
    
    def make_predictions(self, df):
        """Make predictions on the input data"""
        logger.info("Making predictions")
        
        # Remove target column if it exists (for evaluation data)
        if 'target' in df.columns:
            X = df.drop('target', axis=1)
            actual_targets = df['target'].values
        else:
            X = df
            actual_targets = None
        
        # Make predictions
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        # Create results DataFrame
        results_df = df.copy()
        results_df['predicted_class'] = predictions
        results_df['prediction_confidence'] = np.max(probabilities, axis=1)
        results_df['prediction_timestamp'] = datetime.now().isoformat()
        
        # Add probability scores for each class
        for i, class_name in enumerate(self.model.classes_):
            results_df[f'prob_class_{class_name}'] = probabilities[:, i]
        
        logger.info(f"Predictions completed for {len(results_df)} samples")
        
        # Calculate accuracy if actual targets are available
        if actual_targets is not None:
            from sklearn.metrics import accuracy_score
            accuracy = accuracy_score(actual_targets, predictions)
            logger.info(f"Prediction accuracy: {accuracy:.4f}")
            
            return results_df, {'accuracy': accuracy}
        
        return results_df, None
    
    def save_predictions(self, predictions_df, metrics=None):
        """Save predictions to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        predictions_filename = f"predictions_{timestamp}.csv"
        predictions_path = os.path.join(self.output_path, predictions_filename)
        
        # Save predictions
        predictions_df.to_csv(predictions_path, index=False)
        
        # Save latest predictions symlink
        latest_predictions_path = os.path.join(self.output_path, "latest_predictions.csv")
        if os.path.exists(latest_predictions_path):
            os.remove(latest_predictions_path)
        os.symlink(predictions_filename, latest_predictions_path)
        
        logger.info(f"Predictions saved to: {predictions_path}")
        
        # Save metrics if available
        if metrics:
            metrics_filename = f"prediction_metrics_{timestamp}.json"
            metrics_path = os.path.join(self.output_path, metrics_filename)
            
            with open(metrics_path, 'w') as f:
                json.dump({
                    **metrics,
                    'timestamp': datetime.now().isoformat(),
                    'num_predictions': len(predictions_df)
                }, f, indent=2)
            
            logger.info(f"Prediction metrics saved to: {metrics_path}")
        
        return predictions_path
    
    def run_pipeline(self, data_path=None):
        """Run the complete prediction pipeline"""
        logger.info("Starting ML prediction pipeline")
        
        try:
            # Load model
            self.load_model()
            
            # Load prediction data
            if data_path:
                df = self.load_prediction_data(data_path)
            else:
                logger.info("No data path provided, generating sample data")
                df = self.generate_sample_prediction_data()
            
            # Make predictions
            predictions_df, metrics = self.make_predictions(df)
            
            # Save predictions
            predictions_path = self.save_predictions(predictions_df, metrics)
            
            logger.info("Prediction pipeline completed successfully")
            return {
                'status': 'success',
                'predictions_path': predictions_path,
                'num_predictions': len(predictions_df),
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Prediction pipeline failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }


def main():
    parser = argparse.ArgumentParser(description='ML Prediction Pipeline')
    parser.add_argument('--data-path', type=str, help='Path to prediction data CSV/JSON file')
    parser.add_argument('--model-path', type=str, default='/app/models/latest_model.pkl',
                       help='Path to trained model file')
    parser.add_argument('--output-path', type=str, default='/app/predictions',
                       help='Path to save predictions')
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = MLPredictionPipeline(
        model_path=args.model_path,
        output_path=args.output_path
    )
    
    result = pipeline.run_pipeline(data_path=args.data_path)
    
    if result['status'] == 'success':
        logger.info("Prediction completed successfully!")
        logger.info(f"Generated {result['num_predictions']} predictions")
        exit(0)
    else:
        logger.error("Prediction failed!")
        exit(1)


if __name__ == "__main__":
    main()
