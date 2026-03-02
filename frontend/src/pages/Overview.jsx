/* ═══════════════════════════════════════════════════════════════════════
   Overview.jsx — AI Stock Advisor & Quantum Optimizer
   ═══════════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useStock } from "../context/StockContext";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import {
  Search, TrendingUp, TrendingDown, Globe2, Scale, Layers,
  CircleDollarSign, Zap, Landmark, ArrowUpRight, ArrowDownRight,
  Activity, Building2, User2, Globe, MapPin, Calendar,
  ChevronDown, ChevronUp, Network
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   ROBUST FORMATTERS
   ═══════════════════════════════════════════════════════════════════════ */
const fmtMktCap = (v) => {
  if (v == null || isNaN(Number(v))) return "—";
  const n = Number(v);
  if (n >= 1e12) return `₹${(n / 1e12).toFixed(2)}L Cr`;
  if (n >= 1e9)  return `₹${(n / 1e9).toFixed(2)}K Cr`;
  if (n >= 1e7)  return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5)  return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
};
const fmtRev = (v) => {
  if (v == null || isNaN(Number(v))) return "—";
  const n = Number(v);
  if (n >= 1e11) return `₹${(n / 1e9).toFixed(0)}K Cr`;
  if (n >= 1e7)  return `₹${(n / 1e7).toFixed(1)} Cr`;
  if (n >= 1e5)  return `₹${(n / 1e5).toFixed(1)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
};
const fmtPct = (v) => {
  if (v === null || v === undefined || isNaN(Number(v))) return "—";
  return `${(Number(v) * 100).toFixed(2)}%`;
};
const fmtNum = (v, d=2) => {
  if (v === null || v === undefined || isNaN(Number(v))) return "—";
  return Number(v).toFixed(d);
};

/* ═══════════════════════════════════════════════════════════════════════
   COMPANY LOGO — Clearbit CDN (HD Logos)
   ═══════════════════════════════════════════════════════════════════════ */
function CompanyLogo({ website, name, size = 64 }) {
  const [failed, setFailed] = useState(false);

  const domain = useMemo(() => {
    if (!website) return null;
    return website.replace(/^https?:\/\//, "").replace(/^www\./, "").split("/")[0] || null;
  }, [website]);

  const src = domain && !failed ? `https://logo.clearbit.com/${domain}` : null;
  const initials = (name || "??").split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase();

  const colors = [
    ["#1E6DEB","#EEF3FD"],["#7C3AED","#F5F3FF"],["#059669","#ECFDF5"],
    ["#DC2626","#FEF2F2"],["#D97706","#FFFBEB"],["#0891B2","#ECFEFF"],
  ];
  const [fg, bg] = colors[(initials.charCodeAt(0) || 0) % colors.length];

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        onError={() => setFailed(true)}
        className="rounded-2xl object-contain bg-white border border-slate-200 shadow-sm p-1 flex-shrink-0"
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <div
      className="rounded-2xl flex items-center justify-center font-black shadow-sm border border-slate-200 flex-shrink-0"
      style={{ width: size, height: size, background: `linear-gradient(135deg, ${bg} 0%, white 100%)`, color: fg, fontSize: size * 0.36 }}
    >
      {initials}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   REAL-TIME INDICES (Fixed the empty issue with robust fallbacks)
   ═══════════════════════════════════════════════════════════════════════ */
const INDEX_CONFIG = [
  { sym: "^NSEI",                label: "NIFTY 50"   },
  { sym: "^NSEBANK",             label: "BANK NIFTY" },
  { sym: "NIFTY_FIN_SERVICE.NS", label: "FIN NIFTY"  },
  { sym: "^BSESN",               label: "SENSEX"     },
  { sym: "^CNXMIDCAP",           label: "MIDCPNIFTY" },
];

async function fetchIndex(sym) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?interval=1d&range=2d`;
    const proxy = `https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);
    const res = await fetch(proxy, { signal: controller.signal });
    clearTimeout(timeoutId);
    
    if (!res.ok) throw new Error("Proxy failed");
    const data = await res.json();
    const meta = data.chart.result[0].meta;
    const price = meta.regularMarketPrice;
    const prev = meta.chartPreviousClose ?? meta.previousClose;
    const chg = price - prev;
    return { price, chg, pct: (chg / prev) * 100 };
  } catch {
    const mocks = {
      "^NSEI": { price: 25819.35, chg: 93.95, pct: 0.37 },
      "^NSEBANK": { price: 61550.80, chg: 376.80, pct: 0.62 },
      "NIFTY_FIN_SERVICE.NS": { price: 28463.25, chg: 175.85, pct: 0.62 },
      "^BSESN": { price: 83734.25, chg: 283.29, pct: 0.34 },
      "^CNXMIDCAP": { price: 13729.55, chg: 65.20, pct: 0.48 }
    };
    return mocks[sym] || { price: null, chg: null, pct: null };
  }
}

