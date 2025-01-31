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
CORS(app)  # Enable CORS

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
    "IEX.NS", "IOC.NS", "IRCTC.NS", "IRFC.NS",
    "IGL.NS", "INDUSTOWER.NS", "INDUSINDBK.NS", "NAUKRI.NS",
    "INFY.NS", "INDIGO.NS", "JKCEMENT.NS", "JSWENERGY.NS",
    "JSWSTEEL.NS", "JSL.NS", "JINDALSTEL.NS", "JIOFIN.NS",
    "JUBLFOOD.NS", "KEI.NS", "KPITTECH.NS", "KALYANKJIL.NS",
    "KOTAKBANK.NS", "LTF.NS", "LTTS.NS", "LICHSGFIN.NS",
    "LTIM.NS", "LT.NS", "LAURUSLABS.NS", "LICI.NS",
    "LUPIN.NS", "MRF.NS", "LODHA.NS", "MGL.NS",
    "M&MFIN.NS", "M&M.NS", "MANAPPURAM.NS", "MARICO.NS",
    "MARUTI.NS", "MFSL.NS", "MAXHEALTH.NS", "METROPOLIS.NS",
    "MPHASIS.NS", "MCX.NS", "MUTHOOTFIN.NS", "NCC.NS",
    "NHPC.NS", "NMDC.NS", "NTPC.NS", "NATIONALUM.NS",
    "NAVINFLUOR.NS", "NESTLEIND.NS", "OBEROIRLTY.NS", "ONGC.NS",
    "OIL.NS", "PAYTM.NS", "OFSS.NS", "POLICYBZR.NS",
    "PIIND.NS", "PVRINOX.NS", "PAGEIND.NS", "PERSISTENT.NS",
    "PETRONET.NS", "PIDILITIND.NS", "PEL.NS", "POLYCAB.NS",
    "POONAWALLA.NS", "PFC.NS", "POWERGRID.NS", "PRESTIGE.NS",
    "PNB.NS", "RBLBANK.NS", "RECLTD.NS", "RELIANCE.NS",
    "SBICARD.NS", "SBILIFE.NS", "SHREECEM.NS", "SJVN.NS",
    "SRF.NS", "MOTHERSON.NS", "SHRIRAMFIN.NS", "SIEMENS.NS",
    "SONACOMS.NS", "SBIN.NS", "SAIL.NS", "SUNPHARMA.NS",
    "SUNTV.NS", "SUPREMEIND.NS", "SYNGENE.NS", "TATACONSUM.NS",
    "TVSMOTOR.NS", "TATACHEM.NS", "TATACOMM.NS", "TCS.NS",
    "TATAELXSI.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS",
    "TECHM.NS", "FEDERALBNK.NS", "INDHOTEL.NS", "RAMCOCEM.NS",
    "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "TIINDIA.NS",
    "UPL.NS", "ULTRACEMCO.NS", "UNIONBANK.NS", "UBL.NS",
    "UNITDSPR.NS", "VBL.NS", "VEDL.NS", "IDEA.NS",
    "VOLTAS.NS", "WIPRO.NS", "YESBANK.NS", "ZOMATO.NS"
    # Add more symbols as needed
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
scheduler.start()


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
