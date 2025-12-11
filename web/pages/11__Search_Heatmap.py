"""
Search Heatmap Analytics Page - Displays search patterns and compliance trends
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent paths
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check authentication
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.switch_page("pages/00__Login.py")
    st.stop()

# Page configuration
st.set_page_config(page_title="Search Heatmap - Legal Metrology OCR", page_icon="🔥", layout="wide")

# Custom CSS
st.markdown("""
<style>
    /* Hide streamlit_app from sidebar navigation */
    [data-testid="stSidebarNav"] li:first-child {
        display: none !important;
    }
    
    .stApp {
        background: #FFFFFF !important;
    }
    
    .metric-card {
        background: #ffffff;
        color: #000000;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        box-shadow: none;
        border: 1px solid #e5e7eb;
        margin: 10px 0;
    }
    
    .stat-number {
        font-size: 28px;
        font-weight: bold;
        color: #000000;
    }
    
    .stat-label {
        font-size: 14px;
        color: #000000;
    }
    
    .header {
        background: #3866D5;
        color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .header h1, .header p {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='header'>
    <h1>🔥 Search Analytics & Heatmap</h1>
    <p>Track search patterns, popular products, and compliance trends</p>
</div>
""", unsafe_allow_html=True)

# Load heatmap data
@st.cache_data
def load_heatmap_data():
    """Load heatmap data from JSON file"""
    try:
        with open('data/heatmap.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Sidebar filters
with st.sidebar:
    st.subheader("📊 Analytics Filters")
    
    view_type = st.radio(
        "Select View:",
        ["📈 Heatmap", "🔝 Popular Products", "📅 Timeline", "📊 Statistics", "🗂️ Categories"]
    )
    
    st.divider()
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Load data
heatmap_data = load_heatmap_data()

if heatmap_data:
    search_history = heatmap_data.get('search_history', [])
    summary = heatmap_data.get('summary', {})
    category_summary = heatmap_data.get('category_summary', {})
    
    # Convert to DataFrame
    df = pd.DataFrame(search_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Display key metrics
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number'>{summary.get('total_searches', 0)}</div>
            <div class='stat-label'>Total Searches</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number'>{summary.get('unique_products', 0)}</div>
            <div class='stat-label'>Unique Products</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number'>{summary.get('total_results', 0)}</div>
            <div class='stat-label'>Results Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number'>{summary.get('average_compliance', 0):.1f}%</div>
            <div class='stat-label'>Avg Compliance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='stat-number'>{len(df)}</div>
            <div class='stat-label'>Search Records</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display based on selected view
    if view_type == "📈 Heatmap":
        st.subheader("🔥 Search Heatmap - Product vs Category")
        
        # Create heatmap data
        heatmap_pivot = df.groupby(['search_term', 'category']).agg({
            'search_count': 'sum',
            'compliance_rate': 'mean'
        }).reset_index()
        
        # Create figure with heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot['search_count'],
            x=heatmap_pivot['category'],
            y=heatmap_pivot['search_term'],
            colorscale='YlOrRd',
            colorbar=dict(title="Search Count")
        ))
        
        fig.update_layout(
            title="Search Frequency Heatmap by Product & Category",
            xaxis_title="Category",
            yaxis_title="Product",
            height=600,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Show data table
        st.subheader("📋 Detailed Heatmap Data")
        st.dataframe(
            df[['search_term', 'category', 'search_count', 'compliance_rate', 'user']].sort_values('search_count', ascending=False),
            width='stretch',
            hide_index=True
        )
    
    elif view_type == "🔝 Popular Products":
        st.subheader("🏆 Top Searched Products")
        
        # Sort by search count
        df_sorted = df.sort_values('search_count', ascending=True)
        
        # Create bar chart
        fig = px.bar(
            df_sorted,
            y='search_term',
            x='search_count',
            color='compliance_rate',
            orientation='h',
            color_continuous_scale='RdYlGn',
            title="Top Searched Products by Count"
        )
        
        fig.update_layout(height=500, template='plotly_white')
        st.plotly_chart(fig, width='stretch')
    
    elif view_type == "📅 Timeline":
        st.subheader("📈 Search Timeline")
        
        # Group by date
        timeline_df = df.groupby(df['timestamp'].dt.date).agg({
            'search_count': 'sum',
            'results_found': 'sum',
            'compliance_rate': 'mean'
        }).reset_index()
        timeline_df.columns = ['date', 'searches', 'results', 'compliance']
        
        fig = px.line(timeline_df, x='date', y='searches', title="Search Activity", template='plotly_white')
        st.plotly_chart(fig, width='stretch')
    
    elif view_type == "📊 Statistics":
        st.subheader("📊 Detailed Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Highest Searched", summary.get('most_searched', 'N/A'))
            st.metric("Most Compliant", summary.get('most_compliant', 'N/A'))
        
        with col2:
            st.metric("Max Compliance", f"{df['compliance_rate'].max():.1f}%")
            st.metric("Min Compliance", f"{df['compliance_rate'].min():.1f}%")
    
    elif view_type == "🗂️ Categories":
        st.subheader("🗂️ Category Analysis")
        
        # Create category breakdown
        category_data = []
        for cat, stats in category_summary.items():
            category_data.append({
                'Category': cat,
                'Searches': stats.get('searches', 0),
                'Products': stats.get('products', 0),
                'Compliance': stats.get('compliance_rate', 0)
            })
        
        category_df = pd.DataFrame(category_data).sort_values('Searches', ascending=True)
        
        # Create charts
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig_pie = px.pie(
                category_df,
                names='Category',
                values='Searches',
                title="Search Distribution by Category"
            )
            st.plotly_chart(fig_pie, width='stretch')
        
        with col2:
            fig_bar = px.bar(
                category_df,
                y='Category',
                x='Compliance',
                orientation='h',
                color='Compliance',
                color_continuous_scale='RdYlGn',
                title="Category Compliance Rate"
            )
            st.plotly_chart(fig_bar, width='stretch')
else:
    st.error("❌ Unable to load heatmap data")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; opacity: 0.7;'>
    💡 Tip: Search data is collected automatically from all product searches. 
    These analytics help identify trends and improve compliance checking.
</div>
""", unsafe_allow_html=True)



