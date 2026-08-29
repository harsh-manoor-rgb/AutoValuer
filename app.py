import streamlit as st
import yfinance as yf
import pandas as pd
from dcf_engine import calculate_dcf

# Page Setup
st.set_page_config(page_title="AutoValuer - DCF Dashboard", layout="wide", page_icon="📈")

# --- CUSTOM CSS FOR FINTECH UI ---
st.markdown("""
    <style>
    /* Gradient Hero Title */
    .hero-title {
        background: -webkit-linear-gradient(45deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    
    /* Subtitle Styling */
    .hero-subtitle {
        text-align: center;
        font-size: 1.2em;
        color: #A0AEC0;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* Glowing Metrics */
    [data-testid="stMetricValue"] {
        text-shadow: 0 0 15px rgba(0, 201, 255, 0.4);
        font-weight: bold;
    }
    
    /* Educational Box */
    .edu-box {
        background: rgba(0, 201, 255, 0.05);
        border-left: 4px solid #00C9FF;
        padding: 20px;
        border-radius: 5px;
        margin-top: 30px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown('<h1 class="hero-title">AutoValuer: Pro-Tier DCF</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">🚀 Developed with Pride by Harshdeep Singh. Unlocking Valuation Knowledge Together.</p>', unsafe_allow_html=True)
st.divider()

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

# --- 2. SIDEBAR: INPUTS ---
st.sidebar.header("🏢 Select Asset")
selected_company = st.sidebar.selectbox("Choose from database:", list(COMPANY_DB.keys()))
default_data = COMPANY_DB[selected_company]

st.sidebar.header("1. Financial Inputs")
user_ticker = st.sidebar.text_input("Stock Ticker (Yahoo Finance)", value=default_data["ticker"])
live_data = get_company_data(user_ticker, default_data)

current_price = st.sidebar.number_input("Current Stock Price", value=live_data["current_price"], min_value=0.01)
fcf_base = st.sidebar.number_input("Base Free Cash Flow (Cr / 10M)", value=live_data["fcf_base"])
cash = st.sidebar.number_input("Cash & Equivalents", value=live_data["cash"])
debt = st.sidebar.number_input("Total Debt", value=live_data["debt"])
shares = st.sidebar.number_input("Shares Outstanding", value=live_data["shares"], min_value=0.01)

st.sidebar.header("2. Stress Test Variables")
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
    col2.metric(f"Live Market Price", f"{current_price:,.2f}")

    if results["is_undervalued"]:
        col3.metric("Valuation Verdict", "UNDERVALUED", f"{results['diff_percentage']:.1f}% Upside")
    else:
        col3.metric("Valuation Verdict", "OVERVALUED", f"{results['diff_percentage']:.1f}% Downside")

    st.divider()

    # --- TWO-COLUMN LAYOUT ---
    col_table, col_chart = st.columns([1, 1.2])

    with col_table:
        st.subheader("💡 Enterprise Breakdown")
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
        st.subheader("📈 Projected Growth Engine")
        projected_fcfs = [fcf_base * (1 + growth_rate)**year for year in range(1, 6)]
        chart_data = pd.DataFrame({
            "Year": ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"],
            "Free Cash Flow": projected_fcfs
        }).set_index("Year")
        st.bar_chart(chart_data, use_container_width=True)

    st.divider()

    # --- SENSITIVITY MATRIX ---
    st.subheader("🎯 Institutional Risk Matrix")
    wacc_steps = [discount_rate - 0.02, discount_rate - 0.01, discount_rate, discount_rate + 0.01, discount_rate + 0.02]
    g_steps = [growth_rate + 0.02, growth_rate + 0.01, growth_rate, growth_rate - 0.01, growth_rate - 0.02]

    matrix_data = []
    for g in g_steps:
        row = []
        for w in wacc_steps:
            try:
                if w <= terminal_growth:
                    row.append(None)
                else:
                    res = calculate_dcf(fcf_base, cash, debt, shares, current_price, g, w, terminal_growth)
                    row.append(res['intrinsic_value'])
            except:
                row.append(None)
        matrix_data.append(row)

    col_headers = [f"WACC {w*100:.1f}%" for w in wacc_steps]
    row_headers = [f"Growth {g*100:.1f}%" for g in g_steps]
    df_matrix = pd.DataFrame(matrix_data, columns=col_headers, index=row_headers)

    def format_cells(val):
        if pd.isna(val):
            return "N/A"
        return f"{val:,.2f}"

    styled_matrix = df_matrix.style.format(format_cells).background_gradient(cmap="RdYlGn", axis=None)
    st.dataframe(styled_matrix, use_container_width=True)

    # --- EDUCATIONAL CALLOUT ---
    st.markdown("""
        <div class="edu-box">
            <h4>💡 Why does the Risk Matrix matter?</h4>
            <p>Traditional single-point valuations are highly fragile. By stress-testing the <b>Cost of Capital (WACC)</b> against the <b>Expected Growth Rate</b>, we visualize a "Margin of Safety." Notice how changing the WACC by just 1% dramatically shifts the color of the board? That is because WACC acts as the gravitational pull on long-term terminal value.</p>
        </div>
    """, unsafe_allow_html=True)

except ValueError as e:
    st.error(f"⚠️ {e}")
