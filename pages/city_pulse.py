import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="City Pulse", layout="wide")

# Underline all headers via CSS
st.markdown(
    """
    <style>
    h1, h2, h3, h4 {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("City Pulse: Economic Health by Location")

st.markdown("This dashboard highlights unemployment rates and recent disaster events for key cities.")

# --- FRED Unemployment series ---
city_fred_series = {
    "Richmond, VA":      "VARICH0URN",
    "Owings Mills, MD":  "MDBALT5URN",
    "Sandy Springs, GA": "ATLA013URN",
    "Greenville, SC":    "SCGREE5URN",
    "Charlotte, NC":     "CHAR737URN"
}

# --- City selection ---
selected_cities = st.multiselect(
    "Select Cities to View Current Unemployment",
    options=list(city_fred_series.keys()),
    default=list(city_fred_series.keys()),
    key="current_city_select"
)

# --- News Screener for Selected Cities ---
st.subheader("City News Screener")

@st.cache_data
def fetch_city_news(city):
    try:
        api_key = st.secrets["NEWS_API_KEY"]
        url = f"https://newsapi.org/v2/everything?q={city}&language=en&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
        response = requests.get(url)
        articles = response.json().get("articles", [])
        return articles
    except Exception as e:
        st.error(f"Error fetching news for {city}: {e}")
        return []

for city in selected_cities:
    st.markdown(f"#### ️{city}")
    articles = fetch_city_news(city)
    if articles:
        for article in articles:
            st.markdown(f"- [{article['title']}]({article['url']})")
    else:
        st.write("No recent headlines — check back later or view FEMA alerts below.")



# --- FRED Unemployment series ---
city_fred_series = {
    "Richmond, VA":      "VARICH0URN",
    "Owings Mills, MD":  "MDBALT5URN",
    "Sandy Springs, GA": "ATLA013URN",
    "Greenville, SC":    "SCGREE5URN",
    "Charlotte, NC":     "CHAR737URN"
}

FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

@st.cache_data
def fetch_unemployment(series_id, start_date="2024-01-01"):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date
    }
    try:
        response = requests.get(url, params=params, timeout=10).json()
        df = pd.DataFrame(response.get("observations", []))
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df[["date", "value"]].dropna()
    except:
        return pd.DataFrame(columns=["date", "value"])

# --- Latest Unemployment ---
st.subheader("Latest Unemployment Rates")
unemp_rows = []
for city in selected_cities:
    df = fetch_unemployment(city_fred_series[city])
    if not df.empty:
        latest = df.iloc[-1]
        unemp_rows.append({
            "City": city,
            "Date": latest["date"].strftime("%Y-%m-%d"),
            "Unemployment Rate (%)": latest["value"]
        })
if unemp_rows:
    df_latest = pd.DataFrame(unemp_rows).set_index("City")
    st.dataframe(df_latest)
else:
    st.write("No unemployment data available.")

st.divider()

# --- Historical Trends ---
st.subheader("Historical Unemployment Trends")
chart_cities = st.multiselect(
    "Select Cities for Historical Line Chart",
    options=list(city_fred_series.keys()),
    default=["Richmond, VA", "Charlotte, NC"],
    key="line_chart_select"
)
if chart_cities:
    chart_df = pd.DataFrame()
    for city in chart_cities:
        df = fetch_unemployment(city_fred_series[city])
        if not df.empty:
            df = df.rename(columns={"value": city})
            if chart_df.empty:
                chart_df = df[["date", city]]
            else:
                chart_df = pd.merge(chart_df, df[["date", city]], on="date", how="outer")
    if not chart_df.empty:
        chart_df = chart_df.sort_values("date").set_index("date")
        st.line_chart(chart_df, use_container_width=True)
    else:
        st.write("No historical data available.")

st.divider()

# --- FEMA Disasters ---
st.subheader("FEMA Disaster Events (2024–Present)")

@st.cache_data
def get_fema_events():
    url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
    params = {
        "$filter": "declarationDate ge '2024-01-01' and state in ('VA','NC','MD','SC','GA') and incidentType ne null",
        "$orderby": "declarationDate desc",
        "$format": "json"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("DisasterDeclarationsSummaries") or data.get("value") or []
    except:
        return []

disaster_events = get_fema_events()
for city in selected_cities:
    st.markdown(f"#### {city}")
    state = city.split(",")[1].strip()
    state_events = [e for e in disaster_events if e.get("state") == state]
    seen = set()
    unique_events = []
    for e in state_events:
        key = (e.get("incidentType"), e.get("declarationDate"))
        if key not in seen:
            seen.add(key)
            unique_events.append(e)
    if unique_events:
        for e in unique_events:
            inc_type = e.get("incidentType", "Unknown")
            begin = (e.get("incidentBeginDate") or "")[:10]
            end = (e.get("incidentEndDate") or "")[:10]
            area = e.get("designatedArea") or ""
            decl = (e.get("declarationDate") or "")[:10]
            st.markdown(f"- **{inc_type}** ({begin} to {end}) in {area}, declared on {decl}")
    else:
        st.write("No recent FEMA disaster events since Jan 2024.")
