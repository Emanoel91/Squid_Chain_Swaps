import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# --- Page Config: Tab Title & Icon ---
st.set_page_config(
    page_title="Squid: Chain Swaps",
    page_icon="https://axelarscan.io/logos/accounts/squid.svg",
    layout="wide"
)

st.title("📋Chains Activities")

st.info(
    "📊Charts initially display data for a default time range. Select a custom range to view results for your desired period."

)

st.info(
    "⏳On-chain data retrieval may take a few moments. Please wait while the results load."
)

# --- Snowflake Connection ----------------------------------------------------------------------------------------
snowflake_secrets = st.secrets["snowflake"]
user = snowflake_secrets["user"]
account = snowflake_secrets["account"]
private_key_str = snowflake_secrets["private_key"]
warehouse = snowflake_secrets.get("warehouse", "")
database = snowflake_secrets.get("database", "")
schema = snowflake_secrets.get("schema", "")

private_key_pem = f"-----BEGIN PRIVATE KEY-----\n{private_key_str}\n-----END PRIVATE KEY-----".encode("utf-8")
private_key = serialization.load_pem_private_key(
    private_key_pem,
    password=None,
    backend=default_backend()
)
private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

conn = snowflake.connector.connect(
    user=user,
    account=account,
    private_key=private_key_bytes,
    warehouse=warehouse,
    database=database,
    schema=schema
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
            TRUNC(block_timestamp,'month') AS "Date",
            source_chain || '➡' || destination_chain AS "Path",
            COUNT(DISTINCT sender) AS "Number of Swappers",
            ROUND(COUNT(DISTINCT tx_hash) / NULLIF(COUNT(DISTINCT sender), 0)) AS "Avg Swap per Swapper"
        FROM axelar.defi.ez_bridge_squid
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1, 2
        ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Row 2: Top Paths by Number of Swappers ---
@st.cache_data
def load_top_paths_stats(start_date, end_date):
    query = f"""
        SELECT
            source_chain || '➡' || destination_chain AS "Path",
            COUNT(DISTINCT sender) AS "Number of Swappers",
            ROUND(COUNT(DISTINCT tx_hash) / NULLIF(COUNT(DISTINCT sender), 0)) AS "Avg Swap per Swapper"
        FROM axelar.defi.ez_bridge_squid
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1
        ORDER BY "Number of Swappers" DESC
    """
    return pd.read_sql(query, conn)

# --- Row 3: Monthly Number of Swaps by Path ---

@st.cache_data
def load_monthly_swaps_by_path(start_date, end_date):
    query = f"""
        SELECT
            TRUNC(block_timestamp, 'month') AS "Date",
            source_chain || '➡' || destination_chain AS "Path",
            COUNT(DISTINCT tx_hash) AS "Number of Swaps"
        FROM axelar.defi.ez_bridge_squid
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1, 2
        ORDER BY 1
    """
    return pd.read_sql(query, conn)

# --- Row 4: Top 10 Paths by Number of Swaps ---

@st.cache_data
def load_paths_by_swaps(start_date, end_date):
    query = f"""
        SELECT
            source_chain || '➡' || destination_chain AS "Path",
            COUNT(DISTINCT tx_hash) AS "Number of Swaps"
        FROM axelar.defi.ez_bridge_squid
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1
        ORDER BY 2 DESC
    """
    return pd.read_sql(query, conn)

# --- Row 5: Top 10 Swappers by Most Number of Swaps ---

@st.cache_data
def load_top_swappers(start_date, end_date):
    query = f"""
        SELECT
            sender AS "👨‍💻Swapper",
            COUNT(DISTINCT tx_hash) AS "🔄# of Swaps",
            COUNT(DISTINCT (source_chain || '➡' || destination_chain)) AS "🔀# of Paths",
            COUNT(DISTINCT source_chain) AS "📤# of Source Chains",
            COUNT(DISTINCT destination_chain) AS "📥# of Destination Chains",
            COUNT(DISTINCT token_address) AS "🔘# of Tokens",
            COUNT(DISTINCT block_timestamp::date) AS "📅# of Days of Activity"
        FROM axelar.defi.ez_bridge_squid
        WHERE block_timestamp::date >= '{start_date}'
          AND block_timestamp::date <= '{end_date}'
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 10
    """
    return pd.read_sql(query, conn)

# --- Load Data ----------------------------------------------------------------------------------------
weekly_path_stats = load_weekly_path_stats(start_date, end_date)
top_paths_stats = load_top_paths_stats(start_date, end_date)
monthly_swaps_path = load_monthly_swaps_by_path(start_date, end_date)
paths_swaps_df = load_paths_by_swaps(start_date, end_date)
top_swappers_df = load_top_swappers(start_date, end_date)
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
    title="Monthly Number of Swappers By Path"
)
fig_stacked.update_layout(barmode="stack", yaxis_title="Number of Swappers")

