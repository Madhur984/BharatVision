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

    # 4. Detailed Data Table with Enhanced Information
    st.subheader("📋 Detailed Compliance Records")
    
    # Filter Controls
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        status_filter = st.multiselect("Filter by Status", options=df['compliance_status'].unique(), default=df['compliance_status'].unique())
    with f_col2:
        platform_filter = st.multiselect("Filter by Platform", options=df['platform'].unique(), default=df['platform'].unique())
    with f_col3:
        score_range = st.slider("Score Range", 0, 100, (0, 100))
        
    filtered_df = df[
        (df['compliance_status'].isin(status_filter)) &
        (df['platform'].isin(platform_filter)) &
        (df['compliance_score'] >= score_range[0]) &
        (df['compliance_score'] <= score_range[1])
    ].copy()
    
    # Parse details JSON to extract missing fields and other information
    import json
    
    def parse_details(details_str):
        """Parse the details JSON and extract key information"""
        if not details_str or details_str == 'null':
            return {
                'missing_fields': 'N/A',
                'brand': 'N/A',
                'mrp': 'N/A',
                'issues_count': 0
            }
        
        try:
            details = json.loads(details_str)
            issues = details.get('issues', [])
            
            # Extract missing fields from issues
            missing_fields = []
            for issue in issues:
                if 'missing' in issue.lower():
                    # Extract field name from issue text
                    field = issue.split(':')[1].strip() if ':' in issue else issue
                    missing_fields.append(field)
            
            return {
                'missing_fields': ', '.join(missing_fields) if missing_fields else 'None',
                'brand': details.get('brand', 'N/A'),
                'mrp': details.get('mrp', 'N/A'),
                'issues_count': len(issues),
                'company': details.get('company', ''),
                'category': details.get('category', '')
            }
        except:
            return {
                'missing_fields': 'Error parsing',
                'brand': 'N/A',
                'mrp': 'N/A',
                'issues_count': 0
            }
    
    # Apply parsing to create new columns
    parsed_data = filtered_df['details'].apply(parse_details)
    filtered_df['missing_fields'] = parsed_data.apply(lambda x: x['missing_fields'])
    filtered_df['brand'] = parsed_data.apply(lambda x: x['brand'])
    filtered_df['mrp'] = parsed_data.apply(lambda x: x['mrp'])
    filtered_df['issues_count'] = parsed_data.apply(lambda x: x['issues_count'])
    filtered_df['search_info'] = parsed_data.apply(lambda x: x.get('company') or x.get('category') or '')
    
    # Format the datetime column
    if 'checked_at' in filtered_df.columns:
        filtered_df['check_time'] = filtered_df['checked_at'].dt.strftime('%d %b %Y, %I:%M %p')
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} total records**")
    
    # Display comprehensive table
    display_df = filtered_df[[
        'product_title', 
        'platform', 
        'compliance_score', 
        'compliance_status',
        'missing_fields',
        'brand',
        'mrp',
        'issues_count',
        'check_time'
    ]].copy()
    
    # Rename columns for better display
    display_df.columns = [
        'Product / File Name',
        'Platform / Source',
        'Score',
        'Status',
        'Missing LMPC Fields',
        'Brand',
        'MRP',
        'Total Issues',
        'Checked At'
    ]
    
    # Style the dataframe
    def highlight_status(row):
        if row['Status'] == 'COMPLIANT':
            return ['background-color: #d4edda'] * len(row)
        elif row['Status'] == 'NON_COMPLIANT':
            return ['background-color: #f8d7da'] * len(row)
        elif row['Status'] == 'PARTIAL':
            return ['background-color: #fff3cd'] * len(row)
        else:
            return [''] * len(row)
    
    # Display the styled dataframe
    st.dataframe(
        display_df.style.apply(highlight_status, axis=1),
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # Add expandable sections for detailed view
    st.markdown("---")
    st.subheader("🔍 Detailed Product Information")
    
    # Show detailed information for each product in expandable sections
    for idx, row in filtered_df.head(20).iterrows():  # Show top 20 for performance
        with st.expander(f"📦 {row['product_title'][:80]}... (Score: {row['compliance_score']})"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Basic Information:**")
                st.write(f"🏷️ **Product:** {row['product_title']}")
                st.write(f"🛒 **Platform:** {row['platform']}")
                st.write(f"🏢 **Brand:** {row['brand']}")
                st.write(f"💰 **MRP:** {row['mrp']}")
                if row['search_info']:
                    st.write(f"🔍 **Search:** {row['search_info']}")
            
            with col2:
                st.markdown("**Compliance Information:**")
                score = row['compliance_score']
                status = row['compliance_status']
                
                if status == 'COMPLIANT':
                    st.success(f"✅ **Status:** COMPLIANT")
                elif status == 'NON_COMPLIANT':
                    st.error(f"❌ **Status:** NON-COMPLIANT")
                else:
                    st.warning(f"⚠️ **Status:** {status}")
                
                st.write(f"📊 **Score:** {score}%")
                st.write(f"⚠️ **Total Issues:** {row['issues_count']}")
                st.write(f"🕐 **Checked:** {row['check_time']}")
            
            # Show missing fields
            if row['missing_fields'] and row['missing_fields'] != 'None':
                st.markdown("**❌ Missing LMPC Fields:**")
                st.error(row['missing_fields'])
            else:
                st.success("✅ All required LMPC fields are present")
            
            # Show raw details
            if row['details'] and row['details'] != 'null':
                with st.expander("📄 View Raw JSON Data"):
                    try:
                        details_json = json.loads(row['details'])
                        st.json(details_json)
                    except:
                        st.text(row['details'])



# Call main function
main()
