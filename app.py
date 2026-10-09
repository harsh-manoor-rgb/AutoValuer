import inspect
from datetime import date
from io import BytesIO
from urllib.parse import quote

import pandas as pd
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, .stApp, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
    .stApp { background: radial-gradient(1100px 560px at 50% -8%, #153a6b 0%, transparent 62%), #070f1f; }
    .block-container { max-width: 1280px; padding-top: 1.6rem; animation: fadeUp .6s ease both; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
    @keyframes gradientMove { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .landing-title, .main-title { font-size: 3.4rem; font-weight: 800; letter-spacing: -0.03em; text-align: center; margin-bottom: 4px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399, #38bdf8); background-size: 300% 100%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: gradientMove 8s ease infinite; }
    .landing-subtitle, .sub-title { color: #94a3b8; font-size: 1.05rem; text-align: center; margin-bottom: 28px; }
    .feature-box { background: rgba(15, 28, 53, .7); border: 1px solid rgba(148, 163, 184, .16); border-radius: 18px; padding: 28px;
        height: 190px; overflow: hidden; backdrop-filter: blur(12px); transition: all .4s cubic-bezier(.16, 1, .3, 1); }
    .feature-box:hover { height: 270px; transform: translateY(-6px); border-color: #38bdf8; box-shadow: 0 18px 40px rgba(56, 189, 248, .18); }
    .hidden-info { opacity: 0; transition: opacity .3s ease; font-size: .9rem; color: #34d399; margin-top: 12px; border-top: 1px solid rgba(255, 255, 255, .1); padding-top: 10px; }
    .feature-box:hover .hidden-info { opacity: 1; }
    .stButton > button, [data-testid="stDownloadButton"] > button { width: 100%; padding: 14px 28px; font-size: 1.05rem; font-weight: 700; color: #fff; border: 0; border-radius: 14px;
        background: linear-gradient(90deg, #0ea5e9, #6366f1); box-shadow: 0 8px 24px rgba(99, 102, 241, .35); transition: all .25s ease; }
    .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(99, 102, 241, .5); color: #fff !important; }
    [data-testid="stExpander"] { background: rgba(15, 28, 53, .55); border: 1px solid rgba(148, 163, 184, .16); border-radius: 18px; backdrop-filter: blur(10px); }
    [data-baseweb="input"], [data-baseweb="select"] > div { background: rgba(7, 15, 31, .85) !important; border-radius: 10px !important; }
    [data-testid="stWidgetLabel"] p { color: #94a3b8; font-weight: 600; font-size: .82rem; }
    [data-baseweb="slider"] [role="slider"] { background: #38bdf8 !important; }
    h3 { font-weight: 700; letter-spacing: -0.01em; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: rgba(15, 28, 53, .6); padding: 6px; border-radius: 14px; border: 1px solid rgba(148, 163, 184, .14); flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; color: #94a3b8; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #0ea5e9, #6366f1); color: #fff; }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
    [data-testid="stChatMessage"] { background: rgba(15, 28, 53, .55); border: 1px solid rgba(148, 163, 184, .14); border-radius: 16px; }
    .kpi { background: rgba(15, 28, 53, .7); border: 1px solid rgba(148, 163, 184, .16); border-radius: 18px; padding: 22px 24px; min-height: 150px;
        backdrop-filter: blur(12px); transition: all .3s ease; }
    .kpi:hover { transform: translateY(-4px); border-color: #38bdf8; box-shadow: 0 14px 34px rgba(56, 189, 248, .16); }
    .kpi-label { color: #94a3b8; font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
    .kpi-value { color: #fff; font-size: 2.3rem; font-weight: 800; margin: 6px 0; font-variant-numeric: tabular-nums; }
    .kpi-sub { color: #64748b; font-size: .8rem; }
    .pill { display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: .82rem; font-weight: 700; letter-spacing: .03em; }
    .pill.up { background: rgba(52, 211, 153, .15); color: #34d399; } .pill.down { background: rgba(248, 113, 113, .15); color: #f87171; }
    .pill.live { background: rgba(52, 211, 153, .15); color: #34d399; } .pill.preset { background: rgba(251, 191, 36, .15); color: #fbbf24; }
    .kpi .pill { font-size: 1.05rem; margin: 10px 0 14px; }
    .bar { height: 6px; border-radius: 999px; background: rgba(148, 163, 184, .2); overflow: hidden; margin-bottom: 8px; }
    .fill { height: 100%; border-radius: 999px; } .fill.up { background: #34d399; } .fill.down { background: #f87171; }
    .foot { text-align: center; color: #64748b; font-size: .78rem; margin: 40px 0 10px; }
    @media (max-width: 768px) { .landing-title, .main-title { font-size: 2.1rem; } .kpi-value { font-size: 1.8rem; } }
    </style>
""", unsafe_allow_html=True)


# Newer Streamlit versions replaced use_container_width with width="stretch".
# This helper works on both old and new versions.
_NEW_WIDTH_API = "width" in inspect.signature(st.plotly_chart).parameters


def style_fig(fig):
    fig.update_layout(font=dict(family="Inter, sans-serif", color="#cbd5e1"),
                      xaxis=dict(gridcolor="rgba(148,163,184,.12)"), yaxis=dict(gridcolor="rgba(148,163,184,.12)"))
    return fig


def show_chart(fig):
    fig = style_fig(fig)
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
    sum_pv_5yr = sum(fcf_base * (1 + g) ** t / (1 + wacc) ** t for t in range(1, 6))
    base_yr5 = fcf_base * (1 + g) ** 5
    tv = (base_yr5 * (1 + tg)) / (wacc - tg)
    pv_tv = tv / (1 + wacc) ** 5
    ev = sum_pv_5yr + pv_tv
    eq = ev + cash - debt
    intrinsic_value = eq / shares if shares > 0 else 0
    diff = ((intrinsic_value - current_price) / current_price) * 100 if current_price > 0 else 0
    return {"pv_fcf_5yr": sum_pv_5yr, "pv_terminal_value": pv_tv, "enterprise_value": ev, "net_cash": cash - debt,
            "equity_value": eq, "intrinsic_value": intrinsic_value, "diff_percentage": diff,
            "is_undervalued": intrinsic_value > current_price}


def scenario_value(fcf_base, cash, debt, shares, g, w, tg):
    """Intrinsic value per share, or None if the inputs are impossible."""
    if w <= tg or g <= -0.99:
        return None
    return calculate_dcf(fcf_base, cash, debt, shares, 1, g, w, tg)["intrinsic_value"]


def solve_implied_growth(fcf_base, cash, debt, shares, price, wacc, tg):
    """Reverse DCF: which 5-year growth rate makes the DCF value equal today's price?"""
    if fcf_base <= 0 or shares <= 0 or price <= 0 or wacc <= tg:
        return None
    def gap(g):
        return scenario_value(fcf_base, cash, debt, shares, g, wacc, tg) - price
    lo, hi = -0.5, 1.5
    if gap(lo) > 0 or gap(hi) < 0:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if gap(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def capm_cost_of_equity(rf_rate, beta, market_return):
    return rf_rate + beta * (market_return - rf_rate)


def full_wacc(ke, kd, tax, equity_value, debt):
    """Weighted average cost of capital using market-value weights."""
    total = equity_value + debt
    if total <= 0:
        return ke, 1.0, 0.0
    we, wd = equity_value / total, debt / total
    return we * ke + wd * kd * (1 - tax), we, wd


def cagr(old, new, years):
    if old is None or new is None or years <= 0 or old <= 0 or new <= 0:
        return None
    return (new / old) ** (1 / years) - 1


def run_monte_carlo(fcf_base, cash, debt, shares, growth_rate, discount_rate, terminal_growth, n=10000, seed=42):
    """Simulates n scenarios with random growth and WACC. Fixed seed = repeatable results."""
    rng = np.random.default_rng(seed)
    mc_g = rng.normal(growth_rate, 0.02, n)
    mc_w = rng.normal(discount_rate, 0.01, n)
    valid = mc_w > terminal_growth
    mc_g, mc_w = mc_g[valid], mc_w[valid]
    tv = (fcf_base * (1 + mc_g) ** 5 * (1 + terminal_growth)) / (mc_w - terminal_growth)
    pv_tv = tv / (1 + mc_w) ** 5
    sum_pv = sum((fcf_base * (1 + mc_g) ** t) / (1 + mc_w) ** t for t in range(1, 6))
    return (sum_pv + pv_tv + cash - debt) / shares


# --- SMALL HELPERS ---
def money(x, symbol, d=2):
    """Currency text that is safe inside st.write / st.info (escapes the $ sign)."""
    return f"{symbol}{x:,.{d}f}".replace("$", "\\$")


def kpi(label, value, sub="", extra=""):
    html = f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{extra}<div class="kpi-sub">{sub}</div></div>'
    return html.replace("$", "&#36;")


def _num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def _series(df, names):
    """Oldest-to-newest values of the first matching row of a yfinance table."""
    try:
        if df is None or df.empty:
            return None
        for n in names:
            if n in df.index:
                s = df.loc[n].dropna().sort_index()
                if len(s) >= 2:
                    return [float(v) for v in s.values]
    except Exception:
        pass
    return None


def history_growth(stock):
    out = {}
    try:
        fcf = _series(stock.cashflow, ["Free Cash Flow"])
        rev = _series(stock.financials, ["Total Revenue", "Operating Revenue"])
        if fcf:
            out["fcf_cagr"], out["fcf_years"] = cagr(fcf[0], fcf[-1], len(fcf) - 1), len(fcf) - 1
        if rev:
            out["rev_cagr"], out["rev_years"] = cagr(rev[0], rev[-1], len(rev) - 1), len(rev) - 1
    except Exception:
        pass
    return out


# --- DATA FETCHING (Yahoo Finance, with preset fallback) ---
@st.cache_data(ttl=900)
def get_company_data(ticker_symbol, backup_data):
    """Any value Yahoo Finance cannot supply falls back to the preset figure.
    'live_fields' lists exactly which values really came from Yahoo Finance."""
    if not ticker_symbol or ticker_symbol.strip() == "":
        return backup_data, False
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info or {}
        px = stock.history(period="1d")
        live_fields = []
        if not px.empty:
            live_price = float(px['Close'].iloc[-1])
            live_fields.append("price")
        else:
            live_price = backup_data["current_price"]

        div = 10**7 if ".NS" in ticker_symbol.upper() or ".BO" in ticker_symbol.upper() else 10**6

        def pick(key, name, backup_key):
            raw = _num(info.get(key))
            if raw is not None:
                live_fields.append(name)
                return raw / div
            return backup_data[backup_key]

        fcf_base = pick('freeCashflow', "free cash flow", "fcf_base")
        cash = pick('totalCash', "cash", "cash")
        debt = pick('totalDebt', "debt", "debt")
        shares = pick('sharesOutstanding', "shares", "shares")

        beta = _num(info.get('beta'))
        if beta is None:
            beta = backup_data.get("live_beta", 1.0)
        else:
            live_fields.append("beta")
        try:
            rf_rate = float(yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]) / 100.0
            live_fields.append("risk-free rate")
        except Exception:
            rf_rate = RF_FALLBACK

        ebitda = _num(info.get('ebitda'))
        return {
            "current_price": live_price, "fcf_base": fcf_base, "cash": cash, "debt": debt, "shares": shares,
            "g": backup_data["g"], "wacc": backup_data["wacc"], "tg": backup_data["tg"],
            "live_beta": beta, "rf_rate": rf_rate, "live_fields": live_fields,
            "eps": _num(info.get('trailingEps')), "ebitda": (ebitda / div) if ebitda else None,
            "wk_low": _num(info.get('fiftyTwoWeekLow')), "wk_high": _num(info.get('fiftyTwoWeekHigh')),
            "hist": history_growth(stock),
        }, len(live_fields) > 0
    except Exception:
        return backup_data, False


@st.cache_data(ttl=900)
def get_peer_multiples(tickers):
    rows = []
    for t in tickers:
        row = {"Ticker": t, "Name": t, "P/E": None, "EV/EBITDA": None}
        try:
            info = yf.Ticker(t).info or {}
            row["Name"] = info.get("shortName", t)
            pe, ev = _num(info.get("trailingPE")), _num(info.get("enterpriseToEbitda"))
            row["P/E"] = pe if pe and pe > 0 else None
            row["EV/EBITDA"] = ev if ev and ev > 0 else None
        except Exception:
            pass
        rows.append(row)
    return rows


def build_excel(summary_rows, cash_flows, scenarios, peers):
    """Returns Excel bytes, or None if the openpyxl library is not installed."""
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        return None
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        sheets = {"Summary": pd.DataFrame(summary_rows, columns=["Item", "Value"]),
                  "Cash Flows": cash_flows, "Scenarios": scenarios}
        if peers is not None and not peers.empty:
            sheets["Peers"] = peers
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
            for col in writer.sheets[name].columns:
                writer.sheets[name].column_dimensions[col[0].column_letter].width = 30
    return buf.getvalue()


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
# Starting peer sets (editable in the app)
PEERS_DB = {
    "AAPL": ["MSFT", "GOOGL", "AMZN", "META"], "MSFT": ["AAPL", "GOOGL", "AMZN", "ORCL"],
    "NVDA": ["AMD", "AVGO", "INTC", "QCOM"], "TATAMOTORS.NS": ["MARUTI.NS", "M&M.NS", "EICHERMOT.NS"],
    "RELIANCE.NS": ["ONGC.NS", "BPCL.NS", "IOC.NS"], "HDFCBANK.NS": ["ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS"],
}
APP_URL = "https://autovaluer-live.onrender.com/"


def query_param(name):
    try:
        return st.query_params.get(name)
    except Exception:
        return None


if query_param("start") == "1":
    st.session_state.app_started = True

# ==========================================
# PAGE ROUTING (INTRO WINDOW VS DASHBOARD)
# ==========================================
if not st.session_state.app_started:
    st.markdown('<div class="landing-title">AutoValuer Terminal</div>', unsafe_allow_html=True)
    st.markdown('<div class="landing-subtitle">Equity Valuation & Risk Analytics Suite</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    cards = [
        ("📡 Live Market Data", "Share prices and financials from Yahoo Finance, with preset figures as a fallback.", "Every input is editable, and the app shows which values are live."),
        ("⚙️ DCF, Scenarios & Reverse DCF", "Bear/base/bull cases, a full WACC build-up, and the growth rate the market price implies.", "Answers: what is the market actually assuming?"),
        ("🎯 Risk, Peers & Football Field", "3D sensitivity, 10,000 Monte Carlo scenarios, peer multiples and a football-field chart.", "Export the whole valuation to Excel."),
    ]
    for col, (title, text, hover) in zip((col1, col2, col3), cards):
        with col:
            st.markdown(f'<div class="feature-box"><h3 style="color:#38bdf8; margin-top:0;">{title}</h3><p style="color:#94a3b8; font-size:0.95rem;">{text}</p><div class="hidden-info">⚡ {hover}</div></div>', unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([2, 1.5, 2])
    with center_col:
        if st.button("🚀 INITIATE TERMINAL"):
            st.session_state.app_started = True
            st.rerun()

else:
    st.markdown('<div class="main-title">AutoValuer Terminal</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Equity Valuation & Risk Analytics Engine</div>', unsafe_allow_html=True)

    # --- TOP CONTROL DESK ---
    with st.expander("⚙️ ASSET CONFIGURATION & BALANCE SHEET", expanded=True):
        names = list(COMPANY_DB.keys())
        qp_company = query_param("company")
        default_idx, ticker_default = 0, None
        if qp_company:
            matches = [i for i, n in enumerate(names) if COMPANY_DB[n]["ticker"].upper() == qp_company.upper()]
            if matches:
                default_idx = matches[0]
            else:
                default_idx, ticker_default = len(names) - 1, qp_company.upper()

        col_db, col_tick, col_price = st.columns(3)
        with col_db:
            selected_company = st.selectbox("Search & Select Company", names, index=default_idx)
            default_data = COMPANY_DB[selected_company]
        with col_tick:
            user_ticker = st.text_input("Live Ticker (Yahoo Finance)", value=ticker_default or default_data["ticker"])
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

        if user_ticker:
            live_fields = live_data.get("live_fields", [])
            preset_used = [f for f in ["price", "free cash flow", "cash", "debt", "shares"] if f not in live_fields]
            if not preset_used:
                st.markdown('<span class="pill live">● LIVE DATA</span> <span class="kpi-sub">All inputs loaded from Yahoo Finance</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="pill preset">● PRESET DATA</span> <span class="kpi-sub">Preset values used for: {", ".join(preset_used)}. Check before relying on the result.</span>', unsafe_allow_html=True)

    if user_ticker:
        try:
            st.query_params["start"] = "1"
            st.query_params["company"] = user_ticker.upper()
        except Exception:
            pass
        with st.expander("🔗 Share this valuation"):
            st.caption("Anyone opening this link skips the intro page and lands on this company:")
            st.code(f"{APP_URL}?start=1&company={quote(user_ticker.upper())}", language=None)

    # =========================================================================
    # FRAGMENT: EVERYTHING BELOW UPDATES INSTANTLY WITHOUT A PAGE RELOAD
    # =========================================================================
    @st.fragment
    def interactive_valuation_engine(fcf_base, cash, debt, shares, current_price, currency, unit, live_data, is_indian, user_ticker):

        # ---------- ASSUMPTIONS ----------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎛️ Valuation Assumptions")
        beta = live_data.get("live_beta", 1.0)
        hist = live_data.get("hist") or {}
        hist_g = hist.get("fcf_cagr") if hist.get("fcf_cagr") is not None else hist.get("rev_cagr")

        mode = st.radio("Discount rate method", ["Manual WACC", "CAPM (cost of equity)", "Full WACC (CAPM + debt)"], horizontal=True)
        discount_rate, wacc_note = None, ""
        if mode != "Manual WACC":
            r1, r2, r3, r4 = st.columns(4)
            rf = r1.number_input("Risk-free rate (%)", value=round(live_data.get("rf_rate", RF_FALLBACK) * 100, 2), step=0.1) / 100
            mr = r2.number_input("Expected market return (%)", value=10.0, step=0.5) / 100
            ke = capm_cost_of_equity(rf, beta, mr)
            if mode.startswith("CAPM"):
                discount_rate = ke
                wacc_note = f"CAPM cost of equity (beta {beta:.2f}): {ke * 100:.2f}%"
            else:
                kd = r3.number_input("Pre-tax cost of debt (%)", value=8.5 if is_indian else 5.5, step=0.25) / 100
                tax = r4.number_input("Tax rate (%)", value=25.0 if is_indian else 21.0, step=1.0) / 100
                discount_rate, we, wd = full_wacc(ke, kd, tax, current_price * shares, debt)
                wacc_note = f"Full WACC {discount_rate * 100:.2f}%  (cost of equity {ke * 100:.2f}%, after-tax cost of debt {kd * (1 - tax) * 100:.2f}%, equity weight {we:.0%}, debt weight {wd:.0%})"
            if is_indian:
                st.caption("The default risk-free rate is the US 10-year yield. For Indian stocks, consider entering the Indian 10-year government bond yield. Cost of debt and tax rate are editable assumptions.")

        col_g, col_w, col_tg = st.columns(3)
        with col_g:
            use_hist = st.toggle("Start from historical growth", value=False) if hist_g is not None else False
            g_default = float(min(40.0, max(1.0, round(hist_g * 100, 1)))) if (use_hist and hist_g is not None) else float(live_data["g"])
            growth_rate = st.slider("Growth Rate (%)", 1.0, 40.0, g_default) / 100
            parts = []
            if hist.get("fcf_cagr") is not None:
                parts.append(f"FCF CAGR {hist['fcf_cagr'] * 100:.1f}% ({hist.get('fcf_years')} yrs)")
            if hist.get("rev_cagr") is not None:
                parts.append(f"revenue CAGR {hist['rev_cagr'] * 100:.1f}% ({hist.get('rev_years')} yrs)")
            if parts:
                st.caption("Historical reference: " + ", ".join(parts) + ". Past growth is not a forecast.")
        with col_w:
            if discount_rate is None:
                discount_rate = st.slider("WACC / Discount Rate (%)", 5.0, 25.0, live_data["wacc"]) / 100
            else:
                st.info(wacc_note)
        with col_tg:
            terminal_growth = st.slider("Terminal Growth (%)", 1.0, 10.0, live_data["tg"]) / 100

        if discount_rate <= terminal_growth:
            st.error("⚠️ WACC must be greater than Terminal Growth to get a finite value.")
            return
        if fcf_base <= 0:
            st.warning("Base free cash flow is zero or negative, so a standard DCF is not meaningful for this company. Treat the result with caution.")

        results = calculate_dcf(fcf_base, cash, debt, shares, current_price, growth_rate, discount_rate, terminal_growth)

        sim_prices = run_monte_carlo(fcf_base, cash, debt, shares, growth_rate, discount_rate, terminal_growth) if shares > 0 else np.array([])
        has_sim = sim_prices.size > 0
        if has_sim:
            p10, p50, p90 = [float(x) for x in np.percentile(sim_prices, [10, 50, 90])]
            prob_undervalued = float(np.mean(sim_prices > current_price) * 100)
        else:
            p10 = p50 = p90 = prob_undervalued = None

        # ---------- HERO CARDS ----------
        st.markdown("<br>", unsafe_allow_html=True)
        up, diff = results["is_undervalued"], results["diff_percentage"]
        word = "▲ UNDERVALUED" if up else "▼ OVERVALUED"
        cls = "up" if up else "down"
        verdict = f'<span class="pill {cls}">{word} · {abs(diff):.1f}%</span>'
        bar = f'<div class="bar"><div class="fill {cls}" style="width:{min(abs(diff), 100):.0f}%"></div></div>'
        k1, k2, k3 = st.columns(3)
        k1.markdown(kpi("Intrinsic value", f"{currency}{results['intrinsic_value']:,.2f}", "per share, DCF base case"), unsafe_allow_html=True)
        k2.markdown(kpi("Market price", f"{currency}{current_price:,.2f}", "current trading price"), unsafe_allow_html=True)
        k3.markdown(kpi("Verdict", verdict, "gap between value and price", bar), unsafe_allow_html=True)

        # ---------- PEER SETTINGS ----------
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🏢 Peer comparison settings"):
            peer_text = st.text_input("Peer tickers (comma-separated, up to 6)", value=", ".join(PEERS_DB.get(user_ticker.upper(), [])))
            use_peers = st.toggle("Fetch peer multiples from Yahoo Finance", value=True)
        peers = [p.strip().upper() for p in peer_text.split(",") if p.strip()][:6]
        peer_rows = []
        if use_peers and peers:
            with st.spinner("Fetching peer data..."):
                peer_rows = get_peer_multiples(tuple(peers))

        tabs = st.tabs(["📋 Valuation", "🎯 Scenarios", "🔄 Reverse DCF", "🌋 Risk Analysis", "📊 Football Field", "🏢 Peers", "📝 Summary & Export", "📚 Methodology"])
        tab_val, tab_scen, tab_rev, tab_risk, tab_ff, tab_peer, tab_sum, tab_meth = tabs
        values, scen_cfg, implied_g, scen_df, weighted = {}, {}, None, pd.DataFrame(), None

        # ---------- 1. VALUATION ----------
        with tab_val:
            st.subheader("Enterprise-to-Equity Bridge")
            wf_values = [results['pv_fcf_5yr'], results['pv_terminal_value'], results['enterprise_value'], cash, -debt, results['equity_value']]
            fig_wf = go.Figure(go.Waterfall(
                orientation="v", measure=["relative", "relative", "total", "relative", "relative", "total"],
                x=["5-Yr Cash Flow PV", "Terminal Value PV", "Enterprise Value", "+ Total Cash", "- Total Debt", "Equity Value"],
                textposition="outside", text=[f"{v:,.0f}" for v in wf_values], y=wf_values,
                decreasing={"marker": {"color": "#f87171"}}, increasing={"marker": {"color": "#38bdf8"}}, totals={"marker": {"color": "#34d399"}}))
            fig_wf.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title=f"Value ({unit})")
            show_chart(fig_wf)

            st.subheader("Cash Flow Projection")
            proj_timeline = st.slider("Projection Timeline (Years)", 1.0, 50.0, 15.0, 0.5)
            pts = [round(x * 0.5, 1) for x in range(2, int(proj_timeline * 2) + 1)]
            nominal, discounted = [], []
            for t in pts:
                cf = fcf_base * (1 + growth_rate) ** t if t <= 5 else fcf_base * (1 + growth_rate) ** 5 * (1 + terminal_growth) ** (t - 5)
                nominal.append(cf)
                discounted.append(cf / (1 + discount_rate) ** t)
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=pts, y=nominal, fill='tozeroy', mode='none', name="Nominal Future Cash Flow", fillcolor="rgba(56, 189, 248, 0.3)"))
            fig_line.add_trace(go.Scatter(x=pts, y=discounted, fill='tozeroy', mode='none', name="Discounted Present Value", fillcolor="rgba(52, 211, 153, 0.7)"))
            fig_line.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified", legend=dict(orientation="h", y=1.02), xaxis_title="Years into Future", yaxis_title=f"Cash Flow ({unit})")
            show_chart(fig_line)

        # ---------- 2. SCENARIOS ----------
        with tab_scen:
            st.subheader("Bear / Base / Bull Scenarios")
            st.caption("Each scenario shifts growth and WACC relative to your base case. Edit the shifts and probabilities below.")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**🐻 Bear**")
                bear_dg = st.number_input("Bear: growth change (pts)", value=-4.0, step=0.5, key="bear_dg")
                bear_dw = st.number_input("Bear: WACC change (pts)", value=1.0, step=0.5, key="bear_dw")
                bear_p = st.number_input("Bear: probability (%)", value=25.0, step=5.0, min_value=0.0, key="bear_p")
            with c2:
                st.markdown("**⚖️ Base**")
                st.caption("Uses your assumptions above.")
                base_p = st.number_input("Base: probability (%)", value=50.0, step=5.0, min_value=0.0, key="base_p")
            with c3:
                st.markdown("**🐂 Bull**")
                bull_dg = st.number_input("Bull: growth change (pts)", value=4.0, step=0.5, key="bull_dg")
                bull_dw = st.number_input("Bull: WACC change (pts)", value=-1.0, step=0.5, key="bull_dw")
                bull_p = st.number_input("Bull: probability (%)", value=25.0, step=5.0, min_value=0.0, key="bull_p")

            scen_cfg = {"Bear": (growth_rate + bear_dg / 100, discount_rate + bear_dw / 100, bear_p),
                        "Base": (growth_rate, discount_rate, base_p),
                        "Bull": (growth_rate + bull_dg / 100, discount_rate + bull_dw / 100, bull_p)}
            values = {k: scenario_value(fcf_base, cash, debt, shares, g, w, terminal_growth) for k, (g, w, p) in scen_cfg.items()}
            valid = {k: v for k, v in values.items() if v is not None}
            tot_p = sum(scen_cfg[k][2] for k in valid)
            weighted = sum(valid[k] * scen_cfg[k][2] for k in valid) / tot_p if tot_p > 0 else None
            if abs(sum(p for _, _, p in scen_cfg.values()) - 100) > 0.01:
                st.caption("Probabilities do not add to 100%, so they are rescaled when the weighted value is calculated.")
            for k, (g, w, p) in scen_cfg.items():
                if values[k] is None:
                    st.warning(f"{k} case is invalid (WACC must stay above terminal growth).")

            cols = st.columns(4)
            for col, k in zip(cols[:3], ["Bear", "Base", "Bull"]):
                g, w, p = scen_cfg[k]
                if values[k] is not None:
                    chg = (values[k] / current_price - 1) * 100 if current_price > 0 else 0
                    col.markdown(kpi(f"{k} case", f"{currency}{values[k]:,.2f}", f"growth {g * 100:.1f}% · WACC {w * 100:.1f}% · {chg:+.0f}% vs price"), unsafe_allow_html=True)
            if weighted is not None:
                cols[3].markdown(kpi("Probability-weighted", f"{currency}{weighted:,.2f}", f"{(weighted / current_price - 1) * 100:+.0f}% vs market price" if current_price > 0 else ""), unsafe_allow_html=True)
            if valid:
                colors = {"Bear": "#f87171", "Base": "#38bdf8", "Bull": "#34d399"}
                fig_sc = go.Figure(go.Bar(x=list(valid.keys()), y=list(valid.values()), marker_color=[colors[k] for k in valid],
                                          text=[f"{currency}{v:,.2f}" for v in valid.values()], textposition="outside"))
                fig_sc.add_hline(y=current_price, line_dash="dash", line_color="#fbbf24", annotation_text=f"Market price {currency}{current_price:,.2f}")
                fig_sc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Intrinsic value per share", showlegend=False)
                show_chart(fig_sc)
            scen_df = pd.DataFrame([{"Scenario": k, "Growth %": round(g * 100, 2), "WACC %": round(w * 100, 2), "Probability %": p,
                                     "Intrinsic value": None if values[k] is None else round(values[k], 2)} for k, (g, w, p) in scen_cfg.items()])

        # ---------- 3. REVERSE DCF ----------
        with tab_rev:
            st.subheader("Reverse DCF: What Is the Market Assuming?")
            st.caption("Instead of asking what the company is worth, this asks what 5-year growth rate today's price requires, holding your WACC and terminal growth fixed.")
            implied_g = solve_implied_growth(fcf_base, cash, debt, shares, current_price, discount_rate, terminal_growth)
            if implied_g is None:
                st.info("A market-implied growth rate could not be found for these inputs (for example, negative cash flow, or a price outside the range the model can reach).")
            else:
                gap = (implied_g - growth_rate) * 100
                r1, r2, r3 = st.columns(3)
                r1.markdown(kpi("Market-implied growth", f"{implied_g * 100:.1f}%", "per year for 5 years"), unsafe_allow_html=True)
                r2.markdown(kpi("Your growth assumption", f"{growth_rate * 100:.1f}%", "per year for 5 years"), unsafe_allow_html=True)
                r3.markdown(kpi("Gap", f"{gap:+.1f} pts", "implied minus yours"), unsafe_allow_html=True)
                if gap > 0.5:
                    st.info(f"To justify {money(current_price, currency)} per share, the market needs about **{implied_g * 100:.1f}%** annual growth, which is **{gap:.1f} points higher** than your assumption. If you believe your growth estimate, the stock looks expensive.")
                elif gap < -0.5:
                    st.success(f"The market price only requires about **{implied_g * 100:.1f}%** annual growth, **{abs(gap):.1f} points lower** than your assumption. If you believe your growth estimate, the stock looks cheap.")
                else:
                    st.info("The market price is almost exactly in line with your growth assumption.")
                gs = np.linspace(-0.05, 0.40, 60)
                vs = [scenario_value(fcf_base, cash, debt, shares, g, discount_rate, terminal_growth) for g in gs]
                fig_rv = go.Figure(go.Scatter(x=gs * 100, y=vs, mode="lines", line=dict(color="#38bdf8", width=3), name="DCF value"))
                fig_rv.add_hline(y=current_price, line_dash="dash", line_color="#fbbf24", annotation_text="Market price")
                fig_rv.add_vline(x=implied_g * 100, line_color="#f87171", annotation_text=f"Implied {implied_g * 100:.1f}%")
                fig_rv.add_vline(x=growth_rate * 100, line_color="#34d399", annotation_text=f"Yours {growth_rate * 100:.1f}%")
                fig_rv.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="5-year growth rate (%)", yaxis_title="Intrinsic value per share", showlegend=False)
                show_chart(fig_rv)

        # ---------- 4. RISK ----------
        with tab_risk:
            st.subheader("3D Valuation Surface")
            st.write("Drag and rotate the surface to see how intrinsic value changes with WACC and growth.")
            wacc_steps = np.linspace(max(terminal_growth + 0.005, discount_rate - 0.03), discount_rate + 0.03, 15)
            g_steps = np.linspace(max(0.01, growth_rate - 0.05), growth_rate + 0.05, 15)
            z_data = []
            for g in g_steps:
                row = []
                for w in wacc_steps:
                    v = scenario_value(fcf_base, cash, debt, shares, g, w, terminal_growth)
                    row.append(np.nan if v is None else v)
                z_data.append(row)
            fig_3d = go.Figure(data=[go.Surface(z=z_data, x=[f"{w * 100:.1f}%" for w in wacc_steps], y=[f"{g * 100:.1f}%" for g in g_steps], colorscale='RdYlGn')])
            fig_3d.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                 scene=dict(xaxis_title='WACC', yaxis_title='Growth', zaxis_title='Intrinsic Value', camera=dict(eye=dict(x=1.5, y=-1.5, z=0.5))),
                                 margin=dict(l=0, r=0, b=0, t=0), height=600)
            show_chart(fig_3d)

            st.subheader("Monte Carlo Simulation (10,000 Scenarios)")
            if has_sim:
                st.caption(f"Each scenario randomly varies growth (±2 points) and WACC (±1 point). {len(sim_prices):,} valid scenarios were used. Results are repeatable (fixed random seed).")
                fig_mc = px.histogram(sim_prices, nbins=100, color_discrete_sequence=['#38bdf8'])
                fig_mc.add_vline(x=p10, line_dash="dash", line_color="#f87171", annotation_text=f"10th PCTL: {currency}{p10:.2f}")
                fig_mc.add_vline(x=p50, line_dash="solid", line_color="#34d399", annotation_text=f"MEDIAN: {currency}{p50:.2f}")
                fig_mc.add_vline(x=p90, line_dash="dash", line_color="#34d399", annotation_text=f"90th PCTL: {currency}{p90:.2f}")
                fig_mc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Simulated Intrinsic Value", yaxis_title="Frequency", showlegend=False)
                show_chart(fig_mc)
            else:
                st.warning("Not enough valid scenarios to run the simulation. Check that shares outstanding is above zero and WACC is comfortably above terminal growth.")

        # ---------- peer-based values (used by Football Field and Peers) ----------
        eps, ebitda = live_data.get("eps"), live_data.get("ebitda")
        pe_list = [r["P/E"] for r in peer_rows if r["P/E"]]
        ev_list = [r["EV/EBITDA"] for r in peer_rows if r["EV/EBITDA"]]
        pe_range = (min(pe_list) * eps, max(pe_list) * eps, float(np.median(pe_list)) * eps) if (pe_list and eps and eps > 0) else None
        def ev_to_price(m):
            return (m * ebitda - debt + cash) / shares
        ev_range = (ev_to_price(min(ev_list)), ev_to_price(max(ev_list)), ev_to_price(float(np.median(ev_list)))) if (ev_list and ebitda and ebitda > 0 and shares > 0) else None

        # ---------- 5. FOOTBALL FIELD ----------
        with tab_ff:
            st.subheader("Football Field: Valuation Ranges vs. Market Price")
            ff = []
            vv = [v for v in values.values() if v is not None]
            if len(vv) >= 2:
                ff.append(("DCF scenarios (bear to bull)", min(vv), max(vv), values.get("Base")))
            if has_sim:
                ff.append(("Monte Carlo (10th to 90th pct)", p10, p90, p50))
            if live_data.get("wk_low") and live_data.get("wk_high"):
                ff.append(("52-week trading range", live_data["wk_low"], live_data["wk_high"], None))
            if pe_range:
                ff.append(("Peer P/E (low to high)", pe_range[0], pe_range[1], pe_range[2]))
            if ev_range:
                ff.append(("Peer EV/EBITDA (low to high)", ev_range[0], ev_range[1], ev_range[2]))
            if not ff:
                st.info("Not enough data to draw the chart yet.")
            else:
                palette = ["#38bdf8", "#818cf8", "#64748b", "#34d399", "#f472b6"]
                fig_ff = go.Figure()
                for i, (label, lo, hi, mid) in enumerate(ff):
                    lo, hi = min(lo, hi), max(lo, hi)
                    fig_ff.add_trace(go.Bar(y=[label], x=[hi - lo], base=[lo], orientation="h", marker_color=palette[i % len(palette)],
                                            text=f"{currency}{lo:,.0f} – {currency}{hi:,.0f}", textposition="inside", hoverinfo="text", hovertext=f"{label}: {currency}{lo:,.2f} to {currency}{hi:,.2f}"))
                    if mid is not None:
                        fig_ff.add_trace(go.Scatter(x=[mid], y=[label], mode="markers", marker=dict(symbol="diamond", size=12, color="#ffffff"), hoverinfo="skip"))
                fig_ff.add_vline(x=current_price, line_dash="dash", line_color="#fbbf24", annotation_text=f"Price {currency}{current_price:,.2f}")
                fig_ff.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False,
                                     yaxis=dict(autorange="reversed"), xaxis_title=f"Value per share ({currency})", height=120 + 70 * len(ff))
                show_chart(fig_ff)
                st.caption("Bars show each method's range; the white diamond marks its central value. The dashed line is today's market price. Peer-based bars need live earnings data and peer multiples.")

        # ---------- 6. PEERS ----------
        with tab_peer:
            st.subheader("Peer Comparison")
            own_pe = current_price / eps if (eps and eps > 0) else None
            own_ev = ((current_price * shares + debt - cash) / ebitda) if (ebitda and ebitda > 0 and shares > 0) else None
            peer_df = pd.DataFrame()
            if peer_rows:
                rows = [{"Ticker": user_ticker.upper() + " (this company)", "Name": "", "P/E": own_pe, "EV/EBITDA": own_ev}] + peer_rows
                rows.append({"Ticker": "Peer median", "Name": "", "P/E": float(np.median(pe_list)) if pe_list else None, "EV/EBITDA": float(np.median(ev_list)) if ev_list else None})
                peer_df = pd.DataFrame(rows)
                show_df = peer_df.copy()
                for c in ["P/E", "EV/EBITDA"]:
                    show_df[c] = show_df[c].map(lambda x: "n/a" if x is None or pd.isna(x) else f"{x:.1f}x")
                st.dataframe(show_df, hide_index=True)
                if pe_range:
                    st.write(f"**Implied value from peer P/E:** {money(pe_range[0], currency)} to {money(pe_range[1], currency)} per share (median multiple gives {money(pe_range[2], currency)}).")
                if ev_range:
                    st.write(f"**Implied value from peer EV/EBITDA:** {money(ev_range[0], currency)} to {money(ev_range[1], currency)} per share (median multiple gives {money(ev_range[2], currency)}).")
                if not pe_range and not ev_range:
                    st.caption("Peer multiples loaded, but this company's earnings data was not available from Yahoo Finance, so no implied values can be shown.")
            else:
                st.info("No peer data loaded. Add peer tickers in the settings above the tabs and keep the fetch toggle on.")
            st.caption("Multiples are only comparable between similar businesses. Banks and conglomerates in particular are hard to compare this way.")

        # ---------- 7. SUMMARY & EXPORT ----------
        with tab_sum:
            st.subheader("Automated Analyst Summary")
            st.caption("This summary is generated automatically from the numbers in the app using fixed rules. It is not an AI model.")
            with st.chat_message("assistant"):
                st.write(f"Here is a breakdown of **{user_ticker if user_ticker else 'the selected asset'}**:")
                st.write("### 1. Base case")
                if results["is_undervalued"]:
                    st.success(f"Under your assumptions the intrinsic value is **{money(results['intrinsic_value'], currency)}**, so the stock appears **undervalued by {results['diff_percentage']:.1f}%**.")
                else:
                    st.error(f"Under your assumptions the intrinsic value is **{money(results['intrinsic_value'], currency)}**, so the stock appears **overvalued by {abs(results['diff_percentage']):.1f}%**.")
                st.write("### 2. Range of outcomes")
                if weighted is not None:
                    st.write(f"- Probability-weighted value across bear, base and bull cases: **{money(weighted, currency)}**.")
                if has_sim:
                    st.write(f"- In **{prob_undervalued:.1f}%** of {len(sim_prices):,} Monte Carlo scenarios the intrinsic value is above the market price. The 10th to 90th percentile range is {money(p10, currency)} to {money(p90, currency)}.")
                if implied_g is not None:
                    st.write(f"- The market price implies about **{implied_g * 100:.1f}%** annual growth for 5 years, compared with your **{growth_rate * 100:.1f}%**.")
                st.write("### 3. The bridge")
                st.write(f"- Present value of 5 years of cash flow: **{money(results['pv_fcf_5yr'], currency, 0)} {unit}**.")
                st.write(f"- Present value of the terminal value: **{money(results['pv_terminal_value'], currency, 0)} {unit}**.")
                st.write(f"- Plus {money(cash, currency, 0)} {unit} cash, minus {money(debt, currency, 0)} {unit} debt, gives equity value of **{money(results['equity_value'], currency, 0)} {unit}**.")

            st.subheader("Download Report")
            cash_flows = pd.DataFrame([{"Year": t, f"Free cash flow ({unit})": round(fcf_base * (1 + growth_rate) ** t, 2),
                                        f"Present value ({unit})": round(fcf_base * (1 + growth_rate) ** t / (1 + discount_rate) ** t, 2)} for t in range(1, 6)])
            summary_rows = [("Company / ticker", user_ticker.upper()), ("Report date", str(date.today())), ("Currency / unit", f"{currency} / {unit}"),
                            ("Market price", round(current_price, 2)), ("Base FCF", round(fcf_base, 2)), ("Cash", round(cash, 2)), ("Debt", round(debt, 2)),
                            ("Shares outstanding", round(shares, 2)), ("Growth rate %", round(growth_rate * 100, 2)), ("Discount rate %", round(discount_rate * 100, 2)),
                            ("Discount rate method", mode), ("Terminal growth %", round(terminal_growth * 100, 2)),
                            ("Intrinsic value per share", round(results["intrinsic_value"], 2)), ("Upside / (downside) %", round(results["diff_percentage"], 1)),
                            ("Enterprise value", round(results["enterprise_value"], 2)), ("Equity value", round(results["equity_value"], 2)),
                            ("Probability-weighted value", None if weighted is None else round(weighted, 2)),
                            ("Market-implied growth %", None if implied_g is None else round(implied_g * 100, 2)),
                            ("Monte Carlo: P(value > price) %", None if prob_undervalued is None else round(prob_undervalued, 1))]
            xlsx = build_excel(summary_rows, cash_flows, scen_df, peer_df if peer_rows else None)
            fname = f"AutoValuer_{(user_ticker or 'report').upper().replace('.', '_')}"
            if xlsx:
                st.download_button("⬇️ Download Excel report", data=xlsx, file_name=fname + ".xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.download_button("⬇️ Download summary (CSV)", data=pd.DataFrame(summary_rows, columns=["Item", "Value"]).to_csv(index=False), file_name=fname + ".csv", mime="text/csv")

        # ---------- 8. METHODOLOGY ----------
        with tab_meth:
            st.subheader("Methodology & Limitations")
            st.markdown("""
**Discounted cash flow (DCF).** Free cash flow (FCF) is projected for 5 years at the growth rate. A terminal value, `FCF in year 5 x (1 + terminal growth) / (WACC - terminal growth)`, captures all later years. Everything is discounted to today at the discount rate. Enterprise value plus cash minus debt gives equity value, and dividing by shares gives value per share.

**Discount rate.** Three options. *Manual* uses the slider. *CAPM* uses `risk-free rate + beta x (market return - risk-free rate)`, which is the cost of equity. *Full WACC* blends the cost of equity with the after-tax cost of debt using market-value weights (market capitalisation and book debt).

**Reverse DCF.** Solves, by repeated bisection, for the 5-year growth rate at which the DCF value equals today's price. It shows what the market is assuming rather than what you assume.

**Scenarios.** Bear and bull cases shift growth and WACC from your base case. The probability-weighted value uses the probabilities you enter.

**Monte Carlo.** 10,000 random draws of growth (standard deviation 2 points) and WACC (1 point), with a fixed seed so results are repeatable. Scenarios where WACC is not above terminal growth are discarded.

**Football field and peers.** Ranges from the DCF scenarios, the simulation, the 52-week range, and peer P/E and EV/EBITDA multiples applied to this company's earnings and EBITDA. Peer multiples are only meaningful for comparable businesses.

**Data and limitations.**
- Prices and financials come from Yahoo Finance and can be delayed, incomplete or wrong. The app shows which inputs are live and which are preset.
- Unit scale: millions for US tickers, crore for `.NS` and `.BO` tickers.
- A DCF depends heavily on growth, WACC and terminal growth; small changes move the answer a lot.
- The default risk-free rate is the US 10-year Treasury yield, even for Indian stocks, and cost of debt and tax rates are assumptions you can edit.
- Historical growth is a reference, not a forecast.
- This tool is for learning and demonstration. It is not investment advice.
""")

    interactive_valuation_engine(fcf_base, cash, debt, shares, current_price, currency, unit, live_data, is_indian, user_ticker)
    st.markdown('<div class="foot">AutoValuer Terminal · For learning and demonstration only · Not investment advice</div>', unsafe_allow_html=True)
