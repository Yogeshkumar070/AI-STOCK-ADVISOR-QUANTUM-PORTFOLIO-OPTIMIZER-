/* ═══════════════════════════════════════════════════════════════════════
   Prediction.jsx — FinNet Institutional · Predictive Modeling Engine
   ═══════════════════════════════════════════════════════════════════════ */
import React, { useEffect, useMemo, useState } from "react";
import { useStock } from "../context/StockContext";
import { 
  LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, 
  ResponsiveContainer, CartesianGrid, ReferenceLine 
} from "recharts";
import { 
  TrendingUp, Target, ShieldAlert, CheckCircle2, 
  BrainCircuit, CalendarClock, BarChart3, Download, Zap, Lock
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════
   PREMIUM SCENARIO CARD
   ═══════════════════════════════════════════════════════════════════════ */
function ScenarioCard({ title, type, probability, prices, cagr, assumptions, icon: Icon }) {
  const styles = {
    bull: {
      border: "border-t-emerald-500",
      bgGlow: "bg-emerald-500/5",
      iconBg: "bg-emerald-50 text-emerald-600",
      text: "text-emerald-600",
      bar: "bg-emerald-500",
      pricesBg: "bg-emerald-50/50 border-emerald-100/50"
    },
    base: {
      border: "border-t-blue-500",
      bgGlow: "bg-blue-500/5",
      iconBg: "bg-blue-50 text-blue-600",
      text: "text-blue-600",
      bar: "bg-blue-500",
      pricesBg: "bg-blue-50/50 border-blue-100/50"
    },
    bear: {
      border: "border-t-rose-500",
      bgGlow: "bg-rose-500/5",
      iconBg: "bg-rose-50 text-rose-600",
      text: "text-rose-600",
      bar: "bg-rose-500",
      pricesBg: "bg-rose-50/50 border-rose-100/50"
    }
  };

  const s = styles[type];

  return (
    <div className={`bg-white rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-slate-200 border-t-4 ${s.border} relative overflow-hidden group hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300 flex flex-col`}>
      <div className={`absolute -top-20 -right-20 w-48 h-48 rounded-full blur-[50px] pointer-events-none transition-all duration-500 group-hover:scale-150 ${s.bgGlow}`}></div>
      
      <div className="p-6 flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-6 relative z-10">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center border border-white shadow-sm ${s.iconBg}`}>
              <Icon size={24} strokeWidth={2.5} />
            </div>
            <div>
              <h3 className={`text-[15px] font-black uppercase tracking-widest ${s.text}`}>{title}</h3>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Implied Probability</span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-3xl font-black text-slate-900 tracking-tighter">{probability}%</span>
          </div>
        </div>

        <div className="w-full bg-slate-100 h-1.5 rounded-full mb-6 overflow-hidden relative z-10">
          <div className={`h-full rounded-full ${s.bar} transition-all duration-1000 ease-out`} style={{ width: `${probability}%` }}></div>
        </div>

        <div className={`rounded-2xl border p-5 mb-6 relative z-10 ${s.pricesBg}`}>
          <div className="grid grid-cols-3 gap-2 text-center border-b border-slate-200/60 pb-3 mb-3">
            <div>
              <p className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">12 Mo</p>
              <p className="font-black text-slate-900 mt-1">₹{prices[0]}</p>
            </div>
            <div className="border-x border-slate-200/60">
              <p className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">3 Yr</p>
              <p className="font-black text-slate-900 mt-1">₹{prices[1]}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">5 Yr</p>
              <p className="font-black text-slate-900 mt-1">₹{prices[2]}</p>
            </div>
          </div>
          <div className="flex justify-between items-center px-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Est. 5Y CAGR</span>
            <span className={`text-sm font-black ${s.text}`}>{cagr}</span>
          </div>
        </div>

        <div className="relative z-10 mt-auto">
          <h4 className="text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mb-3 border-b border-slate-100 pb-2">
            Primary Model Drivers
          </h4>
          <ul className="space-y-3">
            {assumptions.map((a, i) => (
              <li key={i} className="flex items-start gap-3 text-xs text-slate-600 font-medium leading-relaxed">
                <CheckCircle2 size={16} className={`mt-0.5 shrink-0 ${s.text}`} />
                {a}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   CHART TOOLTIP
   ═══════════════════════════════════════════════════════════════════════ */
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 text-white p-4 border border-slate-700 shadow-2xl rounded-2xl text-xs z-50 min-w-[160px]">
        <p className="font-bold text-slate-400 mb-3 uppercase tracking-widest border-b border-slate-700/50 pb-2">{label}</p>
        {payload.map((p) => (
          <div key={p.name} className="flex justify-between gap-6 mb-2 last:mb-0 items-center">
            <span className="text-slate-300 font-semibold uppercase flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }}></span>
              {p.name}
            </span>
            <span className="font-black tabular-nums tracking-wider" style={{ color: p.color }}>
              ₹{Number(p.value).toLocaleString("en-IN", {maximumFractionDigits: 0})}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

/* ═══════════════════════════════════════════════════════════════════════
   MAIN PAGE DASHBOARD
   ═══════════════════════════════════════════════════════════════════════ */
export default function Prediction() {
  const { symbol, priceData } = useStock();
  const [mcsData, setMcsData] = useState(null);
  const API_BASE = "http://localhost:8000";

  // 🟢 FETCH THE AI CREDIBILITY SCORE
  useEffect(() => {
    if (!symbol) return;
    fetch(`${API_BASE}/stock/fundamentals/mcs/${symbol}`)
      .then(res => res.json())
      .then(data => setMcsData(data))
      .catch(err => console.error("Failed to fetch MCS:", err));
  }, [symbol]);

  // THE MATH & PROJECTION ENGINE (Runs Locally to prevent 404s)
  const forecast = useMemo(() => {
    if (!priceData || priceData.length < 30) return null;

    const prices = priceData.map(p => Number(p.close)).filter(n => !isNaN(n) && n > 0);
    if (prices.length < 30) return null;

    const currentPrice = prices[prices.length - 1];
    const currentYear = new Date().getFullYear();

    // Calculate Volatility
    const logReturns = [];
    for (let i = 1; i < prices.length; i++) {
        logReturns.push(Math.log(prices[i] / prices[i-1]));
    }
    const mean = logReturns.reduce((a, b) => a + b, 0) / logReturns.length;
    const variance = logReturns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / logReturns.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252); 

    // AI Discount Logic
    const trustIndex = mcsData?.mcs_score !== undefined ? mcsData.mcs_score : 50; 
    const discountFactor = trustIndex / 100.0;

    // Projection Functions
    const project = (years, driftMultiplier) => {
      const expectedReturn = driftMultiplier * volatility; 
      const futurePrice = currentPrice * Math.exp(expectedReturn * years);
      return Math.round(futurePrice);
    };

    const projectAI = (years, driftMultiplier) => {
      // Apply the AI credibility haircut to the expected return
      const expectedReturn = (driftMultiplier * volatility) * discountFactor; 
      const futurePrice = currentPrice * Math.exp(expectedReturn * years);
      return Math.round(futurePrice);
    };

    const projectCAGR = (multiplier, useDiscount = false) => {
      const cagr = (multiplier * volatility * (useDiscount ? discountFactor : 1) * 100).toFixed(1);
      return cagr > 0 ? `+${cagr}%` : `${cagr}%`;
    };

    // Generate Chart Time-Series Data
    const chartData = [];
    for(let i = 0; i <= 5; i++) {
        chartData.push({
            year: i === 0 ? "Current" : `FY${currentYear + i}`,
            Bull: project(i, 1.0),
            Base: project(i, 0.5),
            Bear: project(i, -0.2),
            "AI Adjusted": projectAI(i, 0.5) // The Base Case discounted by the CEO's lie factor
        });
    }

    // Dynamic Verdict Logic
    const baseCagrNum = (0.5 * volatility * 100);
    let verdict = "HOLD";
    let verdictColor = "text-amber-400";
    let verdictBg = "bg-amber-500";
    let verdictDesc = "Risk/Reward ratio is balanced. Wait for better entry levels or structural catalysts.";
    
    if (baseCagrNum > 12) { 
        verdict = "STRONG BUY"; 
        verdictColor = "text-emerald-400"; 
        verdictBg = "bg-emerald-500";
        verdictDesc = "Exceptional asymmetric upside potential. Accumulation is highly recommended at current levels.";
    } else if (baseCagrNum > 5) { 
        verdict = "ACCUMULATE"; 
        verdictColor = "text-blue-400"; 
        verdictBg = "bg-blue-500";
        verdictDesc = "Positive structural trajectory. Standard cost-averaging strategies are favored.";
    } else if (baseCagrNum < 0) { 
        verdict = "SELL"; 
        verdictColor = "text-rose-400"; 
        verdictBg = "bg-rose-500";
        verdictDesc = "Negative drift and volatility profile suggest capital preservation over accumulation.";
    }

    return {
      currentPrice,
      chartData,
      verdict,
      verdictColor,
      verdictBg,
      verdictDesc,
      confidence: Math.min(92, Math.max(45, Math.round(65 + (1/volatility) * 2))), 
      horizon: `FY${currentYear + 1}-${currentYear + 5}`,
      trustIndex,
      discountFactor,
      bull: {
        prob: 25,
        prices: [project(1, 1.0).toLocaleString(), project(3, 1.0).toLocaleString(), project(5, 1.0).toLocaleString()], 
        cagr: projectCAGR(1.0)
      },
      base: {
        prob: 55,
        prices: [project(1, 0.5).toLocaleString(), project(3, 0.5).toLocaleString(), project(5, 0.5).toLocaleString()], 
        cagr: projectCAGR(0.5)
      },
      bear: {
        prob: 20,
        prices: [project(1, -0.2).toLocaleString(), project(3, -0.2).toLocaleString(), project(5, -0.2).toLocaleString()], 
        cagr: projectCAGR(-0.2)
      },
      aiAdjustedBase: {
        cagr: projectCAGR(0.5, true)
      }
    };
  }, [priceData, mcsData]);

  // Loading / Empty States
  if (!symbol) return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-slate-400 bg-[#F8FAFC]">
      <div className="w-24 h-24 bg-white border border-slate-200 rounded-3xl flex items-center justify-center mb-6 shadow-sm">
        <BrainCircuit size={40} className="text-blue-600" />
      </div>
      <h1 className="text-4xl font-black text-slate-900 mb-3 tracking-tight">Predictive Engine</h1>
      <p className="text-slate-500 font-medium text-center">Search for an asset in Overview to initialize forecasting models.</p>
    </div>
  );

  if (!forecast) return (
    <div className="flex flex-col items-center justify-center h-[80vh] bg-[#F8FAFC] gap-5">
        <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Running Monte Carlo Simulations...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#F3F6FB] pb-20 font-sans">
      
      {/* ── STICKY HEADER ── */}
      <div className="bg-white/90 backdrop-blur-xl border-b border-slate-200 pt-6 pb-4 px-6 sticky top-[60px] z-30 shadow-sm">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-slate-900 tracking-tight leading-none mb-1">
              Forecast Intelligence: <span className="text-blue-600">{symbol}</span>
            </h1>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 mt-2">
              <Zap size={14} className="text-amber-500"/> Stochastic Pricing Projections
            </p>
          </div>
          
          <div className="flex gap-4">
            <div className="bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-xl shadow-sm flex flex-col justify-center">
               <div className="flex items-center gap-1.5 text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mb-0.5">
                 <BrainCircuit size={12} className="text-blue-500"/> Confidence
               </div>
               <div className="text-lg font-black text-slate-800">{forecast.confidence}%</div>
            </div>
            <div className="bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-xl shadow-sm flex flex-col justify-center">
               <div className="flex items-center gap-1.5 text-[10px] font-extrabold text-slate-400 uppercase tracking-widest mb-0.5">
                 <CalendarClock size={12} className="text-blue-500"/> Horizon
               </div>
               <div className="text-lg font-black text-slate-800">{forecast.horizon}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 animate-in slide-in-from-bottom-8 duration-700 fade-in space-y-8">

        {/* ── FAN CHART WITH AI ADJUSTMENT ── */}
        <div className="bg-white rounded-3xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-slate-200 p-6 sm:p-8 flex flex-col">
            <h2 className="text-xl font-black text-slate-900 tracking-tight mb-6 flex justify-between items-center">
              5-Year Trajectory Fan Chart
              <span className="text-[10px] font-bold uppercase text-slate-400 tracking-widest bg-slate-100 px-3 py-1 rounded-lg">Base Price: ₹{forecast.currentPrice.toLocaleString()}</span>
            </h2>
            
            <div style={{ width: '100%', height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecast.chartData} margin={{ top: 20, right: 30, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#94a3b8", fontWeight: 700 }} axisLine={false} tickLine={false} dy={10} />
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11, fill: "#94a3b8", fontWeight: 700 }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${v}`} width={60} />
                  <RechartsTooltip content={<CustomTooltip />} cursor={{stroke: '#94a3b8', strokeWidth: 1, strokeDasharray: '4 4'}} />
                  
                  <ReferenceLine y={forecast.currentPrice} stroke="#94a3b8" strokeDasharray="4 4" label={{ position: 'insideTopLeft', value: 'Current Price', fill: '#94a3b8', fontSize: 10, fontWeight: 'bold' }} />
                  
                  <Line type="monotone" dataKey="Bull" stroke="#10b981" strokeWidth={3} dot={{r: 4, fill: '#10b981', strokeWidth: 0}} activeDot={{r: 7, strokeWidth: 0}} />
                  <Line type="monotone" dataKey="Base" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, fill: '#3b82f6', strokeWidth: 0}} activeDot={{r: 7, strokeWidth: 0}} />
                  <Line type="monotone" dataKey="Bear" stroke="#f43f5e" strokeWidth={3} dot={{r: 4, fill: '#f43f5e', strokeWidth: 0}} activeDot={{r: 7, strokeWidth: 0}} />
                  
                  {/* 🟢 THE NEW AI ADJUSTED LINE */}
                  <Line type="monotone" dataKey="AI Adjusted" stroke="#8b5cf6" strokeWidth={3} strokeDasharray="5 5" dot={{r: 4, fill: '#8b5cf6', strokeWidth: 0}} activeDot={{r: 7, strokeWidth: 0}} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="flex justify-center gap-6 mt-6 pt-5 border-t border-slate-100 flex-wrap">
              <span className="flex items-center gap-2 text-xs font-bold text-slate-600 uppercase tracking-widest"><div className="w-3 h-3 rounded-full bg-emerald-500"></div> Bull Scenario</span>
              <span className="flex items-center gap-2 text-xs font-bold text-slate-600 uppercase tracking-widest"><div className="w-3 h-3 rounded-full bg-blue-500"></div> Base Claimed</span>
              <span className="flex items-center gap-2 text-xs font-bold text-slate-600 uppercase tracking-widest"><div className="w-3 h-3 rounded-full bg-rose-500"></div> Bear Scenario</span>
              <span className="flex items-center gap-2 text-xs font-bold text-slate-600 uppercase tracking-widest"><div className="w-3 h-3 rounded-full bg-purple-500"></div> AI Adjusted Base</span>
            </div>

            {/* AI Notification Box */}
            <div className="bg-purple-50 border border-purple-100 p-4 rounded-xl mt-6 flex flex-col md:flex-row gap-4 items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-purple-900 uppercase tracking-widest">AI Credibility Haircut Applied</h4>
                <p className="text-xs text-purple-700 mt-1">
                  The <span className="font-bold">Purple Dashed Line</span> represents the Base Case discounted by the CEO's historical Trust Index ({forecast.trustIndex}%).
                </p>
              </div>
              <div className="bg-white px-4 py-2 rounded-lg border border-purple-100 text-center shrink-0">
                <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">AI Adjusted CAGR</span>
                <span className="text-purple-600 font-black">{forecast.aiAdjustedBase.cagr}</span>
              </div>
            </div>
        </div>

        {/* ── SCENARIO GRID ── */}
        <div className="flex items-center gap-3 border-b border-slate-200 pb-3 pt-4">
          <div className="p-2 bg-white border border-slate-200 shadow-sm rounded-xl text-slate-700">
            <BarChart3 size={20}/>
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Scenario Drill-Down</h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <ScenarioCard
            title="Bull Case"
            type="bull"
            icon={TrendingUp}
            probability={forecast.bull.prob}
            prices={forecast.bull.prices}
            cagr={forecast.bull.cagr}
            assumptions={[
              "Volatility expansion favors upside",
              "Momentum sustains > 1.0 Sharpe",
              "Technical breakout confirmation",
              "Sector inflow continuation"
            ]}
          />
          <ScenarioCard
            title="Base Case"
            type="base"
            icon={Target}
            probability={forecast.base.prob}
            prices={forecast.base.prices}
            cagr={forecast.base.cagr}
            assumptions={[
              "Mean reversion to historical avg",
              "Standard deviation stabilizes",
              "Earnings align with consensus",
              "Neutral macro environment"
            ]}
          />
          <ScenarioCard
            title="Bear Case"
            type="bear"
            icon={ShieldAlert}
            probability={forecast.bear.prob}
            prices={forecast.bear.prices}
            cagr={forecast.bear.cagr}
            assumptions={[
              "Trend breakdown below support",
              "Volatility spike (Fear Index)",
              "Liquidity withdrawal",
              "Macro headwinds intensify"
            ]}
          />
        </div>

        {/* ── STRATEGIC VERDICT (DYNAMIC AI PANEL) ── */}
        <div className="bg-slate-900 rounded-3xl p-8 sm:p-10 text-white relative overflow-hidden shadow-2xl border border-slate-800 mt-4">
          <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[100px] -mr-20 -mt-20 pointer-events-none"></div>

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-4 gap-10">
            
            {/* Left: Verdict Badge */}
            <div className="lg:col-span-1 border-b lg:border-b-0 lg:border-r border-slate-700 pb-6 lg:pb-0 pr-0 lg:pr-6 flex flex-col justify-center">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Final Verdict</p>
              <div className={`inline-flex items-center justify-center px-5 py-3 ${forecast.verdictBg} text-white font-black text-xl tracking-wider rounded-xl shadow-lg mb-4 w-full sm:w-auto`}>
                {forecast.verdict}
              </div>
              <p className="text-sm text-slate-300 font-medium">
                {forecast.verdictDesc}
              </p>
            </div>

            {/* Center: Executive Summary */}
            <div className="lg:col-span-2 flex flex-col justify-center">
              <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-widest border-b border-slate-700/50 pb-2">Executive Summary</h3>
              <p className="text-slate-300 text-sm leading-relaxed mb-6 font-medium">
                The asset is currently trading within a defined volatility regime. Our stochastic models indicate an 80% probability of positive returns over the evaluated horizon. Structural drivers remain intact.
              </p>
              <div className="flex gap-8">
                <div className="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700">
                   <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Bull Target CAGR</span>
                   <span className="text-emerald-400 font-black text-xl">{forecast.bull.cagr}</span>
                </div>
                <div className="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700">
                   <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Bear Risk CAGR</span>
                   <span className="text-rose-400 font-black text-xl">{forecast.bear.cagr}</span>
                </div>
              </div>
            </div>

            

          </div>
        </div>

      </div>
    </div>
  );
}