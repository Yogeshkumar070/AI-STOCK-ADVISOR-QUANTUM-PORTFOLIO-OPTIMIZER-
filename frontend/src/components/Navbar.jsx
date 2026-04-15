/* ═══════════════════════════════════════════════════════════════════════
   Navbar.jsx — Premium AI Stock Advisor Navigation
   ═══════════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from "react";
import {
  LayoutDashboard, Activity, LineChart, TrendingUp, BrainCircuit,
  Cpu, Clock
} from "lucide-react";
import TickerBar from "./TickerBar";

const TABS = [
  { id: "Overview",     icon: LayoutDashboard },
  { id: "Fundamentals", icon: Activity        },
  { id: "Technicals",   icon: LineChart       },
  { id: "Prediction",   icon: TrendingUp      },
  { id: "Quantum",      icon: BrainCircuit    },
];

/* --- Real-Time NSE Market Status Logic (IST) --- */
const getMarketStatus = () => {
  const now = new Date();
  // Convert current time to India Standard Time (IST)
  const istString = now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" });
  const istDate = new Date(istString);
  
  const day = istDate.getDay(); // 0 = Sun, 1 = Mon, ..., 6 = Sat
  const hours = istDate.getHours();
  const minutes = istDate.getMinutes();
  const timeInHours = hours + (minutes / 60);

  // NSE Trading Hours: Mon-Fri, 9:15 AM (9.25) to 3:30 PM (15.5)
  const isWeekday = day >= 1 && day <= 5;
  const isOpenTime = timeInHours >= 9.25 && timeInHours < 15.5;

  if (isWeekday && isOpenTime) {
    return { 
      isOpen: true, 
      text: "MARKET OPEN", 
      color: "text-emerald-700", 
      bg: "bg-emerald-50", 
      border: "border-emerald-200", 
      dot: "bg-emerald-500" 
    };
  } else {
    return { 
      isOpen: false, 
      text: "MARKET CLOSED", 
      color: "text-slate-600", 
      bg: "bg-slate-100", 
      border: "border-slate-200", 
      dot: "bg-slate-400" 
    };
  }
};

export default function Navbar({ activeTab, setActiveTab, onTickerClick }) {
  const [marketStatus, setMarketStatus] = useState(getMarketStatus());

  // Update market status every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setMarketStatus(getMarketStatus());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="sticky top-0 z-50">
      {/* ── scrolling Nifty 50 ticker strip ── */}
      <TickerBar onSymbolClick={onTickerClick} />

      {/* ── MAIN NAV BAR ── */}
      <header className="bg-white/90 backdrop-blur-xl border-b border-slate-200 shadow-sm">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6">
          <div className="flex h-[72px] items-center justify-between gap-8">

            {/* LEFT — Premium AI Branding */}
            <div className="flex items-center gap-3 flex-shrink-0 cursor-pointer" onClick={() => setActiveTab("Overview")}>
              <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#0066FF] to-blue-800 text-white flex items-center justify-center shadow-[0_4px_15px_rgba(0,102,255,0.3)]">
                <Cpu size={22} strokeWidth={2.5} />
              </div>
              <div className="flex flex-col justify-center">
                <span className="text-[20px] font-black tracking-tight leading-none text-slate-900 flex items-center gap-1">
                  <span className="text-[#0066FF]">AI</span> Stock Advisor
                </span>
                <span className="text-[9px] font-extrabold tracking-[0.25em] text-slate-400 uppercase mt-0.5">
                  Institutional Terminal
                </span>
              </div>
            </div>

            {/* CENTER — Flat UI Nav Links */}
            <nav className="hidden lg:flex items-center gap-2 flex-1 justify-center h-full">
              {TABS.map(({ id, icon: Icon }) => {
                const isActive = activeTab === id;
                return (
                  <button
                    key={id}
                    onClick={() => setActiveTab(id)}
                    className={`
                      relative flex items-center gap-2 px-5 h-full text-[14px] font-bold transition-all duration-200
                      ${isActive
                        ? "text-[#0066FF] bg-blue-50/50"
                        : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                      }
                    `}
                  >
                    <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                    {id}
                    {/* Active Bottom Indicator Line */}
                    {isActive && (
                      <span className="absolute bottom-0 left-0 right-0 h-[3px] rounded-t-md bg-[#0066FF] shadow-[0_-2px_10px_rgba(0,102,255,0.4)]" />
                    )}
                  </button>
                );
              })}
            </nav>

            {/* RIGHT — Dynamic Market Pill */}
            <div className="flex items-center flex-shrink-0">
              
              {/* Dynamic Market Status Indicator */}
              <div className={`hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full border shadow-sm ${marketStatus.bg} ${marketStatus.border}`}>
                {marketStatus.isOpen ? (
                  <span className="relative flex h-2 w-2">
                    <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${marketStatus.dot}`} />
                    <span className={`relative inline-flex h-2 w-2 rounded-full ${marketStatus.dot}`} />
                  </span>
                ) : (
                  <Clock size={12} className={marketStatus.color} strokeWidth={3} />
                )}
                <span className={`text-[10px] font-black tracking-widest uppercase ${marketStatus.color}`}>
                  {marketStatus.text}
                </span>
              </div>

            </div>

          </div>
        </div>
      </header>
    </div>
  );
}
