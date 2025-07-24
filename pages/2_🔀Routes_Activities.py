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
# --- Row 1: Weekly Number of Swappers and Average Swap Count by Path ---
@st.cache_data
def load_weekly_path_stats(start_date, end_date):
    query = f"""
        SELECT
            TRUNC(block_timestamp,'week') AS "Date",
            source_chain || '➡' || destination_chain AS "Path",
            COUNT(DISTINCT sender) AS "Number of Swappers",
            ROUND(COUNT(DISTINCT tx_hash) / NULLIF(COUNT(DISTINCT sender), 0), 2) AS "Avg Swap per Swapper"
        FROM axelar.defi.ez_bridge_squid
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1, 2
        ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Load Data ----------------------------------------------------------------------------------------
weekly_path_stats = load_weekly_path_stats(start_date, end_date)

# ------------------------------------------------------------------------------------------------------

# --- Row 1: Metrics ---
st.markdown(
    """
    <div style="background-color:#e6fa36; padding:1px; border-radius:10px;">
        <h2 style="color:#000000; text-align:center;">Swappers (Users)</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Stacked Bar Chart: Weekly Number of Swappers by Path ---
fig_stacked = px.bar(
    weekly_path_stats,
    x="Date",
    y="Number of Swappers",
    color="Path",
    title="Weekly Number of Swappers By Path"
)
fig_stacked.update_layout(barmode="stack", yaxis_title="Number of Swappers")

# --- Line Chart: Weekly Average Swap Count per Swapper by Path ---
fig_line = px.line(
    weekly_path_stats,
    x="Date",
    y="Avg Swap per Swapper",
    color="Path",
    title="Weekly Average Swap Count per Swapper By Path"
)
fig_line.update_layout(yaxis_title="Avg Swap per Swapper")

# --- Display charts side by side ---
col1, col2 = st.columns(2)
col1.plotly_chart(fig_stacked, use_container_width=True)
col2.plotly_chart(fig_line, use_container_width=True)
