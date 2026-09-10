import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="AutoValuer Terminal", layout="wide", initial_sidebar_state="collapsed", page_icon="📈")

# --- INITIALIZE SESSION STATE ---
if 'app_started' not in st.session_state:
    st.session_state.app_started = False

# --- ULTRA-MODERN IMMERSIVE CSS & ANIMATIONS ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(11, 19, 43, 0.92), rgba(11, 19, 43, 0.96)), 
                          url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=2000&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    @keyframes cinematicEntrance {
        0% { opacity: 0; transform: scale(0.95) translateY(25px); }
        100% { opacity: 1; transform: scale(1.0) translateY(0); }
    }
    .block-container {
        animation: cinematicEntrance 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .landing-title, .main-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 4.2rem;
        font-weight: 900;
        background: linear-gradient(270deg, #00d2ff, #3a7bd5, #00ffcc);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientMove 4s ease infinite;
        text-align: center;
        margin-bottom: 5px;
    }
    .landing-subtitle, .sub-title {
        color: #8892b0;
        font-size: 1.2rem;
        font-weight: 400;
        text-align: center;
        margin-bottom: 40px;
    }
    .feature-box {
        background: rgba(17, 34, 64, 0.85);
        border: 1px solid #233554;
        border-radius: 16px;
        padding: 30px;
        text-align: left;
        height: 190px;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    .feature-box:hover {
        height: 270px;
        transform: translateY(-8px);
        border-color: #00ffcc;
        box-shadow: 0 15px 35px rgba(0, 255, 204, 0.2);
    }
    .hidden-info {
        opacity: 0;
        transform: translateY(10px);
        transition: opacity 0.3s ease, transform 0.3s ease;
        font-size: 0.9rem;
        color: #00ffcc;
        margin-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 10px;
    }
    .feature-box:hover .hidden-info {
        opacity: 1;
        transform: translateY(0);
    }
    .stButton>button {
        width: 100%;
        padding: 14px 28px;
        font-size: 1.1rem;
        font-weight: 600;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: #ffffff;
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 12px;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
        border-color: #60a5fa;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        color: #ffffff !important;
    }
    [data-testid="stMetric"] {
        background-color: rgba(17, 34, 64, 0.8);
        border: 1px solid #233554;
        border-radius: 14px;
        padding: 20px;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) scale(1.02);
        border-color: #00ffcc;
        box-shadow: 0 8px 25px rgba(0, 255, 204, 0.2);
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.3rem !important;
        font-weight: 800 !important;
    }
    table {
        background-color: rgba(17, 34, 64, 0.5) !important;
        border-radius: 10px;
        color: white !important;
    }
    th {
        background-color: rgba(0, 210, 255, 0.1) !important;
        color: #00ffcc !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SELF-CONTAINED DCF ENGINE ---
def calculate_dcf(fcf_base, cash, debt, shares, current_price, g, wacc, tg):
    if wacc <= tg:
        raise ValueError("WACC must be strictly greater than Terminal Growth.")
    
    # Stage 1: 5-Year Growth
    sum_pv_5yr = sum([fcf_base * (1 + g)**t / (1 + wacc)**t for t in range(1, 6)])
    
    # Stage 2: Terminal Value
    base_yr5 = fcf_base * (1 + g)**5
    tv = (base_yr5 * (1 + tg)) / (wacc - tg)
    pv_tv = tv / (1 + wacc)**5
    
    # Bridge to Equity
    ev = sum_pv_5yr + pv_tv
    eq = ev + cash - debt
    intrinsic_value = eq / shares if shares > 0 else 0
    diff = ((intrinsic_value - current_price) / current_price) * 100
    
    return {
        "sum_pv_5yr_cr": sum_pv_5yr,
        "pv_terminal_value_cr": pv_tv,
        "enterprise_value_cr": ev,
        "net_cash_cr": cash - debt,
        "equity_value_cr": eq,
        "intrinsic_value": intrinsic_value,
        "diff_percentage": diff,
        "is_undervalued": intrinsic_value > current_price
    }

# --- ROBUST API FETCHING (NOW WITH CAPM DATA) ---
@st.cache_data(ttl=900)
def get_company_data(ticker_symbol, backup_data):
    if not ticker_symbol or ticker_symbol.strip() == "":
        return backup_data, False
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        hist = stock.history(period="1d")
        live_price = float(hist['Close'].iloc[-1]) if not hist.empty else backup_data["current_price"]
        
        raw_fcf = info.get('freeCashflow')
        raw_cash = info.get('totalCash')
        raw_debt = info.get('totalDebt')
        raw_shares = info.get('sharesOutstanding')
        
        # Live CAPM Data (Beta & Risk-Free Rate)
        live_beta = info.get('beta', 1.0)
        try:
            tnx = yf.Ticker("^TNX") # US 10-Year Treasury
            rf_rate = float(tnx.history(period="1d")['Close'].iloc[-1]) / 100.0
        except:
            rf_rate = 0.042 # Fallback historical average
        
        # CAPM Calculation: Risk Free + Beta * (Market Return Assumed 10% - Risk Free)
        capm_wacc = rf_rate + live_beta * (0.10 - rf_rate)
        
        div = 10**7 if ".NS" in ticker_symbol.upper() or ".BO" in ticker_symbol.upper() else 10**6
        
        return {
            "current_price": live_price,
            "fcf_base": (raw_fcf / div) if raw_fcf is not None else backup_data["fcf_base"],
            "cash": (raw_cash / div) if raw_cash is not None else backup_data["cash"],
            "debt": (raw_debt / div) if raw_debt is not None else backup_data["debt"],
            "shares": (raw_shares / div) if raw_shares is not None else backup_data["shares"],
            "g": backup_data["g"], 
            "wacc": backup_data["wacc"], 
            "tg": backup_data["tg"],
            "capm_wacc": capm_wacc,
            "live_beta": live_beta
        }, True
    except Exception:
        return backup_data, False

# --- COMPREHENSIVE GLOBAL & INDIAN COMPANY DATABASE ---
COMPANY_DB = {
    "Apple Inc. (AAPL)": {"ticker": "AAPL", "current_price": 225.00, "fcf_base": 95000.0, "cash": 150000.0, "debt": 110000.0, "shares": 15200.0, "g": 10.0, "wacc": 8.5, "tg": 3.0, "capm_wacc": 0.085, "live_beta": 1.1},
    "Microsoft Corp. (MSFT)": {"ticker": "MSFT", "current_price": 415.00, "fcf_base": 75000.0, "cash": 80000.0, "debt": 60000.0, "shares": 7430.0, "g": 11.0, "wacc": 8.5, "tg": 3.0, "capm_wacc": 0.085, "live_beta": 1.05},
    "NVIDIA Corp. (NVDA)": {"ticker": "NVDA", "current_price": 125.00, "fcf_base": 50000.0, "cash": 35000.0, "debt": 8500.0, "shares": 24600.0, "g": 20.0, "wacc": 10.0, "tg": 4.0, "capm_wacc": 0.12, "live_beta": 1.7},
    "Tata Motors (TATAMOTORS.NS)": {"ticker": "TATAMOTORS.NS", "current_price": 980.00, "fcf_base": 21000.0, "cash": 42500.0, "debt": 58000.0, "shares": 367.0, "g": 12.0, "wacc": 10.0, "tg": 4.0, "capm_wacc": 0.11, "live_beta": 1.4},
    "Reliance (RELIANCE.NS)": {"ticker": "RELIANCE.NS", "current_price": 2950.00, "fcf_base": 65000.0, "cash": 185000.0, "debt": 310000.0, "shares": 676.0, "g": 10.0, "wacc": 10.5, "tg": 4.0, "capm_wacc": 0.09, "live_beta": 1.0},
    "HDFC Bank (HDFCBANK.NS)": {"ticker": "HDFCBANK.NS", "current_price": 1600.00, "fcf_base": 40000.0, "cash": 150000.0, "debt": 250000.0, "shares": 760.0, "g": 11.0, "wacc": 11.0, "tg": 3.5, "capm_wacc": 0.08, "live_beta": 0.9},
    "Custom Ticker Entry": {"ticker": "", "current_price": 1000.00, "fcf_base": 10000.0, "cash": 5000.0, "debt": 2000.0, "shares": 100.0, "g": 10.0, "wacc": 10.0, "tg": 3.0, "capm_wacc": 0.10, "live_beta": 1.0}
}

# ==========================================
# PAGE ROUTING (INTRO WINDOW VS DASHBOARD)
# ==========================================

if not st.session_state.app_started:
    # --- INTRODUCTION / LANDING WINDOW ---
    st.markdown('<div class="landing-title">AutoValuer Terminal</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Institutional-Grade Equity Valuation & Risk Analytics Suite</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3 style='color:#00d2ff; margin-top:0;'>📡 Live Market API</h3>
            <p style='color:#8892b0; font-size:0.95rem;'>Pulls real-time balance sheets, free cash flows, and debt profiles instantly via Yahoo Finance.</p>
            <div class="hidden-info">⚡ Active Connection: Streaming real-time exchange feeds directly to your model workspace.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3 style='color:#00d2ff; margin-top:0;'>⚙️ Dynamic DCF Engine</h3>
            <p style='color:#8892b0; font-size:0.95rem;'>Calculates enterprise value, equity value, and intrinsic margin of safety seamlessly.</p>
            <div class="hidden-info">⚡ Algorithmic Core: Calculates CAPM models and terminal multipliers instantly.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h3 style='color:#00d2ff; margin-top:0;'>🎯 3D Risk & Monte Carlo</h3>
            <p style='color:#8892b0; font-size:0.95rem;'>Runs 10,000 probabilistic scenarios and 3D volatility maps to validate assumptions.</p>
            <div class="hidden-info">⚡ Sensitivity Suite: Evaluates standard deviations for bulletproof valuations.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([2, 1.5, 2])
    with center_col:
        if st.button("🚀 INITIATE TERMINAL"):
            st.session_state.app_started = True
            st.rerun()

else:
    # --- MAIN TERMINAL DASHBOARD ---
    st.markdown('<div class="main-title">AutoValuer Terminal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Institutional Equity Valuation & Risk Analytics Engine</div>', unsafe_allow_html=True)

    # --- TOP CONTROL DESK ---
    with st.expander("⚙️ ASSET CONFIGURATION & BALANCE SHEET", expanded=True):
        col_db, col_tick, col_price = st.columns(3)
        with col_db:
            selected_company = st.selectbox("Search & Select Company", list(COMPANY_DB.keys()))
            default_data = COMPANY_DB[selected_company]
        
        with col_tick:
            user_ticker = st.text_input("Live Ticker (Yahoo Finance)", value=default_data["ticker"])
            currency = "₹" if ".NS" in user_ticker.upper() or ".BO" in user_ticker.upper() else "$"
            unit = "Cr" if currency == "₹" else "M"
            
            with st.spinner("Extracting Global APIs & CAPM Parameters..."):
                live_data, is_live = get_company_data(user_ticker, default_data)
                if is_live and user_ticker != "":
                    st.toast(f"Live API Data Sync Complete: {user_ticker.upper()}", icon="📡")
                    
        with col_price:
            current_price = st.number_input(f"Market Price ({currency})", value=live_data["current_price"])

        st.markdown("---")
        
        col_fcf, col_cash, col_debt, col_shares = st.columns(4)
        with col_fcf:
            fcf_base = st.number_input(f"Base FCF ({unit})", value=live_data["fcf_base"])
        with col_cash:
            cash = st.number_input(f"Total Cash ({unit})", value=live_data["cash"])
        with col_debt:
            debt = st.number_input(f"Total Debt ({unit})", value=live_data["debt"])
        with col_shares:
            shares = st.number_input(f"Shares Out. ({unit})", value=live_data["shares"])

    # =========================================================================
    # STREAMLIT FRAGMENT: EVERYTHING BELOW UPDATES INSTANTLY WITHOUT PAGE RELOAD
    # =========================================================================
    @st.fragment
    def interactive_valuation_engine(fcf_base, cash, debt, shares, current_price, currency, unit, live_data):
        
        # --- MACRO ASSUMPTIONS (Inside Fragment for speed) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎛️ Macro Assumptions & Cost of Capital")
        
        # Automated CAPM Engine Toggle
        use_capm = st.toggle(f"🤖 Use Automated CAPM WACC (Live Beta: {live_data.get('live_beta', 1.0):.2f})", value=False)
        
        col_g, col_w, col_tg = st.columns(3)
        with col_g:
            growth_rate = st.slider("Growth Rate (%)", 1.0, 40.0, live_data["g"]) / 100
        with col_w:
            if use_capm:
                st.info(f"CAPM Target: {live_data['capm_wacc']*100:.2f}%")
                discount_rate = live_data["capm_wacc"]
            else:
                discount_rate = st.slider("WACC / Discount Rate (%)", 5.0, 25.0, live_data["wacc"]) / 100
        with col_tg:
            terminal_growth = st.slider("Terminal Growth (%)", 1.0, 10.0, live_data["tg"]) / 100

        # Math Safety Net
        if discount_rate <= terminal_growth:
            st.error("⚠️ **Mathematical Constraint Violation:** WACC (Cost of Capital) MUST be greater than the Terminal Growth Rate to calculate a finite intrinsic value.")
            return

        # Calculate Primary DCF
        results = calculate_dcf(fcf_base, cash, debt, shares, current_price, growth_rate, discount_rate, terminal_growth)

        # --- HERO METRICS ---
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Intrinsic Value", f"{currency} {results['intrinsic_value']:,.2f}")
        col2.metric("Market Price", f"{currency} {current_price:,.2f}")
        
        if results["is_undervalued"]:
            col3.metric("Verdict", "🟢 UNDERVALUED", f"{results['diff_percentage']:.1f}% Upside")
        else:
            col3.metric("Verdict", "🔴 OVERVALUED", f"{results['diff_percentage']:.1f}% Downside")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- ADVANCED TABS ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Enterprise Waterfall", "📈 Dynamic Projections", "🌋 3D Risk Surface", "🎲 Monte Carlo Engine", "🤖 AI Analyst"])

        with tab1:
            st.subheader("Enterprise-to-Equity Bridge")
            # The Waterfall Chart Engine
            fig_wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "total", "relative", "relative", "total"],
                x=["5-Yr Cash Flow PV", "Terminal Value PV", "Enterprise Value", "+ Total Cash", "- Total Debt", "Equity Value"],
                textposition="outside",
                text=[f"{v:,.0f}" for v in [results['sum_pv_5yr_cr'], results['pv_terminal_value_cr'], results['enterprise_value_cr'], cash, -debt, results['equity_value_cr']]],
                y=[results['sum_pv_5yr_cr'], results['pv_terminal_value_cr'], results['enterprise_value_cr'], cash, -debt, results['equity_value_cr']],
                decreasing={"marker": {"color": "#ff4b4b"}},
                increasing={"marker": {"color": "#00d2ff"}},
                totals={"marker": {"color": "#00ffcc"}}
            ))
            fig_wf.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title=f"Value ({unit})")
            st.plotly_chart(fig_wf, use_container_width=True)

        with tab2:
            st.subheader("Cash Flow Decay Curve")
            proj_timeline = st.slider("Projection Timeline (Years)", 1.0, 50.0, 15.0, 0.5)
            timeline_points = [round(x * 0.5, 1) for x in range(2, int(proj_timeline * 2) + 1)]
            nominal_fcfs, discounted_pvs = [], []
            
            for t in timeline_points:
                cf = (fcf_base * (1 + growth_rate)**t) if t <= 5 else (fcf_base * (1 + growth_rate)**5 * (1 + terminal_growth)**(t - 5))
                pv = cf / ((1 + discount_rate)**t)
                nominal_fcfs.append(cf)
                discounted_pvs.append(pv)
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=timeline_points, y=nominal_fcfs, fill='tozeroy', mode='none', name="Nominal Future Cash Flow", fillcolor="rgba(0, 210, 255, 0.3)"))
            fig_line.add_trace(go.Scatter(x=timeline_points, y=discounted_pvs, fill='tozeroy', mode='none', name="Discounted Present Value", fillcolor="rgba(0, 255, 204, 0.7)"))
            fig_line.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified", legend=dict(orientation="h", y=1.02), xaxis_title="Years into Future", yaxis_title=f"Cash Flow ({unit})")
            st.plotly_chart(fig_line, use_container_width=True)

        with tab3:
            st.subheader("Interactive 3D Valuation Matrix")
            st.write("Drag and rotate the surface to identify valuation cliffs.")
            
            wacc_steps = np.linspace(max(terminal_growth + 0.005, discount_rate - 0.03), discount_rate + 0.03, 15)
            g_steps = np.linspace(max(0.01, growth_rate - 0.05), growth_rate + 0.05, 15)
            
            z_data = []
            for g in g_steps:
                row = []
                for w in wacc_steps:
                    try:
                        row.append(calculate_dcf(fcf_base, cash, debt, shares, current_price, g, w, terminal_growth)['intrinsic_value'])
                    except:
                        row.append(0)
                z_data.append(row)

            fig_3d = go.Figure(data=[go.Surface(
                z=z_data, 
                x=[f"{w*100:.1f}%" for w in wacc_steps], 
                y=[f"{g*100:.1f}%" for g in g_steps],
                colorscale='RdYlGn'
            )])
            fig_3d.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", 
                scene=dict(xaxis_title='WACC', yaxis_title='Growth', zaxis_title='Target Price', camera=dict(eye=dict(x=1.5, y=-1.5, z=0.5))),
                margin=dict(l=0, r=0, b=0, t=0),
                height=600
            )
            st.plotly_chart(fig_3d, use_container_width=True)

        with tab4:
            st.subheader("Monte Carlo Simulation (10,000 Scenarios)")
            
            with st.spinner("Executing 10,000 Probabilistic Scenarios..."):
                # Normal Distribution Arrays
                mc_g = np.random.normal(growth_rate, 0.02, 10000) # 2% StdDev on Growth
                mc_w = np.random.normal(discount_rate, 0.01, 10000) # 1% StdDev on WACC
                
                # Filter mathematical impossibilities
                valid_scenarios = mc_w > terminal_growth
                mc_g, mc_w = mc_g[valid_scenarios], mc_w[valid_scenarios]
                
                # Fast Vectorized DCF Math
                base_yr5_arr = fcf_base * (1 + mc_g)**5
                tv_arr = (base_yr5_arr * (1 + terminal_growth)) / (mc_w - terminal_growth)
                pv_tv_arr = tv_arr / (1 + mc_w)**5
                
                sum_pv_arr = 0
                for t in range(1, 6):
                    sum_pv_arr += (fcf_base * (1 + mc_g)**t) / (1 + mc_w)**t
                    
                ev_arr = sum_pv_arr + pv_tv_arr
                eq_arr = ev_arr + cash - debt
                sim_prices = eq_arr / shares
                
                # Percentiles & Probabilities
                p10, p50, p90 = np.percentile(sim_prices, 10), np.percentile(sim_prices, 50), np.percentile(sim_prices, 90)
                prob_undervalued = np.mean(sim_prices > current_price) * 100

                fig_mc = px.histogram(sim_prices, nbins=100, color_discrete_sequence=['#00d2ff'])
                fig_mc.add_vline(x=p10, line_dash="dash", line_color="red", annotation_text=f"10th PCTL: {currency}{p10:.2f}")
                fig_mc.add_vline(x=p50, line_dash="solid", line_color="#00ffcc", annotation_text=f"BASE: {currency}{p50:.2f}")
                fig_mc.add_vline(x=p90, line_dash="dash", line_color="green", annotation_text=f"90th PCTL: {currency}{p90:.2f}")
                fig_mc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Simulated Intrinsic Value", yaxis_title="Frequency", showlegend=False)
                st.plotly_chart(fig_mc, use_container_width=True)

        with tab4:
            # We share tab 4 data directly into Tab 5
            pass

        with tab5:
            st.subheader("Automated AI Explainer")
            with st.chat_message("assistant"):
                st.write(f"Hello! I am the logic engine underlying this terminal. Based on the advanced parameters provided, here is my institutional breakdown of **{user_ticker if user_ticker else 'the selected asset'}**:")
                
                st.write("### 1. Statistical Probability")
                st.info(f"I just executed **{len(sim_prices):,} randomized Monte Carlo simulations** running varying scenarios of growth and risk. In **{prob_undervalued:.1f}%** of those future universes, the intrinsic value of this company is higher than the current market price of {currency}{current_price}.")
                
                st.write("### 2. The Base Case Breakdown")
                if results["is_undervalued"]:
                    st.success(f"Under your specific Base Case assumptions, the true intrinsic value is **{currency}{results['intrinsic_value']:,.2f}**. Because the market price is lower than the true value, this asset is fundamentally **Undervalued by {results['diff_percentage']:.1f}%**.")
                else:
                    st.error(f"Under your specific Base Case assumptions, the true intrinsic value is only **{currency}{results['intrinsic_value']:,.2f}**. Because the market price is higher than the true value, this asset is fundamentally **Overvalued by {results['diff_percentage']:.1f}%**.")
                    
                st.write("### 3. The Mathematical Bridge")
                st.write(f"- We project the company will generate a present value of **{currency}{results['sum_pv_5yr_cr']:,.2f} {unit}** over the next 5 years.")
                st.write(f"- The Terminal Value (the present value of all cash generated from Year 6 into infinity) is **{currency}{results['pv_terminal_value_cr']:,.2f} {unit}**.")
                st.write(f"- After adding {currency}{cash} {unit} in cash and subtracting {currency}{debt} {unit} in debt, the final equity belongs to the shareholders.")

    # Call the fragment function
    interactive_valuation_engine(fcf_base, cash, debt, shares, current_price, currency, unit, live_data)
#deploy
