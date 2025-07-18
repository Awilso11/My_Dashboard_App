
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime

# Always use dark
is_dark = True

# Unified dark background & text
card_bg   = bg_color = "#0B1021"
txt_color = "#FFFFFF"

st.markdown(f"""
<style>
  /* main app background */
  [data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
  }}
  /* sidebar background */
  [data-testid="stSidebar"] {{
    background-color: {bg_color} !important;
  }}
  /* top toolbar (hamburger menu area) */
  [data-testid="stToolbar"] {{
    background-color: {bg_color} !important;
  }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'''
    <style>
        .metric-box {{
            padding: 1.5rem;
            border-radius: 10px;
            background-color: {card_bg};
            color: {txt_color};
            text-align: center;
            border: 1px solid {'#333' if is_dark else '#ddd'};
            font-size: 1.3rem;
        }}
        .bullish {{
            color: #32CD32;
            font-weight: bold;
            font-size: 2.5rem;
        }}
        .bearish {{
            color: #FF6B6B;
            font-weight: bold;
            font-size: 2.5rem;
        }}
    </style>
''', unsafe_allow_html=True)


FRED_API_KEY = st.secrets["FRED_API_KEY"]
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

def fetch_fred_latest(series_id):
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json", "sort_order": "desc", "limit": 1}
    resp = requests.get(FRED_BASE, params=params).json().get("observations", [])
    if resp:
        val, date = resp[0]["value"], resp[0]["date"]
        return val, pd.to_datetime(date).strftime("%b %d, %Y")
    return "N/A", "N/A"

def make_gauge(val):
    # Use the same dark card background
    bg = card_bg

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=val,
        number={"font": {"color": txt_color, "size": 48}},
        title={"text": "CNN Fear & Greed", "font": {"color": txt_color, "size": 24}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickmode": "array",
                "tickvals": [0, 20, 40, 60, 80, 100],
                "tickfont": {"color": txt_color}
            },
            "bar": {"color": "rgba(0,0,0,0)"},
            "steps": [
                {"range": [0, 20],  "color": "#8B0000"},
                {"range": [20, 40], "color": "#FF6347"},
                {"range": [40, 60], "color": "#32CD32"},
                {"range": [60, 80], "color": "#228B22"},
                {"range": [80, 100],"color": "#006400"}
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": val
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font={"color": txt_color},
        title_font_color=txt_color,
        margin=dict(l=0, r=0, t=40, b=0),
        height=400
    )
    return fig


col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("## Richmond Concierge Health")
    st.markdown("### Live Economic Dashboard")
with col2:
    st.markdown(f'<a href="/calendar" target="_self">{datetime.now():%B %d, %Y}</a>', unsafe_allow_html=True)

metrics = {
    "U.S. Unemployment": ("UNRATE", "bearish"),
    "Richmond Unemployment": ("RICH051URN", "bearish"),
    "Charlotte Unemployment": ("CHAR737URN", "bearish"),
    "Fed Funds Rate": ("FEDFUNDS", "bullish"),
    "Michigan Consumer Sentiment": ("UMCSENT","bullish")
}
def fetch_inflation_yoy():
    params = {
        "series_id": "CPIAUCSL",
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 13
    }
    resp = requests.get(FRED_BASE, params=params).json().get("observations", [])
    if len(resp) >= 13:
        latest = float(resp[0]["value"])
        year_ago = float(resp[12]["value"])
        yoy_change = ((latest - year_ago) / year_ago) * 100
        date = pd.to_datetime(resp[0]["date"]).strftime("%b %d, %Y")
        return f"{yoy_change:.1f}%", date
    return "N/A", "N/A"

def fetch_fear_and_greed():
    """
    Return the latest Fear & Greed index (0–100) as an int,
    or None on failure.
    """
    url = "https://api.alternative.me/fng/?limit=1&format=json"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data and "value" in data[0]:
            # API returns the value as a string, e.g. "55"
            return int(data[0]["value"])
    except Exception as e:
        # Optional: log or display the error somewhere
        st.error(f"Error loading Fear & Greed: {e}")
    return None


cols = st.columns(len(metrics) + 1)

for idx, (label, (sid, sentiment)) in enumerate(metrics.items()):
    val, date = fetch_fred_latest(sid)
    html = f'''
    <div class="metric-box">
        <h5>{label}</h5>
        <div class="{sentiment}">{val}</div>
        <small>as of {date}</small>
    </div>'''
    cols[idx].markdown(html, unsafe_allow_html=True)

# Append the CPI YoY chart
cpi_val, cpi_date = fetch_inflation_yoy()
cols[-1].markdown(f"""
    <div class="metric-box">
        <h5>Inflation (YoY CPI)</h5>
        <div class="bearish">{cpi_val}</div>
        <small>as of {cpi_date}</small>
    </div>
""", unsafe_allow_html=True)


st.markdown("### Markets & Sentiment")
chart_col, gauge_col = st.columns([3, 1])

with chart_col:
    st.markdown("---")
    
    # Define theme for TradingView based on current mode
    tv_theme = "dark" if is_dark else "light"
    chart_link = "/stock_market_dashboard"  # Update path if needed

    # Embed TradingView chart
    def embed_tradingview_chart(symbol):
        st.markdown(f"""
        <a href="{chart_link}" target="_self" style="text-decoration: none;">
            <iframe
                src="https://www.tradingview.com/widgetembed/?symbol={symbol}&interval=D&theme={tv_theme}&style=3&withdateranges=1&hide_top_toolbar=1&hideideas=1&toolbarbg=0&studies=[]"
                width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no">
            </iframe>
        </a>
        """, unsafe_allow_html=True)

    # Call the function for SPY
    embed_tradingview_chart("AMEX:SPY")

with gauge_col:
    fng_value = fetch_fear_and_greed()
    if fng_value is not None:
        st.plotly_chart(make_gauge(fng_value), use_container_width=True)
    else:
        st.error("⚠️ Could not load Fear & Greed index")

footer = "<div style='text-align:center;color:gray;'>Data: FRED & Yahoo Finance • Richmond Concierge Health</div>"
st.markdown(footer, unsafe_allow_html=True)

