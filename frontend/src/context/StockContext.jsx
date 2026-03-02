import { createContext, useContext, useState } from "react";

const StockContext = createContext();

export const StockProvider = ({ children }) => {
  // 1. GLOBAL STATE: This data survives when tabs change
  const [symbol, setSymbol] = useState("");
  const [stockData, setStockData] = useState(null); // Holds Market Cap, PE, etc.
  const [priceData, setPriceData] = useState([]);   // Holds Graph Data
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const value = {
    symbol, setSymbol,
    stockData, setStockData,
    priceData, setPriceData,
    loading, setLoading,
    error, setError
  };

  return (
    <StockContext.Provider value={value}>
      {children}
    </StockContext.Provider>
  );
};

export const useStock = () => useContext(StockContext);