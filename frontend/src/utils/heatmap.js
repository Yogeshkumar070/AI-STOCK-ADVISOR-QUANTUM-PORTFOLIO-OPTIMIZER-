// utils/heatmap.js
export function buildHeatmapData(corrMatrix) {
  const stocks = Object.keys(corrMatrix);
  const data = [];

  stocks.forEach((row, i) => {
    stocks.forEach((col, j) => {
      data.push({
        x: i,
        y: j,
        value: corrMatrix[row][col],
        rowLabel: row,
        colLabel: col
      });
    });
  });

  return { data, stocks };
}
