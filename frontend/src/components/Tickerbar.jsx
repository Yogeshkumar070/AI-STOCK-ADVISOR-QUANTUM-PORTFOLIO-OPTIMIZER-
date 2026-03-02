/* TickerBar.jsx — scrolling Nifty 50 ticker strip (Tickertape style) */
import React, { useEffect, useRef, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

const NIFTY50_STOCKS = [
  "RELIANCE.NS","TCS.NS","HDFCBANK.NS","BHARTIARTL.NS","ICICIBANK.NS",
  "INFOSYS.NS","SBIN.NS","HINDUNILVR.NS","ITC.NS","LT.NS",
  "KOTAKBANK.NS","AXISBANK.NS","MARUTI.NS","SUNPHARMA.NS","ULTRACEMCO.NS",
  "TITAN.NS","BAJFINANCE.NS","WIPRO.NS","HCLTECH.NS","ADANIENT.NS",
  "ONGC.NS","NTPC.NS","POWERGRID.NS","COALINDIA.NS","BAJAJFINSV.NS",
  "JSWSTEEL.NS","TATASTEEL.NS","HINDALCO.NS","DRREDDY.NS","CIPLA.NS",
  "DIVISLAB.NS","EICHERMOT.NS","HEROMOTOCO.NS","BRITANNIA.NS","NESTLEIND.NS",
  "APOLLOHOSP.NS","INDUSINDBK.NS","TATACONSUM.NS","BPCL.NS","GRASIM.NS",
  "SBILIFE.NS","HDFCLIFE.NS","ADANIPORTS.NS","M&M.NS","TATAMOTORS.NS",
  "TECHM.NS","LTIM.NS","BAJAJ-AUTO.NS","SHRIRAMFIN.NS","TRENT.NS",
];

const DISPLAY_NAMES = {
  "RELIANCE.NS":"RELIANCE","TCS.NS":"TCS","HDFCBANK.NS":"HDFCBANK",
  "BHARTIARTL.NS":"BHARTIARTL","ICICIBANK.NS":"ICICIBANK","INFOSYS.NS":"INFY",
  "SBIN.NS":"SBIN","HINDUNILVR.NS":"HINDUNILVR","ITC.NS":"ITC","LT.NS":"L&T",
  "KOTAKBANK.NS":"KOTAKBANK","AXISBANK.NS":"AXISBANK","MARUTI.NS":"MARUTI",
  "SUNPHARMA.NS":"SUNPHARMA","ULTRACEMCO.NS":"ULTRACEMCO","TITAN.NS":"TITAN",
  "BAJFINANCE.NS":"BAJFINANCE","WIPRO.NS":"WIPRO","HCLTECH.NS":"HCLTECH",
  "ADANIENT.NS":"ADANIENT","ONGC.NS":"ONGC","NTPC.NS":"NTPC",
  "POWERGRID.NS":"POWERGRID","COALINDIA.NS":"COALINDIA","BAJAJFINSV.NS":"BAJAJFINSV",
  "JSWSTEEL.NS":"JSWSTEEL","TATASTEEL.NS":"TATASTEEL","HINDALCO.NS":"HINDALCO",
  "DRREDDY.NS":"DRREDDY","CIPLA.NS":"CIPLA","DIVISLAB.NS":"DIVISLAB",
  "EICHERMOT.NS":"EICHERMOT","HEROMOTOCO.NS":"HEROMOTOCO","BRITANNIA.NS":"BRITANNIA",
  "NESTLEIND.NS":"NESTLEIND","APOLLOHOSP.NS":"APOLLOHOSP","INDUSINDBK.NS":"INDUSINDBK",
  "TATACONSUM.NS":"TATACONSUM","BPCL.NS":"BPCL","GRASIM.NS":"GRASIM",
  "SBILIFE.NS":"SBILIFE","HDFCLIFE.NS":"HDFCLIFE","ADANIPORTS.NS":"ADANIPORTS",
  "M&M.NS":"M&M","TATAMOTORS.NS":"TATAMOTORS","TECHM.NS":"TECHM",
  "LTIM.NS":"LTIM","BAJAJ-AUTO.NS":"BAJAJ-AUTO","SHRIRAMFIN.NS":"SHRIRAMFIN","TRENT.NS":"TRENT",
};

async function fetchBatch(syms) {
  const results = {};
  await Promise.all(
    syms.map(async (sym) => {
      try {
        const url   = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?interval=1d&range=2d`;
        const proxy = `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`;
        const res   = await fetch(proxy);
        const outer = await res.json();
        const meta  = JSON.parse(outer.contents).chart.result[0].meta;
        const price = meta.regularMarketPrice;
        const prev  = meta.chartPreviousClose ?? meta.previousClose;
        const chg   = price - prev;
        const pct   = (chg / prev) * 100;
        results[sym] = { price, chg, pct };
      } catch {
        results[sym] = null;
      }
    })
  );
  return results;
}

export default function TickerBar({ onSymbolClick }) {
  const [tickers, setTickers] = useState(
    NIFTY50_STOCKS.map((s) => ({ sym: s, name: DISPLAY_NAMES[s] || s.replace(".NS",""), price: null, chg: null, pct: null }))
  );
  const trackRef   = useRef(null);
  const animRef    = useRef(null);
  const offsetRef  = useRef(0);
  const pausedRef  = useRef(false);

  /* fetch in small batches to avoid proxy rate-limiting */
  useEffect(() => {
    let alive = true;
    async function load() {
      const BATCH = 10;
      for (let i = 0; i < NIFTY50_STOCKS.length; i += BATCH) {
        const slice   = NIFTY50_STOCKS.slice(i, i + BATCH);
        const results = await fetchBatch(slice);
        if (!alive) return;
        setTickers((prev) =>
          prev.map((t) =>
            results[t.sym] ? { ...t, ...results[t.sym] } : t
          )
        );
      }
    }
    load();
    const id = setInterval(load, 60_000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  /* smooth CSS animation scroll */
  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    let pos = 0;
    const speed = 0.5; // px per frame
    const step = () => {
      if (!pausedRef.current) {
        pos += speed;
        const half = el.scrollWidth / 2;
        if (pos >= half) pos = 0;
        el.style.transform = `translateX(-${pos}px)`;
      }
      animRef.current = requestAnimationFrame(step);
    };
    animRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animRef.current);
  }, []);

  const items = [...tickers, ...tickers]; // duplicate for seamless loop

  return (
    <div
      className="w-full overflow-hidden bg-[#0f172a] border-b border-slate-700/60 select-none"
      style={{ height: "36px" }}
      onMouseEnter={() => (pausedRef.current = true)}
      onMouseLeave={() => (pausedRef.current = false)}
    >
      <div ref={trackRef} className="flex items-center h-full whitespace-nowrap will-change-transform">
        {items.map((t, i) => {
          const up      = t.chg !== null && t.chg >= 0;
          const hasData = t.price !== null;
          return (
            <button
              key={`${t.sym}-${i}`}
              onClick={() => onSymbolClick && onSymbolClick(t.sym.replace(".NS", ""))}
              className="inline-flex items-center gap-2 px-4 h-full hover:bg-white/5 transition-colors duration-150 border-r border-slate-700/40"
            >
              <span className="text-[11px] font-bold text-slate-300 tracking-wide">{t.name}</span>
              {hasData ? (
                <>
                  <span className="text-[11px] font-semibold text-white tabular-nums">
                    {t.price.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                  </span>
                  <span className={`flex items-center gap-0.5 text-[10px] font-bold ${up ? "text-emerald-400" : "text-red-400"}`}>
                    {up ? <TrendingUp size={9} strokeWidth={2.5}/> : <TrendingDown size={9} strokeWidth={2.5}/>}
                    {(up ? "+" : "")}{t.pct.toFixed(2)}%
                  </span>
                </>
              ) : (
                <span className="text-[10px] text-slate-600">—</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}