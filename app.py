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

# Enable CORS for both localhost and the Netlify frontend
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://gleaming-lokum-2106f6.netlify.app"]}})

# List of all stock symbols
symbols = [
    "AXISBANK.NS", "AUBANK.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BANKINDIA.NS", "CANBK.NS", "CUB.NS", "FEDERALBNK.NS", 
    "HDFCBANK.NS", "ICICIBANK.NS", "IDFCFIRSTB.NS", "INDUSINDBK.NS", "KOTAKBANK.NS", "PNB.NS", "RBLBANK.NS", "SBIN.NS", 
    "YESBANK.NS", "ABCAPITAL.NS", "ANGELONE.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "CANFINHOME.NS", "CHOLAFIN.NS", "HDFCAMC.NS", 
    "HDFCLIFE.NS", "ICICIGI.NS", "ICICIPRULI.NS", "LICIHSGFIN.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MUTHOOTFIN.NS", "PEL.NS", 
    "PFC.NS", "POONAWALLA.NS", "RECLTD.NS", "SBICARD.NS", "SBILIFE.NS", "SHRIRAMFIN.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", 
    "BPCL.NS", "GAIL.NS", "GUJGASLTD.NS", "IGL.NS", "IOC.NS", "MGL.NS", "NTPC.NS", "OIL.NS", "ONGC.NS", "PETRONET.NS", 
    "POWERGRID.NS", "RELIANCE.NS", "SJVN.NS", "TATAPOWER.NS", "ADANIENSOL.NS", "NHPC.NS", "NTPC.NS", "POWERGRID.NS", 
    "SJVN.NS", "TATAPOWER.NS", "ACC.NS", "AMBUJACEM.NS", "DALBHARAT.NS", "JKCEMENT.NS", "RAMCOCEM.NS", "SHREECEM.NS", 
    "ULTRACEMCO.NS", "APLAPOLLO.NS", "HINDALCO.NS", "HINDCOPPER.NS", "JINDALSTEL.NS", "JSWSTEEL.NS", "NATIONALUM.NS", 
    "NMDC.NS", "SAIL.NS", "TATASTEEL.NS", "VEDL.NS", "BSOFT.NS", "COFORGE.NS", "CYIENT.NS", "INFY.NS", "LTIM.NS", "LTTS.NS", 
    "MPHASIS.NS", "PERSISTENT.NS", "TATAELXSI.NS", "TCS.NS", "TECHM.NS", "WIPRO.NS", "ASHOKLEY.NS", "BAJAJ-AUTO.NS", 
    "BHARATFORG.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "M&M.NS", "MARUTI.NS", "MOTHERSON.NS", "TATAMOTORS.NS", "TVSMOTOR.NS", 
    "ABFRL.NS", "DMART.NS", "NYKAA.NS", "PAGEIND.NS", "PAYTM.NS", "TRENT.NS", "VBL.NS", "ZOMATO.NS", "ASIANPAINT.NS", 
    "BERGEPAINT.NS", "BRITANNIA.NS", "COLPAL.NS", "DABUR.NS", "GODREJCP.NS", "HINDUNILVR.NS", "ITC.NS", "MARICO.NS", 
    "NESTLEIND.NS", "TATACONSUM.NS", "UBL.NS", "UNITEDSPR.NS", "VOLTAS.NS", "ALKEM.NS", "APLLTD.NS", "AUROPHARMA.NS", 
    "BIOCON.NS", "CIPLA.NS", "DIVISLAB.NS", "DRREDDY.NS", "GLENMARK.NS", "GRANULES.NS", "LAURUSLABS.NS", "LUPIN.NS", 
    "SUNPHARMA.NS", "SYNGENE.NS", "TORNTPHARM.NS", "APOLLOHOSP.NS", "LALPATHLAB.NS", "MAXHEALTH.NS", "METROPOLIS.NS", 
    "BHARTIARTL.NS", "HFCL.NS", "IDEA.NS", "INDUSTOWER.NS", "DLF.NS", "GODREJPROP.NS", "LODHA.NS", "OBEROIRLTY.NS", 
    "PRESTIGE.NS", "GUJGASLTD.NS", "IGL.NS", "MGL.NS", "CONCOR.NS", "CESC.NS", "HUDCO.NS", "IRFC.NS", "ABBOTINDIA.NS", 
    "BEL.NS", "CGPOWER.NS", "CUMMINSIND.NS", "HAL.NS", "L&T.NS", "SIEMENS.NS", "TIINDIA.NS", "CHAMBLFERT.NS", 
    "COROMANDEL.NS", "GNFC.NS", "PIIND.NS", "BSE.NS", "DELHIVERY.NS", "GMRAIRPORT.NS", "IRCTC.NS", "KEI.NS", "NAVINFLUOR.NS", 
    "POLYCAB.NS", "SUNTV.NS", "UPL.NS"
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
scheduler.add_job(update_stock_data, 'interval', seconds=30, timezone=IST)
scheduler.start()

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    """API route to get cached stock data."""
    response = jsonify({
        "stocks": cached_stock_data,
        "last_updated": last_updated
    })
    # This header allows the response to be accessed by your frontend
    response.headers.add("Access-Control-Allow-Origin", "*")  # Allows all origins, but can be restricted
    response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
    return response

if __name__ == '__main__':
    update_stock_data()  # Initial data fetch
    app.run(host='0.0.0.0', port=5000, debug=True)   
