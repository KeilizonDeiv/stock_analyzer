"""
Stock Price Prediction Dashboard - Flask Application
Provides web interface for stock analysis and forecasting
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

from data_processor import StockDataProcessor
from forecasting_models import StockForecaster, EnsembleForecaster

app = Flask(__name__)

# Cache for storing recent predictions
prediction_cache = {}


@app.route('/')
def home():
    """Render main dashboard"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    """Fetch and analyze stock data"""
    try:
        data = request.get_json()
        ticker = data.get('ticker', 'AAPL').upper()
        period = data.get('period', '2y')
        
        # Fetch stock data
        processor = StockDataProcessor(ticker)
        
        if not processor.fetch_data(period=period):
            return jsonify({'error': f'Could not fetch data for {ticker}'}), 400
        
        # Add technical indicators
        processor.add_technical_indicators()
        
        # Get statistics
        stats = processor.get_statistics()
        
        # Prepare chart data
        df = processor.data.copy()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        chart_data = {
            'dates': df['Date'].tolist(),
            'prices': df['Close'].round(2).tolist(),
            'volume': df['Volume'].tolist(),
            'sma_20': df['SMA_20'].round(2).tolist(),
            'sma_50': df['SMA_50'].round(2).tolist(),
            'sma_200': df['SMA_200'].round(2).tolist(),
            'rsi': df['RSI'].round(2).tolist(),
            'macd': df['MACD'].round(2).tolist(),
            'signal_line': df['Signal_Line'].round(2).tolist(),
            'bb_upper': df['BB_Upper'].round(2).tolist(),
            'bb_middle': df['BB_Middle'].round(2).tolist(),
            'bb_lower': df['BB_Lower'].round(2).tolist(),
        }
        
        # Store data for prediction
        prediction_cache[ticker] = processor.data['Close'].values
        
        response = {
            'success': True,
            'ticker': ticker,
            'stats': stats,
            'chart_data': chart_data
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict_stock():
    """Generate price predictions"""
    try:
        data = request.get_json()
        ticker = data.get('ticker', 'AAPL').upper()
        days = int(data.get('days', 30))
        model_type = data.get('model_type', 'random_forest')
        
        # Check if we have data for this ticker
        if ticker not in prediction_cache:
            return jsonify({'error': 'Please analyze the stock first'}), 400
        
        # Get historical data
        historical_prices = prediction_cache[ticker]
        
        # Train model
        print(f"Training {model_type} model for {ticker}...")
        forecaster = StockForecaster(model_type=model_type)
        metrics, actual_test, pred_test = forecaster.train(
            historical_prices, 
            lookback=60, 
            test_size=0.2
        )
        
        # Predict future
        print(f"Predicting next {days} days...")
        future_predictions = forecaster.predict_future(historical_prices, days=days)
        
        # Generate future dates
        last_date = datetime.now()
        future_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                       for i in range(days)]
        
        # Calculate prediction statistics
        pred_stats = {
            'mean': round(float(np.mean(future_predictions)), 2),
            'min': round(float(np.min(future_predictions)), 2),
            'max': round(float(np.max(future_predictions)), 2),
            'trend': 'Bullish' if future_predictions[-1] > future_predictions[0] else 'Bearish',
            'change_percent': round(((future_predictions[-1] - historical_prices[-1]) / historical_prices[-1]) * 100, 2)
        }
        
        response = {
            'success': True,
            'ticker': ticker,
            'predictions': {
                'dates': future_dates,
                'prices': [round(float(p), 2) for p in future_predictions]
            },
            'metrics': metrics,
            'pred_stats': pred_stats,
            'test_performance': {
                'actual': [round(float(p), 2) for p in actual_test[-50:]],  # Last 50 points
                'predicted': [round(float(p), 2) for p in pred_test[-50:]]
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare_models', methods=['POST'])
def compare_models():
    """Compare different forecasting models"""
    try:
        data = request.get_json()
        ticker = data.get('ticker', 'AAPL').upper()
        days = int(data.get('days', 30))
        
        if ticker not in prediction_cache:
            return jsonify({'error': 'Please analyze the stock first'}), 400
        
        historical_prices = prediction_cache[ticker]
        
        # Train and compare multiple models
        models = ['random_forest', 'gradient_boost', 'linear']
        results = {}
        
        for model_type in models:
            print(f"Training {model_type}...")
            forecaster = StockForecaster(model_type=model_type)
            metrics, _, _ = forecaster.train(historical_prices, lookback=60)
            predictions = forecaster.predict_future(historical_prices, days=days)
            
            results[model_type] = {
                'metrics': metrics,
                'predictions': [round(float(p), 2) for p in predictions]
            }
        
        # Generate dates
        last_date = datetime.now()
        future_dates = [(last_date + timedelta(days=i+1)).strftime('%Y-%m-%d') 
                       for i in range(days)]
        
        response = {
            'success': True,
            'ticker': ticker,
            'dates': future_dates,
            'models': results
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/popular_stocks')
def get_popular_stocks():
    """Return list of popular stocks"""
    stocks = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla, Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        {'symbol': 'V', 'name': 'Visa Inc.'},
        {'symbol': 'WMT', 'name': 'Walmart Inc.'}
    ]
    
    return jsonify(stocks)


if __name__ == '__main__':
    print("="*60)
    print("Stock Price Prediction Dashboard")
    print("="*60)
    print("Starting server...")
    print("Open http://localhost:5000 in your browser")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
