import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import gdown
import os
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# 1. Page Config & Professional Branding
st.set_page_config(page_title="Vehicle Analytics Pro", layout="wide", page_icon="🏎️")

# Custom CSS for UI Polish and Responsive Spec Cards
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 26px; color: #00d4ff; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    
    .spec-card {
        border: 1px solid #333; 
        padding: 20px; 
        border-radius: 12px; 
        background-color: #1e252e;
        margin-bottom: 20px;
        transition: 0.3s;
        min-height: 280px; /* Adjusted to ensure no spill-over */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .spec-card:hover { 
        border-color: #00d4ff; 
        transform: translateY(-3px);
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.15);
    }
    .spec-label { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .spec-value { color: #ffffff; font-size: 14px; font-weight: 500; margin-bottom: 10px; }
    .model-title { color: #00d4ff; margin-top: 0; margin-bottom: 15px; font-size: 1.1rem; border-bottom: 1px solid #333; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA CONFIGURATION ---
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"
OUTPUT_FILE = "vehicles.parquet"

@st.cache_data(show_spinner="📥 Syncing Market Data...")
def load_data(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    if not os.path.exists(OUTPUT_FILE):
        gdown.download(url, OUTPUT_FILE, quiet=False)
    try:
        cols = ["manufacturer", "model", "year", "price", "lat", "long", 
                "fuel", "drive", "transmission", "type"]
        df = pd.read_parquet(OUTPUT_FILE, columns=cols)
        
        # --- NEW: DROP ROWS WITH 'other' ---
        # Checks manufacturer, fuel, transmission, and type for the word 'other'
        for col in ["manufacturer", "fuel", "transmission", "type"]:
            df = df[~df[col].astype(str).str.lower().str.contains("other", na=False)]

        # Optimization
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')
        for col in ["manufacturer", "fuel", "drive", "transmission", "type"]:
            df[col] = df[col].astype('category')
            
        return df.dropna(subset=["manufacturer", "model", "price"])
    except Exception as e:
        st.error(f"Load Error: {e}"); return pd.DataFrame()

df = load_data(FILE_ID)

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h1 style='text-align: center; color: #00d4ff;'>🏎️ VehiclePro</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

page = st.sidebar.radio("NAVIGATE EXPLORER", [
    "🏠 Dashboard Home", 
    "📊 Manufacturer Inventory",
    "📈 Market Trends", 
    "🗺️ Regional Heatmap"
])

st.sidebar.markdown("---")
st.sidebar.caption("BSc Data Science Portfolio")
st.sidebar.caption("By Riddhiman Mazumder")

# --- PAGES ---

if page == "🏠 Dashboard Home":
    st.title("🚗 Market Intelligence Dashboard")
    if not df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Active Listings", f"{len(df):,}")
        c2.metric("Market Brands", df['manufacturer'].nunique())
        c3.metric("Avg Price", f"${df['price'].mean():,.0f}")
        c4.metric("Avg Age", f"{int(2026 - df['year'].median())} Yrs")
        st.markdown("---")
        st.dataframe(df.head(15), use_container_width=True)

elif page == "📊 Manufacturer Inventory":
    st.title("🏭 Manufacturer Inventory")
    if not df.empty:
        brand = st.selectbox("Select a Manufacturer:", sorted(df['manufacturer'].unique()))
        b_df = df[df['manufacturer'] == brand].copy()
        b_df['model'] = b_df['model'].astype(str)
        
        search = st.text_input("🔍 Filter Model Name:")
        if search:
            b_df = b_df[b_df['model'].str.contains(search, case=False)]

        grouped = b_df.groupby('model', observed=True).agg({
            'price': 'mean', 'year': 'median',
            'fuel': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'transmission': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'drive': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'type': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A'
        }).reset_index().head(24)

        cols = st.columns(3)
        for i, (idx, row) in enumerate(grouped.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="spec-card">
                    <h3 class="model-title">{row['model'].title()}</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        <div style="flex: 1; min-width: 100px;">
                            <div class="spec-label">Avg Price</div>
                            <div class="spec-value">${row['price']:,.0f}</div>
                            <div class="spec-label">Fuel</div>
                            <div class="spec-value">{row['fuel'].title()}</div>
                        </div>
                        <div style="flex: 1; min-width: 100px;">
                            <div class="spec-label">Median Year</div>
                            <div class="spec-value">{int(row['year'])}</div>
                            <div class="spec-label">Gearbox</div>
                            <div class="spec-value">{row['transmission'].title()}</div>
                        </div>
                    </div>
                    <div style="margin-top: 10px;">
                        <div class="spec-label">Drive / Configuration</div>
                        <div class="spec-value">{row['drive'].upper()} • {row['type'].title()}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

elif page == "📈 Market Trends":
    st.title("📈 Advanced Market Insights")
    t1, t2, t3 = st.tabs(["📉 Depreciation", "🏗️ Market Mix", "🔗 Correlations"])
    
    with t1:
        st.subheader("Price Depreciation vs. Vehicle Year")
        sample_df = df.sample(min(len(df), 3000))
        # This chart requires 'statsmodels' in requirements.txt
        fig_trend = px.scatter(sample_df, x="year", y="price", color="fuel",
                               trendline="lowess", template="plotly_dark", opacity=0.4)
        st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
        st.subheader("Inventory Composition by Body Style")
        fig_sun = px.sunburst(df.sample(2000), path=['drive', 'type'], values='price',
                              template="plotly_dark", color_discrete_sequence=px.colors.sequential.Viridis)
        st.plotly_chart(fig_sun, use_container_width=True)

    with t3:
        st.subheader("Statistical Correlation Matrix")
        corr = df[['price', 'year', 'lat', 'long']].corr()
        fig_heat = px.imshow(corr, text_auto=".2f", color_continuous_scale='RdBu_r', template="plotly_dark")
        st.plotly_chart(fig_heat, use_container_width=True)

elif page == "🗺️ Regional Heatmap":
    st.title("🗺️ Geographic Supply Density")
    brand_m = st.selectbox("Filter Map by Brand:", sorted(df['manufacturer'].unique()))
    m_df = df[df['manufacturer'] == brand_m].dropna(subset=['lat', 'long'])
    if not m_df.empty:
        center = [m_df['lat'].mean(), m_df['long'].mean()]
        m = folium.Map(location=center, zoom_start=4, tiles="CartoDB dark_matter")
        HeatMap(m_df[['lat', 'long']].head(3000).values.tolist(), radius=10, blur=15).add_to(m)
        folium_static(m)
