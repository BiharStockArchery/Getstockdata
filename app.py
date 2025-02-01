import logging
import yfinance as yf
from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime

# Set up logging with timestamps
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for a specific origin
CORS(app, resources={r"/get_stock_data": {"origins": "https://gleaming-lokum-2106f6.netlify.app"}})

symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ACC.NS",
    "APLAPOLLO.NS", "AUBANK.NS", "AARTIIND.NS", "ABBOTINDIA.NS",
    "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS",
    "ATGL.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS",
    "AMBUJACEM.NS", "ANGELONE.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS",
    "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS",
    "AUROPHARMA.NS", "DMART.NS", "AXISBANK.NS", "BSOFT.NS",
    "BSE.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BALKRISIND.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BANKINDIA.NS",
    "BATAINDIA.NS", "BERGEPAINT.NS", "BEL.NS", "BHARATFORG.NS",
    "BHEL.NS", "BPCL.NS", "BHARTIARTL.NS", "BIOCON.NS",
    "BOSCHLTD.NS", "BRITANNIA.NS", "CESC.NS", "CGPOWER.NS",
    "CANFINHOME.NS", "CANBK.NS", "CDSL.NS", "CHAMBLFERT.NS",
    "CHOLAFIN.NS", "CIPLA.NS", "CUB.NS", "COALINDIA.NS",
    "COFORGE.NS", "COLPAL.NS", "CAMS.NS", "CONCOR.NS",
    "COROMANDEL.NS", "CROMPTON.NS", "CUMMINSIND.NS", "CYIENT.NS",
    "DLF.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS",
    "DELHIVERY.NS", "DIVISLAB.NS", "DIXON.NS", "LALPATHLAB.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS", "EXIDEIND.NS",
    "NYKAA.NS", "GAIL.NS", "GMRAIRPORT.NS", "GLENMARK.NS",
    "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS",
    "GUJGASLTD.NS", "GNFC.NS", "HCLTECH.NS", "HDFCAMC.NS",
    "HDFCBANK.NS", "HDFCLIFE.NS", "HFCL.NS", "HAVELLS.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HAL.NS", "HINDCOPPER.NS",
    "HINDPETRO.NS", "HINDUNILVR.NS", "HUDCO.NS", "ICICIBANK.NS",
    "ICICIGI.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "IPCALAB.NS",
    "IRB.NS", "ITC.NS", "INDIAMART.NS", "INDIANB.NS",
    "IEX.NS", "IOC.NS", "IRCTC.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS",
    "L&T.NS", "LICHSGFIN.NS", "LTIMINDRA.NS", "M&M.NS",
    "MINDTREE.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS",
    "MUTHOOTFIN.NS", "NATIONALUM.NS", "NESTLEIND.NS", "NMDC.NS",
    "NTPC.NS", "OIL.NS", "PAGEIND.NS", "PERSISTENT.NS",
    "PHILIPCARB.NS", "PIDILITIND.NS", "PNB.NS", "POLYCAB.NS",
    "POWERGRID.NS", "RECLTD.NS", "SBILIFE.NS", "SBIN.NS",
    "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS",
    "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TECHM.NS",
    "TITAN.NS", "TORNTPOWER.NS", "ULTRACEMCO.NS", "UPL.NS",
    "WIPRO.NS", "ZOMATO.NS"
]

# Timezone setting
IST = pytz.timezone('Asia/Kolkata')

# In-memory cache to store stock data
cached_stock_data = {}
last_updated = None

def fetch_stock(symbol):
    """Fetch stock data for a single symbol."""
    try:
        # Fetch historical data for the last 5 days with daily frequency
        data = yf.download(symbol, period="5d", interval="1d")
        
        if data.empty:
            logger.warning(f"No data for {symbol}")
            return symbol, None

        # Extract closing prices
        closing_prices = data['Close'].dropna()
        
        # Ensure we have at least 2 data points (the last day and the day before)
        if len(closing_prices) < 2:
            logger.warning(f"Insufficient data for {symbol}")
            return symbol, None

        # Get the most recent and the previous day's closing prices
        previous_close = closing_prices.iloc[-2]  # Previous day's closing price
        current_price = closing_prices.iloc[-1]    # Current day's closing price

        # Calculate the percentage change
        percentage_change = ((current_price - previous_close) / previous_close) * 100

        # Return as a dictionary with serializable values
        return symbol, {
            "current_price": round(float(current_price), 2),  # Explicitly convert to float
            "previous_close": round(float(previous_close), 2),  # Previous day's closing price
            "percentage_change": round(float(percentage_change), 2)  # Percentage change
        }
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return symbol, None

def get_sector_data():
    """Fetch stock data one by one and store results in cache."""
    global cached_stock_data, last_updated
    try:
        start_time = datetime.now()

        stock_data = {}

        # Fetch stock data one by one (sequentially)
        for symbol in symbols:
            data = fetch_stock(symbol)  # Fetch data for one stock at a time
            if data[1] is not None:  # If the data is valid
                stock_data[data[0]] = data[1]

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
scheduler.start ```python
())

# Fetch stock data immediately upon startup
get_sector_data()

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    """API endpoint to return cached stock data."""
    return jsonify(cached_stock_data)

@app.route('/get_last_updated', methods=['GET'])
def get_last_updated():
    """API endpoint to return the last updated timestamp."""
    return jsonify({"last_updated": last_updated})

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode
