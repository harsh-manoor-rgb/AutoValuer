# AutoValuer Terminal

**Equity valuation and risk analytics web app, built with Python and Streamlit.**

AutoValuer estimates what a stock is worth with a **Discounted Cash Flow (DCF)** model, compares it with the market price, and then tests how reliable that answer is. It goes beyond a single number: it shows what growth the market price is assuming, how the value changes in bear, base and bull cases, and how the result compares with peer multiples.

**Live demo:** https://autovaluer-live.onrender.com/
(Hosted on a free plan, so the first load may take about a minute while the app wakes up.)

![AutoValuer screenshot](screenshot.png)

---

## Features

| Tab | What it does |
|---|---|
| **Valuation** | Enterprise-to-equity waterfall and a cash flow projection (nominal vs. discounted) |
| **Scenarios** | Bear / base / bull cases with editable growth and WACC shifts and probabilities, plus a probability-weighted value |
| **Reverse DCF** | Solves for the 5-year growth rate that today's price implies, and compares it with your assumption |
| **Risk Analysis** | Interactive 3D valuation surface (WACC vs. growth) and a 10,000-scenario Monte Carlo simulation |
| **Football Field** | One chart comparing DCF scenarios, Monte Carlo range, 52-week range and peer-multiple ranges against the market price |
| **Peers** | P/E and EV/EBITDA for the company and its peers, with the implied value per share |
| **Summary & Export** | Rule-based written summary and a downloadable Excel report |
| **Methodology** | Formulas, assumptions and limitations explained in plain language |

### Other features
- **Three discount-rate methods:** manual WACC, CAPM cost of equity (live beta and Treasury yield, editable), or a full WACC that blends cost of equity with after-tax cost of debt.
- **Historical growth reference:** shows the company's past FCF and revenue growth, with an option to start from it.
- **Live data with an honest fallback:** inputs come from Yahoo Finance via `yfinance`. If something is unavailable, the app uses a preset figure and clearly labels which inputs are live and which are presets.
- **Shareable links:** the address bar updates with the selected company, so a link opens straight to that valuation.
- Automatic currency and units (Rs. and crore for `.NS` / `.BO` tickers; $ and millions otherwise).

## Example

Apple Inc. (AAPL) with the app's preset inputs and default assumptions: base free cash flow $95,000M, cash $150,000M, debt $110,000M, 15,200M shares, 10% growth, 8.5% WACC, 3% terminal growth.

| Result | Value |
|---|---|
| Intrinsic value per share | $160.56 |
| Market price (live when captured) | $336.67 |
| Verdict | Overvalued (about 52% downside) |

The Reverse DCF tab then shows what growth rate would be needed to justify the market price. This is an illustration of how the tool works, not a recommendation.

## How the valuation works

1. Project free cash flow for 5 years using the growth rate.
2. Terminal value = Year 5 cash flow x (1 + terminal growth) / (WACC - terminal growth).
3. Discount everything to today at WACC.
4. Equity value = enterprise value + cash - debt; divide by shares for the value per share.

## Limitations

- A DCF is only as reliable as its assumptions; small changes in growth or WACC move the answer a lot.
- Yahoo Finance data can be delayed, incomplete or wrong. Peer multiples are only meaningful for comparable businesses.
- The default risk-free rate is the US 10-year yield, even for Indian stocks; cost of debt and tax rate are editable assumptions.
- Historical growth is a reference, not a forecast.

## Tech stack

Python, Streamlit, Plotly, NumPy, pandas, yfinance, openpyxl. Deployed on Render.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | The whole application: interface, valuation logic, charts and export |
| `requirements.txt` | Python libraries needed to run the app |

## Run it on your own computer

1. Install Python from python.org.
2. Download this repository (green **Code** button, then **Download ZIP**) and unzip it.
3. In a terminal in that folder run `pip install -r requirements.txt`
4. Start the app with `streamlit run app.py`

## Disclaimer

For learning and demonstration only. **Not investment advice.**

## Author

**Harshdeep Singh**, BSc Economics (Hons), Lovely Professional University
LinkedIn: https://www.linkedin.com/in/harsh-manoor

Special thanks to Ajitesh and Jai (Gemini).
