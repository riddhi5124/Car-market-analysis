import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import gdown
import os
from streamlit_folium import folium_static
from folium.plugins import HeatMap

# 1. Page Config & Custom Styling
st.set_page_config(page_title="Vehicle Analytics Pro", layout="wide", page_icon="🏎️")

# Custom CSS for a sleek look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #00d4ff;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22;
    }
    .stHeader {
        background: rgba(0,0,0,0);
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA CONFIGURATION ---
FILE_ID = "17VhcD1SApY6M1escKpKloilcO3XAMeWK"
OUTPUT_FILE = "vehicles.parquet"

@st.cache_data(show_spinner="📥 Synchronizing with Data Lake...")
def load_data(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    if not os.path.exists(OUTPUT_FILE):
        try:
            gdown.download(url, OUTPUT_FILE, quiet=False)
        except Exception as e:
            st.error(f"Sync Failed: {e}")
            return pd.DataFrame()

    try:
        cols_to_load = ["manufacturer", "model", "year", "price", "lat", "long", 
                        "cylinders", "fuel", "drive", "type", "transmission"]
        df = pd.read_parquet(OUTPUT_FILE, columns=cols_to_load)
        
        # Memory Optimization
        df['price'] = pd.to_numeric(df['price'], downcast='float')
        df['year'] = pd.to_numeric(df['year'], downcast='integer')
        for col in ["manufacturer", "fuel", "drive", "type", "transmission"]:
            df[col] = df[col].astype('category')
        return df.dropna(subset=["manufacturer", "model", "price", "lat", "long"])
    except Exception as e:
        st.error(f"Processing Error: {e}")
        return pd.DataFrame()

df = load_data(FILE_ID)

# --- SIDEBAR BRANDING ---
st.sidebar.markdown("<h1 style='text-align: center; color: #00d4ff;'>🏎️ VehiclePro</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")
page = st.sidebar.radio("NAVIGATE EXPLORER", [
    "🏠 Dashboard Home", 
    "📊 Manufacturer Analysis",
    "📈 Market Trends", 
    "⚙️ Technical Specs", 
    "🗺️ Regional Heatmap"
])

st.sidebar.markdown("---")
st.sidebar.caption("BSc Data Science Project")
st.sidebar.caption("Developed by Riddhiman Mazumder")

# --- PAGES ---

if page == "🏠 Dashboard Home":
    st.title("🚗 Used Vehicle Market Intelligence")
    st.info("Real-time data visualization of the US used car market.")
    
    if not df.empty:
        # High-level Metrics in nice containers
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Inventory", f"{len(df):,}")
        m2.metric("Market Brands", df['manufacturer'].nunique())
        m3.metric("Avg Listing Price", f"${df['price'].mean():,.0f}")
        m4.metric("Newest Model Year", int(df['year'].max()))

        st.markdown("### 📋 Recent Listings Snapshot")
        st.dataframe(df.head(15), use_container_width=True)
    else:
        st.warning("Awaiting data sync...")

elif page == "📊 Manufacturer Analysis":
    st.title("🏭 Manufacturer Deep-Dive")
    if not df.empty:
        brand = st.selectbox("Select a Brand to Explore:", sorted(df['manufacturer'].unique()))
        b_df = df[df['manufacturer'] == brand].copy()
        b_df['model'] = b_df['model'].astype(str)
        
        search = st.text_input("🔍 Search for a model (e.g., 'Civic' or 'F-150')")
        if search:
            b_df = b_df[b_df['model'].str.contains(search, case=False)]

        # Show filtered model cards
        grouped = b_df.groupby('model', observed=True).agg({'price': 'mean', 'year': 'median'}).reset_index()
        
        st.write(f"Showing {len(grouped)} models for **{brand}**")
        cols = st.columns(3)
        for i, row in grouped.iterrows():
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #333; padding:15px; border-radius:10px; margin-bottom:10px; background-color:#1e252e;">
                        <h4 style="color:#00d4ff; margin:0;">{row['model'].title()}</h4>
                        <p style="margin:0; font-size:14px;">Avg: <b>${row['price']:,.0f}</b></p>
                        <p style="margin:0; font-size:12px; color:#888;">Typical Year: {int(row['year'])}</p>
                    </div>
                    """, unsafe_allow_html=True)

elif page == "📈 Market Trends":
    st.title("📈 Supply & Demand Visualization")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Top 10 Manufacturers")
        m_counts = df['manufacturer'].value_counts().nlargest(10)
        fig1 = px.pie(names=m_counts.index, values=m_counts.values, hole=0.5, 
                      color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig1.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Transmission Popularity by Type")
        fig2 = px.histogram(df, x="transmission", color="type", barmode="group",
                            color_discrete_sequence=px.colors.qualitative.Vivid)
        fig2.update_layout(template="plotly_dark", yaxis_title="Number of Listings")
        st.plotly_chart(fig2, use_container_width=True)

elif page == "⚙️ Technical Specs":
    st.title("⚙️ Engineering Breakdown")
    st.subheader("Manufacturer vs. Drive Configuration")
    
    top_brands = df['manufacturer'].value_counts().nlargest(12).index
    t_df = df[df['manufacturer'].isin(top_brands)]
    
    fig3 = px.bar(t_df, x="manufacturer", color="drive", 
                  color_discrete_sequence=px.colors.sequential.Viridis)
    fig3.update_layout(template="plotly_dark", xaxis_tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)

elif page == "🗺️ Regional Heatmap":
    st.title("🗺️ Geographic Supply Density")
    brand_m = st.selectbox("Filter Map by Brand:", sorted(df['manufacturer'].unique()))
    m_df = df[df['manufacturer'] == brand_m].dropna(subset=['lat', 'long'])

    if not m_df.empty:
        st.success(f"Mapping {len(m_df):,} locations for {brand_m}")
        center = [m_df['lat'].mean(), m_df['long'].mean()]
        m = folium.Map(location=center, zoom_start=4, tiles="CartoDB dark_matter")
        
        heat_data = m_df[['lat', 'long']].head(4000).values.tolist()
        HeatMap(heat_data, radius=8, blur=12).add_to(m)
        folium_static(m)
    else:
        st.error("No coordinate data available for this brand.")
