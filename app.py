import inspect
import streamlit as st
import yfinance as yf
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
    /* CLEAN INSTITUTIONAL RADIAL GRADIENT BACKGROUND */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #112240 0%, #0a192f 100%);
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


# Newer Streamlit versions replaced use_container_width with width="stretch".
# This helper works on both old and new versions.
_NEW_WIDTH_API = "width" in inspect.signature(st.plotly_chart).parameters


def show_chart(fig):
    if _NEW_WIDTH_API:
        st.plotly_chart(fig, width="stretch")
    else:
        st.plotly_chart(fig, use_container_width=True)

# Used when the live US 10-year Treasury yield cannot be fetched
RF_FALLBACK = 0.042


# --- SELF-CONTAINED DCF ENGINE ---
def calculate_dcf(fcf_base, cash, debt, shares, current_price, g, wacc, tg):
    """Two-stage DCF: 5 years of growth, then a Gordon Growth terminal value."""
    if wacc <= tg:
        raise ValueError("WACC must be strictly greater than Terminal Growth.")

    # Stage 1: 5-Year Growth
    sum_pv_5yr = sum(fcf_base * (1 + g) ** t / (1 + wacc) ** t for t in range(1, 6))

    # Stage 2: Terminal Value
    base_yr5 = fcf_base * (1 + g) ** 5
    tv = (base_yr5 * (1 + tg)) / (wacc - tg)
    pv_tv = tv / (1 + wacc) ** 5

    # Bridge to Equity
    ev = sum_pv_5yr + pv_tv
    eq = ev + cash - debt
    intrinsic_value = eq / shares if shares > 0 else 0
    diff = ((intrinsic_value - current_price) / current_price) * 100 if current_price > 0 else 0

    return {
        "pv_fcf_5yr": sum_pv_5yr,
        "pv_terminal_value": pv_tv,
        "enterprise_value": ev,
        "net_cash": cash - debt,
        "equity_value": eq,
        "intrinsic_value": intrinsic_value,
        "diff_percentage": diff,
        "is_undervalued": intrinsic_value > current_price,
    }


def capm_cost_of_equity(rf_rate, beta, market_return):
    """CAPM: risk-free rate + beta x (expected market return - risk-free rate)."""
    return rf_rate + beta * (market_return - rf_rate)


def run_monte_carlo(fcf_base, cash, debt, shares, growth_rate, discount_rate, terminal_growth, n=10000, seed=42):
    """Simulates n scenarios with random growth and WACC. Fixed seed = repeatable results."""
    rng = np.random.default_rng(seed)
    mc_g = rng.normal(growth_rate, 0.02, n)       # 2% standard deviation on growth
    mc_w = rng.normal(discount_rate, 0.01, n)     # 1% standard deviation on WACC

    # Remove impossible scenarios (WACC must be above terminal growth)
    valid = mc_w > terminal_growth
    mc_g, mc_w = mc_g[valid], mc_w[valid]

    tv = (fcf_base * (1 + mc_g) ** 5 * (1 + terminal_growth)) / (mc_w - terminal_growth)
    pv_tv = tv / (1 + mc_w) ** 5
    sum_pv = sum((fcf_base * (1 + mc_g) ** t) / (1 + mc_w) ** t for t in range(1, 6))
    return (sum_pv + pv_tv + cash - debt) / shares


