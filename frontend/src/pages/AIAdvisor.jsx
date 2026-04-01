/* ═══════════════════════════════════════════════════════════════════════
   AIAdvisor.jsx — Management Credibility Score + Bull vs Bear Debate
   ═══════════════════════════════════════════════════════════════════════ */
import React, { useState } from "react";
import { useStock } from "../context/StockContext";
import {
  Brain, TrendingUp, TrendingDown, Zap, Shield, Target,
  ChevronRight, AlertTriangle, CheckCircle, XCircle,
  BarChart2, Scale, Swords, Award, Loader, Star,
  ArrowUpRight, ArrowDownRight, Minus
} from "lucide-react";

const API = "http://127.0.0.1:8000";

/* ── Circular Score Gauge ─────────────────────────────────────────── */
function ScoreGauge({ score, size = 140 }) {
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = (score / 100) * circumference;
  const gap = circumference - filled;

  const color =
    score >= 80 ? "#10b981"   // emerald
    : score >= 65 ? "#3b82f6" // blue
    : score >= 45 ? "#f59e0b" // amber
    : score >= 25 ? "#f97316" // orange
    : "#ef4444";              // red

  return (
    <svg width={size} height={size} className="drop-shadow-sm">
      {/* Track */}
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" stroke="#e2e8f0" strokeWidth="10"
      />
      {/* Progress */}
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" stroke={color} strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${gap}`}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dasharray 1s ease" }}
      />
      {/* Score text */}
      <text x="50%" y="46%" textAnchor="middle" dominantBaseline="middle"
        fontSize="28" fontWeight="800" fill={color}>
        {score}
      </text>
      <text x="50%" y="66%" textAnchor="middle" dominantBaseline="middle"
        fontSize="10" fontWeight="700" fill="#94a3b8">
        / 100
      </text>
    </svg>
  );
}

