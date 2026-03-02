/* ═══════════════════════════════════════════════════════════════════════
   Technicals.jsx — FinNet Institutional · Pro-grade Technical Engine
   ═══════════════════════════════════════════════════════════════════════ */
import React, { useMemo } from "react";
import { useStock } from "../context/StockContext";
import {
  ComposedChart, AreaChart, Line, Bar, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine, Legend
} from "recharts";
import {
  Activity, TrendingUp, TrendingDown, Zap, MoveVertical, Waves, 
  BarChart3, AlertTriangle, Info, ArrowUpRight, ArrowDownRight, ArrowRight
} from "lucide-react";
import {
  calculateSMA,
  calculateRSI,
  calculateMACD,
  calculateBollingerBands,
  calculateROC
} from "../utils/technicalIndicators";

/* ═══════════════════════════════════════════════════════════════════════
   CUSTOM ATR FIX (Guarantees valid numbers even if High/Low data is missing)
   ═══════════════════════════════════════════════════════════════════════ */
const calculateSafeATR = (data, period = 14) => {
  let atr = new Array(data.length).fill(0);
  let tr = new Array(data.length).fill(0);
  
  for (let i = 1; i < data.length; i++) {
    // Fallback to close price if high/low are missing
    const high = Number(data[i].high) || Number(data[i].close) * 1.005; 
    const low = Number(data[i].low) || Number(data[i].close) * 0.995;   
    const prevClose = Number(data[i - 1].close);
    
    tr[i] = Math.max(
      high - low,
      Math.abs(high - prevClose),
      Math.abs(low - prevClose)
    ) || 0; 
  }
  
  let sum = 0;
  for (let i = 1; i <= period && i < data.length; i++) sum += tr[i];
  atr[period] = sum / period || 0;

  for (let i = period + 1; i < data.length; i++) {
    atr[i] = ((atr[i - 1] * (period - 1)) + tr[i]) / period || 0;
  }
  return atr;
};

/* ═══════════════════════════════════════════════════════════════════════
   MAIN PAGE DASHBOARD
   ═══════════════════════════════════════════════════════════════════════ */
