"""
Faiter Terminal — Stock Chart API v2
Alpha Vantage backend (works from Render, no IP blocks)
Free: 25 req/day | Get key: https://www.alphavantage.co/support/#api-key
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, os, logging
from datetime import datetime

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

AV_API_KEY = os.environ.get("AV_API_KEY", "demo")
AV_BASE = "https://www.alphavantage.co/query"

SYMBOL_MAP = {
    "RELIANCE":"RELIANCE.BSE","TCS":"TCS.BSE","HDFCBANK":"HDFCBANK.BSE",
    "INFY":"INFY.BSE","WIPRO":"WIPRO.BSE","SBIN":"SBIN.BSE",
    "ONGC":"ONGC.BSE","ICICIBANK":"ICICIBANK.BSE","BHARTI":"BHARTIARTL.BSE",
    "ADANIENT":"ADANIENT.BSE","HINDALCO":"HINDALCO.BSE","NTPC":"NTPC.BSE",
    "BPCL":"BPCL.BSE","COALINDIA":"COALINDIA.BSE","HCLTECH":"HCLTECH.BSE",
    "LT":"LT.BSE","MARUTI":"MARUTI.BSE","BAJFINANCE":"BAJFINANCE.BSE",
    "AXISBANK":"AXISBANK.BSE","KOTAKBANK":"KOTAKBANK.BSE",
    "TATASTEEL":"TATASTEEL.BSE","TATAMOTORS":"TATAMOTORS.BSE",
    "SUNPHARMA":"SUNPHARMA.BSE","TITAN":"TITAN.BSE","TECHM":"TECHM.BSE",
    "HDFC":"HDFCBANK.BSE","NIFTY":"NIFTY50.BSE","NIFTY50":"NIFTY50.BSE",
    "BANKNIFTY":"NSEBANK.BSE","BNIFTY":"NSEBANK.BSE","SENSEX":"SENSEX.BSE",
}

_cache = {}

def resolve(sym):
    s = sym.strip().upper()
    return SYMBOL_MAP.get(s, s + ".BSE")

def cached(key):
    d = _cache.get(key)
    if d and (datetime.utcnow().timestamp() - d[1]) < 300:
        return d[0]

@app.route("/")
def index():
    return jsonify({"name":"Faiter Chart API","status":"running","key_set": AV_API_KEY != "demo"})

@app.route("/health")
def health():
    return jsonify({"status":"ok"})

@app.route("/chart/<symbol>")
def chart(symbol):
    interval = request.args.get("interval","1d")
    range_ = request.args.get("range","3mo")
    key = f"{symbol}_{interval}_{range_}"
    c = cached(key)
    if c: return jsonify(c)

    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": resolve(symbol),
        "apikey": AV_API_KEY,
        "outputsize": "compact" if range_ in ("1mo","3mo") else "full",
        "datatype": "json",
    }
    try:
        r = requests.get(AV_BASE, params=params, timeout=15)
        data = r.json()
        if "Information" in data or "Note" in data:
            return jsonify({"error":"API rate limit. Set AV_API_KEY in Render environment.","get_key":"https://www.alphavantage.co/support/#api-key"}), 429
        ts_key = next((k for k in data if "Time Series" in k), None)
        if not ts_key:
            return jsonify({"error":f"No data for {symbol}"}), 404
        ts = data[ts_key]
        range_days = {"1mo":30,"3mo":90,"6mo":180,"1y":365,"2y":730,"5y":1825}
        candles = sorted([{
            "time": d[:10],
            "open": round(float(v["1. open"]),2),
            "high": round(float(v["2. high"]),2),
            "low":  round(float(v["3. low"]),2),
            "close":round(float(v["5. adjusted close"]),2),
            "volume":int(float(v["6. volume"])),
        } for d,v in ts.items()], key=lambda x: x["time"])[-range_days.get(range_,90):]
        result = {"symbol":symbol.upper(),"ticker":resolve(symbol),"interval":interval,"range":range_,"count":len(candles),"data":candles}
        _cache[key] = (result, datetime.utcnow().timestamp())
        return jsonify(result)
    except Exception as e:
        log.error(f"Error: {e}")
        return jsonify({"error":str(e)}), 500

@app.route("/quote/<symbol>")
def quote(symbol):
    try:
        r = requests.get(AV_BASE, params={"function":"GLOBAL_QUOTE","symbol":resolve(symbol),"apikey":AV_API_KEY}, timeout=10)
        q = r.json().get("Global Quote",{})
        return jsonify({"symbol":symbol.upper(),"price":round(float(q.get("05. price",0)),2),"change":round(float(q.get("09. change",0)),2),"change_pct":round(float(q.get("10. change percent","0%").replace("%","")),2)})
    except Exception as e:
        return jsonify({"error":str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