# --- ROBUST API FETCHING ---
@st.cache_data(ttl=900)
def get_company_data(ticker_symbol, backup_data):
    """Tries Yahoo Finance first. Any value it cannot supply falls back to the preset figure.
    'live_fields' lists exactly which values really came from Yahoo Finance."""
    if not ticker_symbol or ticker_symbol.strip() == "":
        return backup_data, False
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info or {}
        hist = stock.history(period="1d")
        live_fields = []

        if not hist.empty:
            live_price = float(hist['Close'].iloc[-1])
            live_fields.append("price")
        else:
            live_price = backup_data["current_price"]

        def pick(key, name, backup_key, div):
            raw = info.get(key)
            if raw is not None:
                live_fields.append(name)
                return raw / div
            return backup_data[backup_key]

        div = 10**7 if ".NS" in ticker_symbol.upper() or ".BO" in ticker_symbol.upper() else 10**6
        fcf_base = pick('freeCashflow', "free cash flow", "fcf_base", div)
        cash = pick('totalCash', "cash", "cash", div)
        debt = pick('totalDebt', "debt", "debt", div)
        shares = pick('sharesOutstanding', "shares", "shares", div)

        # Beta can be missing (None) - fall back instead of crashing later
        beta = info.get('beta')
        if beta is None:
            beta = backup_data.get("live_beta", 1.0)
        else:
            live_fields.append("beta")

        # Risk-free rate: US 10-Year Treasury yield
        try:
            tnx = yf.Ticker("^TNX")
            rf_rate = float(tnx.history(period="1d")['Close'].iloc[-1]) / 100.0
            live_fields.append("risk-free rate")
        except Exception:
            rf_rate = RF_FALLBACK

        return {
            "current_price": live_price,
            "fcf_base": fcf_base,
            "cash": cash,
            "debt": debt,
            "shares": shares,
            "g": backup_data["g"],
            "wacc": backup_data["wacc"],
            "tg": backup_data["tg"],
            "live_beta": beta,
            "rf_rate": rf_rate,
            "live_fields": live_fields,
        }, len(live_fields) > 0
    except Exception:
        return backup_data, False


# --- COMPANY DATABASE (preset figures, used as a fallback) ---
COMPANY_DB = {
    "Apple Inc. (AAPL)": {"ticker": "AAPL", "current_price": 225.00, "fcf_base": 95000.0, "cash": 150000.0, "debt": 110000.0, "shares": 15200.0, "g": 10.0, "wacc": 8.5, "tg": 3.0, "live_beta": 1.1},
    "Microsoft Corp. (MSFT)": {"ticker": "MSFT", "current_price": 415.00, "fcf_base": 75000.0, "cash": 80000.0, "debt": 60000.0, "shares": 7430.0, "g": 11.0, "wacc": 8.5, "tg": 3.0, "live_beta": 1.05},
    "NVIDIA Corp. (NVDA)": {"ticker": "NVDA", "current_price": 125.00, "fcf_base": 50000.0, "cash": 35000.0, "debt": 8500.0, "shares": 24600.0, "g": 20.0, "wacc": 10.0, "tg": 4.0, "live_beta": 1.7},
    "Tata Motors (TATAMOTORS.NS)": {"ticker": "TATAMOTORS.NS", "current_price": 980.00, "fcf_base": 21000.0, "cash": 42500.0, "debt": 58000.0, "shares": 367.0, "g": 12.0, "wacc": 10.0, "tg": 4.0, "live_beta": 1.4},
    "Reliance (RELIANCE.NS)": {"ticker": "RELIANCE.NS", "current_price": 2950.00, "fcf_base": 65000.0, "cash": 185000.0, "debt": 310000.0, "shares": 676.0, "g": 10.0, "wacc": 10.5, "tg": 4.0, "live_beta": 1.0},
    "HDFC Bank (HDFCBANK.NS)": {"ticker": "HDFCBANK.NS", "current_price": 1600.00, "fcf_base": 40000.0, "cash": 150000.0, "debt": 250000.0, "shares": 760.0, "g": 11.0, "wacc": 11.0, "tg": 3.5, "live_beta": 0.9},
    "Custom Ticker Entry": {"ticker": "", "current_price": 1000.00, "fcf_base": 10000.0, "cash": 5000.0, "debt": 2000.0, "shares": 100.0, "g": 10.0, "wacc": 10.0, "tg": 3.0, "live_beta": 1.0},
}

# ==========================================
# PAGE ROUTING (INTRO WINDOW VS DASHBOARD)
# ==========================================

