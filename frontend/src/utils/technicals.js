export function calculateRSI(data, period = 14) {
  let gains = 0;
  let losses = 0;
  const rsi = [];

  for (let i = 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close;
    if (diff >= 0) gains += diff;
    else losses -= diff;

    if (i >= period) {
      const rs = gains / (losses || 1);
      rsi.push(100 - 100 / (1 + rs));
    } else {
      rsi.push(null);
    }
  }

  return rsi;
}

export function calculateEMA(data, period) {
  const k = 2 / (period + 1);
  let ema = data[0].close;
  return data.map(d => {
    ema = d.close * k + ema * (1 - k);
    return ema;
  });
}

export function calculateMACD(data) {
  const ema12 = calculateEMA(data, 12);
  const ema26 = calculateEMA(data, 26);
  const macd = ema12.map((v, i) => v - ema26[i]);
  const signal = calculateEMA(
    macd.map(v => ({ close: v })), 9
  );
  return { macd, signal };
}