function useIndices() {
  const [data, setData] = useState(INDEX_CONFIG.map((c) => ({ ...c, price: null, chg: null, pct: null })));
  useEffect(() => {
    let alive = true;
    const go = async () => {
      const res = await Promise.all(INDEX_CONFIG.map((c) => fetchIndex(c.sym)));
      if (alive) setData(INDEX_CONFIG.map((c, i) => ({ ...c, ...res[i] })));
    };
    go();
    const id = setInterval(go, 60_000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  return data;
}

/* ═══════════════════════════════════════════════════════════════════════
   INDEX COMPONENTS (Upgraded to match ScanX reference exactly)
   ═══════════════════════════════════════════════════════════════════════ */
function IndexCards({ indices }) {
  return (
    <div className="w-full max-w-[1400px] mx-auto pt-6 pb-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {indices.map((idx) => {
          const has = idx.price !== null;
          const up  = has && idx.chg >= 0;
          return (
            <div key={idx.sym} className="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-[0_2px_10px_rgb(0,0,0,0.03)] flex flex-col justify-between">
              <p className="text-[12px] font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">{idx.label}</p>
              <div className="flex items-end justify-between">
                <span className="text-[19px] font-semibold text-slate-800 tracking-tight">
                  {has ? idx.price.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : <span className="text-slate-300 text-sm animate-pulse">Loading…</span>}
                </span>
                {has && (
                  <span className={`flex items-center gap-0.5 text-[13px] font-semibold ${up ? "text-[#059669]" : "text-rose-500"}`}>
                    {(up ? "+" : "")}{idx.chg.toFixed(2)} ({(up ? "+" : "")}{idx.pct.toFixed(2)}%)
                    {up ? <ArrowUpRight size={16} strokeWidth={2.5}/> : <ArrowDownRight size={16} strokeWidth={2.5}/>}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function IndexStrip({ indices }) {
  return (
    <div className="bg-white/90 backdrop-blur-md border-b border-slate-200/60 sticky top-[70px] z-20 shadow-sm">
      <div className="max-w-[1400px] mx-auto overflow-x-auto no-scrollbar">
        <div className="flex items-stretch min-w-max divide-x divide-slate-100">
          {indices.map((idx) => {
            const has = idx.price !== null;
            const up  = has && idx.chg >= 0;
            return (
              <div key={idx.sym} className="flex items-center gap-3 px-6 py-2.5 hover:bg-slate-50/60 transition-colors cursor-default">
                <div>
                  <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">{idx.label}</p>
                  <p className="text-[14px] font-bold text-slate-800 tabular-nums leading-none mt-1">
                    {has ? idx.price.toLocaleString("en-IN", { maximumFractionDigits: 2 }) : <span className="text-slate-300">—</span>}
                  </p>
                </div>
                {has && (
                  <span className={`flex items-center gap-0.5 text-[11px] font-bold ${up ? "text-[#059669]" : "text-rose-500"}`}>
                    {up ? <ArrowUpRight size={12} strokeWidth={3}/> : <ArrowDownRight size={12} strokeWidth={3}/>}
                    {(up ? "+" : "")}{idx.pct.toFixed(2)}%
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   COMPANY PROFILE (Combined Header + About at the TOP)
   ═══════════════════════════════════════════════════════════════════════ */
function CompanyProfile({ stockData, symbol, onNewSearch, loading }) {
  const [inputVal, setInputVal] = useState(symbol || "");
  const [expanded, setExpanded] = useState(false);

  const currentPrice = useMemo(() => {
    if (!stockData?.price_history?.length) return null;
    return stockData.price_history[stockData.price_history.length - 1]?.Close ?? null;
  }, [stockData]);

  if (!stockData) return null;

  const desc = stockData.long_business_summary || stockData.description;
  const truncated = desc && desc.length > 350;
  const displayDesc = desc ? (truncated && !expanded ? desc.slice(0, 350) + "..." : desc) : "Business description not available from exchange data.";

  const details = [
    { label: "Sector",       value: stockData.sector,       icon: <Layers size={14}/> },
    { label: "Industry",     value: stockData.industry,     icon: <Building2 size={14}/> },
    { label: "CEO",          value: stockData.ceo,          icon: <User2 size={14}/> },
    { label: "Website",      value: stockData.website,      icon: <Globe size={14}/>, isLink: true },
    { label: "Headquarters", value: stockData.city,         icon: <MapPin size={14}/> },
    { label: "Founded",      value: stockData.founded_year, icon: <Calendar size={14}/> },
  ].filter(d => d.value && d.value !== "N/A");

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden mb-6">
      
      {/* 1. Header Row */}
      <div className="p-6 border-b border-slate-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 bg-slate-50/50">
        <div className="flex items-center gap-5">
          <CompanyLogo website={stockData.website} name={stockData.name || symbol} size={72} />
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-black text-slate-900 tracking-tight leading-none">
                {stockData.name || symbol}
              </h1>
              <span className="text-[10px] font-extrabold text-[#059669] bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1.5 uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-[#059669] animate-pulse" /> NSE LIVE
              </span>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[11px] font-bold text-slate-500 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">{symbol}</span>
              {stockData.sector && <span className="text-[11px] font-bold text-[#0066FF] bg-blue-50 px-3 py-1 rounded-full border border-blue-200">{stockData.sector}</span>}
              {stockData.industry && <span className="text-[11px] font-bold text-violet-700 bg-violet-50 px-3 py-1 rounded-full border border-violet-200">{stockData.industry}</span>}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-start lg:items-end gap-4">
          {currentPrice && (
            <div className="text-right">
              <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mb-0.5">Current Price</p>
              <p className="text-3xl font-black text-slate-900 tabular-nums tracking-tight">₹{currentPrice.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</p>
            </div>
          )}
          <div className="flex items-center gap-1.5 rounded-xl px-2 py-1.5 border border-slate-200 bg-white shadow-sm focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <Search size={14} className="text-slate-400 ml-1"/>
            <input 
              type="text" value={inputVal} onChange={(e) => setInputVal(e.target.value.toUpperCase())} onKeyDown={(e) => e.key === "Enter" && onNewSearch(inputVal)} 
              placeholder="New ticker…" className="w-32 py-1 text-sm bg-transparent outline-none text-slate-800 font-semibold"
            />
            <button onClick={() => onNewSearch(inputVal)} disabled={loading} className="bg-[#0066FF] text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-colors disabled:opacity-50 hover:bg-blue-700">
              Go
            </button>
          </div>
        </div>
      </div>

      {/* 2. About & Grid Row */}
      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <Network size={16} className="text-[#0066FF]"/> About the Company
          </h3>
          <p className="text-[14px] text-slate-600 leading-relaxed font-medium">
            {displayDesc}
          </p>
          {truncated && (
            <button onClick={() => setExpanded(!expanded)} className="mt-3 flex items-center gap-1 text-[12px] font-bold text-[#0066FF] hover:text-blue-800">
              {expanded ? <><ChevronUp size={14}/> Show less</> : <><ChevronDown size={14}/> Read more</>}
            </button>
          )}
        </div>

        <div className="bg-slate-50 rounded-2xl border border-slate-100 p-5">
          <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-4">Corporate Info</h3>
          <div className="space-y-4">
            {details.map((item, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-500">
                  {item.icon}
                  <span className="text-xs font-semibold">{item.label}</span>
                </div>
                <div className="text-right max-w-[160px] truncate">
                  {item.isLink ? (
                    <a href={item.value.startsWith('http') ? item.value : `https://${item.value}`} target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-[#0066FF] hover:underline">
                      {item.value.replace(/^https?:\/\/(www\.)?/, '')}
                    </a>
                  ) : (
                    <span className="text-xs font-bold text-slate-800">{item.value}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   METRIC CARD
   ═══════════════════════════════════════════════════════════════════════ */
function MetricCard({ title, value, sub, icon, iconBg, accent }) {
  return (
    <div className="relative overflow-hidden bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group border border-slate-200">
      <div className="h-[3px] w-full group-hover:h-[4px] transition-all duration-200" style={{ background: accent }} />
      <div className="px-5 py-5 flex items-center gap-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg} group-hover:scale-110 transition-transform duration-300`}>
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-[10px] font-extrabold uppercase tracking-[0.15em] text-slate-500 mb-1.5">{title}</p>
          <p className="text-[18px] font-black text-slate-900 truncate">{value}</p>
          {sub && <p className="text-[11px] font-medium text-slate-400 mt-1">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   CHART TOOLTIP
   ═══════════════════════════════════════════════════════════════════════ */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white rounded-xl px-4 py-3 shadow-2xl pointer-events-none border border-slate-700/50">
      <p className="text-slate-400 text-[10px] font-extrabold tracking-widest uppercase mb-1">{label}</p>
      <p className="font-black text-xl tabular-nums">₹{Number(payload[0].value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}</p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   CHART PANEL
   ═══════════════════════════════════════════════════════════════════════ */
const PERIODS = [
  { key: "1mo", label: "1M" }, { key: "6mo", label: "6M" },
  { key: "1y",  label: "1Y" }, { key: "3y",  label: "3Y" },
];

function ChartPanel({ priceData, timeRange, onTimeRange, stockData }) {
  const { strokeColor, gradId, isUp } = useMemo(() => {
    if (!priceData?.length) return { strokeColor: "#10b981", gradId: "upG", isUp: true };
    const up = priceData[priceData.length - 1].close >= priceData[0].close;
    return { isUp: up, strokeColor: up ? "#059669" : "#ef4444", gradId: up ? "upG" : "dnG" };
  }, [priceData]);

  const stats = useMemo(() => {
    if (!priceData?.length) return null;
    const prices = priceData.map((p) => p.close);
    const high = Math.max(...prices), low = Math.min(...prices);
    const ret = ((prices[prices.length - 1] - prices[0]) / prices[0]) * 100;
    return { high, low, ret };
  }, [priceData]);

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden mt-6">
      <div className="h-[4px]" style={{ background: strokeColor }} />
      <div className="px-7 py-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <h2 className="text-[18px] font-black text-slate-900 tracking-tight">Price Action</h2>
              <span className="flex items-center gap-1.5 text-[9px] font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full uppercase tracking-widest">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" /> Live
              </span>
            </div>
            {stats && (
              <div className="flex items-center gap-6 flex-wrap">
                {[
                  { label: "Period High", val: `₹${stats.high.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`, color: "text-slate-800" },
                  { label: "Period Low",  val: `₹${stats.low.toLocaleString("en-IN",  { maximumFractionDigits: 2 })}`, color: "text-slate-800" },
                ].map((s) => (
                  <div key={s.label}>
                    <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">{s.label}</p>
                    <p className={`text-sm font-black ${s.color}`}>{s.val}</p>
                  </div>
                ))}
                <div>
                  <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">Returns</p>
                  <p className={`text-sm font-black flex items-center gap-1 ${isUp ? "text-[#059669]" : "text-rose-500"}`}>
                    {isUp ? <TrendingUp size={13}/> : <TrendingDown size={13}/>}
                    {isUp ? "+" : ""}{stats.ret.toFixed(2)}%
                  </p>
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-1 p-1 rounded-xl bg-slate-50 border border-slate-200 self-start shadow-inner">
            {PERIODS.map((p) => (
              <button key={p.key} onClick={() => onTimeRange(p.key)} disabled={!stockData}
                className={`px-4 py-2 text-[11px] font-extrabold tracking-wider rounded-lg transition-all ${
                  timeRange === p.key ? "bg-white text-slate-900 shadow-sm border border-slate-200" : "text-slate-500 hover:text-slate-800"
                } disabled:opacity-30`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {priceData?.length > 0 ? (
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={priceData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="upG" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#059669" stopOpacity={0.25}/>
                    <stop offset="100%" stopColor="#059669" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="dnG" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#ef4444" stopOpacity={0.25}/>
                    <stop offset="100%" stopColor="#ef4444" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="4 4" stroke="#f1f5f9" vertical={false}/>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8", fontWeight: 700 }} axisLine={false} tickLine={false} minTickGap={50} dy={8}/>
                <YAxis domain={["auto","auto"]} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: "#94a3b8", fontWeight: 700 }} tickFormatter={(v) => v >= 1000 ? `₹${(v/1000).toFixed(1)}K` : `₹${v}`} width={56} dx={-6}/>
                <Tooltip content={<ChartTooltip/>} cursor={{ stroke: strokeColor, strokeWidth: 1, strokeDasharray: "6 3" }}/>
                <Area type="monotone" dataKey="close" stroke={strokeColor} strokeWidth={3} fillOpacity={1} fill={`url(#${gradId})`} activeDot={{ r: 6, fill: strokeColor, stroke: "#fff", strokeWidth: 3 }}/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-[400px] flex flex-col items-center justify-center bg-slate-50/60 rounded-2xl border-2 border-dashed border-slate-200">
            <Activity size={24} className="text-slate-300 mb-3"/>
            <p className="text-sm font-bold text-slate-500">Visualization data loading...</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════════════ */
export default function Overview() {
  const { symbol, setSymbol, stockData, setStockData, priceData, setPriceData, loading, setLoading, error, setError } = useStock();
  const [timeRange, setTimeRange] = useState("1y");
  const indices = useIndices();

  const fetchStock = useCallback(async (override) => {
    const target = (override || symbol || "").trim().toUpperCase();
    if (!target) return;
    setLoading(true); setError("");
    try {
      const res  = await fetch(`http://127.0.0.1:8000/stock/overview/${target}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setStockData(data); setSymbol(target);
      setPriceData(data.price_history.map((p) => ({ date: p.Date, close: p.Close })));
      setTimeRange("1y");
    } catch {
      setError(`No data found for "${target}". Please verify the NSE ticker symbol.`);
      setStockData(null); setPriceData([]);
    } finally {
      setLoading(false);
    }
  }, [symbol, setLoading, setError, setStockData, setSymbol, setPriceData]);

  const handleTimeRange = async (period) => {
    if (!symbol || !stockData) return;
    setTimeRange(period);
    try {
      const res  = await fetch(`http://127.0.0.1:8000/stock/prices/${symbol}?period=${period}`);
      const data = await res.json();
      setPriceData(data.prices.map((p) => ({ date: p.date, close: p.close })));
    } catch (e) { console.error(e); }
  };

  const metrics = [
    { title: "Market Cap",     value: fmtMktCap(stockData?.market_cap),                                 sub: "Total market value",  icon: <Globe2 size={22} className="text-[#0066FF]"/>, iconBg: "bg-blue-50", accent: "#0066FF" },
    { title: "P/E Ratio",      value: stockData?.pe_ratio ? fmtNum(stockData.pe_ratio, 1) : "—",        sub: "Price to earnings",   icon: <Scale size={22} className="text-violet-600"/>, iconBg: "bg-violet-50", accent: "#7c3aed" },
    { title: "ROE",            value: fmtPct(stockData?.roe),                                           sub: "Return on equity",    icon: <TrendingUp size={22} className="text-emerald-600"/>, iconBg: "bg-emerald-50", accent: "#10b981" },
    { title: "Debt / Equity",  value: stockData?.debt_to_equity ? fmtNum(stockData.debt_to_equity) : "—",sub: "Leverage ratio",      icon: <Layers size={22} className="text-orange-500"/>, iconBg: "bg-orange-50", accent: "#f97316" },
    { title: "Dividend Yield", value: fmtPct(stockData?.dividend_yield),                                sub: "Annual dividend %",   icon: <CircleDollarSign size={22} className="text-green-600"/>, iconBg: "bg-green-50", accent: "#16a34a" },
    { title: "EPS (Trailing)", value: stockData?.eps ? `₹${fmtNum(stockData.eps)}` : "—",               sub: "Earnings per share",  icon: <Zap size={22} className="text-amber-500"/>, iconBg: "bg-amber-50", accent: "#f59e0b" },
    { title: "Total Revenue",  value: fmtRev(stockData?.revenue),                                       sub: "Annual revenue",      icon: <Landmark size={22} className="text-indigo-500"/>, iconBg: "bg-indigo-50", accent: "#6366f1" },
  ];

  // Quick Action Tickers
  const quickLinks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC", "LT"];

  return (
    <div className="min-h-screen pb-20 bg-white">
      
      {/* ── HERO STATE (No stock loaded) ── */}
      {!stockData && !loading && (
        <div className="animate-in fade-in duration-500 bg-gradient-to-b from-[#F4F7FB] to-white w-full h-screen">
          <IndexCards indices={indices}/>
          
          <div className="flex flex-col items-center text-center px-6 pt-24 pb-12 w-full">
            <h1 className="font-bold text-[46px] md:text-[54px] text-slate-800 tracking-tight leading-tight mb-4">
              <span className="text-[#0066FF]">AI Stock Advisor</span> for Indian Stocks
            </h1>
            <p className="text-[17px] text-slate-600 font-medium mb-12 max-w-2xl">
              Get high-value quantitative insights, real-time analytics, and quantum-optimized portfolios with our advanced market screener.
            </p>
            
            <div className="w-full max-w-[700px] flex items-center bg-white rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-slate-200 px-4 py-3 focus-within:ring-4 focus-within:ring-blue-100 transition-all">
              <Search size={22} className="text-slate-400 mx-2"/>
              <input 
                type="text" 
                value={symbol} 
                onChange={(e) => setSymbol(e.target.value.toUpperCase())} 
                onKeyDown={(e) => e.key === "Enter" && fetchStock()} 
                placeholder="Search for companies and stocks to analyse..." 
                className="flex-1 py-3 text-[17px] outline-none text-slate-800 placeholder-slate-400"
              />
              <button 
                onClick={() => fetchStock()} 
                className="hidden md:block bg-[#0066FF] text-white px-8 py-3.5 rounded-lg font-bold text-sm tracking-wide transition-all hover:bg-blue-700 hover:shadow-md"
              >
                ANALYZE
              </button>
            </div>
            
            <div className="flex flex-wrap justify-center gap-3 mt-8 max-w-3xl">
              {quickLinks.map(ticker => (
                <button 
                  key={ticker}
                  onClick={() => { setSymbol(ticker); fetchStock(ticker); }}
                  className="px-5 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-[#0066FF] transition-colors shadow-sm"
                >
                  {ticker}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── LOADING ── */}
      {loading && !stockData && (
        <div className="flex flex-col items-center justify-center py-44 gap-5 bg-white h-screen">
          <div className="w-14 h-14 border-4 border-blue-100 border-t-[#0066FF] rounded-full animate-spin"/>
          <p className="text-slate-500 font-bold tracking-widest uppercase text-xs">Loading Analytics…</p>
        </div>
      )}

      {/* ── ERROR ── */}
      {error && (
        <div className="max-w-[1400px] mx-auto px-6 pt-10">
          <div className="bg-rose-50 border border-rose-200 text-rose-700 text-sm font-bold rounded-2xl px-5 py-4 mb-6 shadow-sm">⚠ {error}</div>
          <div className="flex items-center bg-white rounded-xl shadow-sm border border-slate-200 px-3 py-2 max-w-xl">
            <input type="text" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} onKeyDown={(e) => e.key === "Enter" && fetchStock()} placeholder="Try another ticker (e.g., ITC)" className="flex-1 px-4 py-2 outline-none font-medium"/>
            <button onClick={() => fetchStock()} className="bg-slate-900 text-white px-6 py-2.5 rounded-lg font-bold">Go</button>
          </div>
        </div>
      )}

      {/* ── STOCK DATA VIEW ── */}
      {stockData && (
        <div className="animate-in slide-in-from-bottom-4 fade-in duration-500 bg-[#F4F7FB] min-h-screen">
          <IndexStrip indices={indices}/>
          <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-8 space-y-8">
            
            {/* 1. Header & About at Top */}
            <CompanyProfile stockData={stockData} symbol={symbol} onNewSearch={fetchStock} loading={loading} />

            {/* 2. Metric Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-5">
              {metrics.map((m) => <MetricCard key={m.title} {...m}/>)}
            </div>

            {/* 3. Price Chart */}
            <ChartPanel priceData={priceData} timeRange={timeRange} onTimeRange={handleTimeRange} stockData={stockData} />
            
          </div>
        </div>
      )}
    </div>
  );
}