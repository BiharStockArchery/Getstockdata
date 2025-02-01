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

# Enable CORS for the specific frontend URL
CORS(app, resources={r"/*": {"origins": "https://gleaming-lokum-2106f6.netlify.app"}})

# List of all stock symbols
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
    "HDFCLIFE.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
    "HAL.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "IDFCFIRSTB.NS", "IPCALAB.NS", "INDIAMART.NS",
    "IRCTC.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "JUBLFOOD.NS",
    "KOTAKBANK.NS", "LICHSGFIN.NS", "LTIM.NS", "M&M.NS",
    "MOTHERSON.NS", "MPHASIS.NS", "MUTHOOTFIN.NS", "NESTLEIND.NS",
    "NTPC.NS", "OIL.NS", "PAGEIND.NS", "PERSISTENT.NS",
    "PIDILITIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS",
    "RECLTD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS",
    "SIEMENS.NS", "SUNPHARMA.NS", "TATAMOTORS.NS", "TATAPOWER.NS",
    "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "TORNTPOWER.NS",
    "ULTRACEMCO.NS", "WIPRO.NS", "ZOMATO.NS"
]

# Timezone setting
IST = pytz.timezone('Asia/Kolkata')

# In-memory cache to store stock data
cached_stock_data = {}
last_updated = None

def fetch_stock(symbol):
    """Fetch stock data for a single symbol."""
    try:
        data = yf.download(symbol, period="5d", interval="1d")
        
        if data.empty:
            logger.warning(f"No data for {symbol}")
            return symbol, None

        closing_prices = data['Close'].dropna()
        
        if len(closing_prices) < 2:
            logger.warning(f"Insufficient data for {symbol}")
            return symbol, None

        previous_close = closing_prices.iloc[-2]
        current_price = closing_prices.iloc[-1]
        percentage_change = ((current_price - previous_close) / previous_close) * 100

        return symbol, {
            "current_price": round(float(current_price), 2),
            "previous_close": round(float(previous_close), 2),
            "percentage_change": round(float(percentage_change), 2)
        }
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return symbol, None

def update_stock_data():
    """Fetch stock data and update cache."""
    global cached_stock_data, last_updated
    stock_data = {}

    for symbol in symbols:
        data = fetch_stock(symbol)
        if data[1] is not None:
            stock_data[data[0]] = data[1]

    if stock_data:
        cached_stock_data = stock_data
        last_updated = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Stock data updated at {last_updated}")

# Schedule periodic updates
scheduler = BackgroundScheduler()
scheduler.add_job(update_stock_data, 'interval', minutes=5, timezone=IST)
scheduler.start()

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    """API route to get cached stock data."""
    response = jsonify({
        "stocks": cached_stock_data,
        "last_updated": last_updated
    })
    response.headers.add("Access-Control-Allow-Origin", "https://gleaming-lokum-2106f6.netlify.app")
    response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
    return response

if __name__ == '__main__':
    update_stock_data()  # Initial data fetch
    app.run(host='0.0.0.0', port=5000, debug=True)
