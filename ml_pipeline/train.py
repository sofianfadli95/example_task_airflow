#!/usr/bin/env python3
"""
Machine Learning Training Pipeline
Trains a simple model on sample data and saves it for later use.
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.datasets import make_classification
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    def __init__(self, model_output_path="/app/models", data_path=None):
        self.model_output_path = model_output_path
        self.data_path = data_path
        self.model = None
        self.model_metrics = {}
        
        # Ensure output directory exists
        os.makedirs(self.model_output_path, exist_ok=True)
    
    def generate_sample_data(self, n_samples=1000, n_features=20):
        """Generate sample classification data for demonstration"""
        logger.info(f"Generating sample data with {n_samples} samples and {n_features} features")
        
        X, y = make_classification(
            n_samples=n_samples,
            n_features=n_features,
            n_informative=10,
            n_redundant=5,
            n_classes=2,
            random_state=42
        )
        
        # Convert to DataFrame for easier handling
        feature_names = [f"feature_{i}" for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_names)
        df['target'] = y
        
        return df
    
    def load_data(self):
        """Load data from file or generate sample data"""
        if self.data_path and os.path.exists(self.data_path):
            logger.info(f"Loading data from {self.data_path}")
            df = pd.read_csv(self.data_path)
        else:
            logger.info("No data path provided or file not found, generating sample data")
            df = self.generate_sample_data()
        
        return df
    
    def preprocess_data(self, df):
        """Basic data preprocessing"""
        logger.info("Preprocessing data")
        
        # Separate features and target
        if 'target' in df.columns:
            X = df.drop('target', axis=1)
            y = df['target']
        else:
            # Assume last column is target
            X = df.iloc[:, :-1]
            y = df.iloc[:, -1]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training set size: {X_train.shape[0]}")
        logger.info(f"Test set size: {X_test.shape[0]}")
        
        return X_train, X_test, y_train, y_test
    
    def train_model(self, X_train, y_train):
        """Train the machine learning model"""
        logger.info("Training Random Forest model")
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        logger.info("Model training completed")
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate the trained model"""
        logger.info("Evaluating model performance")
        
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.model_metrics = {
            'accuracy': accuracy,
            'timestamp': datetime.now().isoformat(),
            'test_samples': len(y_test)
        }
        
        logger.info(f"Model accuracy: {accuracy:.4f}")
        logger.info("Classification Report:")
        logger.info(f"\n{classification_report(y_test, y_pred)}")
        
        return self.model_metrics
    
    def save_model(self):
        """Save the trained model and metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = f"ml_model_{timestamp}.pkl"
        model_path = os.path.join(self.model_output_path, model_filename)
        
        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save latest model symlink
        latest_model_path = os.path.join(self.model_output_path, "latest_model.pkl")
        if os.path.exists(latest_model_path):
            os.remove(latest_model_path)
        os.symlink(model_filename, latest_model_path)
        
        # Save metrics
        metrics_path = os.path.join(self.model_output_path, f"metrics_{timestamp}.json")
        import json
        with open(metrics_path, 'w') as f:
            json.dump(self.model_metrics, f, indent=2)
        
        logger.info(f"Model saved to: {model_path}")
        logger.info(f"Metrics saved to: {metrics_path}")
        
        return model_path
    
    def run_pipeline(self):
        """Run the complete training pipeline"""
        logger.info("Starting ML training pipeline")
        
        try:
            # Load and preprocess data
            df = self.load_data()
            X_train, X_test, y_train, y_test = self.preprocess_data(df)
            
            # Train model
            self.train_model(X_train, y_train)
            
            # Evaluate model
            metrics = self.evaluate_model(X_test, y_test)
            
            # Save model
            model_path = self.save_model()
            
            logger.info("Training pipeline completed successfully")
            return {
                'status': 'success',
                'model_path': model_path,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }


def main():
    parser = argparse.ArgumentParser(description='ML Training Pipeline')
    parser.add_argument('--data-path', type=str, help='Path to training data CSV file')
    parser.add_argument('--model-output-path', type=str, default='/app/models',
                       help='Path to save trained model')
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = MLTrainingPipeline(
        model_output_path=args.model_output_path,
        data_path=args.data_path
    )
    
    result = pipeline.run_pipeline()
    
    if result['status'] == 'success':
        logger.info("Training completed successfully!")
        exit(0)
    else:
        logger.error("Training failed!")
        exit(1)


if __name__ == "__main__":
    main()
