import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import gdown
import os
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# 1. Page Config
st.set_page_config(page_title="Vehicle Analytics Pro", layout="wide", page_icon="🏎️")

# Custom CSS for polished UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00d4ff; }
    section[data-testid="stSidebar"] { background-color: #161b22; }
    .car-card {
        border: 1px solid #333; 
        padding: 15px; 
        border-radius: 12px; 
        background-color: #1e252e;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .car-card:hover { border-color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA CONFIGURATION ---
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"
OUTPUT_FILE = "vehicles.parquet"

@st.cache_data(show_spinner="📥 Syncing Database...")
def load_data(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    if not os.path.exists(OUTPUT_FILE):
        gdown.download(url, OUTPUT_FILE, quiet=False)

    try:
        # Added 'image_url' to the columns to load
        cols = ["manufacturer", "model", "year", "price", "lat", "long", 
                "fuel", "drive", "transmission", "image_url"]
        
        df = pd.read_parquet(OUTPUT_FILE, columns=cols)
        
        # Optimization
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')
        for col in ["manufacturer", "fuel", "drive", "transmission"]:
            df[col] = df[col].astype('category')
            
        return df.dropna(subset=["manufacturer", "model", "price"])
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame()

df = load_data(FILE_ID)

# --- NAVIGATION ---
st.sidebar.markdown("<h1 style='text-align: center; color: #00d4ff;'>🏎️ VehiclePro</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("NAVIGATE", ["🏠 Home", "📊 Manufacturer Analysis", "📈 Market Trends", "🗺️ Heatmap"])

# --- PAGES ---

if page == "🏠 Home":
    st.title("🚗 Market Intelligence Dashboard")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Listings", f"{len(df):,}")
        c2.metric("Avg Price", f"${df['price'].mean():,.0f}")
        c3.metric("Brands", df['manufacturer'].nunique())
        st.markdown("### 📋 Recent Data Stream")
        st.dataframe(df.head(10), use_container_width=True)

elif page == "📊 Manufacturer Analysis":
    st.title("🏭 Brand Explorer")
    if not df.empty:
        brand = st.selectbox("Select Brand:", sorted(df['manufacturer'].unique()))
        b_df = df[df['manufacturer'] == brand].copy()
        
        # Search filter
        search = st.text_input("🔍 Search model:")
        if search:
            b_df = b_df[b_df['model'].astype(str).str.contains(search, case=False)]

        # Display Cards with Images
        st.write(f"Displaying top results for **{brand}**")
        
        # Taking a sample to avoid overloading the page with thousands of images
        display_df = b_df.head(12) 
        cols = st.columns(3)
        
        for i, (index, row) in enumerate(display_df.iterrows()):
            with cols[i % 3]:
                # Image Logic
                img = row['image_url'] if pd.notnull(row['image_url']) else "https://via.placeholder.com/300x200?text=No+Image+Available"
                
                st.markdown(f"""
                <div class="car-card">
                    <img src="{img}" style="width:100%; border-radius:8px; height:150px; object-fit:cover; margin-bottom:10px;">
                    <h4 style="margin:0; color:#00d4ff;">{row['model'].title()}</h4>
                    <p style="margin:0; font-size:14px; color:#ddd;">Year: {int(row['year'])} | Price: <b>${row['price']:,.0f}</b></p>
                    <p style="margin:0; font-size:12px; color:#888;">{row['fuel'].upper()} • {row['transmission'].upper()}</p>
                </div>
                """, unsafe_allow_html=True)

elif page == "📈 Market Trends":
    st.title("📈 Supply Analysis")
    fig = px.pie(df['manufacturer'].value_counts().nlargest(10), hole=0.5, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

elif page == "🗺️ Heatmap":
    st.title("🗺️ Inventory Density")
    brand_m = st.selectbox("Map Filter:", sorted(df['manufacturer'].unique()))
    m_df = df[df['manufacturer'] == brand_m].dropna(subset=['lat', 'long'])
    if not m_df.empty:
        m = folium.Map(location=[m_df['lat'].mean(), m_df['long'].mean()], zoom_start=4, tiles="CartoDB dark_matter")
        HeatMap(m_df[['lat', 'long']].head(2000).values.tolist()).add_to(m)
        folium_static(m)
