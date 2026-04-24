/* ═══════════════════════════════════════════════════
   Faiter Terminal — Chart Integration
   Plug this into faiter-terminal-v4.html
   Replace FAITER_API_URL with your Render.com URL
═══════════════════════════════════════════════════ */

const FAITER_API_URL = 'https://faiter-api.onrender.com'; // ← Change this after deploy

const CHART_SYM_MAP = {
  RELIANCE:'RELIANCE', TCS:'TCS', HDFCBANK:'HDFCBANK',
  INFY:'INFY', WIPRO:'WIPRO', SBIN:'SBIN',
  ONGC:'ONGC', ICICIBANK:'ICICIBANK', BHARTI:'BHARTI',
  ADANIENT:'ADANIENT', HINDALCO:'HINDALCO', NTPC:'NTPC',
  BPCL:'BPCL', COALINDIA:'COALINDIA', HCLTECH:'HCLTECH',
  LT:'LT', MARUTI:'MARUTI', BAJFINANCE:'BAJFINANCE',
  AXISBANK:'AXISBANK', KOTAKBANK:'KOTAKBANK',
  TATASTEEL:'TATASTEEL', TATAMOTORS:'TATAMOTORS',
  SUNPHARMA:'SUNPHARMA', TITAN:'TITAN', TECHM:'TECHM',
  NIFTY50:'NIFTY50', NIFTY:'NIFTY',
  BANKNIFTY:'BANKNIFTY', BNIFTY:'BANKNIFTY',
  SENSEX:'SENSEX', HDFC:'HDFCBANK',
};

const INTERVAL_MAP = {'1d':'1d','1wk':'1wk','1mo':'1mo'};
const _cache = {};
const CACHE_TTL = 5 * 60 * 1000;

let _chart = null;
let _candleSeries = null;
let _chartSym = 'RELIANCE';
let _chartInterval = '1d';
let _chartRange = '3mo';

function initChart(){
  const el = document.getElementById('chart');
  if(!el || _chart) return;
  if(typeof LightweightCharts === 'undefined'){ setTimeout(initChart, 100); return; }

  _chart = LightweightCharts.createChart(el, {
    autoSize: true,
    layout:{ background:{type:'solid',color:'#000'}, textColor:'#9a9080' },
    grid:{ vertLines:{color:'rgba(30,28,24,.6)'}, horzLines:{color:'rgba(30,28,24,.6)'} },
    crosshair:{
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine:{ color:'rgba(232,160,32,.5)', labelBackgroundColor:'#e8a020' },
      horzLine:{ color:'rgba(232,160,32,.5)', labelBackgroundColor:'#e8a020' },
    },
    rightPriceScale:{ borderColor:'#1e1c18', textColor:'#9a9080' },
    timeScale:{ borderColor:'#1e1c18', timeVisible:true, secondsVisible:false },
    handleScroll:true, handleScale:true,
  });

  _candleSeries = _chart.addCandlestickSeries({
    upColor:'#28a060', downColor:'#d83028',
    borderUpColor:'#28a060', borderDownColor:'#d83028',
    wickUpColor:'#28a060', wickDownColor:'#d83028',
  });

  _chart.subscribeCrosshairMove(p => {
    const d = p?.seriesData?.get(_candleSeries);
    if(!d) return;
    const f = v => v?.toFixed(2) ?? '—';
    const set = (id, v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
    set('cf-open', f(d.open)); set('cf-high', f(d.high));
    set('cf-low', f(d.low)); set('cf-close', f(d.close));
  });

  new ResizeObserver(() =>
    _chart?.applyOptions({ width: el.clientWidth, height: el.clientHeight })
  ).observe(el);

  loadChart('RELIANCE');
}

async function fetchChartData(symbol, interval, range){
  const key = `${symbol}_${interval}_${range}`;
  if(_cache[key] && Date.now() - _cache[key].ts < CACHE_TTL) return _cache[key].data;

  const url = `${FAITER_API_URL}/chart/${symbol}?interval=${interval}&range=${range}`;
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
    if(!res.ok) throw new Error(`API error ${res.status}`);
    const json = await res.json();
    if(!json.data?.length) throw new Error('No data');
    _cache[key] = { data: json.data, ts: Date.now() };
    return json.data;
  } catch(e) {
    console.warn('[FaiterChart]', e.message);
    return null;
  }
}

function updatePriceBar(candles, sym, live) {
  const last = candles[candles.length - 1];
  const prev = candles[candles.length - 2];
  const chg  = prev ? +(last.close - prev.close).toFixed(2) : 0;
  const pct  = prev ? +((chg / prev.close) * 100).toFixed(2) : 0;
  const up   = chg >= 0;

  const set = (id, v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
  set('cpi-sym',   sym);
  set('cpi-price', last.close.toFixed(2));
  const ce = document.getElementById('cpi-change');
  if(ce){ ce.textContent = `${up?'+':''}${chg} (${up?'+':''}${pct}%)`; ce.className = `cpi-change ${up?'up':'dn'}`; }
  set('cf-open',  last.open.toFixed(2));
  set('cf-high',  last.high.toFixed(2));
  set('cf-low',   last.low.toFixed(2));
  set('cf-close', last.close.toFixed(2));
  const inp = document.getElementById('chart-symbol-input');
  if(inp) inp.value = sym;
  document.querySelectorAll('.cs-sym-btn').forEach(b => b.classList.toggle('active', b.dataset.sym === sym));
  const st = document.getElementById('chart-status');
  if(st){ st.textContent = live ? `${candles.length} bars · NSE Live` : ''; st.style.color = live ? 'var(--grn)' : 'var(--txt3)'; }
}

async function loadChart(sym) {
  sym = (sym || document.getElementById('chart-symbol-input')?.value || 'RELIANCE').trim().toUpperCase();
  _chartSym = sym;
  const st = document.getElementById('chart-status');
  if(st){ st.textContent = 'Loading…'; st.style.color = 'var(--txt3)'; }

  const candles = await fetchChartData(sym, _chartInterval, _chartRange);

  if(!candles) {
    if(st){ st.textContent = 'Data unavailable'; st.style.color = 'var(--red)'; }
    return;
  }

  if(!_chart) initChart();
  _candleSeries.setData(candles);
  _chart.timeScale().fitContent();
  updatePriceBar(candles, sym, true);
}

function chartLoad(){ loadChart(document.getElementById('chart-symbol-input')?.value); }
function quickLoad(btn){ loadChart(btn.dataset.sym); }
function setChartInterval(btn){
  document.querySelectorAll('.ci-btn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  _chartInterval = INTERVAL_MAP[btn.dataset.interval] || '1d';
  _chartRange    = btn.dataset.range;
  delete _cache[`${_chartSym}_${_chartInterval}_${_chartRange}`];
  loadChart(_chartSym);
}
