import streamlit as st

# --- Page Config: Tab Title & Icon ---
st.set_page_config(
    page_title="Squid: Chain Swaps",
    page_icon="https://axelarscan.io/logos/accounts/squid.svg",
    layout="wide"
)


st.title("🟡Squid: Chain Swaps")

st.markdown("""
Squid Router is a cross-chain liquidity and messaging protocol built on the Axelar Network, designed to facilitate seamless token swaps, transfers, and smart contract 
interactions across multiple blockchains. Squid enables users to swap any token across over 90 blockchains (e.g., Ethereum, Polygon, Arbitrum, Solana, Bitcoin) in a single click. 
""")

# --- Display Image ---
st.image("https://i.postimg.cc/s2HY308v/axelar.jpg", caption="", use_container_width=True)

st.markdown("""
https://www.axelar.network/

https://www.squidrouter.com/

https://x.com/axelar

""")