if not st.session_state.app_started:
    # --- INTRODUCTION / LANDING WINDOW ---
    st.markdown('<div class="landing-title">AutoValuer Terminal</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Equity Valuation & Risk Analytics Suite</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-box">
            <h3 style='color:#00d2ff; margin-top:0;'>📡 Live Market Data</h3>
            <p style='color:#8892b0; font-size:0.95rem;'>Fetches share prices and company financials from Yahoo Finance, with preset figures as a fallback.</p>
            <div class="hidden-info">⚡ Every input can be edited by hand, and the app shows which values came from live data.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-box">
            <h3 style='color:#00d2ff; margin-top:0;'>⚙️ Dynamic DCF Engine</h3>
            <p style='color:#8892b0; font-size:0.95rem;'>Calculates enterprise value, equity value, and intrinsic margin of safety seamlessly.</p>
            <div class="hidden-info">⚡ Optional CAPM discount rate and a Gordon Growth terminal value.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-box">
            <h3 style='color:#00d2ff; margin-top:0;'>🎯 3D Risk & Monte Carlo</h3>
            <p style='color:#8892b0; font-size:0.95rem;'>Runs 10,000 probabilistic scenarios and a 3D sensitivity surface to test assumptions.</p>
            <div class="hidden-info">⚡ Shows how much the valuation depends on growth and WACC.</div>
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
    st.markdown('<div class="sub-title">Equity Valuation & Risk Analytics Engine</div>', unsafe_allow_html=True)

    # --- TOP CONTROL DESK ---
    with st.expander("⚙️ ASSET CONFIGURATION & BALANCE SHEET", expanded=True):
        col_db, col_tick, col_price = st.columns(3)
        with col_db:
            selected_company = st.selectbox("Search & Select Company", list(COMPANY_DB.keys()))
            default_data = COMPANY_DB[selected_company]

        with col_tick:
            user_ticker = st.text_input("Live Ticker (Yahoo Finance)", value=default_data["ticker"])
            is_indian = ".NS" in user_ticker.upper() or ".BO" in user_ticker.upper()
            currency = "₹" if is_indian else "$"
            unit = "Cr" if is_indian else "M"

            with st.spinner("Fetching market data..."):
                live_data, is_live = get_company_data(user_ticker, default_data)
                if is_live and user_ticker != "":
                    st.toast(f"Live data sync complete: {user_ticker.upper()}", icon="📡")

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

        # Be honest about where the numbers came from
        if user_ticker:
            live_fields = live_data.get("live_fields", [])
            expected = ["price", "free cash flow", "cash", "debt", "shares"]
            preset_used = [f for f in expected if f not in live_fields]
            if not preset_used:
                st.caption("✅ All inputs above were loaded live from Yahoo Finance.")
            else:
                st.caption("⚠️ Preset values are being used for: " + ", ".join(preset_used) + ". Check these before relying on the result.")

    # =========================================================================
    # STREAMLIT FRAGMENT: EVERYTHING BELOW UPDATES INSTANTLY WITHOUT PAGE RELOAD
    # =========================================================================
    @st.fragment
    def interactive_valuation_engine(fcf_base, cash, debt, shares, current_price, currency, unit, live_data, is_indian):

        # --- MACRO ASSUMPTIONS ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎛️ Macro Assumptions & Cost of Capital")

        beta = live_data.get("live_beta", 1.0)
        use_capm = st.toggle(f"📐 Use CAPM discount rate (cost of equity, Beta: {beta:.2f})", value=False)

        col_g, col_w, col_tg = st.columns(3)
        with col_g:
            growth_rate = st.slider("Growth Rate (%)", 1.0, 40.0, live_data["g"]) / 100
        with col_w:
            if use_capm:
                rf_pct = st.number_input("Risk-free rate (%)", value=round(live_data.get("rf_rate", RF_FALLBACK) * 100, 2), step=0.1)
                mr_pct = st.number_input("Expected market return (%)", value=10.0, step=0.5)
                discount_rate = capm_cost_of_equity(rf_pct / 100, beta, mr_pct / 100)
                st.info(f"CAPM cost of equity: {discount_rate * 100:.2f}%")
                if is_indian:
                    st.caption("The default risk-free rate is the US 10-year yield. For Indian stocks, consider entering the Indian 10-year government bond yield instead.")
            else:
                discount_rate = st.slider("WACC / Discount Rate (%)", 5.0, 25.0, live_data["wacc"]) / 100
        with col_tg:
            terminal_growth = st.slider("Terminal Growth (%)", 1.0, 10.0, live_data["tg"]) / 100

        # Math Safety Net
        if discount_rate <= terminal_growth:
            st.error("⚠️ **Mathematical Constraint Violation:** WACC (Cost of Capital) MUST be greater than the Terminal Growth Rate to calculate a finite intrinsic value.")
            return
        if fcf_base <= 0:
            st.warning("Base free cash flow is zero or negative, so a standard DCF is not meaningful for this company. Treat the result with caution.")

        # Calculate Primary DCF
        results = calculate_dcf(fcf_base, cash, debt, shares, current_price, growth_rate, discount_rate, terminal_growth)

        # Monte Carlo (computed once, used by two tabs)
        sim_prices = run_monte_carlo(fcf_base, cash, debt, shares, growth_rate, discount_rate, terminal_growth) if shares > 0 else np.array([])
        has_sim = sim_prices.size > 0

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

        # --- ANALYSIS TABS ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Enterprise Waterfall", "📈 Dynamic Projections", "🌋 3D Risk Surface", "🎲 Monte Carlo Engine", "📝 Analyst Summary"])

        with tab1:
            st.subheader("Enterprise-to-Equity Bridge")
            wf_values = [results['pv_fcf_5yr'], results['pv_terminal_value'], results['enterprise_value'], cash, -debt, results['equity_value']]
            fig_wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "total", "relative", "relative", "total"],
                x=["5-Yr Cash Flow PV", "Terminal Value PV", "Enterprise Value", "+ Total Cash", "- Total Debt", "Equity Value"],
                textposition="outside",
                text=[f"{v:,.0f}" for v in wf_values],
                y=wf_values,
                decreasing={"marker": {"color": "#ff4b4b"}},
                increasing={"marker": {"color": "#00d2ff"}},
                totals={"marker": {"color": "#00ffcc"}}
            ))
            fig_wf.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title=f"Value ({unit})")
            show_chart(fig_wf)

        with tab2:
            st.subheader("Cash Flow Decay Curve")
            proj_timeline = st.slider("Projection Timeline (Years)", 1.0, 50.0, 15.0, 0.5)
            timeline_points = [round(x * 0.5, 1) for x in range(2, int(proj_timeline * 2) + 1)]
            nominal_fcfs, discounted_pvs = [], []

            for t in timeline_points:
                cf = (fcf_base * (1 + growth_rate) ** t) if t <= 5 else (fcf_base * (1 + growth_rate) ** 5 * (1 + terminal_growth) ** (t - 5))
                nominal_fcfs.append(cf)
                discounted_pvs.append(cf / ((1 + discount_rate) ** t))

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=timeline_points, y=nominal_fcfs, fill='tozeroy', mode='none', name="Nominal Future Cash Flow", fillcolor="rgba(0, 210, 255, 0.3)"))
            fig_line.add_trace(go.Scatter(x=timeline_points, y=discounted_pvs, fill='tozeroy', mode='none', name="Discounted Present Value", fillcolor="rgba(0, 255, 204, 0.7)"))
            fig_line.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified", legend=dict(orientation="h", y=1.02), xaxis_title="Years into Future", yaxis_title=f"Cash Flow ({unit})")
            show_chart(fig_line)

        with tab3:
            st.subheader("Interactive 3D Valuation Surface")
            st.write("Drag and rotate the surface to see how intrinsic value changes with WACC and growth.")

            wacc_steps = np.linspace(max(terminal_growth + 0.005, discount_rate - 0.03), discount_rate + 0.03, 15)
            g_steps = np.linspace(max(0.01, growth_rate - 0.05), growth_rate + 0.05, 15)

            z_data = []
            for g in g_steps:
                row = []
                for w in wacc_steps:
                    try:
                        row.append(calculate_dcf(fcf_base, cash, debt, shares, current_price, g, w, terminal_growth)['intrinsic_value'])
                    except ValueError:
                        row.append(np.nan)   # leave a gap instead of a fake zero
                z_data.append(row)

            fig_3d = go.Figure(data=[go.Surface(
                z=z_data,
                x=[f"{w * 100:.1f}%" for w in wacc_steps],
                y=[f"{g * 100:.1f}%" for g in g_steps],
                colorscale='RdYlGn'
            )])
            fig_3d.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                scene=dict(xaxis_title='WACC', yaxis_title='Growth', zaxis_title='Intrinsic Value', camera=dict(eye=dict(x=1.5, y=-1.5, z=0.5))),
                margin=dict(l=0, r=0, b=0, t=0),
                height=600
            )
            show_chart(fig_3d)

        with tab4:
            st.subheader("Monte Carlo Simulation (10,000 Scenarios)")
            if has_sim:
                p10, p50, p90 = np.percentile(sim_prices, 10), np.percentile(sim_prices, 50), np.percentile(sim_prices, 90)
                prob_undervalued = np.mean(sim_prices > current_price) * 100

                st.caption(f"Each scenario randomly varies growth (±2 points) and WACC (±1 point). {len(sim_prices):,} valid scenarios were used. Results are repeatable (fixed random seed).")
                fig_mc = px.histogram(sim_prices, nbins=100, color_discrete_sequence=['#00d2ff'])
                fig_mc.add_vline(x=p10, line_dash="dash", line_color="red", annotation_text=f"10th PCTL: {currency}{p10:.2f}")
                fig_mc.add_vline(x=p50, line_dash="solid", line_color="#00ffcc", annotation_text=f"MEDIAN: {currency}{p50:.2f}")
                fig_mc.add_vline(x=p90, line_dash="dash", line_color="green", annotation_text=f"90th PCTL: {currency}{p90:.2f}")
                fig_mc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Simulated Intrinsic Value", yaxis_title="Frequency", showlegend=False)
                show_chart(fig_mc)
            else:
                st.warning("Not enough valid scenarios to run the simulation. Check that shares outstanding is above zero and WACC is comfortably above terminal growth.")

        with tab5:
            st.subheader("Automated Analyst Summary")
            st.caption("This summary is generated automatically from the numbers above using fixed rules. It is not an AI model.")
            with st.chat_message("assistant"):
                st.write(f"Here is a breakdown of **{user_ticker if user_ticker else 'the selected asset'}**:")

                st.write("### 1. Statistical Probability")
                if has_sim:
                    st.info(f"Across **{len(sim_prices):,} randomized Monte Carlo scenarios** with varying growth and discount rates, the intrinsic value is higher than the current market price of {currency}{current_price:,.2f} in **{prob_undervalued:.1f}%** of cases.")
                else:
                    st.info("The Monte Carlo simulation could not run with the current inputs.")

                st.write("### 2. The Base Case Breakdown")
                if results["is_undervalued"]:
                    st.success(f"Under your Base Case assumptions, the intrinsic value is **{currency}{results['intrinsic_value']:,.2f}**. Because the market price is lower, this asset appears **undervalued by {results['diff_percentage']:.1f}%**.")
                else:
                    st.error(f"Under your Base Case assumptions, the intrinsic value is only **{currency}{results['intrinsic_value']:,.2f}**. Because the market price is higher, this asset appears **overvalued by {abs(results['diff_percentage']):.1f}%**.")

                st.write("### 3. The Mathematical Bridge")
                st.write(f"- The present value of the next 5 years of cash flow is **{currency}{results['pv_fcf_5yr']:,.0f} {unit}**.")
                st.write(f"- The Terminal Value (the present value of all cash generated from Year 6 onward) is **{currency}{results['pv_terminal_value']:,.0f} {unit}**.")
                st.write(f"- After adding {currency}{cash:,.0f} {unit} in cash and subtracting {currency}{debt:,.0f} {unit} in debt, the remaining equity value is **{currency}{results['equity_value']:,.0f} {unit}**.")

    # Call the fragment function
    interactive_valuation_engine(fcf_base, cash, debt, shares, current_price, currency, unit, live_data, is_indian)
