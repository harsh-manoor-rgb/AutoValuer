# AutoValuer Terminal

**Equity valuation and risk analytics web app, built with Python and Streamlit.**

AutoValuer estimates what a stock is worth using a **Discounted Cash Flow (DCF)** model, then compares that value with the current market price to say whether the stock looks **undervalued** or **overvalued**. It also stress-tests the answer with a 3D sensitivity surface and a Monte Carlo simulation, so you can see how much the result depends on your assumptions.

**Live demo:** https://autovaluer-live.onrender.com/
(Hosted on a free plan, so the first load may take about a minute while the app wakes up.)

![AutoValuer screenshot](screenshot.png)

---

## Features

- **DCF valuation:** Projects free cash flow for 5 years, adds a terminal value (Gordon Growth method), and discounts everything to today using the discount rate (WACC).
- **Live market data:** Fetches the current share price from Yahoo Finance (via `yfinance`) for any ticker. It also tries to fetch free cash flow, cash, debt and shares outstanding. If any of these are unavailable, the app falls back to built-in preset figures, tells you which inputs are live and which are presets, and lets you edit every input by hand.
- **CAPM discount rate (optional toggle):** Estimates a discount rate from the stock's live beta and the live US 10-year Treasury yield: `risk-free rate + beta x (expected market return - risk-free rate)`. The risk-free rate and expected market return can both be edited.
- **Automatic currency and units:** Indian tickers (`.NS`, `.BO`) are shown in Rs. and crore; all others in $ and millions.
- **Preset companies:** Apple, Microsoft, NVIDIA, Tata Motors, Reliance, HDFC Bank, plus a custom ticker option.
- **Instant updates:** Sliders for growth, discount rate and terminal growth recalculate everything without reloading the page.

### Analysis tabs

| Tab | What it shows |
|---|---|
| Enterprise Waterfall | How value builds from 5-year cash flows and terminal value to enterprise value, then to equity value after adding cash and subtracting debt |
| Dynamic Projections | Projected cash flow versus its discounted present value over a timeline of up to 50 years |
| 3D Risk Surface | Interactive 3D surface of intrinsic value across different WACC and growth rates (a 15 x 15 grid) |
| Monte Carlo Engine | 10,000 randomised scenarios with varying growth and WACC; shows the 10th, 50th and 90th percentile values and the probability that the stock is undervalued (fixed random seed, so results are repeatable) |
| Analyst Summary | An automatically generated plain-English summary of the results (rule-based text, not an AI model) |

## Example

Apple Inc. (AAPL), using the app's preset inputs and default assumptions:

| Input | Value |
|---|---|
| Base free cash flow | $95,000M |
| Total cash | $150,000M |
| Total debt | $110,000M |
| Shares outstanding | 15,200M |
| Growth rate | 10% |
| WACC (discount rate) | 8.5% |
| Terminal growth | 3% |

| Result | Value |
|---|---|
| Intrinsic value per share | $160.56 |
| Market price (live when captured) | $336.67 |
| Verdict | Overvalued (about 52% downside) |

This only illustrates how the tool works. The result depends heavily on the assumptions chosen, which is why the app includes the risk surface and Monte Carlo simulation.

## How the valuation works

1. Project free cash flow for 5 years using the growth rate.
2. Terminal value = Year 5 cash flow x (1 + terminal growth) / (WACC - terminal growth).
3. Discount all cash flows and the terminal value to today using WACC.
4. Enterprise value = present value of the 5-year cash flows + present value of the terminal value.
5. Equity value = enterprise value + cash - debt.
6. Intrinsic value per share = equity value / shares outstanding.

## Limitations

- A DCF is only as reliable as its assumptions; small changes in WACC or growth move the result a lot.
- The CAPM option gives the cost of equity (it does not blend in the cost of debt). The market return defaults to 10% and the risk-free rate defaults to the live US 10-year Treasury yield, even for Indian companies; both can be edited, and Indian stocks should use an Indian rate.
- Yahoo Finance data can be incomplete or delayed.

## Tech stack

Python, Streamlit, Plotly, NumPy, pandas, yfinance. Deployed on Render.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | The whole application: interface, DCF calculation, charts and simulations |
| `requirements.txt` | Python libraries needed to run the app |

## Run it on your own computer

1. Install Python from python.org.
2. Download this repository (green **Code** button, then **Download ZIP**) and unzip it.
3. Open a terminal in that folder and install the libraries:
   ```
   pip install -r requirements.txt
   ```
4. Start the app:
   ```
   streamlit run app.py
   ```
5. Your browser will open the app automatically.

## Disclaimer

This project is for learning and demonstration only. It is **not investment advice**.

## Author

**Harshdeep Singh**, BSc Economics (Hons), Lovely Professional University
LinkedIn: https://www.linkedin.com/in/harsh-manoor

Special thanks to Ajitesh and Jai (Gemini).
