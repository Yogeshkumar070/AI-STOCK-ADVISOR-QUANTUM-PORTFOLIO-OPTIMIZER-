/* * -----------------------------------------------------------------------------
 * TECHNICAL ANALYSIS ENGINE
 * Implements Standard Financial Formulas
 * -----------------------------------------------------------------------------
 */

/**
 * Simple Moving Average (SMA)
 */
export const calculateSMA = (data, windowSize) => {
  let sma = [];
  for (let i = 0; i < data.length; i++) {
      if (i < windowSize - 1) {
          sma.push(null);
          continue;
      }
      let sum = 0;
      for (let j = 0; j < windowSize; j++) {
          sum += data[i - j].close;
      }
      sma.push(sum / windowSize);
  }
  return sma;
};

/**
 * Relative Strength Index (RSI) - Wilder's Smoothing
 */
export const calculateRSI = (data, period = 14) => {
  let rsi = [];
  let gains = [];
  let losses = [];

  for (let i = 1; i < data.length; i++) {
      const change = data[i].close - data[i - 1].close;
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
  }

  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

  for (let i = 0; i < period; i++) rsi.push(null);
  
  let rs = avgGain / (avgLoss || 1);
  rsi.push(100 - (100 / (1 + rs)));

  for (let i = period; i < gains.length; i++) {
      avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
      avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;
      rs = avgGain / (avgLoss || 1);
      rsi.push(100 - (100 / (1 + rs)));
  }
  
  rsi.unshift(null); // Align length
  return rsi;
};

/**
 * MACD (Moving Average Convergence Divergence)
 */
export const calculateMACD = (data) => {
  const calculateEMA = (values, days) => {
      const k = 2 / (days + 1);
      let ema = [values[0]];
      for (let i = 1; i < values.length; i++) {
          ema.push(values[i] * k + ema[i - 1] * (1 - k));
      }
      return ema;
  };

  const closes = data.map(d => d.close);
  const ema12 = calculateEMA(closes, 12);
  const ema26 = calculateEMA(closes, 26);
  
  const macdLine = ema12.map((v, i) => v - ema26[i]);
  const signalLine = calculateEMA(macdLine, 9);
  const histogram = macdLine.map((v, i) => v - signalLine[i]);

  return { macdLine, signalLine, histogram };
};

/**
 * Bollinger Bands
 */
export const calculateBollingerBands = (data, period = 20) => {
    const sma = calculateSMA(data, period);
    const bands = { upper: [], middle: sma, lower: [] };

    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            bands.upper.push(null);
            bands.lower.push(null);
            continue;
        }
        let sumSqDiff = 0;
        const mean = sma[i];
        for (let j = 0; j < period; j++) {
            const diff = data[i - j].close - mean;
            sumSqDiff += diff * diff;
        }
        const stdDev = Math.sqrt(sumSqDiff / period);
        bands.upper.push(mean + (2 * stdDev));
        bands.lower.push(mean - (2 * stdDev));
    }
    return bands;
};

/**
 * Average True Range (ATR)
 */
export const calculateATR = (data, period = 14) => {
    let atr = [];
    let trValues = [];

    for (let i = 0; i < data.length; i++) {
        if (i === 0) {
            trValues.push(data[i].high - data[i].low);
            continue;
        }
        const high = data[i].high;
        const low = data[i].low;
        const prevClose = data[i - 1].close;
        const tr = Math.max(high - low, Math.abs(high - prevClose), Math.abs(low - prevClose));
        trValues.push(tr);
    }

    let sum = 0;
    for(let i=0; i<period; i++) { sum += trValues[i]; atr.push(null); }
    
    let prevATR = sum / period;
    atr.push(prevATR);

    for(let i=period + 1; i<data.length; i++) {
        const currentATR = ((prevATR * (period - 1)) + trValues[i]) / period;
        atr.push(currentATR);
        prevATR = currentATR;
    }
    while(atr.length < data.length) atr.unshift(null); 
    return atr.slice(0, data.length);
};

/**
 * Rate of Change (ROC)
 */
export const calculateROC = (data, period = 12) => {
    let roc = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period) {
            roc.push(null);
            continue;
        }
        const currentPrice = data[i].close;
        const pastPrice = data[i - period].close;
        const rocVal = ((currentPrice - pastPrice) / pastPrice) * 100;
        roc.push(rocVal);
    }
    return roc;
};