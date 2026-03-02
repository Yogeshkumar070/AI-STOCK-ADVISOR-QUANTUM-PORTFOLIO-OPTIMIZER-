/**
 * SCORING ENGINE
 * Converts raw financial metrics into a 0-100 normalized score.
 * Handles null/undefined values by returning a neutral 50 score.
 */

export const scoreROE = (roe) => {
    // ROE is often returned as 0.15 (15%) or 15. We handle both.
    if (roe == null) return 50;
    
    // Normalize: if > 1, assume it's a percentage (e.g., 15), so divide by 100
    const val = roe > 1 ? roe / 100 : roe;

    if (val >= 0.20) return 95; // >20% is Excellent
    if (val >= 0.15) return 80; // >15% is Good
    if (val >= 0.10) return 60; // >10% is Average
    return 40; // <10% is Poor
};

export const scorePE = (pe) => {
    if (!pe) return 50;
    
    // Lower P/E is generally better (value investing)
    // But too low (<5) might indicate distress, though we'll simplify here.
    if (pe < 15) return 90; // Cheap
    if (pe < 25) return 75; // Fair
    if (pe < 40) return 55; // Expensive
    return 30; // Very Expensive
};

export const scoreDebtEquity = (de) => {
    if (de == null) return 50;
    
    if (de < 0.5) return 90; // Low Debt (Great)
    if (de < 1.0) return 70; // Moderate Debt (Okay)
    if (de < 2.0) return 40; // High Debt (Risky)
    return 20; // Very High Debt (Dangerous)
};

export const scoreGrowth = (revenue, profit) => {
    // A simple proxy: Net Profit Margin (Profit / Revenue)
    if (!revenue || !profit) return 50;
    
    const margin = profit / revenue;
    
    if (margin > 0.20) return 90; // 20% Margin is huge
    if (margin > 0.10) return 75; // 10% is healthy
    if (margin > 0.05) return 60;
    return 40;
};

export const getRatingColor = (score) => {
    if (score >= 80) return "green";
    if (score >= 60) return "blue";
    if (score >= 40) return "yellow";
    return "red";
};