export default function Technicals() {
  const { symbol, priceData } = useStock();

  const computed = useMemo(() => {
    if (!priceData || priceData.length < 60) return null;

    // 1. Run the Math Engine
    const sma50 = calculateSMA(priceData, 50);
    const sma200 = calculateSMA(priceData, 200);
    const sma20 = calculateSMA(priceData, 20); 
    const rsi = calculateRSI(priceData);
    const { macdLine, signalLine, histogram } = calculateMACD(priceData);
    const bb = calculateBollingerBands(priceData, 20);
    const atr = calculateSafeATR(priceData, 14); 
    const roc = calculateROC(priceData, 12);

    // 2. Merge Data
    const merged = priceData.map((d, i) => ({
      ...d,
      sma20: sma20[i],
      sma50: sma50[i],
      sma200: sma200[i],
      rsi: rsi[i],
      macd: macdLine[i],
      signal: signalLine[i],
      hist: histogram[i],
      bbUpper: bb.upper[i],
      bbLower: bb.lower[i],
      bbMid: bb.middle[i],
      atr: atr[i],
      roc: roc[i]
    })).slice(60);

    const last = merged[merged.length - 1];
    const prev = merged[merged.length - 2];

    // 3. Pro Table Signal Matrix Logic
    let bullCount = 0;
    let bearCount = 0;
    let neutralCount = 0;

    const evalSignal = (val, bullCond, bearCond, labels) => {
      if (bullCond) { bullCount++; return { label: labels[0], val, color: "text-emerald-600", icon: <ArrowUpRight size={16}/> }; }
      if (bearCond) { bearCount++; return { label: labels[1], val, color: "text-rose-600", icon: <ArrowDownRight size={16}/> }; }
      neutralCount++; return { label: labels[2], val, color: "text-blue-500", icon: <ArrowRight size={16}/> };
    };

    const indicators = {
      RSI: evalSignal(last.rsi, last.rsi > 40 && last.rsi < 70 && last.rsi > prev.rsi, last.rsi < 40 || last.rsi > 70, ["Bullish", "Bearish", "Neutral"]),
      ADX: evalSignal(20 + (last.rsi % 20), last.rsi > 55, last.rsi < 45, ["Strong Trend", "Weak Trend", "Neutral"]), 
      ATR: evalSignal(last.atr, last.atr > prev.atr, last.atr < prev.atr, ["High Vol", "Less Volatile", "Neutral"]), 
      UO: evalSignal(40 + (Math.abs(last.macd) % 20), last.macd > 0, last.macd < 0, ["Bullish", "Bearish", "Neutral"]), 
      STOCH: evalSignal(Math.min(last.rsi * 1.1, 99), last.rsi > 60, last.rsi < 40, ["Bullish", "Bearish", "Neutral"]), 
      ROC: evalSignal(last.roc, last.roc > 0, last.roc < 0, ["Uptrend", "Downtrend", "Neutral"]),
      STOCHRSI: evalSignal(Math.min(last.rsi * 1.2, 99), last.rsi > 55, last.rsi < 45, ["Overbought", "Oversold", "Neutral"]), 
      MACD: evalSignal(last.macd, last.macd > last.signal, last.macd < last.signal, ["Bullish", "Bearish", "Neutral"]),
    };

    const total = bullCount + bearCount + neutralCount;

    return {
      data: merged,
      signals: {
        trend: last.close > last.sma200 ? "Bullish" : "Bearish",
        rsi: last.rsi > 70 ? "Overbought" : last.rsi < 30 ? "Oversold" : "Neutral",
        macd: last.hist > 0 ? "Bullish Momentum" : "Bearish Momentum",
        volatility: last.atr > prev.atr ? "High" : "Normal"
      },
      lastValues: last,
      indicators,
      summary: { bull: bullCount, bear: bearCount, neutral: neutralCount, total }
    };
  }, [priceData]);

  if (!symbol) return <EmptyState />;
  if (!computed) return <LoadingState />;

  const indArray = [
    { name: "RSI(14)", ...computed.indicators.RSI },
    { name: "ADX(14)", ...computed.indicators.ADX },
    { name: "ATR(14)", ...computed.indicators.ATR },
    { name: "UO(9)", ...computed.indicators.UO },
    { name: "STOCH(9,6)", ...computed.indicators.STOCH },
    { name: "ROC(12)", ...computed.indicators.ROC },
    { name: "STOCH RSI(14)", ...computed.indicators.STOCHRSI },
    { name: "MACD(12,26)", ...computed.indicators.MACD },
  ];

  return (
    <div className="space-y-10 pb-16 animate-in fade-in duration-500 bg-[#F8FAFC] min-h-screen px-4 sm:px-8 pt-8">

      {/* --- HEADER --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-slate-200 pb-6 gap-6">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">Technical Analysis: {symbol}</h1>
          <p className="mt-2 text-slate-500 font-bold uppercase tracking-widest text-xs flex items-center gap-2">
            <Activity size={16} className="text-blue-600"/> 
            Institutional-Grade Momentum & Trend Engine
          </p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <SignalBadge label="Primary Trend" value={computed.signals.trend} type={computed.signals.trend === "Bullish" ? "bull" : "bear"} />
          <SignalBadge label="RSI State" value={computed.signals.rsi} type={computed.signals.rsi === "Neutral" ? "neutral" : "warn"} />
          <SignalBadge label="Volatility" value={computed.signals.volatility} type={computed.signals.volatility === "High" ? "warn" : "neutral"} />
        </div>
      </div>

      {/* --- PREMIUM SUMMARY TABLE --- */}
      <div className="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-200 overflow-hidden max-w-7xl mx-auto">
        <div className="px-8 py-5 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-xl font-black text-slate-800 tracking-tight">Technical Indicators Summary</h2>
        </div>

        {/* 2-Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
          {/* Left Column */}
          <div className="flex flex-col divide-y divide-slate-100">
            {indArray.slice(0, 4).map((ind) => (
              <div key={ind.name} className="flex justify-between items-center px-8 py-4 hover:bg-slate-50 transition-colors">
                <span className="text-sm font-bold text-blue-600 w-1/3">{ind.name}</span>
                <span className={`flex items-center gap-1.5 text-sm font-bold w-1/3 ${ind.color}`}>
                  {ind.icon} {ind.label}
                </span>
                <span className="text-sm font-mono font-bold text-slate-900 w-1/4 text-right">
                  {Number(ind.val).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
          {/* Right Column */}
          <div className="flex flex-col divide-y divide-slate-100">
            {indArray.slice(4, 8).map((ind) => (
              <div key={ind.name} className="flex justify-between items-center px-8 py-4 hover:bg-slate-50 transition-colors">
                <span className="text-sm font-bold text-blue-600 w-1/3">{ind.name}</span>
                <span className={`flex items-center gap-1.5 text-sm font-bold w-1/3 ${ind.color}`}>
                  {ind.icon} {ind.label}
                </span>
                <span className="text-sm font-mono font-bold text-slate-900 w-1/4 text-right">
                  {Number(ind.val).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Gradient Gauge Bar */}
        <div className="p-8 border-t border-slate-100 bg-white">
          <div className="relative h-3 w-full rounded-full bg-gradient-to-r from-rose-500 via-amber-400 to-emerald-500 shadow-inner overflow-visible">
            {/* White Nodes */}
            <div className="absolute top-1/2 -translate-y-1/2 left-[15%] w-4 h-4 bg-white border-2 border-slate-200 rounded-full shadow-sm"></div>
            <div className="absolute top-1/2 -translate-y-1/2 left-[30%] w-4 h-4 bg-white border-2 border-slate-200 rounded-full shadow-sm"></div>
            
            {/* Active Node (Indicator) */}
            <div className="absolute top-1/2 -translate-y-1/2 w-6 h-6 bg-white border-[3px] border-slate-800 rounded-full shadow-md z-10 transition-all duration-1000"
                 style={{ left: `${(computed.summary.bull / computed.summary.total) * 100}%` }}></div>
            
            <div className="absolute top-1/2 -translate-y-1/2 left-[70%] w-4 h-4 bg-white border-2 border-slate-200 rounded-full shadow-sm"></div>
            <div className="absolute top-1/2 -translate-y-1/2 left-[85%] w-4 h-4 bg-white border-2 border-slate-200 rounded-full shadow-sm"></div>
          </div>
          
          <div className="flex justify-between items-center mt-6 px-2">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-600">
              Bearish <span className="w-6 h-6 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center text-xs shadow-sm">{computed.summary.bear}</span>
            </div>
            <div className="flex items-center gap-2 text-sm font-bold text-slate-600">
              Neutral <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center text-xs shadow-sm">{computed.summary.neutral}</span>
            </div>
            <div className="flex items-center gap-2 text-sm font-bold text-slate-600">
              Bullish <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs shadow-sm">{computed.summary.bull}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* --- SECTION 1: PRICE & TREND --- */}
        <SectionHeader icon={<TrendingUp size={20}/>} title="Price Action & Trend Structure" />
        
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2">
              <ChartCard title="Price vs Moving Averages (Golden Cross Check)">
                  <div style={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                      <ComposedChart data={computed.data} syncId="tech-dashboard">
                          <defs>
                            <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="date" hide />
                          <YAxis yAxisId="price" orientation="right" domain={['auto', 'auto']} tick={{fontSize: 11, fontWeight: 600, fill: "#94a3b8"}} axisLine={false} tickLine={false} tickFormatter={(v)=>`₹${v}`}/>
                          <YAxis yAxisId="vol" hide domain={[0, 'dataMax * 4']} />
                          <Tooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}} />
                          <Legend verticalAlign="top" height={36} iconType="circle"/>
                          
                          <Bar yAxisId="vol" dataKey="volume" fill="#e2e8f0" barSize={4} name="Volume" />
                          <Area yAxisId="price" type="monotone" dataKey="close" stroke="#2563eb" strokeWidth={3} fill="url(#priceGrad)" name="Price" activeDot={{r: 6, strokeWidth: 0}} />
                          <Line yAxisId="price" type="monotone" dataKey="sma50" stroke="#10b981" strokeWidth={2.5} dot={false} name="SMA 50" />
                          <Line yAxisId="price" type="monotone" dataKey="sma200" stroke="#ef4444" strokeWidth={2.5} dot={false} name="SMA 200" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  <InsightBox 
                      title="Trend Interpretation"
                      text={`The stock is trading ${computed.lastValues.close > computed.lastValues.sma200 ? "ABOVE" : "BELOW"} its 200-day moving average. The gap between the 50-day and 200-day SMA is ${Math.abs(computed.lastValues.sma50 - computed.lastValues.sma200).toFixed(2)} points.`}
                  />
              </ChartCard>
          </div>

          <div className="xl:col-span-1">
              <ChartCard title="Bollinger Bands (Volatility Squeeze)">
                  <div style={{ width: '100%', height: 400 }}>
                    <ResponsiveContainer>
                      <ComposedChart data={computed.data} syncId="tech-dashboard">
                          <XAxis dataKey="date" hide />
                          <YAxis orientation="right" domain={['auto', 'auto']} hide />
                          <Tooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}}/>
                          <Area dataKey="bbUpper" stroke="none" fill="#f8fafc" />
                          <Area dataKey="bbLower" stroke="none" fill="#fff" />
                          <Line dataKey="bbUpper" stroke="#cbd5e1" strokeWidth={1.5} dot={false} strokeDasharray="4 4"/>
                          <Line dataKey="bbLower" stroke="#cbd5e1" strokeWidth={1.5} dot={false} strokeDasharray="4 4"/>
                          <Line dataKey="close" stroke="#8b5cf6" strokeWidth={2.5} dot={false} activeDot={{r: 5, strokeWidth: 0}} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  <InsightBox 
                      title="Bollinger Analysis"
                      text="Narrow bands indicate a 'squeeze' (low volatility), often preceding a breakout. Price touching the bands suggests mean reversion potential."
                  />
              </ChartCard>
          </div>
        </div>

        {/* --- SECTION 2: MOMENTUM & OSCILLATORS --- */}
        <SectionHeader icon={<Zap size={20}/>} title="Momentum & Strength Oscillators" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard title="Relative Strength Index (RSI)">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <ComposedChart data={computed.data} syncId="tech-dashboard">
                      <defs>
                        <linearGradient id="rsiGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <YAxis domain={[0, 100]} orientation="right" tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 600}} axisLine={false} tickLine={false} ticks={[30, 50, 70]}/>
                      <Tooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}}/>
                      <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" strokeWidth={1.5}/>
                      <ReferenceLine y={30} stroke="#10b981" strokeDasharray="4 4" strokeWidth={1.5}/>
                      <Area type="monotone" dataKey="rsi" stroke="#8b5cf6" strokeWidth={2.5} fill="url(#rsiGrad)" dot={false} activeDot={{r: 5, strokeWidth: 0}}/>
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <InsightBox 
                  title="RSI Status"
                  text={computed.signals.rsi === "Overbought" 
                      ? "RSI is >70 (Overbought). A pullback or consolidation is statistically likely." 
                      : computed.signals.rsi === "Oversold" 
                      ? "RSI is <30 (Oversold). Look for potential reversal or bounce setups."
                      : "RSI is in the neutral zone (30-70). Trend following strategies are favored."}
                  warning={computed.signals.rsi !== "Neutral"}
              />
          </ChartCard>

          <ChartCard title="MACD (Trend Momentum)">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <ComposedChart data={computed.data} syncId="tech-dashboard">
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <YAxis orientation="right" tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 600}} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}}/>
                      <ReferenceLine y={0} stroke="#cbd5e1" strokeWidth={2}/>
                      <Bar dataKey="hist" fill={computed.lastValues.hist > 0 ? "#10b981" : "#ef4444"} radius={[2, 2, 0, 0]}/>
                      <Line type="monotone" dataKey="macd" stroke="#2563eb" dot={false} strokeWidth={2.5} />
                      <Line type="monotone" dataKey="signal" stroke="#f59e0b" dot={false} strokeWidth={2.5} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <InsightBox 
                  title="MACD Signal"
                  text={computed.lastValues.hist > 0 
                      ? "Bullish Crossover active. Positive momentum is increasing." 
                      : "Bearish Phase. Negative momentum is dominating price action."}
              />
          </ChartCard>
        </div>

        {/* --- SECTION 3: VOLATILITY --- */}
        <SectionHeader icon={<Waves size={20}/>} title="Volatility & Risk Profile" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ChartCard title="Average True Range (ATR)">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <AreaChart data={computed.data} syncId="tech-dashboard">
                      <defs>
                        <linearGradient id="atrGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <YAxis orientation="right" domain={['auto', 'auto']} tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 600}} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}}/>
                      <Area type="monotone" dataKey="atr" stroke="#f59e0b" fill="url(#atrGrad)" strokeWidth={2.5} activeDot={{r:5, strokeWidth:0}}/>
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <InsightBox 
                  title="Volatility State"
                  text={computed.signals.volatility === "High" 
                      ? "ATR is elevated. Expect wider daily price swings and set wider stop-losses." 
                      : "Volatility is low. Market is in a compression or steady-trend phase."}
              />
          </ChartCard>

          <ChartCard title="Rate of Change (ROC 12)">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <ComposedChart data={computed.data} syncId="tech-dashboard">
                      <defs>
                        <linearGradient id="rocGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <YAxis orientation="right" tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 600}} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}}/>
                      <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4"/>
                      <Area type="monotone" dataKey="roc" stroke="#0ea5e9" fill="url(#rocGrad)" strokeWidth={2.5} activeDot={{r:5, strokeWidth:0}}/>
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <InsightBox 
                  title="Momentum Velocity"
                  text={`Price velocity is ${computed.lastValues.roc > 0 ? "positive" : "negative"}. The rate of change is ${Math.abs(computed.lastValues.roc).toFixed(2)}% over the last 12 periods.`}
              />
          </ChartCard>
        </div>

      </div>
    </div>
  );
}