/* ── Factor Score Bar ─────────────────────────────────────────────── */
function FactorBar({ label, score, color }) {
  return (
    <div className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-semibold text-slate-600">{label}</span>
        <span className="text-xs font-black text-slate-800">{score}</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

/* ── Verdict Badge ─────────────────────────────────────────────────── */
function VerdictBadge({ verdict }) {
  const map = {
    EXCELLENT: { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" },
    STRONG:    { bg: "bg-blue-50",    text: "text-blue-700",    border: "border-blue-200" },
    MODERATE:  { bg: "bg-amber-50",   text: "text-amber-700",   border: "border-amber-200" },
    WEAK:      { bg: "bg-orange-50",  text: "text-orange-700",  border: "border-orange-200" },
    POOR:      { bg: "bg-red-50",     text: "text-red-700",     border: "border-red-200" },
  };
  const s = map[verdict] || map.MODERATE;
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest border ${s.bg} ${s.text} ${s.border}`}>
      {verdict}
    </span>
  );
}

/* ── Action Badge ──────────────────────────────────────────────────── */
function ActionBadge({ action }) {
  const map = {
    "STRONG BUY":  { bg: "bg-emerald-600", text: "text-white" },
    "BUY":         { bg: "bg-emerald-500", text: "text-white" },
    "ACCUMULATE":  { bg: "bg-blue-500",    text: "text-white" },
    "HOLD":        { bg: "bg-amber-500",   text: "text-white" },
    "REDUCE":      { bg: "bg-orange-500",  text: "text-white" },
    "SELL":        { bg: "bg-red-500",     text: "text-white" },
    "STRONG SELL": { bg: "bg-red-700",     text: "text-white" },
  };
  const s = map[action] || { bg: "bg-slate-500", text: "text-white" };
  return (
    <span className={`px-4 py-1.5 rounded-lg text-sm font-black uppercase tracking-widest ${s.bg} ${s.text}`}>
      {action}
    </span>
  );
}

/* ── Conviction Bar ────────────────────────────────────────────────── */
function ConvictionBar({ value }) {
  // value: -100 (fully bearish) to +100 (fully bullish)
  const pct = ((value + 100) / 200) * 100;
  const color = value >= 20 ? "#10b981" : value >= -20 ? "#f59e0b" : "#ef4444";
  return (
    <div>
      <div className="flex justify-between text-[10px] font-bold text-slate-400 mb-1">
        <span>BEARISH</span>
        <span>NEUTRAL</span>
        <span>BULLISH</span>
      </div>
      <div className="relative h-3 bg-gradient-to-r from-red-100 via-amber-50 to-emerald-100 rounded-full overflow-hidden border border-slate-200">
        {/* Center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-300" />
        {/* Marker */}
        <div
          className="absolute top-0 bottom-0 w-3 rounded-full shadow-md transition-all duration-700"
          style={{ left: `calc(${pct}% - 6px)`, backgroundColor: color }}
        />
      </div>
      <div className="text-center mt-1">
        <span className="text-xs font-black" style={{ color }}>
          {value > 0 ? `+${value}` : value} Net Conviction
        </span>
      </div>
    </div>
  );
}

/* ── Argument Card ─────────────────────────────────────────────────── */
function ArgumentCard({ arg, side, index }) {
  const isBull = side === "bull";
  return (
    <div className={`p-4 rounded-xl border mb-3 ${isBull ? "border-emerald-100 bg-emerald-50/40" : "border-red-100 bg-red-50/40"}`}>
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-black ${isBull ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
          {index}
        </div>
        <div>
          <p className={`text-[13px] font-bold mb-1 ${isBull ? "text-emerald-800" : "text-red-800"}`}>
            {arg.point}
          </p>
          <p className="text-[12px] text-slate-600 leading-relaxed">{arg.detail}</p>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════════════════ */
export default function AIAdvisor() {
  const { symbol } = useStock();
  const [loading, setLoading] = useState(false);
  const [mcsData, setMcsData] = useState(null);
  const [debateData, setDebateData] = useState(null);
  const [error, setError] = useState("");
  const [loadingStep, setLoadingStep] = useState("");

  const runAnalysis = async () => {
    if (!symbol) return;
    setLoading(true);
    setError("");
    setMcsData(null);
    setDebateData(null);

    try {
      setLoadingStep("Fetching management history & earnings data...");
      const [mcsRes, debateRes] = await Promise.all([
        fetch(`${API}/ai/management-score/${symbol}`),
        fetch(`${API}/ai/debate/${symbol}`),
      ]);

      setLoadingStep("Running AI analysis...");

      if (!mcsRes.ok) {
        const err = await mcsRes.json();
        throw new Error(err.detail || "Management score analysis failed");
      }
      if (!debateRes.ok) {
        const err = await debateRes.json();
        throw new Error(err.detail || "Debate engine failed");
      }

      const [mcs, debate] = await Promise.all([mcsRes.json(), debateRes.json()]);
      setMcsData(mcs);
      setDebateData(debate);
    } catch (e) {
      setError(e.message || "AI analysis failed. Please try again.");
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  /* ── No stock selected ─────────────────────────────────────────── */
  if (!symbol) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center mb-5 shadow-lg">
          <Brain size={32} className="text-white" />
        </div>
        <h2 className="text-2xl font-black text-slate-800 mb-2">AI Advisor</h2>
        <p className="text-slate-500 text-sm max-w-xs">
          Search for a stock in the <strong>Overview</strong> tab first, then come back here to run the AI analysis.
        </p>
      </div>
    );
  }

  /* ── Loading state ─────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <div className="relative mb-6">
          <div className="w-20 h-20 rounded-full border-4 border-blue-100 flex items-center justify-center">
            <Brain size={36} className="text-blue-500" />
          </div>
          <div className="absolute inset-0 rounded-full border-4 border-t-blue-500 animate-spin" />
        </div>
        <h3 className="text-xl font-black text-slate-800 mb-2">AI is thinking...</h3>
        <p className="text-sm text-slate-500 max-w-sm">{loadingStep}</p>
        <p className="text-xs text-slate-400 mt-2">This takes 15–30 seconds. Claude is analyzing {symbol} in depth.</p>
      </div>
    );
  }

  /* ── CTA before analysis ──────────────────────────────────────── */
  const showCTA = !mcsData && !debateData && !loading;

  return (
    <div className="space-y-8">

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center shadow-md">
            <Brain size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900">AI Advisor</h1>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-widest">
              Management Credibility · Bull vs Bear Debate · {symbol}
            </p>
          </div>
        </div>

        <button
          onClick={runAnalysis}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 text-white font-bold text-sm shadow-lg hover:shadow-xl hover:from-violet-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Zap size={16} />
          {mcsData ? "Re-run Analysis" : "Run AI Analysis"}
        </button>
      </div>

      {/* ── Error ────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm font-semibold">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      {/* ── CTA Banner ───────────────────────────────────────────── */}
      {showCTA && (
        <div className="bg-gradient-to-br from-slate-900 via-violet-950 to-blue-950 rounded-2xl p-8 text-white">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Star size={16} className="text-yellow-400" />
                <span className="text-xs font-black uppercase tracking-widest text-slate-400">Powered by Claude AI</span>
              </div>
              <h2 className="text-2xl font-black mb-2">Deep AI Analysis for <span className="text-blue-400">{symbol}</span></h2>
              <p className="text-slate-400 text-sm max-w-lg">
                Two AI features in one click: a <strong className="text-white">Management Credibility Score</strong> that tracks how
                well management delivers on expectations, and a <strong className="text-white">Bull vs Bear Debate</strong> where
                two AI analysts argue the stock from opposing sides.
              </p>
            </div>
            <div className="flex gap-4 flex-shrink-0">
              <div className="text-center">
                <div className="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center mb-2 mx-auto">
                  <Shield size={24} className="text-blue-400" />
                </div>
                <p className="text-[11px] font-bold text-slate-400">Credibility<br/>Score</p>
              </div>
              <div className="text-center">
                <div className="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center mb-2 mx-auto">
                  <Swords size={24} className="text-violet-400" />
                </div>
                <p className="text-[11px] font-bold text-slate-400">Bull vs Bear<br/>Debate</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════
          SECTION 1: Management Credibility Score
          ════════════════════════════════════════════════════════════ */}
      {mcsData && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Section header */}
          <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <Shield size={18} className="text-blue-600" />
            <h2 className="text-base font-black text-slate-800 uppercase tracking-wider">Management Credibility Score</h2>
            <div className="ml-auto flex items-center gap-2">
              <VerdictBadge verdict={mcsData.verdict} />
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                mcsData.trend === "IMPROVING" ? "bg-emerald-50 text-emerald-600" :
                mcsData.trend === "STABLE"    ? "bg-blue-50 text-blue-600" :
                                                "bg-red-50 text-red-600"
              }`}>
                {mcsData.trend === "IMPROVING" ? "↑" : mcsData.trend === "STABLE" ? "→" : "↓"} {mcsData.trend}
              </span>
            </div>
          </div>

          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Score Gauge */}
            <div className="flex flex-col items-center justify-center py-4">
              <ScoreGauge score={mcsData.score} />
              <p className="mt-3 text-xs font-black uppercase tracking-widest text-slate-500">Overall Score</p>
              <div className="mt-3 grid grid-cols-2 gap-2 w-full">
                <div className="text-center bg-slate-50 rounded-lg p-2 border border-slate-100">
                  <p className="text-[10px] text-slate-400 font-semibold mb-0.5">Beat Rate</p>
                  <p className="text-xs font-black text-slate-800">{mcsData.beat_rate}</p>
                </div>
                <div className="text-center bg-slate-50 rounded-lg p-2 border border-slate-100">
                  <p className="text-[10px] text-slate-400 font-semibold mb-0.5">Avg Surprise</p>
                  <p className={`text-xs font-black ${mcsData.avg_surprise_pct?.startsWith("+") ? "text-emerald-600" : "text-red-600"}`}>
                    {mcsData.avg_surprise_pct}
                  </p>
                </div>
              </div>
            </div>

            {/* Factor Breakdown */}
            <div>
              <h3 className="text-xs font-black uppercase tracking-widest text-slate-500 mb-4">Factor Breakdown</h3>
              <FactorBar label="Earnings Delivery" score={mcsData.earnings_delivery_score} color="#3b82f6" />
              <FactorBar label="Revenue Consistency" score={mcsData.revenue_consistency_score} color="#8b5cf6" />
              <FactorBar label="Financial Discipline" score={mcsData.financial_discipline_score} color="#10b981" />
              <FactorBar label="Analyst Confidence" score={mcsData.analyst_confidence_score} color="#f59e0b" />
            </div>

            {/* Strengths & Concerns */}
            <div className="space-y-4">
              <div>
                <h3 className="text-xs font-black uppercase tracking-widest text-emerald-600 mb-2 flex items-center gap-1">
                  <CheckCircle size={12} /> Key Strengths
                </h3>
                <ul className="space-y-1.5">
                  {mcsData.key_strengths?.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-700">
                      <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-xs font-black uppercase tracking-widest text-red-500 mb-2 flex items-center gap-1">
                  <XCircle size={12} /> Key Concerns
                </h3>
                <ul className="space-y-1.5">
                  {mcsData.key_concerns?.map((c, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-700">
                      <span className="text-red-400 mt-0.5 flex-shrink-0">✗</span>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Summary & Investor Note */}
          <div className="px-6 pb-6 space-y-3">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <p className="text-[11px] font-black uppercase tracking-widest text-slate-400 mb-1">Credibility Analysis</p>
              <p className="text-sm text-slate-700 leading-relaxed">{mcsData.credibility_summary}</p>
            </div>
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <p className="text-[11px] font-black uppercase tracking-widest text-blue-400 mb-1 flex items-center gap-1">
                <Target size={11} /> Investor Note
              </p>
              <p className="text-sm text-blue-800 font-semibold leading-relaxed">{mcsData.investor_note}</p>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════
          SECTION 2: Bull vs Bear Debate
          ════════════════════════════════════════════════════════════ */}
      {debateData && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Section header */}
          <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <Swords size={18} className="text-violet-600" />
            <div>
              <h2 className="text-base font-black text-slate-800 uppercase tracking-wider">AI Bull vs Bear Debate</h2>
              <p className="text-xs text-slate-500 italic">{debateData.debate_title}</p>
            </div>
            <div className="ml-auto">
              <ActionBadge action={debateData.moderator_verdict?.suggested_action} />
            </div>
          </div>

          {/* Bull vs Bear columns */}
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* BULL */}
            <div className="rounded-xl border border-emerald-200 bg-gradient-to-b from-emerald-50/60 to-white overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-emerald-100 bg-emerald-50">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                  <TrendingUp size={16} className="text-emerald-700" />
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-emerald-600">Bull Analyst</p>
                  <p className="text-xs font-bold text-emerald-800 leading-tight">{debateData.bull_opening?.headline}</p>
                </div>
              </div>
              <div className="p-4">
                {/* Price target */}
                <div className="flex justify-between items-center mb-4 p-3 bg-emerald-50 rounded-lg border border-emerald-100">
                  <div>
                    <p className="text-[10px] text-emerald-600 font-bold uppercase">12-mo Target</p>
                    <p className="text-lg font-black text-emerald-700">{debateData.bull_opening?.price_target}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-emerald-600 font-bold uppercase">Upside</p>
                    <p className="text-base font-black text-emerald-700 flex items-center gap-1">
                      <ArrowUpRight size={14} />+{debateData.bull_opening?.upside_pct}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-emerald-600 font-bold uppercase">Conviction</p>
                    <p className="text-base font-black text-emerald-700">{debateData.bull_opening?.confidence}%</p>
                  </div>
                </div>

                <ArgumentCard arg={debateData.bull_opening?.argument_1} side="bull" index={1} />
                <ArgumentCard arg={debateData.bull_opening?.argument_2} side="bull" index={2} />
                <ArgumentCard arg={debateData.bull_opening?.argument_3} side="bull" index={3} />
              </div>
            </div>

            {/* BEAR */}
            <div className="rounded-xl border border-red-200 bg-gradient-to-b from-red-50/60 to-white overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-red-100 bg-red-50">
                <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                  <TrendingDown size={16} className="text-red-700" />
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-red-600">Bear Analyst</p>
                  <p className="text-xs font-bold text-red-800 leading-tight">{debateData.bear_opening?.headline}</p>
                </div>
              </div>
              <div className="p-4">
                {/* Price target */}
                <div className="flex justify-between items-center mb-4 p-3 bg-red-50 rounded-lg border border-red-100">
                  <div>
                    <p className="text-[10px] text-red-600 font-bold uppercase">12-mo Target</p>
                    <p className="text-lg font-black text-red-700">{debateData.bear_opening?.price_target}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-red-600 font-bold uppercase">Downside</p>
                    <p className="text-base font-black text-red-700 flex items-center gap-1">
                      <ArrowDownRight size={14} />-{debateData.bear_opening?.downside_pct}%
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-red-600 font-bold uppercase">Conviction</p>
                    <p className="text-base font-black text-red-700">{debateData.bear_opening?.confidence}%</p>
                  </div>
                </div>

                <ArgumentCard arg={debateData.bear_opening?.argument_1} side="bear" index={1} />
                <ArgumentCard arg={debateData.bear_opening?.argument_2} side="bear" index={2} />
                <ArgumentCard arg={debateData.bear_opening?.argument_3} side="bear" index={3} />
              </div>
            </div>
          </div>

          {/* Rebuttals */}
          <div className="px-6 pb-4">
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200">
                <p className="text-[11px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-1.5">
                  <BarChart2 size={12} /> Cross-Examination · Rebuttals
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp size={13} className="text-emerald-600" />
                    <p className="text-[11px] font-black uppercase tracking-wider text-emerald-600">Bull Rebuttal</p>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">{debateData.bull_rebuttal}</p>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingDown size={13} className="text-red-600" />
                    <p className="text-[11px] font-black uppercase tracking-wider text-red-600">Bear Rebuttal</p>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">{debateData.bear_rebuttal}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Moderator Verdict */}
          {debateData.moderator_verdict && (
            <div className="px-6 pb-6">
              <div className={`rounded-xl overflow-hidden border ${
                debateData.moderator_verdict.winner === "BULL" ? "border-emerald-200 bg-gradient-to-br from-emerald-50 to-white" :
                debateData.moderator_verdict.winner === "BEAR" ? "border-red-200 bg-gradient-to-br from-red-50 to-white" :
                                                                  "border-amber-200 bg-gradient-to-br from-amber-50 to-white"
              }`}>
                <div className={`flex items-center gap-3 px-5 py-3 border-b ${
                  debateData.moderator_verdict.winner === "BULL" ? "border-emerald-100 bg-emerald-50" :
                  debateData.moderator_verdict.winner === "BEAR" ? "border-red-100 bg-red-50" :
                                                                    "border-amber-100 bg-amber-50"
                }`}>
                  <Award size={16} className={
                    debateData.moderator_verdict.winner === "BULL" ? "text-emerald-600" :
                    debateData.moderator_verdict.winner === "BEAR" ? "text-red-600" : "text-amber-600"
                  } />
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Moderator Verdict</p>
                    <p className={`text-sm font-black ${
                      debateData.moderator_verdict.winner === "BULL" ? "text-emerald-700" :
                      debateData.moderator_verdict.winner === "BEAR" ? "text-red-700" : "text-amber-700"
                    }`}>
                      {debateData.moderator_verdict.winner === "DRAW" ? "Draw — Equally Balanced" :
                        `${debateData.moderator_verdict.winner} Wins · ${debateData.moderator_verdict.margin}`}
                    </p>
                  </div>
                  <div className="ml-auto flex items-center gap-2">
                    <ActionBadge action={debateData.moderator_verdict.suggested_action} />
                    <span className={`text-[10px] font-black px-2 py-1 rounded-full ${
                      debateData.moderator_verdict.risk_level === "LOW" ? "bg-emerald-100 text-emerald-700" :
                      debateData.moderator_verdict.risk_level === "MODERATE" ? "bg-amber-100 text-amber-700" :
                      debateData.moderator_verdict.risk_level === "HIGH" ? "bg-orange-100 text-orange-700" :
                      "bg-red-100 text-red-700"
                    }`}>
                      {debateData.moderator_verdict.risk_level} RISK
                    </span>
                  </div>
                </div>

                <div className="p-5 space-y-4">
                  <ConvictionBar value={debateData.moderator_verdict.net_conviction} />

                  <div className="bg-white/80 rounded-lg p-3 border border-slate-100">
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Deciding Factor</p>
                    <p className="text-sm font-bold text-slate-800">{debateData.moderator_verdict.key_deciding_factor}</p>
                  </div>

                  <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1.5">Final Analysis</p>
                    <p className="text-sm text-slate-700 leading-relaxed">{debateData.moderator_verdict.verdict_summary}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
