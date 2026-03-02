/* ═══════════════════════════════════════════════════════════════════════
   Quantum.jsx — FinNet Institutional · QAOA Portfolio Optimizer (Dark Terminal)
   ═══════════════════════════════════════════════════════════════════════ */
import React, { useState, useMemo } from "react";
import {
  AlertTriangle, Cpu, BarChart3, Atom, ShieldCheck, TrendingUp, 
  BrainCircuit, Info, Search, X, Check, Lightbulb, Activity, Grid, Zap
} from "lucide-react";

import {
  Treemap, ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, 
  LineChart, Line, AreaChart, Area, CartesianGrid, Tooltip as RechartsTooltip, Legend
} from "recharts";

/* ---------- NIFTY 50 UNIVERSE ---------- */
const ALL_STOCKS = [
  "ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK",
  "BAJAJ-AUTO","BAJAJFINSV","BAJFINANCE","BHARTIARTL","BPCL",
  "BRITANNIA","CIPLA","COALINDIA","DIVISLAB","DRREDDY",
  "EICHERMOT","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE",
  "HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK",
  "INFY","ITC","JSWSTEEL","KOTAKBANK","LT",
  "M&M","MARUTI","NESTLEIND","NTPC","ONGC",
  "POWERGRID","RELIANCE","SBIN","SBILIFE","SUNPHARMA",
  "TATACONSUM","TATAMOTORS","TATASTEEL","TCS","TECHM",
  "TITAN","ULTRACEMCO","UPL","WIPRO"
];

// Distinct, vibrant color palette for individual asset blocks
const ALLOCATION_COLORS = [
  "#3b82f6", // Blue
  "#8b5cf6", // Violet
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ef4444", // Rose
  "#06b6d4", // Cyan
  "#ec4899", // Pink
  "#84cc16", // Lime
  "#6366f1", // Indigo
  "#14b8a6", // Teal
  "#f97316", // Orange
  "#d946ef", // Fuchsia
  "#0ea5e9", // Light Sea Green
  "#a855f7", // Purple
  "#eab308", // Yellow
];

/* ═══════════════════════════════════════════════════════════════════════
   CUSTOM TREEMAP CELL (Premium Block UI)
   ═══════════════════════════════════════════════════════════════════════ */
const TreemapCell = (props) => {
  const { depth, x, y, width, height, name, value, fill } = props;

  // Skip rendering the invisible root node
  if (depth < 1) return null;

  // Safety fallback
  const alloc = Number(value) || 0;

  return (
    <g>
      {/* Main Block Background */}
      <rect 
        x={x} y={y} width={width} height={height} 
        fill={fill || "#3b82f6"} 
        stroke="#020617" strokeWidth={4} // Dark separation lines
        rx={6} // Smooth rounded corners
        className="transition-all duration-300 hover:brightness-110 cursor-crosshair"
      />
      {/* Inner Glass Highlight (Creates depth) */}
      <rect
        x={x + 2} y={y + 2} width={Math.max(0, width - 4)} height={Math.max(0, height - 4)}
        fill="transparent"
        stroke="#ffffff" strokeWidth={1} strokeOpacity={0.2}
        rx={4}
        style={{ pointerEvents: 'none' }}
      />
      {/* Ticker Symbol */}
      {width > 50 && height > 40 && (
        <text 
          x={x + width / 2} y={y + height / 2 - 4} 
          textAnchor="middle" fill="#ffffff" 
          fontFamily="'Inter', 'SF Pro Display', sans-serif" 
          fontSize={18} fontWeight="900" 
          style={{ pointerEvents: 'none', letterSpacing: '0.5px' }}
        >
          {name}
        </text>
      )}
      {/* Allocation % (Prominent & Clean) */}
      {width > 60 && height > 55 && (
        <text 
          x={x + width / 2} y={y + height / 2 + 18} 
          textAnchor="middle" fill="rgba(255,255,255,0.9)" 
          fontFamily="'Inter', 'SF Pro Display', sans-serif" 
          fontSize={14} fontWeight="700" 
          style={{ pointerEvents: 'none' }}
        >
          {alloc.toFixed(1)}%
        </text>
      )}
    </g>
  );
};