# --- Line Chart: Monthly Average Swap Count per Swapper by Path ---
fig_line = px.line(
    weekly_path_stats,
    x="Date",
    y="Avg Swap per Swapper",
    color="Path",
    title="Monthly Average Swap Count per Swapper By Path"
)
fig_line.update_layout(yaxis_title="Avg Swap per Swapper")

# --- Display charts side by side ---
col1, col2 = st.columns(2)
col1.plotly_chart(fig_stacked, use_container_width=True)
col2.plotly_chart(fig_line, use_container_width=True)

# --- Row 2 --------

top_10_paths = top_paths_stats.head(10)

# --- Horizontal Bar Chart ---
fig_horizontal = px.bar(
    top_10_paths.sort_values("Number of Swappers"),  
    x="Number of Swappers",
    y="Path",
    orientation="h",
    text="Number of Swappers",
    title="🏆Top 10 Paths by Number of Swappers"
)
fig_horizontal.update_traces(textposition="outside")
fig_horizontal.update_layout(
    xaxis_title="Number of Swappers",
    yaxis_title="Path",
    height=500
)

top_paths_stats.index = range(1, len(top_paths_stats) + 1)

col1, col2 = st.columns(2)
col1.plotly_chart(fig_horizontal, use_container_width=True)
col2.dataframe(top_paths_stats, use_container_width=True, height=500)

# --- Row 3 ----
st.markdown(
    """
    <div style="background-color:#e6fa36; padding:1px; border-radius:10px;">
        <h2 style="color:#000000; text-align:center;">Swaps (Transactions)</h2>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Stacked Bar Chart ---
fig_stacked_bar = px.bar(
    monthly_swaps_path,
    x="Date",
    y="Number of Swaps",
    color="Path",
    title="Monthly Number of Swaps By Path",
    barmode="stack"
)
fig_stacked_bar.update_layout(
    xaxis_title="Date",
    yaxis_title="Number of Swaps",
    legend_title="Path",
    height=500
)

# --- Normalized Area Chart ---

normalized_df = monthly_swaps_path.copy()
normalized_df["Total per Date"] = normalized_df.groupby("Date")["Number of Swaps"].transform("sum")
normalized_df["Percentage"] = normalized_df["Number of Swaps"] / normalized_df["Total per Date"] * 100

fig_area_normalized = px.area(
    normalized_df,
    x="Date",
    y="Percentage",
    color="Path",
    groupnorm="percent",
    title="Monthly Number of Swaps By Path (%Normalized)"
)
fig_area_normalized.update_layout(
    xaxis_title="Date",
    yaxis_title="Percentage (%)",
    legend_title="Path",
    height=500
)

col1, col2 = st.columns(2)
col1.plotly_chart(fig_stacked_bar, use_container_width=True)
col2.plotly_chart(fig_area_normalized, use_container_width=True)

# --- Row 4 -------------
# --- Top 10 Paths for Chart ---
top10_paths = paths_swaps_df.head(10)

fig_top10_paths = px.bar(
    top10_paths.sort_values("Number of Swaps"),
    x="Number of Swaps",
    y="Path",
    orientation='h',
    text="Number of Swaps",
    title="🏆Top 10 Paths By Number of Swaps"
)
fig_top10_paths.update_traces(texttemplate='%{text:,}', textposition='outside')
fig_top10_paths.update_layout(
    xaxis_title="Number of Swaps",
    yaxis_title="Path",
    height=500,
    margin=dict(l=10, r=10, t=50, b=10)
)

# --- Table with index starting from 1 ---
paths_swaps_df_display = paths_swaps_df.copy()
paths_swaps_df_display.index = range(1, len(paths_swaps_df_display) + 1)

col1, col2 = st.columns(2)
col1.plotly_chart(fig_top10_paths, use_container_width=True)
col2.dataframe(paths_swaps_df_display, use_container_width=True, height=500)

# --- Row 5 -------------
st.markdown(
    """
    <div style="background-color:#e6fa36; padding:1px; border-radius:10px;">
        <h2 style="color:#000000; text-align:center;">Top Swappers</h2>
    </div>
    """,
    unsafe_allow_html=True
)
top_swappers_df_display = top_swappers_df.copy()
top_swappers_df_display.index = range(1, len(top_swappers_df_display) + 1)

# gold/silver/bronze colors
def highlight_top3(row):
    color = ''
    if row.name == 1:
        color = 'background-color: gold'
    elif row.name == 2:
        color = 'background-color: silver'
    elif row.name == 3:
        color = 'background-color: #cd7f32'  # bronze
    return [color] * len(row)

st.subheader("Top 10 Swappers By Most Number of Swap")
st.dataframe(
    top_swappers_df_display.style.apply(highlight_top3, axis=1),
    use_container_width=True,
    height=500
)
