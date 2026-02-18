"""
Stock Price Forecasting Models
Implements multiple forecasting algorithms for comparison
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class StockForecaster:
    def __init__(self, model_type='random_forest'):
        """
        Initialize forecaster with specified model type
        
        Args:
            model_type: 'random_forest', 'gradient_boost', or 'linear'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.is_trained = False
        self.lookback = 60
        
    def prepare_sequences(self, data, lookback=60):
        """
        Create sequences for time series prediction
        
        Args:
            data: Input data (1D array)
            lookback: Number of previous time steps to use
        """
        X, y = [], []
        for i in range(lookback, len(data)):
            X.append(data[i-lookback:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def train(self, data, lookback=60, test_size=0.2):
        """
        Train the forecasting model
        
        Args:
            data: Time series data (pandas Series or numpy array)
            lookback: Number of previous days to consider
            test_size: Proportion of data for testing
        """
        self.lookback = lookback
        
        # Convert to numpy array if needed
        if isinstance(data, pd.Series):
            data = data.values
        
        # Reshape for scaling
        data = data.reshape(-1, 1)
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = self.prepare_sequences(scaled_data.flatten(), lookback)
        
        # Split into train and test
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Initialize model based on type
        if self.model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boost':
            from sklearn.ensemble import GradientBoostingRegressor
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:  # linear regression
            from sklearn.linear_model import LinearRegression
            self.model = LinearRegression()
        
        # Train the model
        print(f"Training {self.model_type} model...")
        self.model.fit(X_train, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        
        # Inverse transform for actual values
        y_test_actual = self.scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
        y_pred_actual = self.scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()
        
        # Calculate metrics
        mse = mean_squared_error(y_test_actual, y_pred_actual)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test_actual, y_pred_actual)
        r2 = r2_score(y_test_actual, y_pred_actual)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_test_actual - y_pred_actual) / y_test_actual)) * 100
        
        metrics = {
            'rmse': round(rmse, 2),
            'mae': round(mae, 2),
            'r2': round(r2, 4),
            'mape': round(mape, 2),
            'model_type': self.model_type
        }
        
        self.is_trained = True
        
        print(f"✓ Model trained successfully")
        print(f"  RMSE: ${metrics['rmse']}")
        print(f"  MAE: ${metrics['mae']}")
        print(f"  R²: {metrics['r2']}")
        print(f"  MAPE: {metrics['mape']}%")
        
        return metrics, y_test_actual, y_pred_actual
    
    def predict_future(self, recent_data, days=30):
        """
        Predict future stock prices
        
        Args:
            recent_data: Recent historical data (at least lookback days)
            days: Number of days to predict into the future
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Convert to numpy array if needed
        if isinstance(recent_data, pd.Series):
            recent_data = recent_data.values
        
        # Use the last 'lookback' days
        recent_data = recent_data[-self.lookback:]
        
        # Scale the data
        recent_scaled = self.scaler.transform(recent_data.reshape(-1, 1)).flatten()
        
        predictions = []
        current_sequence = recent_scaled.copy()
        
        for _ in range(days):
            # Reshape for prediction
            X_pred = current_sequence[-self.lookback:].reshape(1, -1)
            
            # Predict next value
            next_pred = self.model.predict(X_pred)[0]
            predictions.append(next_pred)
            
            # Update sequence for next prediction
            current_sequence = np.append(current_sequence, next_pred)
        
        # Inverse transform predictions
        predictions = np.array(predictions).reshape(-1, 1)
        predictions_actual = self.scaler.inverse_transform(predictions).flatten()
        
        return predictions_actual
    
    def save_model(self, filepath):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'lookback': self.lookback
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        self.lookback = model_data['lookback']
        self.is_trained = True
        
        print(f"✓ Model loaded from {filepath}")


class MovingAverageForecaster:
    """Simple moving average based forecasting"""
    
    def __init__(self, window=20):
        self.window = window
        
    def predict_future(self, data, days=30):
        """Predict using simple moving average"""
        if isinstance(data, pd.Series):
            data = data.values
        
        # Calculate moving average
        ma = np.mean(data[-self.window:])
        
        # Predict same value for all future days (naive forecast)
        predictions = np.full(days, ma)
        
        return predictions


class EnsembleForecaster:
    """Combine multiple models for better predictions"""
    
    def __init__(self):
        self.models = []
        self.weights = []
        
    def add_model(self, model, weight=1.0):
        """Add a model to the ensemble"""
        self.models.append(model)
        self.weights.append(weight)
    
    def predict_future(self, recent_data, days=30):
        """Predict using weighted average of all models"""
        predictions = []
        
        for model, weight in zip(self.models, self.weights):
            pred = model.predict_future(recent_data, days)
            predictions.append(pred * weight)
        
        # Weighted average
        total_weight = sum(self.weights)
        ensemble_pred = np.sum(predictions, axis=0) / total_weight
        
        return ensemble_pred


if __name__ == "__main__":
    # Example usage
    print("Stock Forecasting Models Module")
    print("="*60)
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2022-01-01', periods=500, freq='D')
    prices = 100 + np.cumsum(np.random.randn(500) * 2)
    
    # Train model
    forecaster = StockForecaster(model_type='random_forest')
    metrics, _, _ = forecaster.train(prices, lookback=60)
    
    # Predict future
    future_pred = forecaster.predict_future(prices, days=30)
    print(f"\nPredicted prices for next 30 days:")
    print(f"Mean: ${future_pred.mean():.2f}")
    print(f"Min: ${future_pred.min():.2f}")
    print(f"Max: ${future_pred.max():.2f}")
