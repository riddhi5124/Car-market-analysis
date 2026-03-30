import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import gdown
import os
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# 1. Page Config & Professional Styling
st.set_page_config(page_title="Vehicle Analytics Pro", layout="wide", page_icon="🏎️")

# Custom CSS for the "Spec Cards"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    .spec-card {
        border: 1px solid #333; 
        padding: 20px; 
        border-radius: 12px; 
        background-color: #1e252e;
        margin-bottom: 20px;
        transition: 0.3s;
        height: 220px;
    }
    .spec-card:hover { 
        border-color: #00d4ff; 
        transform: translateY(-5px);
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
    }
    .spec-label { color: #888; font-size: 12px; text-transform: uppercase; }
    .spec-value { color: #ffffff; font-size: 15px; font-weight: 500; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA CONFIGURATION ---
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"
OUTPUT_FILE = "vehicles.parquet"

@st.cache_data(show_spinner="📥 Synchronizing Market Data...")
def load_data(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    if not os.path.exists(OUTPUT_FILE):
        gdown.download(url, OUTPUT_FILE, quiet=False)

    try:
        # Loading only the columns needed for current analysis
        cols = ["manufacturer", "model", "year", "price", "lat", "long", 
                "fuel", "drive", "transmission", "type", "cylinders"]
        
        df = pd.read_parquet(OUTPUT_FILE, columns=cols)
        
        # Performance Optimizations
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')
        for col in ["manufacturer", "fuel", "drive", "transmission", "type"]:
            df[col] = df[col].astype('category')
            
        return df.dropna(subset=["manufacturer", "model", "price"])
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

df = load_data(FILE_ID)

# --- SIDEBAR BRANDING ---
st.sidebar.markdown("<h1 style='text-align: center; color: #00d4ff;'>🏎️ VehiclePro</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("NAVIGATE EXPLORER", [
    "🏠 Dashboard Home", 
    "📊 Manufacturer Analysis",
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
        c4.metric("Avg Age", f"{int(2026 - df['year'].median())} Years")
        
        st.markdown("---")
        st.markdown("### 📋 Dataset Overview")
        st.dataframe(df.head(15), use_container_width=True)

elif page == "📊 Manufacturer Analysis":
    st.title("🏭 Manufacturer Inventory")
    if not df.empty:
        brand = st.selectbox("Select a Manufacturer:", sorted(df['manufacturer'].unique()))
        
        # Filtering logic
        b_df = df[df['manufacturer'] == brand].copy()
        b_df['model'] = b_df['model'].astype(str)
        
        search = st.text_input("🔍 Filter by Model Name:")
        if search:
            b_df = b_df[b_df['model'].str.contains(search, case=False)]

        # Aggregate for unique model cards
        # We take the mode (most common value) for categorical specs
        grouped = b_df.groupby('model', observed=True).agg({
            'price': 'mean',
            'year': 'median',
            'fuel': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'transmission': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'drive': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A',
            'type': lambda x: x.mode().iat[0] if not x.mode().empty else 'N/A'
        }).reset_index().head(24) # Limit to 24 cards for performance

        st.write(f"Showing performance specs for **{brand}** top models:")
        
        cols = st.columns(3)
        for i, (idx, row) in enumerate(grouped.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="spec-card">
                    <h3 style="color:#00d4ff; margin-top:0; margin-bottom:15px;">{row['model'].title()}</h3>
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <div class="spec-label">Avg Price</div>
                            <div class="spec-value">${row['price']:,.0f}</div>
                            <div class="spec-label">Fuel Type</div>
                            <div class="spec-value">{row['fuel'].title()}</div>
                        </div>
                        <div>
                            <div class="spec-label">Median Year</div>
                            <div class="spec-value">{int(row['year'])}</div>
                            <div class="spec-label">Transmission</div>
                            <div class="spec-value">{row['transmission'].title()}</div>
                        </div>
                    </div>
                    <div class="spec-label">Drive / Body Style</div>
                    <div class="spec-value">{row['drive'].upper()} • {row['type'].title()}</div>
                </div>
                """, unsafe_allow_html=True)

elif page == "📈 Market Trends":
    st.title("📈 Inventory & Pricing Insights")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Inventory Distribution (Top 10)")
        fig = px.pie(df['manufacturer'].value_counts().nlargest(10), hole=0.5, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Price vs. Year Density")
        # Sample for faster plotting
        sample_df = df.sample(min(len(df), 5000))
        fig2 = px.scatter(sample_df, x="year", y="price", color="fuel", template="plotly_dark", opacity=0.5)
        st.plotly_chart(fig2, use_container_width=True)

elif page == "🗺️ Regional Heatmap":
    st.title("🗺️ Geographic Supply Density")
    brand_m = st.selectbox("Filter Density by Brand:", sorted(df['manufacturer'].unique()))
    m_df = df[df['manufacturer'] == brand_m].dropna(subset=['lat', 'long'])
    if not m_df.empty:
        center = [m_df['lat'].mean(), m_df['long'].mean()]
        m = folium.Map(location=center, zoom_start=4, tiles="CartoDB dark_matter")
        HeatMap(m_df[['lat', 'long']].head(3000).values.tolist(), radius=10, blur=15).add_to(m)
        folium_static(m)
