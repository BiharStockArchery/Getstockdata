import logging
import yfinance as yf
from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime
import concurrent.futures

# Set up logging with timestamps
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS

# Stock symbols
symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS", "SBIN.NS", "BAJFINANCE.NS", "LT.NS", 
    "AXISBANK.NS", "WIPRO.NS", "ICICIBANK.NS", "MARUTI.NS", "HCLTECH.NS", "SUNPHARMA.NS"
]

# Timezone setting
IST = pytz.timezone('Asia/Kolkata')

# In-memory cache to store stock data
cached_stock_data = {}
last_updated = None


def fetch_stock(symbol):
    """Fetch stock data for a single symbol to speed up processing."""
    try:
        data = yf.download(symbol, period="5d", interval="1m")
        if data.empty:
            logger.warning(f"No data for {symbol}")
            return symbol, None
        
        # Extract closing prices and convert to list
        closing_prices = data['Close'].dropna()
        
        # Ensure enough data points exist
        if len(closing_prices) < 2:
            return symbol, None
        
        previous_close = closing_prices.iloc[-2]
        current_price = closing_prices.iloc[-1]
        percentage_change = ((current_price - previous_close) / previous_close) * 100

        # Return as a dictionary with serializable values
        return symbol, {
            "current_price": round(float(current_price), 2),  # Explicitly convert to float
            "percentage_change": round(float(percentage_change), 2)  # Explicitly convert to float
        }
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return symbol, None


def get_sector_data():
    """Fetch stock data in parallel and store results in cache."""
    global cached_stock_data, last_updated
    try:
        start_time = datetime.now()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(fetch_stock, symbols)

        stock_data = {symbol: data for symbol, data in results if data is not None}

        if stock_data:
            cached_stock_data = stock_data
            last_updated = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Stock data updated successfully at {last_updated}")
        else:
            logger.warning("No valid stock data was fetched.")

        logger.info(f"Data fetch completed in {(datetime.now() - start_time).seconds} seconds")
        return cached_stock_data
    except Exception as e:
        logger.error(f"Error fetching stock data: {e}")
        return {"error": "Error fetching stock data."}


def update_data():
    """Background job to update stock data periodically."""
    logger.info("Updating stock data...")
    get_sector_data()


# Schedule periodic data updates every 2 minutes
scheduler = BackgroundScheduler(timezone=IST)
scheduler.add_job(update_data, 'interval', minutes=2)
scheduler.start()


@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    """API endpoint to return cached stock data quickly."""
    if not cached_stock_data:
        logger.warning("Serving empty cache, fetching new data...")
        get_sector_data()  # Fetch new data if cache is empty

    # Convert cached data to a serializable format
    response = {
        "data": {
            symbol: {
                "current_price": stock_data["current_price"],
                "percentage_change": stock_data["percentage_change"]
            }
            for symbol, stock_data in cached_stock_data.items()
        },
        "last_updated": last_updated
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
