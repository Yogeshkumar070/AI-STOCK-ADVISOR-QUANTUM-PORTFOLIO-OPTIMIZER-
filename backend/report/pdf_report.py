from fpdf import FPDF

def generate_pdf_report(result):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Quantum Portfolio Report", ln=True)

    pdf.cell(0, 10, f"Selected Stocks: {', '.join(result['tickers'])}", ln=True)
    pdf.cell(0, 10, f"Expected Return: {result['metrics']['expected_return']}%", ln=True)
    pdf.cell(0, 10, f"Volatility: {result['metrics']['portfolio_volatility']}%", ln=True)
    pdf.cell(0, 10, f"Sharpe Ratio: {result['metrics']['sharpe_ratio']}", ln=True)

    path = "data/reports/quantum_portfolio_report.pdf"
    pdf.output(path)

    return path