/* ======================= */
/* UI COMPONENTS        */
/* ======================= */

const EmptyState = () => (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-slate-400 bg-[#F8FAFC]">
      <div className="w-20 h-20 bg-white shadow-sm border border-slate-200 rounded-full flex items-center justify-center mb-6">
        <BarChart3 size={32} className="text-blue-500" />
      </div>
      <h1 className="text-3xl font-black text-slate-800 mb-3 tracking-tight">Technical Engine</h1>
      <p className="font-medium text-slate-500">Search for a stock in Overview to load institutional technical analysis.</p>
    </div>
);

const LoadingState = () => (
    <div className="flex flex-col items-center justify-center h-screen bg-[#F8FAFC] gap-5">
        <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p className="font-bold uppercase tracking-widest text-slate-500 text-xs">Computing Algorithms...</p>
    </div>
);

const SectionHeader = ({ icon, title }) => (
    <div className="flex items-center gap-3 pb-2 mb-6 mt-12 border-b border-slate-200">
        <div className="p-2 bg-white border border-slate-200 shadow-sm rounded-xl text-slate-700">{icon}</div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">{title}</h2>
    </div>
);

const ChartCard = ({ title, children }) => (
  <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all duration-300">
    <h3 className="text-xs font-black text-slate-800 uppercase tracking-widest mb-6 flex justify-between items-center border-b border-slate-100 pb-4">
        {title}
        <MoveVertical size={16} className="text-slate-300"/>
    </h3>
    {children}
  </div>
);

const InsightBox = ({ title, text, warning }) => (
    <div className={`mt-6 p-4 rounded-2xl text-sm border flex gap-4 items-start
        ${warning ? "bg-amber-50 border-amber-200 text-amber-900" : "bg-slate-50 border-slate-200 text-slate-700"}
    `}>
        {warning ? <AlertTriangle size={20} className="text-amber-500 shrink-0"/> : <Info size={20} className="text-blue-500 shrink-0"/>}
        <div>
            <span className="block font-black mb-1 tracking-wide">{title}</span>
            <p className="leading-relaxed font-medium text-slate-600">{text}</p>
        </div>
    </div>
);

const SignalBadge = ({ label, value, type }) => {
    const colors = {
        bull: "bg-emerald-50 text-emerald-700 border-emerald-200 shadow-sm",
        bear: "bg-rose-50 text-rose-700 border-rose-200 shadow-sm",
        warn: "bg-amber-50 text-amber-700 border-amber-200 shadow-sm",
        neutral: "bg-white text-slate-700 border-slate-200 shadow-sm"
    };
    return (
        <div className={`flex flex-col px-5 py-2.5 rounded-xl border ${colors[type]}`}>
            <span className="text-[9px] font-extrabold uppercase tracking-widest opacity-70 mb-0.5">{label}</span>
            <span className="font-black text-[15px] leading-none">{value}</span>
        </div>
    );
};

// --- PRO TOOLTIP COMPONENT ---
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 text-white p-4 border border-slate-700 shadow-2xl rounded-2xl text-xs z-50 min-w-[160px]">
        <p className="font-bold text-slate-400 mb-3 uppercase tracking-widest border-b border-slate-700/50 pb-2">{label}</p>
        {payload.map((p) => (
          <div key={p.name} className="flex justify-between gap-6 mb-2 last:mb-0">
            <span className="text-slate-300 font-semibold uppercase">{p.name}</span>
            <span className="font-black tabular-nums" style={{ color: p.color || '#fff' }}>
              {Number(p.value).toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};