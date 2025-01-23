import logging
import yfinance as yf
from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for the Flask app
CORS(app)

# List of stock symbols (same as you provided)
symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ACC.NS",
    "APLAPOLLO.NS", "AUBANK.NS", "AARTIIND.NS", "ABBOTINDIA.NS",
    "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS",
    "ATGL.NS", "ABCAPITAL.NS", "ABFRL.NS", "ALKEM.NS", "AMBUJACEM.NS",
    "ANGELONE.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS",
    "ASIANPAINT.NS", "ASTRAL.NS", "ATUL.NS", "AUROPHARMA.NS", "DMART.NS",
    "AXISBANK.NS", "BSOFT.NS", "BSE.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "BALKRISIND.NS", "BANDHANBNK.NS", "BANKBARODA.NS",
    "BANKINDIA.NS", "BATAINDIA.NS", "BERGEPAINT.NS", "BEL.NS", "BHARATFORG.NS",
    "BHEL.NS", "BPCL.NS", "BHARTIARTL.NS", "BIOCON.NS", "BOSCHLTD.NS",
    "BRITANNIA.NS", "CESC.NS", "CGPOWER.NS", "CANFINHOME.NS", "CANBK.NS",
    "CDSL.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS", "CUB.NS",
    "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS", "CAMS.NS", "CONCOR.NS",
    "COROMANDEL.NS", "CROMPTON.NS", "CUMMINSIND.NS", "CYIENT.NS", "DLF.NS",
    "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DIVISLAB.NS",
    "DIXON.NS", "LALPATHLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS",
    "EXIDEIND.NS", "NYKAA.NS", "GAIL.NS", "GMRAIRPORT.NS", "GLENMARK.NS",
    "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS",
    "GNFC.NS", "HCLTECH.NS", "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HFCL.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HAL.NS",
    "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "HUDCO.NS", "ICICIBANK.NS",
    "ICICIGI.NS", "ICICIPRULI.NS", "IDFCFIRSTB.NS", "IPCALAB.NS", "IRB.NS",
    "ITC.NS", "INDIAMART.NS", "INDIANB.NS", "IEX.NS", "IOC.NS", "IRCTC.NS",
    "IRFC.NS", "IGL.NS", "INDUSTOWER.NS", "INDUSINDBK.NS", "NAUKRI.NS",
    "INFY.NS", "INDIGO.NS", "JKCEMENT.NS", "JSWENERGY.NS", "JSWSTEEL.NS",
    "JSL.NS", "JINDALSTEL.NS", "JIOFIN.NS", "JUBLFOOD.NS", "KEI.NS",
    "KPITTECH.NS", "KALYANKJIL.NS", "KOTAKBANK.NS", "LTF.NS", "LTTS.NS",
    "LICHSGFIN.NS", "LTIM.NS", "LT.NS", "LAURUSLABS.NS", "LICI.NS", "LUPIN.NS",
    "MRF.NS", "LODHA.NS", "MGL.NS", "M&MFIN.NS", "M&M.NS", "MANAPPURAM.NS",
    "MARICO.NS", "MARUTI.NS", "MFSL.NS", "MAXHEALTH.NS", "METROPOLIS.NS",
    "MPHASIS.NS", "MCX.NS", "MUTHOOTFIN.NS", "NCC.NS", "NHPC.NS", "NMDC.NS",
    "NTPC.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "OBEROIRLTY.NS",
    "ONGC.NS", "OIL.NS", "PAYTM.NS", "OFSS.NS", "POLICYBZR.NS", "PIIND.NS",
    "PVRINOX.NS", "PAGEIND.NS", "PERSISTENT.NS", "PETRONET.NS", "PIDILITIND.NS",
    "PEL.NS", "POLYCAB.NS", "POONAWALLA.NS", "PFC.NS", "POWERGRID.NS",
    "PRESTIGE.NS", "PNB.NS", "RBLBANK.NS", "RECLTD.NS", "RELIANCE.NS",
    "SBICARD.NS", "SBILIFE.NS", "SHREECEM.NS", "SJVN.NS", "SRF.NS",
    "MOTHERSON.NS", "SHRIRAMFIN.NS", "SIEMENS.NS", "SONACOMS.NS", "SBIN.NS",
    "SAIL.NS", "SUNPHARMA.NS", "SUNTV.NS", "SUPREMEIND.NS", "SYNGENE.NS",
    "TATACONSUM.NS", "TVSMOTOR.NS", "TATACHEM.NS", "TATACOMM.NS", "TCS.NS",
    "TATAELXSI.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TECHM.NS",
    "FEDERALBNK.NS", "INDHOTEL.NS", "RAMCOCEM.NS", "TITAN.NS", "TORNTPHARM.NS",
    "TRENT.NS", "TIINDIA.NS", "UPL.NS", "ULTRACEMCO.NS", "UNIONBANK.NS",
    "UBL.NS", "UNITDSPR.NS", "VBL.NS", "VEDL.NS", "IDEA.NS", "VOLTAS.NS",
    "WIPRO.NS", "YESBANK.NS", "ZOMATO.NS",
]

# Define the timezone (Indian Standard Time)
IST = pytz.timezone('Asia/Kolkata')

def fetch_data_with_retry():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Fetch 5 days of minute-level data
            data = yf.download(symbols, period="5d", interval="1m")
            if not data.empty:
                return data
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(5)  # wait before retrying
    return None  # Return None if all attempts fail

def get_sector_data():
    try:
        # Get the current date and time
        now = datetime.now(IST)

        # Fetch data with retries
        data = fetch_data_with_retry()
        if data is None or data.empty:
            logger.error("No data returned from Yahoo Finance.")
            return {"error": "No stock data available."}

        # Check if the data contains 'Adj Close' or 'Close' for accurate price info
        stock_data = data.get('Adj Close', data.get('Close'))

        if stock_data is None or stock_data.empty:
            logger.error("No valid stock data for symbols.")
            return {"error": "No valid stock data available."}

        # Prepare the result data dictionary
        result_data = {}

        for symbol in symbols:
            # Handle missing data more gracefully
            if symbol not in stock_data.columns:
                logger.warning("Missing data for symbol %s", symbol)
                continue
            
            try:
                previous_day_close = stock_data[symbol].iloc[-2]
                current_price = stock_data[symbol].iloc[-1]
                percentage_change = ((current_price - previous_day_close) / previous_day_close) * 100

                if not (current_price != current_price or previous_day_close != previous_day_close):
                    result_data[symbol] = {
                        "current_price": current_price,
                        "percentage_change": percentage_change
                    }
            except Exception as e:
                logger.error("Error processing data for symbol %s: %s", symbol, e)

        return result_data

    except Exception as e:
        logger.error("Error fetching stock data: %s", e)
        return {"error": str(e)}

# Define the background task function
def update_data():
    try:
        result = get_sector_data()
        logger.info("Data updated successfully: %s", result)
    except Exception as e:
        logger.error("Error in background task: %s", e)

# Schedule the background task to run every minute
scheduler = BackgroundScheduler(timezone=IST)
scheduler.add_job(update_data, 'interval', minutes=1)
scheduler.start()

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    try:
        result = get_sector_data()
        return jsonify(result)
    except Exception as e:
        logger.error("Error fetching stock data: %s", e)
        return jsonify({"error": "Error fetching stock data."}), 500

if __name__ == '__main__':
    app.run(debug=True)
