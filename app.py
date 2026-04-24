"""
Faiter Terminal — Stock Chart API
Yahoo Finance backend for NSE stocks + NIFTY/BANKNIFTY indices
Deploy free on Render.com
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import logging

app = Flask(__name__)
CORS(app)  # Allow requests from any origin (your frontend)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ─── Symbol map: short name → Yahoo Finance ticker ───────────
SYMBOL_MAP = {
    # NSE Stocks
    "RELIANCE":    "RELIANCE.NS",
    "TCS":         "TCS.NS",
    "HDFCBANK":    "HDFCBANK.NS",
    "INFY":        "INFY.NS",
    "WIPRO":       "WIPRO.NS",
    "SBIN":        "SBIN.NS",
    "ONGC":        "ONGC.NS",
    "ICICIBANK":   "ICICIBANK.NS",
    "BHARTI":      "BHARTIARTL.NS",
    "BHARTIARTL":  "BHARTIARTL.NS",
    "ADANIENT":    "ADANIENT.NS",
    "HINDALCO":    "HINDALCO.NS",
    "NTPC":        "NTPC.NS",
    "BPCL":        "BPCL.NS",
    "COALINDIA":   "COALINDIA.NS",
    "HCLTECH":     "HCLTECH.NS",
    "LT":          "LT.NS",
    "MARUTI":      "MARUTI.NS",
    "BAJFINANCE":  "BAJFINANCE.NS",
    "AXISBANK":    "AXISBANK.NS",
    "KOTAKBANK":   "KOTAKBANK.NS",
    "TATASTEEL":   "TATASTEEL.NS",
    "TATAMOTORS":  "TATAMOTORS.NS",
    "SUNPHARMA":   "SUNPHARMA.NS",
    "TITAN":       "TITAN.NS",
    "TECHM":       "TECHM.NS",
    "HDFC":        "HDFCBANK.NS",
    "DRREDDY":     "DRREDDY.NS",
    "ASIANPAINT":  "ASIANPAINT.NS",
    "BAJAJFINSV":  "BAJAJFINSV.NS",
    "ULTRACEMCO":  "ULTRACEMCO.NS",
    "NESTLEIND":   "NESTLEIND.NS",
    "POWERGRID":   "POWERGRID.NS",
    "DIVISLAB":    "DIVISLAB.NS",
    "PFC":         "PFC.NS",
    "REC":         "REC.NS",
    "HDFC":        "HDFCBANK.NS",
    # NSE Indices
    "NIFTY":       "^NSEI",
    "NIFTY50":     "^NSEI",
    "BANKNIFTY":   "^NSEBANK",
    "BNIFTY":      "^NSEBANK",
    "NIFTYMIDCAP": "^NSEMDCP50",
    "FINNIFTY":    "^CNXFIN",
    # BSE
    "SENSEX":      "^BSESN",
}

# ─── Valid intervals and ranges ──────────────────────────────
VALID_INTERVALS = {"1m","2m","5m","15m","30m","60m","1h","1d","5d","1wk","1mo","3mo"}
VALID_RANGES    = {"1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"}

def resolve_symbol(sym: str) -> str:
    """Convert short symbol to Yahoo Finance ticker."""
    s = sym.strip().upper()
    if s in SYMBOL_MAP:
        return SYMBOL_MAP[s]
    # If already has suffix (.NS, .BO) or is index (^), use as-is
    if "." in s or s.startswith("^"):
        return s
    # Default: assume NSE
    return s + ".NS"

# ─── Routes ──────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "name": "Faiter Terminal Chart API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/chart/<symbol>": "OHLC candlestick data",
            "/quote/<symbol>": "Latest price + change",
            "/search/<query>": "Symbol search",
            "/health": "Health check"
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

@app.route("/chart/<symbol>")
def get_chart(symbol):
    """
    Returns OHLC candlestick data for a symbol.
    Query params:
      interval: 1d (default), 1wk, 1mo, 5m, 15m etc.
      range:    3mo (default), 1mo, 6mo, 1y, 5y etc.
    """
    try:
        interval = request.args.get("interval", "1d")
        range_   = request.args.get("range", "3mo")

        # Validate
        if interval not in VALID_INTERVALS:
            return jsonify({"error": f"Invalid interval. Use: {', '.join(VALID_INTERVALS)}"}), 400
        if range_ not in VALID_RANGES:
            return jsonify({"error": f"Invalid range. Use: {', '.join(VALID_RANGES)}"}), 400

        yahoo_sym = resolve_symbol(symbol)
        log.info(f"Fetching {yahoo_sym} | interval={interval} range={range_}")

        ticker = yf.Ticker(yahoo_sym)
        hist   = ticker.history(period=range_, interval=interval, auto_adjust=True)

        if hist.empty:
            return jsonify({"error": f"No data found for symbol: {symbol}"}), 404

        candles = []
        for date, row in hist.iterrows():
            # Skip rows with null OHLC
            if any(v != v for v in [row["Open"], row["High"], row["Low"], row["Close"]]):
                continue
            candles.append({
                "time":   date.strftime("%Y-%m-%d") if interval in ("1d","1wk","1mo","3mo") else int(date.timestamp()),
                "open":   round(float(row["Open"]),  2),
                "high":   round(float(row["High"]),  2),
                "low":    round(float(row["Low"]),   2),
                "close":  round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if "Volume" in row else 0,
            })

        return jsonify({
            "symbol":   symbol.upper(),
            "ticker":   yahoo_sym,
            "interval": interval,
            "range":    range_,
            "count":    len(candles),
            "data":     candles
        })

    except Exception as e:
        log.error(f"Error fetching {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/quote/<symbol>")
def get_quote(symbol):
    """Returns latest price, change, and % change for a symbol."""
    try:
        yahoo_sym = resolve_symbol(symbol)
        ticker    = yf.Ticker(yahoo_sym)
        info      = ticker.fast_info

        price     = round(float(info.last_price), 2)
        prev      = round(float(info.previous_close), 2)
        change    = round(price - prev, 2)
        change_pct= round((change / prev) * 100, 2) if prev else 0

        return jsonify({
            "symbol":      symbol.upper(),
            "ticker":      yahoo_sym,
            "price":       price,
            "prev_close":  prev,
            "change":      change,
            "change_pct":  change_pct,
            "currency":    "INR",
        })

    except Exception as e:
        log.error(f"Quote error {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/search/<query>")
def search_symbols(query):
    """Returns matching NSE symbols for a search query."""
    q = query.upper()
    matches = [
        {"symbol": k, "ticker": v}
        for k, v in SYMBOL_MAP.items()
        if q in k
    ]
    return jsonify({"query": query, "results": matches[:10]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
