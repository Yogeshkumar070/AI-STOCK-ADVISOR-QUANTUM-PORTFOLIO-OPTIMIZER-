import os
import json
from dotenv import load_dotenv

print("--- FINNET ROOT DIAGNOSTIC TOOL ---")

# 1. Test Environment Variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ ROOT CAUSE 1: GOOGLE_API_KEY is missing from your .env file.")
    exit()
else:
    print(f"✅ Found API Key: {api_key[:10]}...")

# 2. Test ChromaDB Connection & Data
try:
    from backend.data.vector_db import collection
except Exception as e:
    try:
        from data.vector_db import collection
    except Exception:
        print(f"❌ ROOT CAUSE 2: Failed to connect to ChromaDB. Error: {e}")
        exit()

TICKER = "HDFCBANK"
print(f"\nSearching ChromaDB for ticker: {TICKER}...")
results = collection.get(where={"ticker": TICKER}, include=["documents", "metadatas"])

if not results or not results.get('documents') or len(results['documents']) == 0:
    print("\n❌ ROOT CAUSE 3: CHROMADB IS EMPTY FOR THIS TICKER.")
    print(f"The AI has no text to read for {TICKER}.")
    print("THE FIX: You must place a PDF inside backend/data/raw_pdfs/HDFCBANK/ and run backend/data/ingestion.py")
    exit()

print(f"✅ ChromaDB has {len(results['documents'])} text chunks for {TICKER}.")
print("Preview of chunk 1:", repr(results['documents'][0][:150] + "..."))

# 3. Test Gemini API Extraction
print("\nSending data to Gemini 1.5 Flash...")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    try:
        from langchain_core.prompts import PromptTemplate
    except ImportError:
        from langchain.prompts import PromptTemplate
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    combined_text = " ".join(results['documents'])
    
    prompt = PromptTemplate.from_template("""
    You are an expert quantitative financial auditor analyzing earnings transcripts for {ticker}.
    Extract ANY forward-looking financial targets, guidance, or projections.
    
    CRITICAL PROXY MAPPING RULES:
    Because our verification engine relies on standardized accounting APIs, you MUST translate management's industry-specific jargon into one of these EXACT keys: 'Total Revenue', 'Operating Income', or 'Net Income'.
    
    - If management discusses "Loan Growth", "Advances Growth", "Credit Growth", "NII", or "Top-line", you MUST map the metric to: "Total Revenue".
    - If management discusses "Profits", "PAT", "Bottom-line", or "Earnings", map it to: "Net Income".
    - If management discusses "EBITDA", "Core Operating Profit", or "Margins", map it to: "Operating Income".
    
    Do NOT extract targets for highly specific ratios (like Cost-to-Income or NPA) as they cannot be verified.
    
    Convert relative time ("next year", "FY22") into an absolute target year. Assume the text is from the 'year_made'.
    
    Output ONLY a valid JSON array of objects. 
    Format: [{{"year_made": 2020, "target_year": 2021, "metric": "Total Revenue", "promised_growth_pct": 15.0, "quote": "We expect our loan book to grow by 15 percent..."}}]
    
    Transcripts: {text}
    """)
    
    response = llm.invoke(prompt.format(ticker=TICKER, text=combined_text))
    print("\n--- RAW GEMINI OUTPUT ---")
    print(response.content)
    print("-------------------------")
    
    clean_json = response.content.replace("```json", "").replace("```", "").strip()
    parsed_json = json.loads(clean_json)
    print(f"✅ SUCCESS: Gemini extracted {len(parsed_json)} promises.")
    
except json.JSONDecodeError:
    print("\n❌ ROOT CAUSE 4: Gemini did not return valid JSON. It returned text.")
    print("THE FIX: The prompt in mcs_engine.py needs to be stricter.")
except Exception as e:
    print(f"\n❌ ROOT CAUSE 5: GEMINI API FAILED. Error: {e}")
