
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import investpy

st.set_page_config(page_title="Economic Calendar", layout="wide")
st.title("U.S. Economic Calendar")

# ---- Month & Year Picker ----
today = datetime.today()
min_year = 2024
max_year = today.year + 1

years = list(range(min_year, max_year + 1))
months = list(calendar.month_name)[1:]

col1, col2 = st.columns(2)
selected_year = col1.selectbox("Select Year", years, index=years.index(today.year), key="year_select")
selected_month = col2.selectbox("Select Month", months, index=today.month - 1, key="month_select")
month_number = months.index(selected_month) + 1

# ---- Date Formatting ----
start_date = f"01/{month_number:02d}/{selected_year}"
end_day = calendar.monthrange(selected_year, month_number)[1]
end_date = f"{end_day}/{month_number:02d}/{selected_year}"

# ---- Fetch Economic Events ----
try:
    cal_df = investpy.economic_calendar(
        from_date=start_date,
        to_date=end_date,
        countries=["United States"],
        importances=["high", "medium"]
    )
except Exception as e:
    st.error(f"Could not fetch calendar data: {e}")
    cal_df = pd.DataFrame()

# ---- Filter by Event Type with Select All Option ----
event_types = sorted(cal_df['event'].unique()) if not cal_df.empty else []

# Sync default safely to options
cached_filter = st.session_state.get("event_filter", [])
default_event_filter = [et for et in cached_filter if et in event_types]

select_all = st.checkbox("Select All Events", value=len(default_event_filter) == len(event_types))

if select_all:
    selected_types = st.multiselect(
        "Filter by Event Type",
        event_types,
        default=event_types,
        key="event_type_selector"
    )
else:
    selected_types = st.multiselect(
        "Filter by Event Type",
        event_types,
        default=default_event_filter,
        key="event_type_selector"
    )

st.session_state["event_filter"] = selected_types
cal_df = cal_df[cal_df['event'].isin(selected_types)]

# ---- Build Calendar Grid ----
cal_df['parsed_date'] = pd.to_datetime(cal_df['date'], dayfirst=True)
events = {}
for _, row in cal_df.iterrows():
    day = row['parsed_date'].day
    label = row['event']
    label_lower = label.lower()
    if label_lower.startswith('us holiday'):
        color = 'mediumorchid'
    elif row.get('importance') == 'high':
        color = 'lightcoral'
    else:
        color = 'lightblue'
    events.setdefault(day, []).append((label, color))

calendar_grid = []
first_day, num_days = calendar.monthrange(selected_year, month_number)
week = [""] * first_day
for day in range(1, num_days + 1):
    week.append(day)
    if len(week) == 7:
        calendar_grid.append(week)
        week = []
if week:
    week += [""] * (7 - len(week))
    calendar_grid.append(week)

# ---- Render HTML ----
calendar_html = f"""
<style>
.calendar {{
    font-family: Arial, sans-serif;
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}}
.calendar th {{
    background: #333;
    color: white;
    padding: 10px;
}}
.calendar td {{
    height: 120px;
    vertical-align: top;
    border: 1px solid #888;
    padding: 4px;
    font-size: 14px;
}}
.event {{
    margin: 2px 0;
    padding: 2px 4px;
    border-radius: 4px;
    font-size: 12px;
    color: #000;
}}
</style>

<h3>{selected_month} {selected_year}</h3>
<table class='calendar'>
<tr>
{''.join([f"<th>{day}</th>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]])}
</tr>
"""

for week in calendar_grid:
    calendar_html += "<tr>"
    for day in week:
        if day == "":
            calendar_html += "<td></td>"
        else:
            event_html = ""
            if day in events:
                for title, color in events[day]:
                    event_html += f"<div class='event' style='background:{color};'>{title}</div>"
            calendar_html += f"<td><strong>{day}</strong><br>{event_html}</td>"
    calendar_html += "</tr>"

calendar_html += "</table><br><strong>Legend:</strong> High (coral), Medium (blue), U.S. Holiday (purple)"

st.markdown(calendar_html, unsafe_allow_html=True)