/* ═══════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════════ */
export default function Quantum() {
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredStocks = ALL_STOCKS.filter(stock => 
    stock.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const toggleStock = (stock) => {
    setError("");
    setResult(null);
    if (selectedStocks.includes(stock)) {
      setSelectedStocks(selectedStocks.filter(s => s !== stock));
    } else {
      if (selectedStocks.length >= 15) {
        setError("Max 15 assets for the free optimization tier.");
        return;
      }
      setSelectedStocks([...selectedStocks, stock]);
    }
  };

  const clearSelection = () => {
    setSelectedStocks([]);
    setResult(null);
    setError("");
  };

  const runQuantumOptimization = async () => {
    if (selectedStocks.length < 3) {
      setError("Select a minimum of 3 assets to construct a valid matrix.");
      return;
    }
    setLoading(true); setError(""); setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/quantum/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tickers: selectedStocks, risk_tolerance: 0.5 })
      });
      if (!res.ok) throw new Error("Backend optimization failed");
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Quantum matrix computation failed.");
    } finally {
      setLoading(false);
    }
  };

  // Prepare Treemap Data Structure (Sorted & Colored)
  const treeMapData = useMemo(() => {
    if (!result) return [];
    
    const children = Object.entries(result.weights)
      .filter(([name, value]) => value * 100 > 0.5) // Hide micro-allocations
      .sort((a, b) => b[1] - a[1]) // Sort largest to smallest
      .map(([name, value], index) => ({
        name,
        size: value * 100, 
        fill: ALLOCATION_COLORS[index % ALLOCATION_COLORS.length] // Assign unique color
      }));

    return [{ name: "Portfolio", children }];
  }, [result]);

  /* ---------- CORRELATION HEATMAP ---------- */
  const renderCorrelationHeatmap = () => {
    if (!result?.correlation_matrix) return null;
    const stocks = Object.keys(result.correlation_matrix);
    const heatmapData = [];
    let highRiskPairs = 0;

    stocks.forEach((row) => {
      stocks.forEach((col) => {
        const val = result.correlation_matrix[row][col];
        heatmapData.push({ x: col, y: row, value: val });
        if (row !== col && val > 0.75) highRiskPairs++;
      });
    });

    highRiskPairs = highRiskPairs / 2;
    const totalPairs = (stocks.length * (stocks.length - 1)) / 2;

    const colorScale = (v) => {
      if (v > 0.75) return "#ef4444";  // Neon Red
      if (v > 0.4) return "#f59e0b";   // Neon Amber
      return "#10b981";                // Neon Emerald
    };

    return (
      <div className="bg-[#1e293b] p-8 rounded-3xl shadow-2xl border border-slate-700 mt-8 relative overflow-hidden group">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-yellow-300"></div>
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
            <h3 className="text-xl font-black text-white flex items-center gap-3">
            <Grid size={24} className="text-amber-400" />
            Diversification Matrix
            </h3>
            <div className="flex items-center gap-3 text-xs font-bold">
                <span className="bg-[#0f172a] text-slate-300 px-4 py-1.5 rounded-xl border border-slate-700 shadow-inner">
                    Pairs: {totalPairs}
                </span>
                <span className={`px-4 py-1.5 rounded-xl border shadow-lg ${highRiskPairs === 0 ? 'bg-emerald-900/40 border-emerald-500/50 text-emerald-400' : 'bg-rose-900/40 border-rose-500/50 text-rose-400'}`}>
                    High Risk Overlaps: {highRiskPairs}
                </span>
            </div>
        </div>
        
        <div style={{ width: '100%', height: 400, position: 'relative' }} className="bg-[#020617] rounded-2xl border border-slate-800 p-4 shadow-inner">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 50 }}>
              <XAxis type="category" dataKey="x" allowDuplicatedCategory={false} axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 'bold'}} />
              <YAxis type="category" dataKey="y" allowDuplicatedCategory={false} axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 'bold'}} />
              <RechartsTooltip
                cursor={{ strokeDasharray: '4 4', stroke: '#334155' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-[#020617] text-white p-4 border border-slate-700 shadow-2xl rounded-2xl text-xs z-50">
                        <p className="font-bold text-slate-400 mb-2 uppercase tracking-widest border-b border-slate-800 pb-2">{data.y} × {data.x}</p>
                        <p className="font-bold text-lg">Correlation: <span style={{color: colorScale(data.value)}}>{data.value.toFixed(2)}</span></p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter data={heatmapData} shape={(props) => {
                  const { cx, cy, payload } = props;
                  if (isNaN(cx) || isNaN(cy)) return null;
                  return <rect x={cx - 16} y={cy - 16} width={32} height={32} fill={colorScale(payload.value)} rx={6} className="hover:opacity-75 transition-opacity cursor-crosshair"/>;
              }}/>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-8 bg-[#0f172a] p-5 rounded-2xl border border-slate-700 flex gap-4 items-start shadow-inner">
          <Lightbulb className="text-amber-500 shrink-0 mt-0.5" size={20} />
          <div>
            <h4 className="text-xs font-black text-slate-200 uppercase tracking-widest mb-1">Matrix Intelligence</h4>
            <p className="text-sm text-slate-400 leading-relaxed font-medium">
              Green squares represent assets that move independently, providing true portfolio diversification. Red squares indicate highly correlated assets that will compound your downside risk during sector-specific sell-offs.
            </p>
          </div>
        </div>
      </div>
    );
  };

  /* ── QUANTUM GRID BACKGROUND STYLE ── */
  const quantumGridStyle = {
    backgroundImage: `
      linear-gradient(to right, rgba(234, 179, 8, 0.08) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(234, 179, 8, 0.08) 1px, transparent 1px)
    `,
    backgroundSize: '40px 40px',
  };

  return (
    <div className="min-h-screen bg-[#020617] pb-20 font-sans selection:bg-amber-500/30">
      
      {/* ── HIGH-TECH HEADER WITH YELLOW QUANTUM GRID ── */}
      <div className="text-white pt-16 pb-24 px-8 relative border-b border-slate-800" style={quantumGridStyle}>
        {/* Glow Effects */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-amber-600/10 blur-[150px] rounded-full pointer-events-none"></div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-yellow-600/10 blur-[100px] rounded-full pointer-events-none"></div>
        
        <div className="max-w-7xl mx-auto relative z-10 text-center flex flex-col items-center">
            <div className="inline-flex items-center gap-2 bg-[#0f172a] border border-amber-500/30 px-5 py-2 rounded-full mb-6 shadow-[0_0_20px_rgba(245,158,11,0.2)]">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
                <span className="text-[10px] font-black text-amber-400 uppercase tracking-[0.2em]">QAOA Matrix Initialized</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-black tracking-tighter mb-5 flex justify-center items-center gap-4 text-white">
                <Atom className="text-amber-400 animate-spin-slow drop-shadow-[0_0_15px_rgba(245,158,11,0.8)]" size={56} />
                Quantum Portfolio Optimization
            </h1>
            <p className="text-slate-400 text-lg font-medium max-w-2xl mx-auto leading-relaxed">
                Deploy advanced quantum-approximate optimization (QAOA) to construct hyper-efficient portfolios. Our algorithmic engine minimizes correlation drag while maximizing risk-adjusted returns across the top 50 equities.
            </p>
        </div>
      </div>

      {/* ── MAIN CONTENT GRID ── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 relative z-20">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          
          {/* ── LEFT PANEL: ASSET UNIVERSE ── */}
          <div className="xl:col-span-4 space-y-6">
            <div className="bg-[#0f172a]/95 backdrop-blur-2xl rounded-3xl shadow-2xl border border-slate-700 overflow-hidden flex flex-col h-[700px] relative">
              {/* Subtle grid behind the sidebar */}
              <div className="absolute inset-0 pointer-events-none opacity-30" style={quantumGridStyle}></div>

              {/* Search Header */}
              <div className="p-6 border-b border-slate-800 bg-[#020617]/90 relative z-10">
                <div className="flex justify-between items-center mb-5">
                  <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
                    <Cpu size={20} className="text-amber-400"/> NIFTY 50 Stocks
                  </h2>
                  {selectedStocks.length > 0 && (
                    <button onClick={() => {clearSelection(); setSearchTerm("");}} className="text-[10px] uppercase tracking-widest bg-rose-500/10 text-rose-400 border border-rose-500/20 px-3 py-1.5 rounded-lg font-bold hover:bg-rose-500/20 transition-colors">
                      Clear
                    </button>
                  )}
                </div>
                <div className="relative group">
                  <Search className="absolute left-4 top-3.5 text-slate-500 group-focus-within:text-amber-400 transition-colors" size={18} />
                  <input 
                    type="text" placeholder="Search Nifty 50 tickers..."
                    className="w-full pl-11 pr-4 py-3 bg-[#1e293b] text-white text-sm font-bold border border-slate-700 rounded-xl focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all placeholder-slate-500 shadow-inner"
                    value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className="flex justify-between items-center mt-4 text-[10px] font-black uppercase tracking-widest text-slate-500">
                  <span className={selectedStocks.length > 0 ? "text-amber-400" : ""}>{selectedStocks.length} Selected</span>
                  <span className={selectedStocks.length >= 15 ? "text-rose-500 animate-pulse" : ""}>Max 15 Limit</span>
                </div>
              </div>

              {/* Scrollable List */}
              <div className="flex-1 overflow-y-auto p-5 custom-scrollbar relative z-10">
                {filteredStocks.length === 0 ? (
                   <div className="text-center py-10 text-slate-500 text-sm font-bold">No assets match your search.</div>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {filteredStocks.map(stock => {
                      const isSelected = selectedStocks.includes(stock);
                      return (
                        <button
                          key={stock}
                          onClick={() => toggleStock(stock)}
                          disabled={!isSelected && selectedStocks.length >= 15}
                          className={`relative flex items-center justify-between px-4 py-3.5 text-xs font-black rounded-xl transition-all duration-300
                            ${isSelected 
                              ? "bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-900 border border-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.5)] transform scale-[1.03]" 
                              : "bg-[#1e293b] text-slate-400 border border-slate-700 hover:border-amber-500/50 hover:text-amber-400 shadow-sm"}
                            ${!isSelected && selectedStocks.length >= 15 ? "opacity-30 cursor-not-allowed hover:border-slate-700 hover:text-slate-400" : ""}
                          `}
                        >
                          {stock}
                          {isSelected && <Check size={16} strokeWidth={3} className="text-slate-900 drop-shadow-sm" />}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Action Footer */}
              <div className="p-6 border-t border-slate-800 bg-[#020617]/90 relative z-10">
                {error && (
                  <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-bold rounded-xl flex items-center gap-2">
                    <AlertTriangle size={16} className="shrink-0"/> {error}
                  </div>
                )}
                <button
                  onClick={runQuantumOptimization}
                  disabled={loading || selectedStocks.length < 3}
                  className="w-full py-4 bg-gradient-to-r from-amber-600 via-yellow-500 to-amber-600 text-slate-900 rounded-xl font-black text-sm uppercase tracking-widest shadow-[0_0_20px_rgba(245,158,11,0.3)] hover:shadow-[0_0_30px_rgba(245,158,11,0.6)] hover:scale-[1.02] transition-all disabled:opacity-50 disabled:scale-100 disabled:shadow-none flex justify-center items-center gap-3 border border-yellow-300/50"
                >
                  {loading ? <span className="flex items-center gap-2"><Cpu className="animate-spin text-slate-900" size={20}/> Computing Matrix...</span> : "Initialize Optimization"}
                </button>
              </div>
            </div>
          </div>

          {/* ── RIGHT PANEL: DASHBOARD RESULTS ── */}
          <div className="xl:col-span-8 space-y-8">
            {result ? (
              <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
                
                {/* KPI METRICS */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
                  <MetricCard title="Expected Return" value={`${result.metrics.expected_return}%`} icon={<TrendingUp size={20}/>} color="text-emerald-400" glow="shadow-emerald-500/10" />
                  <MetricCard title="Portfolio Risk (Vol)" value={`${result.metrics.portfolio_volatility}%`} icon={<AlertTriangle size={20}/>} color="text-rose-400" glow="shadow-rose-500/10" />
                  <MetricCard title="Sharpe Ratio" value={result.metrics.sharpe_ratio} icon={<ShieldCheck size={20}/>} color="text-amber-400" glow="shadow-amber-500/10" />
                </div>

                {/* ── THE INSTITUTIONAL TREEMAP ── */}
                <div className="bg-[#1e293b] rounded-3xl shadow-2xl border border-slate-700 mb-8 overflow-hidden">
                  <div className="px-8 py-6 border-b border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#0f172a]/50">
                    <h3 className="text-xl font-black text-white tracking-tight flex items-center gap-3">
                      <Grid size={22} className="text-amber-400" /> Capital Allocation Map
                    </h3>
                    <div className="flex gap-4 text-[10px] font-black uppercase tracking-widest bg-[#020617] px-4 py-2 rounded-xl border border-slate-800">
                       <span className="text-slate-300">Optimal Distributed Weights</span>
                    </div>
                  </div>
                  
                  {/* Treemap Container */}
                  <div style={{ width: '100%', height: 500, position: 'relative' }} className="bg-[#020617] p-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <Treemap
                        data={treeMapData}
                        dataKey="size"
                        stroke="#020617"
                        fill="#334155"
                        content={<TreemapCell />}
                        isAnimationActive={true}
                        animationDuration={1500}
                        animationEasing="ease-out"
                      />
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* ── BACKTEST & NIFTY COMPARISON ── */}
                {result.benchmark_comparison?.equity_curve && (
                  <div className="bg-[#1e293b] p-8 rounded-3xl shadow-2xl border border-slate-700 mb-8 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-600/10 rounded-full blur-[80px] pointer-events-none group-hover:bg-emerald-600/20 transition-all duration-700"></div>
                    
                    <h3 className="text-xl font-black text-white tracking-tight mb-2 flex items-center gap-3">
                      <Activity className="text-emerald-400" size={24} /> Backtest vs NIFTY 50
                    </h3>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-8 border-b border-slate-800 pb-4">
                      Historical Equity Curve (Indexed to NAV 100)
                    </p>

                    <div style={{ width: '100%', height: 380, position: 'relative' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                          data={result.benchmark_comparison.equity_curve.dates.map((date, i) => ({
                            date,
                            "Optimized Portfolio": result.benchmark_comparison.equity_curve.portfolio[i],
                            "NIFTY Benchmark": result.benchmark_comparison.equity_curve.nifty[i],
                          }))}
                          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                        >
                          <defs>
                            <linearGradient id="portGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                          <XAxis dataKey="date" hide />
                          <YAxis domain={['auto', 'auto']} axisLine={false} tickLine={false} tick={{fontSize: 11, fill: '#94a3b8', fontWeight: 700}} width={45} />
                          <RechartsTooltip 
                            contentStyle={{borderRadius: '16px', border: '1px solid #334155', boxShadow: '0 20px 40px -10px rgb(0 0 0 / 0.5)', backgroundColor: '#020617', color: '#fff'}}
                            itemStyle={{fontWeight: '900', color: '#f8fafc'}}
                            labelStyle={{color: '#94a3b8', marginBottom: '8px', borderBottom: '1px solid #1e293b', paddingBottom: '6px', fontWeight: 'bold'}}
                          />
                          <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{fontSize: '12px', fontWeight: 'bold', color: '#cbd5e1'}}/>
                          
                          <Area type="monotone" dataKey="Optimized Portfolio" stroke="#10b981" strokeWidth={3} fill="url(#portGrad)" activeDot={{r: 7, strokeWidth: 0}} />
                          <Line type="monotone" dataKey="NIFTY Benchmark" stroke="#64748b" strokeWidth={2} strokeDasharray="6 6" dot={false} activeDot={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slate-800">
                      <ComparisonMetric label="Portfolio Return" value={`${result.benchmark_comparison?.portfolio_metrics?.annual_return ?? "N/A"}%`} color="text-emerald-400" />
                      <ComparisonMetric label="NIFTY Return" value={`${result.benchmark_comparison?.nifty_metrics?.annual_return ?? "N/A"}%`} color="text-slate-300" />
                      <ComparisonMetric label="Portfolio Max DD" value={`${result.benchmark_comparison?.portfolio_metrics?.max_drawdown ?? "N/A"}%`} color="text-rose-400" />
                      <ComparisonMetric label="NIFTY Max DD" value={`${result.benchmark_comparison?.nifty_metrics?.max_drawdown ?? "N/A"}%`} color="text-slate-400" />
                    </div>
                  </div>
                )}

                {/* ── RISK CONTRIBUTION BARS ── */}
                <div className="bg-[#1e293b] p-8 rounded-3xl shadow-2xl border border-slate-700 mb-8">
                  <h3 className="text-xl font-black text-white tracking-tight mb-2 flex items-center gap-3">
                    <ShieldCheck size={24} className="text-rose-500" /> Component Risk Analysis
                  </h3>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-8 border-b border-slate-800 pb-4">
                    Percentage of Total Portfolio Volatility
                  </p>
                  
                  <div className="space-y-6">
                    {Object.entries(result.risk_contribution).map(([stock, value]) => (
                      <div key={stock}>
                        <div className="flex justify-between items-end mb-2">
                          <span className="text-sm font-bold text-slate-300">{stock}</span>
                          <span className="text-lg font-black text-white">{(value * 100).toFixed(2)}%</span>
                        </div>
                        <div className="w-full bg-[#0f172a] rounded-full h-3 overflow-hidden shadow-inner border border-slate-800">
                          <div
                            className="bg-gradient-to-r from-amber-500 to-rose-600 h-full rounded-full transition-all duration-1000 relative"
                            style={{ width: `${value * 100}%` }}
                          >
                            <div className="absolute inset-0 bg-white/20 w-full h-1/2"></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ── MONTE CARLO FORECAST ── */}
                {result.monte_carlo && (
                  <div className="bg-[#020617] text-white p-8 rounded-3xl shadow-2xl border border-slate-800 relative overflow-hidden mt-8">
                    <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-amber-600/10 blur-[120px] rounded-full pointer-events-none"></div>
                    
                    <div className="relative z-10">
                      <h3 className="text-xl font-black tracking-tight mb-2 flex items-center gap-3">
                        <Zap size={24} className="text-amber-400" /> Monte Carlo Engine
                      </h3>
                      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-8 border-b border-slate-800 pb-4">
                        10,000 Iterations • 1-Year Horizon • Base: ₹100
                      </p>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div>
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Expected Value</p>
                          <p className="text-3xl font-black text-emerald-400">₹{result.monte_carlo.expected_value}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Best Case (95%)</p>
                          <p className="text-3xl font-black text-white">₹{result.monte_carlo.best_case}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Worst Case (5%)</p>
                          <p className="text-3xl font-black text-rose-400">₹{result.monte_carlo.worst_case}</p>
                        </div>
                        <div className="bg-[#1e293b] p-4 rounded-2xl border border-slate-700 shadow-inner flex flex-col justify-center">
                          <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1 text-center">Probability of Loss</p>
                          <p className="text-2xl font-black text-white text-center">{result.monte_carlo.probability_of_loss}%</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Heatmap rendered at the very bottom */}
                {renderCorrelationHeatmap()}

              </div>
            ) : (
              <div 
                className="h-[700px] flex flex-col items-center justify-center text-amber-500/50 border border-slate-800 rounded-3xl bg-[#0f172a]/80 shadow-2xl relative overflow-hidden"
                style={quantumGridStyle} // Applying the thin yellow grid here
              >
                <Atom size={90} className="mb-8 text-amber-400/50 animate-pulse drop-shadow-[0_0_40px_rgba(245,158,11,0.3)]" />
                <p className="text-3xl font-black text-white mb-3 tracking-tight">Quantum Engine Idle</p>
                <p className="text-sm font-medium text-slate-400 max-w-sm text-center leading-relaxed">
                  Select between 3 and 15 assets from the universe panel to initialize the algorithmic matrix.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   HELPER COMPONENTS
   ═══════════════════════════════════════════════════════════════════════ */
const MetricCard = ({ title, value, icon, color, glow }) => (
  <div className={`bg-[#1e293b] p-6 rounded-3xl shadow-xl border border-slate-700 flex flex-col justify-between hover:-translate-y-1 hover:${glow} transition-all duration-300 relative overflow-hidden`}>
    <div className="absolute -right-4 -top-4 opacity-5 text-white">{icon}</div>
    <div className={`text-[10px] font-black mb-3 flex items-center gap-2 uppercase tracking-widest ${color}`}>
      {icon} {title}
    </div>
    <div className="text-4xl font-black text-white tracking-tighter">{value}</div>
  </div>
);

const ComparisonMetric = ({ label, value, color }) => (
  <div className="bg-[#0f172a] p-5 rounded-2xl border border-slate-800 shadow-inner">
    <p className="text-slate-500 text-[9px] uppercase tracking-widest font-black mb-2">{label}</p>
    <p className={`font-black text-2xl tracking-tight ${color}`}>{value}</p>
  </div>
);