import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go

# --- Page Config: Tab Title & Icon ---
st.set_page_config(
    page_title="Squid: Chain Swaps",
    page_icon="https://axelarscan.io/logos/accounts/squid.svg",
    layout="wide"
)

st.title("📋Chains Activities")

# --- Snowflake Connection ---
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"],
    warehouse="SNOWFLAKE_LEARNING_WH",
    database="AXELAR",
    schema="PUBLIC"
)

# --- Time Frame & Period Selection ---
start_date = st.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2025-06-01"))

# --- Query Functions ---------------------------------------------------------------------------------------
@st.cache_data
def load_swap_stats(start_date, end_date):
    query = f"""
    SELECT
        COUNT(DISTINCT tx_hash) AS total_swaps,
        COUNT(DISTINCT sender) AS total_swapper,
        ROUND(COUNT(DISTINCT tx_hash) / NULLIF(COUNT(DISTINCT sender), 0)) AS avg_number_swaped_per_user
    FROM
        axelar.defi.ez_bridge_squid
    WHERE
        block_timestamp::date >= '{start_date}'
        AND block_timestamp::date <= '{end_date}'
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower() 
    return df.iloc[0]

# --- Row 2: Weekly New Swappers and Cumulative ---
@st.cache_data
def load_weekly_new_swappers(start_date, end_date):
    query = f"""
    WITH users AS (
        SELECT block_timestamp, sender AS user
        FROM axelar.defi.ez_bridge_squid
        
    ),
    new_user AS (
        SELECT MIN(block_timestamp::date) AS date, user
        FROM users 
        GROUP BY 2
    )
    SELECT TRUNC(date, 'week') AS "Week",
           COUNT(DISTINCT user) AS "New Swappers",
           SUM(COUNT(DISTINCT user)) OVER (ORDER BY TRUNC(date, 'week') ASC) AS "Cumulative New Swappers"
    FROM new_user
    WHERE date >= '{start_date}'
          AND date <= '{end_date}'
    GROUP BY 1
    ORDER BY 1
    """
    return pd.read_sql(query, conn)
    
# --- Weekly Number of Swaps & Swappers ---
@st.cache_data
def load_weekly_swaps_swappers(start_date, end_date):
    query = f"""
    SELECT
        DATE_TRUNC('WEEK', BLOCK_TIMESTAMP) AS "Week",
        COUNT(DISTINCT tx_hash) AS "Number of Swaps",
        COUNT(DISTINCT sender) AS "Number of Swappers",
        ROUND(COUNT(DISTINCT tx_hash)::numeric / NULLIF(COUNT(DISTINCT sender), 0), 2) AS "Avg Swap per Swapper"
    FROM
        axelar.defi.ez_bridge_squid
    WHERE
        block_timestamp::date >= '{start_date}'
        AND block_timestamp::date <= '{end_date}'
    GROUP BY 1
    ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Load Data ----------------------------------------------------------------------------------------
swap_stats = load_swap_stats(start_date, end_date)
weekly_new_swappers = load_weekly_new_swappers(start_date, end_date)
weekly_swaps_swappers = load_weekly_swaps_swappers(start_date, end_date)
# ------------------------------------------------------------------------------------------------------

# --- Row 1: Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total number of swaps", f"{swap_stats['total_swaps']:,}")
col2.metric("Total number of swappers", f"{swap_stats['total_swapper']:,}")
col3.metric("Average number of swapped per user", f"{swap_stats['avg_number_swaped_per_user']:.2f}")

# --- Row 2 ------------
fig1 = go.Figure()
fig1.add_bar(
    x=weekly_new_swappers["Week"],
    y=weekly_new_swappers["New Swappers"],
    name="New Swappers",
    marker_color="steelblue",
    yaxis="y1"
)
fig1.add_trace(go.Scatter(
    x=weekly_new_swappers["Week"],
    y=weekly_new_swappers["Cumulative New Swappers"],
    name="Cumulative New Swappers",
    mode="lines+markers",
    line=dict(color="orange", width=2),
    yaxis="y2"
))
fig1.update_layout(
    title="Weekly Number of New Swappers and Cumulative Number of New Swappers",
    xaxis=dict(title="Week"),
    yaxis=dict(title="Address count", side="left"),
    yaxis2=dict(title="Address count", overlaying="y", side="right"),
    legend=dict(x=0.01, y=0.99)
)

fig2 = go.Figure()
fig2.add_bar(
    x=weekly_swaps_swappers["Week"],
    y=weekly_swaps_swappers["Number of Swaps"],
    name="Number of Swaps",
    marker_color="teal",
    yaxis="y1"
)
fig2.add_trace(go.Scatter(
    x=weekly_swaps_swappers["Week"],
    y=weekly_swaps_swappers["Number of Swappers"],
    name="Number of Swappers",
    mode="lines+markers",
    line=dict(color="firebrick", width=2),
    yaxis="y2"
))
fig2.update_layout(
    title="Weekly Number of Swaps & Swappers",
    xaxis=dict(title="Week"),
    yaxis=dict(title="Txn count", side="left"),
    yaxis2=dict(title="Address count", overlaying="y", side="right"),
    legend=dict(x=0.01, y=0.99)
)

# --- Display both charts in one row ---
col1, col2 = st.columns(2)
col1.plotly_chart(fig1, use_container_width=True)
col2.plotly_chart(fig2, use_container_width=True)
