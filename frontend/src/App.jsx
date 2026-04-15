import { useState } from "react";
import Navbar from "./components/Navbar";

import Overview from "./pages/Overview";
import Fundamentals from "./pages/Fundamentals";
import Technicals from "./pages/Technicals";
import Prediction from "./pages/Prediction";
import Quantum from "./pages/Quantum";

export default function App() {
  const [activeTab, setActiveTab] = useState("Overview");
  const isOverview = activeTab === "Overview";

  return (
    <div className="min-h-screen">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className={isOverview ? "w-full" : "max-w-7xl mx-auto px-8 pt-24 pb-12"}>
        {/* No props needed! They all read from StockContext now */}
        {activeTab === "Overview" && <Overview />}
        {activeTab === "Fundamentals" && <Fundamentals />}
        {activeTab === "Technicals" && <Technicals />}
        {activeTab === "Prediction" && <Prediction />}
        {activeTab === "Quantum" && <Quantum />}
      </main>
    </div>
  );
}
