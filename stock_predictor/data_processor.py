"""
Stock Data Fetcher and Processor
Handles downloading stock data and calculating technical indicators
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class StockDataProcessor:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.data = None
        
    def fetch_data(self, period='2y', interval='1d'):
        """
        Fetch stock data from Yahoo Finance
        
        Args:
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        """
        try:
            stock = yf.Ticker(self.ticker)
            self.data = stock.history(period=period, interval=interval)
            
            if self.data.empty:
                raise ValueError(f"No data found for ticker {self.ticker}")
            
            # Reset index to make Date a column
            self.data.reset_index(inplace=True)
            
            print(f"✓ Fetched {len(self.data)} data points for {self.ticker}")
            return True
            
        except Exception as e:
            print(f"✗ Error fetching data: {str(e)}")
            return False
    
    def add_technical_indicators(self):
        """Add common technical indicators to the dataset"""
        if self.data is None or self.data.empty:
            raise ValueError("No data available. Fetch data first.")
        
        df = self.data.copy()
        n_points = len(df)
        
        # Adjust window sizes based on available data
        sma_50_window = min(50, max(5, n_points // 4))
        sma_200_window = min(200, max(10, n_points // 2))
        
        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=min(20, n_points)).mean()
        df['SMA_50'] = df['Close'].rolling(window=sma_50_window).mean()
        df['SMA_200'] = df['Close'].rolling(window=sma_200_window).mean()
        df['EMA_12'] = df['Close'].ewm(span=min(12, n_points), adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=min(26, n_points), adjust=False).mean()
        
        # MACD (Moving Average Convergence Divergence)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal_Line'] = df['MACD'].ewm(span=min(9, n_points), adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
        
        # RSI (Relative Strength Index)
        rsi_window = min(14, max(3, n_points // 2))
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        bb_window = min(20, n_points)
        df['BB_Middle'] = df['Close'].rolling(window=bb_window).mean()
        bb_std = df['Close'].rolling(window=bb_window).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Volatility
        df['Daily_Return'] = df['Close'].pct_change()
        df['Volatility'] = df['Daily_Return'].rolling(window=min(20, n_points)).std()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=min(20, n_points)).mean()
        
        # Fill NaN values with the first valid value or 0
        df = df.bfill().fillna(0)
        
        self.data = df
        print(f"✓ Added technical indicators (adjusted for {n_points} data points)")
        
        return df
    
    def get_statistics(self):
        """Calculate basic statistics about the stock"""
        if self.data is None or self.data.empty:
            return None
        
        latest_price = self.data['Close'].iloc[-1]
        first_price = self.data['Close'].iloc[0]
        
        stats = {
            'ticker': self.ticker,
            'latest_price': round(latest_price, 2),
            'first_price': round(first_price, 2),
            'total_return': round(((latest_price - first_price) / first_price) * 100, 2),
            'highest_price': round(self.data['Close'].max(), 2),
            'lowest_price': round(self.data['Close'].min(), 2),
            'average_volume': int(self.data['Volume'].mean()),
            'current_rsi': round(self.data['RSI'].iloc[-1], 2) if 'RSI' in self.data else None,
            'volatility': round(self.data['Volatility'].iloc[-1] * 100, 2) if 'Volatility' in self.data else None,
            'data_points': len(self.data),
            'start_date': self.data['Date'].iloc[0].strftime('%Y-%m-%d'),
            'end_date': self.data['Date'].iloc[-1].strftime('%Y-%m-%d')
        }
        
        return stats
    
    def prepare_training_data(self, target_column='Close', lookback=60):
        """
        Prepare data for time series forecasting
        
        Args:
            target_column: Column to predict
            lookback: Number of previous days to use for prediction
        """
        if self.data is None or self.data.empty:
            raise ValueError("No data available")
        
        # Get the target values
        values = self.data[target_column].values
        
        # Create sequences
        X, y = [], []
        for i in range(lookback, len(values)):
            X.append(values[i-lookback:i])
            y.append(values[i])
        
        X = np.array(X)
        y = np.array(y)
        
        return X, y
    
    def get_latest_data(self, days=60):
        """Get the most recent data for prediction"""
        if self.data is None or self.data.empty:
            raise ValueError("No data available")
        
        return self.data.tail(days)


if __name__ == "__main__":
    # Example usage
    processor = StockDataProcessor('AAPL')
    
    if processor.fetch_data(period='2y'):
        processor.add_technical_indicators()
        stats = processor.get_statistics()
        
        print("\n" + "="*60)
        print("STOCK STATISTICS")
        print("="*60)
        for key, value in stats.items():
            print(f"{key:20s}: {value}")
