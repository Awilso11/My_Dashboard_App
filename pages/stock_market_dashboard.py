import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Market Overview", layout="wide")
st.title("Stock Market Overview")
st.markdown("This page monitors the stock market and major economic indicators.")

# Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="data_refresh")

# Add custom spacing style
st.markdown("""
    <style>
        .stColumn {
            padding: 10px !important;
        }
        div[data-testid="column"] > div {
            border-radius: 12px;
            padding: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Define stock tickers
magnificent_7 = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA"
}

key_indices = {
    "^GSPC": "S&P 500"
}

all_cards = {**key_indices, **magnificent_7}

# Define card rendering function BEFORE it's used
def render_stock_card(ticker, label):
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info

        current_price = info.get("lastPrice")
        previous_close = info.get("previousClose")

        if current_price is None or previous_close is None:
            st.error(f"Data not available for {label}")
            return

        change = current_price - previous_close
        percent_change = (change / previous_close) * 100
        is_up = change >= 0
        arrow = "▲" if is_up else "▼"
        color = "#0f9d58" if is_up else "#d93025"  # Green or Red

        chart_link = f"#chart-{ticker.lower()}"

        st.markdown(
            f"""
            <a href="{chart_link}" style="text-decoration: none;">
                <div style='
                    background-color: #1e1e1e;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    margin: 6px;
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                ' onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 4px 10px rgba(0,0,0,0.5)';"
                   onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 2px 5px rgba(0,0,0,0.3)';">
                    <div style='font-size: 18px; color: white; font-weight: 600;'>{label}</div>
                    <div style='font-size: 24px; color: white; margin: 5px 0;'>${current_price:.2f}</div>
                    <div style='color: {color}; font-weight: bold;'>{arrow} {percent_change:.2f}%</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Error loading {label}: {e}")


# Display cards in 2 rows of 4 columns
st.subheader("The Great 8")
card_keys = list(all_cards.keys())
labels = list(all_cards.values())

row1 = st.columns(4)
for i in range(4):
    with row1[i]:
        render_stock_card(card_keys[i], labels[i])

row2 = st.columns(4)
for i in range(4, 8):
    with row2[i - 4]:
        render_stock_card(card_keys[i], labels[i])

 
# --- COMBINED PLOTLY CHARTS (Year + Quarter Filters, 2 per row, Adj Close) ---
import datetime
import calendar
import yfinance as yf
import pandas as pd
import plotly.express as px

st.markdown("---")
st.subheader("Market & Economic Charts")

# 1) Year selector (last 5 years + current)
today = datetime.date.today()
current_year = today.year
years = list(range(current_year - 5, current_year + 1))
selected_year = st.selectbox("Select Year", years, index=len(years)-1, key="year_filter")

# 2) Quarter selector (with year shown)
quarter_defs = {
    "Q1 (Jan–Mar)": (1, 3),
    "Q2 (Apr–Jun)": (4, 6),
    "Q3 (Jul–Sep)": (7, 9),
    "Q4 (Oct–Dec)": (10, 12),
    "Full Year":    (1, 12)
}
# build labels like "2025 Q1 (Jan–Mar)"
quarter_labels = list(quarter_defs.keys())
quarter_display = [f"{selected_year} {q}" for q in quarter_labels]
selected_q_disp = st.selectbox("Select Quarter", quarter_display, key="quarter_filter")
# pull out the quarter portion ("Q2 (Apr–Jun)")
_, quarter_label = selected_q_disp.split(" ", 1)

# 3) Compute start/end dates (clamped to today)
q_start, q_end = quarter_defs[quarter_label]
start_date = datetime.date(selected_year, q_start, 1)
last_day = calendar.monthrange(selected_year, q_end)[1]
end_date   = datetime.date(selected_year, q_end, last_day)
if end_date > today:
    end_date = today
# yfinance's end is exclusive, so add one day to include today's bar
end_query = end_date + datetime.timedelta(days=1)

st.markdown(f"**Showing data from {start_date} to {end_date}**")

# 4) All tickers in one dict
plot_tickers = {
    # Magnificent 7
    "AAPL":   "Apple",
    "MSFT":   "Microsoft",
    "GOOGL":  "Alphabet",
    "AMZN":   "Amazon",
    "META":   "Meta",
    "TSLA":   "Tesla",
    "NVDA":   "NVIDIA",
    # Key index
    "^GSPC":  "S&P 500",
    # Economic proxies
    "^VIX":   "VIX",
    "^DJI":   "Dow Jones",
    "TIP":    "Inflation",
    "UNG":    "Unemployment",
    "GDP":    "GDP",
    "TLT":    "Federal Debt"
}

# 5) Draw two charts per row
items = list(plot_tickers.items())
for i in range(0, len(items), 2):
    cols = st.columns(2)
    for col, (ticker, label) in zip(cols, items[i : i + 2]):
        # fetch & trim
        raw = yf.download(ticker, start=start_date, end=end_query)
        raw.index = pd.to_datetime(raw.index)
        raw = raw[raw.index <= pd.Timestamp(today)]

        # pick Adj Close if available, else fall back to Close
        if "Adj Close" in raw.columns:
            series = raw["Adj Close"]
        else:
            series = raw.get("Close", raw.iloc[:, 0])

        # build two‑col DataFrame
        df_plot = series.reset_index()
        df_plot.columns = ["Date", "Price"]

        # plot
        fig = px.line(
            df_plot,
            x="Date",
            y="Price",
            title=label,
            labels={"Price": "Price (USD)", "Date": "Date"}
        )
        fig.update_layout(
            xaxis=dict(tickformat="%b %d", showgrid=True, gridcolor="lightgray"),
            yaxis=dict(title="Price"),
            margin=dict(l=20, r=20, t=40, b=30),
            height=350
        )

        with col:
            st.plotly_chart(fig, use_container_width=True)

