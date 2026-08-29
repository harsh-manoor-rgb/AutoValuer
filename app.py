import streamlit as st
import yfinance as yf
import pandas as pd
from dcf_engine import calculate_dcf

# --- PAGE SETUP ---
st.set_page_config(page_title="AutoValuer Terminal", layout="wide", initial_sidebar_state="collapsed", page_icon="📈")

# --- ANIMATED CSS OVERHAUL ---
st.markdown("""
    <style>
    /* 1. Dashboard Fade-In Animation */
    @keyframes floatUp {
        0% { transform: translateY(30px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }
    
    /* Apply animation to the main block */
    .block-container {
        animation: floatUp 0.8s ease-out forwards;
    }

    /* 2. Moving Gradient Title Animation */
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .main-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(270deg, #00d2ff, #3a7bd5, #00d2ff);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientMove 4s ease infinite;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #8892b0;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 25px;
    }

    /* 3. Interactive Pulsing Metric Cards */
    [data-testid="stMetric"] {
        background-color: rgba(17, 34, 64, 0.7);
        border: 1px solid #233554;
        border-radius: 12px;
        padding: 20px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease-in-out;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) scale(1.02);
        border-color: #00d2ff;
        box-shadow: 0 8px 20px rgba(0, 210, 255, 0.15);
    }

    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.3rem !important;
        font-weight: 800 !important;
    }
    
    /* Clean up the expander box */
    .streamlit-expanderHeader {
        font-size: 1.2rem;
        font-weight: 600;
        color: #00d2ff;
    }
    </style>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown('<div class="main-title">AutoValuer Terminal</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Institutional Equity Valuation & Risk Analytics Engine</div>', unsafe_allow_html=True)

# --- HELPER FUNCTION: DATA FETCHING ---
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
            "g": backup_data["g"], "wacc": backup_data["wacc"], "tg": backup_data["tg"]
        }
    except Exception:
        return backup_data 

# --- DATABASE PRESETS ---
COMPANY_DB = {
    "Tata Motors (TATAMOTORS.NS)": {"ticker": "TATAMOTORS.NS", "backup_price": 980.00, "fcf_base": 21000.0, "cash": 42500.0, "debt": 58000.0, "shares": 367.0, "g": 12.0, "wacc": 10.0, "tg": 4.0},
    "Reliance (RELIANCE.NS)": {"ticker": "RELIANCE.NS", "backup_price": 2950.00, "fcf_base": 65000.0, "cash": 185000.0, "debt": 310000.0, "shares": 676.0, "g": 10.0, "wacc": 10.5, "tg": 4.0},
    "TCS (TCS.NS)": {"ticker": "TCS.NS", "backup_price": 3900.00, "fcf_base": 45000.0, "cash": 10000.0, "debt": 0.0, "shares": 361.0, "g": 8.0, "wacc": 11.0, "tg": 3.0},
    "Custom (Enter your own)": {"ticker": "", "backup_price": 1000.00, "fcf_base": 10000.0, "cash": 5000.0, "debt": 2000.0, "shares": 100.0, "g": 10.0, "wacc": 10.0, "tg": 3.0}
}

# --- THE CONTROL DESK ---
with st.expander("⚙️ VALUATION CONTROL DESK", expanded=True):
    col_db, col_tick, col_price = st.columns(3)
    with col_db:
        selected_company = st.selectbox("Database Pre-set", list(COMPANY_DB.keys()))
        default_data = COMPANY_DB[selected_company]
    with col_tick:
        user_ticker = st.text_input("Live Ticker (Yahoo Finance)", value=default_data["ticker"])
        live_data = get_company_data(user_ticker, default_data)
    with col_price:
        current_price = st.number_input("Market Price", value=live_data["current_price"])

    st.markdown("---")
    
    col_fcf, col_cash, col_debt, col_shares = st.columns(4)
    with col_fcf:
        fcf_base = st.number_input("Base FCF (Cr)", value=live_data["fcf_base"])
    with col_cash:
        cash = st.number_input("Total Cash (Cr)", value=live_data["cash"])
    with col_debt:
        debt = st.number_input("Total Debt (Cr)", value=live_data["debt"])
    with col_shares:
        shares = st.number_input("Shares Out.", value=live_data["shares"])

    st.markdown("---")
    
    col_g, col_w, col_tg = st.columns(3)
    with col_g:
        growth_rate = st.slider("Growth Rate (%)", 1.0, 30.0, live_data["g"]) / 100
    with col_w:
        discount_rate = st.slider("WACC / Discount Rate (%)", 5.0, 25.0, live_data["wacc"]) / 100
    with col_tg:
        terminal_growth = st.slider("Terminal Growth (%)", 1.0, 10.0, live_data["tg"]) / 100

# --- BULLETPROOF ERROR HANDLING ---
# The logic safely intercepts the WACC mathematical constraint before crashing.
if discount_rate <= terminal_growth:
    st.warning("⚠️ **Mathematical Constraint:** To calculate a valid terminal value, your **WACC (Discount Rate)** must be strictly greater than your **Terminal Growth Rate**. Please adjust the sliders above.")
else:
    # --- ENGINE EXECUTION ---
    results = calculate_dcf(fcf_base, cash, debt, shares, current_price, growth_rate, discount_rate, terminal_growth)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TOP METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Intrinsic Value", f"₹ {results['intrinsic_value']:,.2f}")
    col2.metric("Market Price", f"₹ {current_price:,.2f}")
    
    if results["is_undervalued"]:
        col3.metric("Verdict", "🟢 UNDERVALUED", f"{results['diff_percentage']:.1f}% Upside")
    else:
        col3.metric("Verdict", "🔴 OVERVALUED", f"{results['diff_percentage']:.1f}% Downside")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- THE 4-TAB DASHBOARD ---
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Breakdown", "📈 Projections", "🎯 Risk Matrix", "🤖 AI Analyst"])

    with tab1:
        st.subheader("Enterprise & Equity Valuation")
        summary_df = pd.DataFrame({
            "Metric": ["5-Year Cash Flow PV", "Terminal Value PV", "Enterprise Value", "Net Cash / (Debt)", "Equity Value"],
            "Value (Cr)": [f"{results['sum_pv_5yr_cr']:,.2f}", f"{results['pv_terminal_value_cr']:,.2f}", f"{results['enterprise_value_cr']:,.2f}", f"{results['net_cash_cr']:,.2f}", f"{results['equity_value_cr']:,.2f}"]
        })
        st.table(summary_df)

    with tab2:
        st.subheader("5-Year Trajectory")
        projected_fcfs = [fcf_base * (1 + growth_rate)**year for year in range(1, 6)]
        chart_data = pd.DataFrame({"Year": [f"Year {i}" for i in range(1, 6)], "FCF": projected_fcfs}).set_index("Year")
        st.bar_chart(chart_data, use_container_width=True)

    with tab3:
        st.subheader("Institutional Risk Heatmap")
        wacc_steps = [discount_rate - 0.02, discount_rate - 0.01, discount_rate, discount_rate + 0.01, discount_rate + 0.02]
        g_steps = [growth_rate + 0.02, growth_rate + 0.01, growth_rate, growth_rate - 0.01, growth_rate - 0.02]
        
        matrix_data = []
        for g in g_steps:
            row = []
            for w in wacc_steps:
                # Secondary safety net for the matrix grid
                if w <= terminal_growth:
                    row.append(None)
                else:
                    try:
                        row.append(calculate_dcf(fcf_base, cash, debt, shares, current_price, g, w, terminal_growth)['intrinsic_value'])
                    except:
                        row.append(None)
            matrix_data.append(row)

        df_matrix = pd.DataFrame(matrix_data, columns=[f"{w*100:.1f}%" for w in wacc_steps], index=[f"{g*100:.1f}%" for g in g_steps])
        styled_matrix = df_matrix.style.format(lambda v: "N/A" if pd.isna(v) else f"{v:,.2f}").background_gradient(cmap="RdYlGn", axis=None)
        st.dataframe(styled_matrix, use_container_width=True)
        
        st.divider()
        csv = df_matrix.to_csv().encode('utf-8')
        st.download_button("💾 Export Matrix to CSV", data=csv, file_name='Risk_Matrix.csv', mime='text/csv')

    with tab4:
        st.subheader("Automated AI Explainer")
        with st.chat_message("assistant"):
            st.write("Hello! I am the logic engine underlying this terminal. Here is the plain-English breakdown of our current scenario:")
            
            if results["is_undervalued"]:
                st.info(f"**Market Opportunity:** The stock is currently trading at **₹{current_price}**, but based on the company's free cash flow, the true intrinsic value is **₹{results['intrinsic_value']:,.2f}**. Because the market price is lower than the true value, this asset is **Undervalued by {results['diff_percentage']:.1f}%**.")
            else:
                st.info(f"**Market Opportunity:** The stock is currently trading at **₹{current_price}**, but based on the company's free cash flow, the true intrinsic value is only **₹{results['intrinsic_value']:,.2f}**. Because the market price is higher than the true value, this asset is **Overvalued by {results['diff_percentage']:.1f}%**.")
                
            st.write(f"**The Mathematical Assumptions:**")
            st.write(f"- We are projecting the company's cash flow will grow by **{growth_rate*100:.1f}%** per year for the next 5 years.")
            st.write(f"- We are applying a **{discount_rate*100:.1f}%** discount rate (WACC) to account for the risk and the time value of money.")
            st.write(f"- After year 5, we assume the company will grow at a stable **{terminal_growth*100:.1f}%** into perpetuity.")
