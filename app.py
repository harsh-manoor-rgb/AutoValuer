import streamlit as st
import yfinance as yf
import pandas as pd
from dcf_engine import calculate_dcf

# Page Setup
st.set_page_config(page_title="AutoValuer - DCF Dashboard", layout="wide", page_icon="📊")

st.title("📊 AutoValuer: Fully Automated DCF Platform")
st.markdown("Select a database company, or choose **Custom** and type a ticker to automatically pull its full balance sheet!")

# --- HELPER FUNCTION: FETCH ALL FINANCIALS ---
@st.cache_data(ttl=900)
def get_company_data(ticker_symbol, backup_data):
    if not ticker_symbol or ticker_symbol.strip() == "" or ticker_symbol == "CUSTOM":
        return backup_data
    
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        hist = stock.history(period="1d")
        live_price = float(hist['Close'].iloc[-1]) if not hist.empty else backup_data["backup_price"]
        
        raw_fcf = info.get('freeCashflow')
        raw_cash = info.get('totalCash')
        raw_debt = info.get('totalDebt')
        raw_shares = info.get('sharesOutstanding')
        
        return {
            "current_price": live_price,
            "fcf_base": (raw_fcf / 10**7) if raw_fcf is not None else backup_data["fcf_base"],
            "cash": (raw_cash / 10**7) if raw_cash is not None else backup_data["cash"],
            "debt": (raw_debt / 10**7) if raw_debt is not None else backup_data["debt"],
            "shares": (raw_shares / 10**7) if raw_shares is not None else backup_data["shares"],
            "g": backup_data["g"],
            "wacc": backup_data["wacc"],
            "tg": backup_data["tg"]
        }
    except Exception as e:
        return backup_data 

# --- 1. COMPANY DATABASE ---
COMPANY_DB = {
    "Tata Motors (TATAMOTORS.NS)": {
        "ticker": "TATAMOTORS.NS", "backup_price": 980.00,
        "fcf_base": 21000.0, "cash": 42500.0, "debt": 58000.0, "shares": 367.0,
        "g": 12.0, "wacc": 10.0, "tg": 4.0
    },
    "Reliance Industries (RELIANCE.NS)": {
        "ticker": "RELIANCE.NS", "backup_price": 2950.00,
        "fcf_base": 65000.0, "cash": 185000.0, "debt": 310000.0, "shares": 676.0,
        "g": 10.0, "wacc": 10.5, "tg": 4.0
    },
    "TCS (TCS.NS)": {
        "ticker": "TCS.NS", "backup_price": 3900.00,
        "fcf_base": 45000.0, "cash": 10000.0, "debt": 0.0, "shares": 361.0,
        "g": 8.0, "wacc": 11.0, "tg": 3.0
    },
    "Custom (Enter your own)": {
        "ticker": "", "backup_price": 1000.00,
        "fcf_base": 10000.0, "cash": 5000.0, "debt": 2000.0, "shares": 100.0,
        "g": 10.0, "wacc": 10.0, "tg": 3.0
    }
}

# --- 2. SIDEBAR: COMPANY SELECTOR ---
st.sidebar.header("🏢 Select a Company")
selected_company = st.sidebar.selectbox("Choose from database:", list(COMPANY_DB.keys()))
default_data = COMPANY_DB[selected_company]

# --- 3. SIDEBAR: FINANCIAL INPUTS ---
st.sidebar.header("1. Financial Inputs")
user_ticker = st.sidebar.text_input("Stock Ticker (Yahoo Finance)", value=default_data["ticker"])

live_data = get_company_data(user_ticker, default_data)

current_price = st.sidebar.number_input("Current Stock Price", value=live_data["current_price"], min_value=0.01)
fcf_base = st.sidebar.number_input("Base Free Cash Flow (Cr / 10M)", value=live_data["fcf_base"])
cash = st.sidebar.number_input("Cash & Equivalents", value=live_data["cash"])
debt = st.sidebar.number_input("Total Debt", value=live_data["debt"])
shares = st.sidebar.number_input("Shares Outstanding", value=live_data["shares"], min_value=0.01)

st.sidebar.header("2. Valuation Sliders")
growth_rate = st.sidebar.slider("5-Year Annual Growth Rate (%)", min_value=1.0, max_value=30.0, value=live_data["g"]) / 100
discount_rate = st.sidebar.slider("Discount Rate / WACC (%)", min_value=5.0, max_value=20.0, value=live_data["wacc"]) / 100
terminal_growth = st.sidebar.slider("Terminal Growth Rate (%)", min_value=1.0, max_value=6.0, value=live_data["tg"]) / 100

# --- 4. RUN VALUATION ENGINE ---
try:
    results = calculate_dcf(
        fcf_base, cash, debt, shares, current_price,
        growth_rate, discount_rate, terminal_growth
    )

    # --- TOP METRICS DISPLAY ---
    col1, col2, col3 = st.columns(3)

    col1.metric("Calculated Intrinsic Value", f"{results['intrinsic_value']:,.2f}")
    
    if user_ticker and user_ticker.strip() != "":
        col2.metric(f"Live Market Price ({user_ticker})", f"{current_price:,.2f}")
    else:
        col2.metric("Manual Market Price", f"{current_price:,.2f}")

    if results["is_undervalued"]:
        col3.metric("Valuation Verdict", "UNDERVALUED", f"{results['diff_percentage']:.1f}% Upside")
    else:
        col3.metric("Valuation Verdict", "OVERVALUED", f"{results['diff_percentage']:.1f}% Downside")

    st.divider()

    # --- TWO-COLUMN LAYOUT FOR TABLE AND CHART ---
    col_table, col_chart = st.columns([1, 1.2])

    with col_table:
        st.subheader("💡 Enterprise & Equity Breakdown")
        summary_data = {
            "Metric": ["5-Year Cash Flow PV", "Terminal Value PV", "Enterprise Value", "Net Cash / (Debt)", "Equity Value"],
            "Value (Cr / 10M)": [
                f"{results['sum_pv_5yr_cr']:,.2f}",
                f"{results['pv_terminal_value_cr']:,.2f}",
                f"{results['enterprise_value_cr']:,.2f}",
                f"{results['net_cash_cr']:,.2f}",
                f"{results['equity_value_cr']:,.2f}"
            ]
        }
        st.table(summary_data)

    with col_chart:
        st.subheader("📈 Projected Free Cash Flows (Years 1-5)")
        # Calculate nominal cash flows for the chart
        projected_fcfs = [fcf_base * (1 + growth_rate)**year for year in range(1, 6)]
        
        # Create a Pandas DataFrame for Streamlit to chart
        chart_data = pd.DataFrame({
            "Year": ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
            "Free Cash Flow": projected_fcfs
        }).set_index("Year")
        
        # Display the interactive bar chart
        st.bar_chart(chart_data)

except ValueError as e:
    st.error(f"⚠️ {e}")
