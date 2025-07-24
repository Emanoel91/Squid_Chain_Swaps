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

# --- Load Data ----------------------------------------------------------------------------------------
swap_stats = load_swap_stats(start_date, end_date)

# --- Row 1: Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total number of swaps", f"{swap_stats['total_swaps']:,}")
col2.metric("Total number of swappers", f"{swap_stats['total_swapper']:,}")
col3.metric("Average number of swapped per user", f"{swap_stats['avg_number_swaped_per_user']:.2f}")
