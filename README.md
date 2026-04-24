# Faiter Terminal — Chart API Backend

Yahoo Finance API backend for Faiter Terminal.
Provides NSE stock + index OHLC data without CORS issues.

---

## 🚀 Deploy Free on Render.com (5 minutes)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Faiter API"
git remote add origin https://github.com/YOUR_USERNAME/faiter-api.git
git push -u origin main
```

### Step 2 — Deploy on Render
1. Go to https://render.com → Sign up free
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Settings auto-detected from render.yaml:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app ...`
   - **Plan:** Free
5. Click **Create Web Service**
6. Wait ~3 minutes for deploy
7. Your API URL: `https://faiter-api.onrender.com`

---

## 📡 API Endpoints

### Chart Data (OHLC Candlesticks)
```
GET /chart/{symbol}?interval=1d&range=3mo
```
**Example:**
```
https://faiter-api.onrender.com/chart/RELIANCE?interval=1d&range=3mo
https://faiter-api.onrender.com/chart/NIFTY?interval=1d&range=6mo
https://faiter-api.onrender.com/chart/BANKNIFTY?interval=1wk&range=1y
```

**Response:**
```json
{
  "symbol": "RELIANCE",
  "ticker": "RELIANCE.NS",
  "interval": "1d",
  "range": "3mo",
  "count": 62,
  "data": [
    {"time": "2025-01-02", "open": 1285.0, "high": 1298.5, "low": 1280.2, "close": 1293.4, "volume": 8234567},
    ...
  ]
}
```

### Latest Quote
```
GET /quote/{symbol}
```
**Response:**
```json
{
  "symbol": "RELIANCE",
  "price": 1293.4,
  "change": 8.4,
  "change_pct": 0.65,
  "currency": "INR"
}
```

### Symbol Search
```
GET /search/{query}
```

### Health Check
```
GET /health
```

---

## 📊 Supported Symbols

### NSE Stocks
RELIANCE, TCS, HDFCBANK, INFY, WIPRO, SBIN, ONGC, ICICIBANK,
BHARTI, ADANIENT, HINDALCO, NTPC, BPCL, COALINDIA, HCLTECH,
LT, MARUTI, BAJFINANCE, AXISBANK, KOTAKBANK, TATASTEEL,
TATAMOTORS, SUNPHARMA, TITAN, TECHM, DRREDDY, ASIANPAINT + more

### NSE Indices
NIFTY / NIFTY50, BANKNIFTY / BNIFTY, FINNIFTY, NIFTYMIDCAP

### BSE
SENSEX

---

## 🔌 Connect to Faiter Terminal

Once deployed, update this line in Faiter Terminal JS:

```javascript
const FAITER_API = 'https://faiter-api.onrender.com';

// Fetch chart data
const res = await fetch(`${FAITER_API}/chart/${symbol}?interval=${interval}&range=${range}`);
const json = await res.json();
const candles = json.data; // Ready for Lightweight Charts
```

---

## 💰 Free vs Paid

| | Free (Render) | Paid ($7/mo) |
|---|---|---|
| Always on | ❌ Sleeps after 15min | ✅ |
| Cold start | ~30 seconds | Instant |
| Requests/month | 750 hours | Unlimited |
| Custom domain | ❌ | ✅ |
| Best for | Testing | Production |

---

## 🛠 Local Development

```bash
pip install -r requirements.txt
python app.py
# API runs at http://localhost:5000
```
