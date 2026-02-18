// Global variables
let currentTicker = 'AAPL';
let chartData = null;
let priceChart = null;
let rsiChart = null;
let macdChart = null;
let predictionChart = null;
let accuracyChart = null;
let comparisonChart = null;

// Load popular stocks on page load
window.addEventListener('load', function() {
    loadPopularStocks();
});

// Scroll detection for footer
window.addEventListener('scroll', function() {
    const footer = document.querySelector('.footer');
    const scrollPosition = window.innerHeight + window.scrollY;
    const documentHeight = document.documentElement.offsetHeight;
    
    // Show footer when user scrolls within 200px of the bottom
    if (scrollPosition >= documentHeight - 200) {
        footer.classList.add('visible');
    } else {
        footer.classList.remove('visible');
    }
});

// Load popular stocks
async function loadPopularStocks() {
    try {
        const response = await fetch('/api/popular_stocks');
        const stocks = await response.json();
        
        const container = document.getElementById('popularStocks');
        container.innerHTML = '<p style="margin-bottom: 10px; color: #666;">Popular stocks:</p>';
        
        stocks.forEach(stock => {
            const chip = document.createElement('div');
            chip.className = 'stock-chip';
            chip.textContent = `${stock.symbol} - ${stock.name}`;
            chip.onclick = () => {
                document.getElementById('tickerInput').value = stock.symbol;
                analyzeStock();
            };
            container.appendChild(chip);
        });
    } catch (error) {
        console.error('Error loading popular stocks:', error);
    }
}

// Analyze stock
async function analyzeStock() {
    const ticker = document.getElementById('tickerInput').value.toUpperCase().trim();
    const period = document.getElementById('periodSelect').value;
    
    if (!ticker) {
        showError('Please enter a stock ticker');
        return;
    }
    
    currentTicker = ticker;
    
    // Show loading
    document.getElementById('loadingAnalysis').style.display = 'block';
    document.getElementById('errorMessage').style.display = 'none';
    document.getElementById('statsSection').style.display = 'none';
    document.getElementById('chartsSection').style.display = 'none';
    document.getElementById('predictionSection').style.display = 'none';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, period })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze stock');
        }
        
        // Store chart data
        chartData = data.chart_data;
        
        // Update statistics
        updateStatistics(data.stats);
        
        // Create charts
        createPriceChart(data.chart_data);
        createRSIChart(data.chart_data);
        createMACDChart(data.chart_data);
        
        // Show sections
        document.getElementById('statsSection').style.display = 'block';
        document.getElementById('chartsSection').style.display = 'block';
        document.getElementById('predictionSection').style.display = 'block';
        
    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('loadingAnalysis').style.display = 'none';
    }
}

// Update statistics cards
function updateStatistics(stats) {
    document.getElementById('latestPrice').textContent = `$${stats.latest_price}`;
    
    const returnValue = stats.total_return;
    const returnElement = document.getElementById('totalReturn');
    returnElement.textContent = `${returnValue > 0 ? '+' : ''}${returnValue}%`;
    returnElement.className = `stat-value ${returnValue >= 0 ? 'positive' : 'negative'}`;
    
    document.getElementById('highPrice').textContent = `$${stats.highest_price}`;
    document.getElementById('lowPrice').textContent = `$${stats.lowest_price}`;
    document.getElementById('rsiValue').textContent = stats.current_rsi || '--';
    document.getElementById('volatilityValue').textContent = stats.volatility ? `${stats.volatility}%` : '--';
}

// Create price chart
function createPriceChart(data) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Price',
                    data: data.prices,
                    borderColor: '#1e3c72',
                    backgroundColor: 'rgba(30, 60, 114, 0.1)',
                    borderWidth: 2,
                    tension: 0.1
                },
                {
                    label: 'SMA 20',
                    data: data.sma_20,
                    borderColor: '#ff6384',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false
                },
                {
                    label: 'SMA 50',
                    data: data.sma_50,
                    borderColor: '#36a2eb',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false
                },
                {
                    label: 'SMA 200',
                    data: data.sma_200,
                    borderColor: '#4bc0c0',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { beginAtZero: false }
            }
        }
    });
}

// Create RSI chart
function createRSIChart(data) {
    const ctx = document.getElementById('rsiChart').getContext('2d');
    
    if (rsiChart) {
        rsiChart.destroy();
    }
    
    rsiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'RSI',
                data: data.rsi,
                borderColor: '#9966ff',
                backgroundColor: 'rgba(153, 102, 255, 0.1)',
                borderWidth: 2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true },
                annotation: {
                    annotations: {
                        overbought: {
                            type: 'line',
                            yMin: 70,
                            yMax: 70,
                            borderColor: '#dc3545',
                            borderWidth: 2,
                            borderDash: [10, 5]
                        },
                        oversold: {
                            type: 'line',
                            yMin: 30,
                            yMax: 30,
                            borderColor: '#28a745',
                            borderWidth: 2,
                            borderDash: [10, 5]
                        }
                    }
                }
            },
            scales: {
                y: { min: 0, max: 100 }
            }
        }
    });
}

// Create MACD chart
function createMACDChart(data) {
    const ctx = document.getElementById('macdChart').getContext('2d');
    
    if (macdChart) {
        macdChart.destroy();
    }
    
    macdChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'MACD',
                    data: data.macd,
                    borderColor: '#ff6384',
                    borderWidth: 2,
                    fill: false
                },
                {
                    label: 'Signal Line',
                    data: data.signal_line,
                    borderColor: '#36a2eb',
                    borderWidth: 2,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true }
            }
        }
    });
}

