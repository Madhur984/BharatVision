import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import pathlib

# Add project root to path
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from web.database import db
except ImportError:
    st.error("Database connection failed.")
    st.stop()

st.set_page_config(
    page_title="Global Compliance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-card h3 {
        margin: 0;
        color: #666;
        font-size: 1rem;
    }
    .metric-card p {
        margin: 10px 0 0 0;
        font-size: 2rem;
        font-weight: bold;
        color: #333;
    }
    .stDataFrame {
        border-radius: 10px; 
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📊 Global Compliance Dashboard")
    st.markdown("Unified view of all compliance checks from **Web Crawler**, **Image Upload**, and **Camera Capture**.")

    # Get current user
    if "user" not in st.session_state:
        st.warning("Please login to view your dashboard.")
        return

    user = st.session_state.user
    username = user.get("username")
    role = user.get("role", "User")
    
    # Access Control: Guests should not access; Authenticated users (Admin/Inspector) can.
    if role == "Guest":
        st.error("⛔ Access Denied: Please login with your ID and password to access the Global Dashboard.")
        st.stop()
    
    # Ideally we'd have a method to get *all* for the user without limit, or a large limit
    # Using existing method with a large limit for now
    history = db.get_user_compliance_history(username, limit=1000)
    
    if not history:
        st.info("No compliance checks found. Start by crawling products or uploading images!")
        return

    # Convert to DataFrame
    df = pd.DataFrame(history)
    
    # Preprocessing
    if 'compliance_score' in df.columns:
        df['compliance_score'] = pd.to_numeric(df['compliance_score'], errors='coerce').fillna(0)
    
    if 'checked_at' in df.columns:
        df['checked_at'] = pd.to_datetime(df['checked_at'])

    # 1. Summary Metrics
    total_checks = len(df)
    compliant_count = len(df[df['compliance_status'] == 'COMPLIANT'])
    non_compliant_count = len(df[df['compliance_status'] != 'COMPLIANT'])
    avg_score = df['compliance_score'].mean()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Checked</h3>
            <p>{total_checks}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: green;">Compliant</h3>
            <p style="color: green;">{compliant_count}</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: red;">Non-Compliant</h3>
            <p style="color: red;">{non_compliant_count}</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Average Score</h3>
            <p>{avg_score:.1f}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. Charts Row
    col_charts_1, col_charts_2 = st.columns([1, 1])
    
    with col_charts_1:
        st.subheader("Compliance Distribution")
        fig_pie = px.pie(
            df, 
            names='compliance_status', 
            title='',
            color='compliance_status',
            color_discrete_map={
                'COMPLIANT': '#2ecc71',
                'NON_COMPLIANT': '#e74c3c',
                'PARTIAL': '#f1c40f',
                'ERROR': '#95a5a6'
            },
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_charts_2:
        st.subheader("Checks by Platform")
        if 'platform' in df.columns:
            platform_counts = df['platform'].value_counts().reset_index()
            platform_counts.columns = ['platform', 'count']
            fig_bar = px.bar(
                platform_counts, 
                x='platform', 
                y='count',
                color='platform',
                text='count'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # 3. Time Series Analysis
    st.subheader("Compliance Trends Over Time")
    if 'checked_at' in df.columns:
        df_daily = df.set_index('checked_at').resample('D').agg({
            'id': 'count', 
            'compliance_score': 'mean'
        }).reset_index()
        
        fig_line = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_line.add_trace(
            go.Bar(x=df_daily['checked_at'], y=df_daily['id'], name="Checks Count", marker_color='lightblue'),
            secondary_y=False
        )
        
        fig_line.add_trace(
            go.Scatter(x=df_daily['checked_at'], y=df_daily['compliance_score'], name="Avg Score", line=dict(color='purple', width=3)),
            secondary_y=True
        )
        
        fig_line.update_layout(title_text="Daily Activity & Average Score")
        fig_line.update_xaxes(title_text="Date")
        fig_line.update_yaxes(title_text="Count", secondary_y=False)
        fig_line.update_yaxes(title_text="Score", secondary_y=True, range=[0, 100])
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    from plotly.subplots import make_subplots

    # 4. Detailed Data Table
    st.subheader("📋 Detailed Records")
    
    # Filter Controls
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        status_filter = st.multiselect("Filter by Status", options=df['compliance_status'].unique(), default=df['compliance_status'].unique())
    with f_col2:
        platform_filter = st.multiselect("Filter by Platform", options=df['platform'].unique(), default=df['platform'].unique())
        
    filtered_df = df[
        (df['compliance_status'].isin(status_filter)) &
        (df['platform'].isin(platform_filter))
    ]
    
    # Display table
    st.dataframe(
        filtered_df[['product_title', 'platform', 'compliance_status', 'compliance_score', 'checked_at', 'details']],
        column_config={
            "product_title": "Product / File",
            "platform": "Method / Source",
            "compliance_status": st.column_config.TextColumn("Status"),
            "compliance_score": st.column_config.ProgressColumn("Score", format="%.2f", min_value=0, max_value=100),
            "checked_at": st.column_config.DatetimeColumn("Date", format="D MMM YYYY, h:mm a"),
            "details": st.column_config.TextColumn("Extracted Details (JSON)", help="Raw extracted data and violations")
        },
        use_container_width=True,
        hide_index=True
    )


# Call main function
main()
