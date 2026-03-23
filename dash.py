import streamlit as st
import pandas as pd
from datetime import timedelta, datetime

# Page config
st.set_page_config(page_title="YouTube Channel Dashboard", layout="wide")

# -------------------- LOAD DATA --------------------
@st.cache_data
def load_data():
    data = pd.read_csv("C:/Users/mohit_zswpgpr/Downloads/youtube_channel_data.csv")
    data['DATE'] = pd.to_datetime(data['DATE'])
    data['NET_SUBSCRIBERS'] = data['SUBSCRIBERS_GAINED'] - data['SUBSCRIBERS_LOST']
    return data

df = load_data()

# -------------------- CUSTOM QUARTER --------------------
def custom_quarter(date):
    month = date.month
    year = date.year
    if month in [2, 3, 4]:
        return pd.Period(year=year, quarter=1, freq='Q')
    elif month in [5, 6, 7]:
        return pd.Period(year=year, quarter=2, freq='Q')
    elif month in [8, 9, 10]:
        return pd.Period(year=year, quarter=3, freq='Q')
    else:
        return pd.Period(year=year if month != 1 else year - 1, quarter=4, freq='Q')

# -------------------- AGGREGATION --------------------
def aggregate_data(df, freq):
    if freq == 'Q':
        df['CUSTOM_Q'] = df['DATE'].apply(custom_quarter)
        df_agg = df.groupby('CUSTOM_Q').agg({
            'VIEWS': 'sum',
            'WATCH_HOURS': 'sum',
            'NET_SUBSCRIBERS': 'sum',
            'LIKES': 'sum',
            'COMMENTS': 'sum',
            'SHARES': 'sum'
        })
        return df_agg
    else:
        return df.resample(freq, on='DATE').agg({
            'VIEWS': 'sum',
            'WATCH_HOURS': 'sum',
            'NET_SUBSCRIBERS': 'sum',
            'LIKES': 'sum',
            'COMMENTS': 'sum',
            'SHARES': 'sum'
        })

def get_weekly_data(df):
    return aggregate_data(df, 'W-MON')

def get_monthly_data(df):
    return aggregate_data(df, 'M')

def get_quarterly_data(df):
    return aggregate_data(df, 'Q')

# -------------------- UTIL FUNCTIONS --------------------
def format_with_commas(number):
    return f"{int(number):,}"

def create_metric_chart(df, column, color, chart_type, height=150, time_frame='Daily'):
    chart_data = df[[column]].copy()

    if time_frame == 'Quarterly':
        chart_data.index = chart_data.index.astype(str)

    if chart_type == 'Bar':
        st.bar_chart(chart_data, height=height)
    elif chart_type == 'Area':
        st.area_chart(chart_data, height=height)

def is_period_complete(date, freq):
    today = datetime.now()

    if freq == 'D':
        return date.date() < today.date()
    elif freq == 'W':
        return date + timedelta(days=6) < today
    elif freq == 'M':
        next_month = date.replace(day=28) + timedelta(days=4)
        return next_month.replace(day=1) <= today
    elif freq == 'Q':
        current_quarter = custom_quarter(today)
        return date < current_quarter

def calculate_delta(df, column):
    if len(df) < 2:
        return 0, 0

    current_value = df[column].iloc[-1]
    previous_value = df[column].iloc[-2]

    delta = current_value - previous_value
    delta_percent = (delta / previous_value * 100) if previous_value != 0 else 0

    return delta, delta_percent

def display_metric(col, title, value, df, column, color, time_frame):
    with col:
        with st.container(border=True):
            delta, delta_percent = calculate_delta(df, column)
            delta_str = f"{delta:+,.0f} ({delta_percent:+.2f}%)"

            st.metric(title, format_with_commas(value), delta=delta_str)

            create_metric_chart(df, column, color, chart_selection, time_frame=time_frame)

            last_period = df.index[-1]
            freq_map = {'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Quarterly': 'Q'}

            if not is_period_complete(last_period, freq_map[time_frame]):
                st.caption(f"Note: Last {time_frame.lower()} is incomplete")

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.title("📊 YouTube Channel Dashboard")

    max_date = df['DATE'].max().date()
    min_date = df['DATE'].min().date()

    default_start = max_date - timedelta(days=365)

    start_date = st.date_input("Start date", default_start, min_value=min_date, max_value=max_date)
    end_date = st.date_input("End date", max_date, min_value=min_date, max_value=max_date)

    time_frame = st.selectbox("Select time frame", ("Daily", "Weekly", "Monthly", "Quarterly"))
    chart_selection = st.selectbox("Select chart type", ("Bar", "Area"))

# -------------------- DATA SELECTION --------------------
if time_frame == 'Daily':
    df_display = df.set_index('DATE')
elif time_frame == 'Weekly':
    df_display = get_weekly_data(df)
elif time_frame == 'Monthly':
    df_display = get_monthly_data(df)
elif time_frame == 'Quarterly':
    df_display = get_quarterly_data(df)

# -------------------- ALL TIME METRICS --------------------
st.subheader("📌 All-Time Statistics")

metrics = [
    ("Total Subscribers", "NET_SUBSCRIBERS", '#29b5e8'),
    ("Total Views", "VIEWS", '#FF9F36'),
    ("Total Watch Hours", "WATCH_HOURS", '#D45B90'),
    ("Total Likes", "LIKES", '#7D44CF')
]

cols = st.columns(4)

for col, (title, column, color) in zip(cols, metrics):
    total_value = df[column].sum()
    display_metric(col, title, total_value, df_display, column, color, time_frame)

# -------------------- FILTERED DATA --------------------
st.subheader("📅 Selected Duration")

if time_frame == 'Quarterly':
    start_q = custom_quarter(start_date)
    end_q = custom_quarter(end_date)
    mask = (df_display.index >= start_q) & (df_display.index <= end_q)
else:
    mask = (df_display.index >= pd.Timestamp(start_date)) & (df_display.index <= pd.Timestamp(end_date))

df_filtered = df_display.loc[mask]

cols = st.columns(4)

for col, (title, column, color) in zip(cols, metrics):
    display_metric(col, title.split()[-1], df_filtered[column].sum(), df_filtered, column, color, time_frame)

# -------------------- DATA TABLE --------------------
with st.expander("📄 View Data"):
    st.dataframe(df_filtered)