// Predict stock price
async function predictStock() {
    const days = parseInt(document.getElementById('predictionDays').value);
    const modelType = document.getElementById('modelSelect').value;
    
    if (days < 7 || days > 90) {
        showError('Prediction days must be between 7 and 90');
        return;
    }
    
    // Show loading
    document.getElementById('loadingPrediction').style.display = 'block';
    document.getElementById('predictionResults').style.display = 'none';
    document.getElementById('comparisonResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                ticker: currentTicker, 
                days: days,
                model_type: modelType
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Prediction failed');
        }
        
        // Update prediction statistics
        document.getElementById('modelRMSE').textContent = `$${data.metrics.rmse}`;
        document.getElementById('modelR2').textContent = data.metrics.r2;
        
        const trend = data.pred_stats.trend;
        const trendElement = document.getElementById('predictedTrend');
        trendElement.textContent = trend;
        trendElement.className = `stat-value ${trend === 'Bullish' ? 'positive' : 'negative'}`;
        
        const change = data.pred_stats.change_percent;
        const changeElement = document.getElementById('expectedChange');
        changeElement.textContent = `${change > 0 ? '+' : ''}${change}%`;
        changeElement.className = `stat-value ${change >= 0 ? 'positive' : 'negative'}`;
        
        // Create accuracy chart
        createAccuracyChart(data.test_performance);
        
        // Create prediction chart
        createPredictionChart(data.predictions, chartData);
        
        // Show results
        document.getElementById('predictionResults').style.display = 'block';
        
    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('loadingPrediction').style.display = 'none';
    }
}

// Create accuracy chart
function createAccuracyChart(performance) {
    const ctx = document.getElementById('accuracyChart').getContext('2d');
    
    if (accuracyChart) {
        accuracyChart.destroy();
    }
    
    const labels = Array.from({length: performance.actual.length}, (_, i) => i + 1);
    
    accuracyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual Price',
                    data: performance.actual,
                    borderColor: '#1e3c72',
                    backgroundColor: 'rgba(30, 60, 114, 0.1)',
                    borderWidth: 2
                },
                {
                    label: 'Predicted Price',
                    data: performance.predicted,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true },
                title: {
                    display: true,
                    text: 'Last 50 Test Predictions vs Actual'
                }
            }
        }
    });
}

// Create prediction chart
function createPredictionChart(predictions, historical) {
    const ctx = document.getElementById('predictionChart').getContext('2d');
    
    if (predictionChart) {
        predictionChart.destroy();
    }
    
    // Combine last 60 days of historical + predictions
    const historicalDays = 60;
    const histDates = historical.dates.slice(-historicalDays);
    const histPrices = historical.prices.slice(-historicalDays);
    
    const allDates = [...histDates, ...predictions.dates];
    const allPrices = [...histPrices, ...Array(predictions.prices.length).fill(null)];
    const predPrices = [...Array(histPrices.length).fill(null), ...predictions.prices];
    
    predictionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                {
                    label: 'Historical Price',
                    data: allPrices,
                    borderColor: '#1e3c72',
                    backgroundColor: 'rgba(30, 60, 114, 0.1)',
                    borderWidth: 2
                },
                {
                    label: 'Predicted Price',
                    data: predPrices,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true },
                title: {
                    display: true,
                    text: `${currentTicker} - Future Price Prediction`
                }
            }
        }
    });
}

// Compare models
async function compareModels() {
    const days = parseInt(document.getElementById('predictionDays').value);
    
    // Show loading
    document.getElementById('loadingPrediction').style.display = 'block';
    document.getElementById('predictionResults').style.display = 'none';
    document.getElementById('comparisonResults').style.display = 'none';
    
    try {
        const response = await fetch('/api/compare_models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                ticker: currentTicker, 
                days: days
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Comparison failed');
        }
        
        // Create comparison chart
        createComparisonChart(data);
        
        // Create metrics table
        createMetricsTable(data.models);
        
        // Show results
        document.getElementById('comparisonResults').style.display = 'block';
        
    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('loadingPrediction').style.display = 'none';
    }
}

// Create model comparison chart
function createComparisonChart(data) {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    
    if (comparisonChart) {
        comparisonChart.destroy();
    }
    
    const datasets = [
        {
            label: 'Random Forest',
            data: data.models.random_forest.predictions,
            borderColor: '#ff6384',
            borderWidth: 2,
            fill: false
        },
        {
            label: 'Gradient Boosting',
            data: data.models.gradient_boost.predictions,
            borderColor: '#36a2eb',
            borderWidth: 2,
            fill: false
        },
        {
            label: 'Linear Regression',
            data: data.models.linear.predictions,
            borderColor: '#4bc0c0',
            borderWidth: 2,
            fill: false
        }
    ];
    
    comparisonChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true },
                title: {
                    display: true,
                    text: 'Model Predictions Comparison'
                }
            }
        }
    });
}

// Create metrics comparison table
function createMetricsTable(models) {
    const table = document.getElementById('metricsTable');
    
    let html = `
        <thead>
            <tr>
                <th>Model</th>
                <th>RMSE</th>
                <th>MAE</th>
                <th>R² Score</th>
                <th>MAPE</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    for (const [modelName, modelData] of Object.entries(models)) {
        const metrics = modelData.metrics;
        html += `
            <tr>
                <td><strong>${modelName.replace('_', ' ').toUpperCase()}</strong></td>
                <td>$${metrics.rmse}</td>
                <td>$${metrics.mae}</td>
                <td>${metrics.r2}</td>
                <td>${metrics.mape}%</td>
            </tr>
        `;
    }
    
    html += '</tbody>';
    table.innerHTML = html;
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

// Allow Enter key in ticker input
document.addEventListener('DOMContentLoaded', function() {
    const tickerInput = document.getElementById('tickerInput');
    if (tickerInput) {
        tickerInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeStock();
            }
        });
    }
});
