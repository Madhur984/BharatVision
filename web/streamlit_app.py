# web/streamlit_app.py
"""
BharatVision / PackNetra - Unified Dashboard (revised)
This file uses the new import path behavior requested:
  sys.path.append('.') and sys.path.insert(0, parent_of_this_file)
It keeps your backend intact (no modifications) and gracefully
adds auth hooks and new navigation items.
"""

# Initialize headless mode FIRST - before any OpenCV imports
import os
os.environ['OPENCV_HEADLESS'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['MPLBACKEND'] = 'Agg'

# CRITICAL: Set ML_API_URL from Streamlit secrets BEFORE backend imports
# This allows backend/ocr_integration.py to use cloud API
try:
    import streamlit as st
    if hasattr(st, 'secrets') and 'ML_API_URL' in st.secrets:
        os.environ['ML_API_URL'] = st.secrets['ML_API_URL']
        print(f"✅ ML_API_URL set from Streamlit secrets: {st.secrets['ML_API_URL']}")
    else:
        print("⚠️ ML_API_URL not found in Streamlit secrets, will use local OCR")
except Exception as e:
    print(f"⚠️ Could not read ML_API_URL from secrets: {e}")

# Optional auto-install of dependencies at startup.
# Set environment variable `AUTO_INSTALL_DEPS=1` to enable automatic pip installs
if os.environ.get('AUTO_INSTALL_DEPS', '0') == '1':
    try:
        import sys, subprocess, shlex
        reqs = [
            str(Path(__file__).parent.parent / 'requirements.txt')
        ]
        # If local full requirements present, include it
        local_reqs = Path(__file__).parent / 'requirements.local.txt'
        if local_reqs.exists():
            reqs.append(str(local_reqs))

        for r in reqs:
            try:
                cmd = [sys.executable, '-m', 'pip', 'install', '-r', r]
                # Run pip synchronously and stream output
                subprocess.check_call(cmd)
            except Exception:
                # Do not crash the app if install fails; just log
                try:
                    print(f"Warning: automatic pip install failed for {r}")
                except Exception:
                    pass
    except Exception:
        pass

import io
import sys
from typing import Dict, Any, List
from pathlib import Path
import json

# Make repo paths available to imports (as requested)
sys.path.append('.')
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import headless initializer
try:
    from web.init_headless import ensure_headless_opencv
except ImportError:
    pass

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns

# Check authentication first
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None

# Redirect to login if not authenticated
if not st.session_state.authenticated:
    st.switch_page("pages/00__Login.py")
    st.stop()

# Optional authentication hooks (non-fatal)
try:
    from backend.auth import AuthManager, UserRole
except Exception:
    AuthManager = None
    UserRole = None

# Backend pipeline - keep unchanged, fail gracefully if missing
try:
    from lmpc_checker.main import run_pipeline_for_image
except Exception:
    run_pipeline_for_image = None

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="BharatVision Dashboard - Legal Metrology OCR",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------
# THEME / CSS (inline) - Teal, Blue, Orange palette
# ---------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --navy: #3866D5;
            --navy-dark: #071c3d;
            --navy-light: #e7edf7;
            --accent: #3866D5;
            --text: #000000;
            --muted: #4a5568;
            --white: #FFFFFF;
        }
        .stApp { background: #FFFFFF !important; color: #000000 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }
        
        /* Force all text to black on white backgrounds */
        .stApp p, .stApp span, .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp label, .stApp li {
            color: #000000 !important;
        }
        
        section[data-testid="stSidebar"] { background: #3866D5 !important; background-color: #3866D5 !important; color: #FFFFFF !important; border-right: 4px solid #3866D5; }
        section[data-testid="stSidebar"] > div { background: #3866D5 !important; background-color: #3866D5 !important; }
        section[data-testid="stSidebar"] > div > div { background: #3866D5 !important; background-color: #3866D5 !important; }
        [data-testid="stSidebar"] { background: #3866D5 !important; background-color: #3866D5 !important; }
        [data-testid="stSidebar"] > div { background: #3866D5 !important; background-color: #3866D5 !important; }
        [data-testid="stSidebarNav"] { background: #3866D5 !important; background-color: #3866D5 !important; }
        section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
        [data-testid="stSidebar"] * { color: #FFFFFF !important; }
        [data-testid="stSidebarNav"] * { color: #FFFFFF !important; }
        .sidebar-header { padding: 16px 12px; border-bottom: 3px solid #FFFFFF; margin-bottom: 12px; border-radius: 8px; background: #3866D5; }
        .sidebar-app-title { font-size: 18px; font-weight: 800; line-height: 1.2; color: #FFFFFF !important; }
        .top-header { background: var(--navy); color: #FFFFFF; padding: 20px 24px; border-radius: 16px; display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; box-shadow:0 4px 15px rgba(7,28,61,0.15); }
        .top-header * { color: #FFFFFF !important; }
        .metric-card, .card { background:#FFFFFF; padding:20px; border-radius:12px; box-shadow:0 4px 15px rgba(11,42,90,0.1); border-left:5px solid var(--navy); color: #000000; }
        .card-title { font-size:16px; font-weight:700; color:#000000; margin-bottom:12px; border-bottom:2px solid var(--navy); padding-bottom:8px; }
        .status-badge-ok { background: var(--navy-light); color: #000000; padding:6px 14px; border-radius:20px; font-weight:700; border:1px solid var(--navy); }
        .status-badge-bad { background: #fbeaea; color:#a4262c; padding:6px 14px; border-radius:20px; font-weight:700; border:1px solid #d1433c; }
        .flagged-result { background: #FFFFFF; border-left:5px solid var(--navy); border-right:1px solid var(--navy); padding:16px; border-radius:12px; margin:12px 0; color: #000000; border: 1px solid #e5e7eb; }
        .violation-flag { background-color:#fbeaea; border-left:5px solid #d1433c; padding:12px; border-radius:8px; margin:8px 0; font-weight:600; color:#a4262c; }
        .stButton>button { background: var(--navy) !important; color:#FFFFFF !important; border-radius:8px !important; padding:10px 20px !important; font-weight:700 !important; border:none !important; }
        .stButton>button:hover { background: #1a3a5c !important; }
        
        /* Hide streamlit_app from sidebar navigation */
        [data-testid="stSidebarNav"] li:first-child { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# ---------------------------------------------------
# Helper utilities (display helpers & analysis)
# ---------------------------------------------------
def severity_icon(sev: str) -> str:
    s = (sev or "").lower()
    if s == "critical":
        return "🔴 Critical"
    if s == "high":
        return "🟠 High"
    if s == "medium":
        return "🟡 Medium"
    if s == "low":
        return "🟢 Low"
    return sev or ""

def status_icon(violated: bool) -> str:
    return "❌ Violated" if violated else "✅ OK"

def analyze_image(image_file) -> Dict[str, Any]:
    """Call backend pipeline with uploaded file. Backend function preserved as-is."""
    if not run_pipeline_for_image:
        raise RuntimeError("run_pipeline_for_image backend is not available; install or check lmpc_checker.")
    bytes_data = image_file.read()
    return run_pipeline_for_image(bytes_data)

def display_flagged_result(title: str, data: Dict[str, Any]):
    st.markdown(f"<div class='flagged-result'><div class='card-title'>{title}</div>", unsafe_allow_html=True)
    for key, value in data.items():
        if isinstance(value, dict):
            with st.expander(f"{key.replace('_', ' ').title()}"):
                st.json(value)
        elif isinstance(value, list):
            if value:
                st.markdown(f"**{key.replace('_',' ').title()}:**")
                for item in value:
                    if isinstance(item, dict):
                        st.json(item)
                    else:
                        st.write(f"- {item}")
        else:
            st.markdown(f"**{key.replace('_',' ').title()}:** {value}")
    st.markdown("</div>", unsafe_allow_html=True)

def display_violations_flagged(violations: List[Dict[str, Any]]):
    if not violations:
        st.success("✅ No violations detected - Fully Compliant")
        return
    st.error(f"⚠️ Found {len(violations)} violation(s)")
    for v in violations:
        sev = (v.get("severity") or "MEDIUM").upper()
        rule_id = v.get("rule_id", "UNKNOWN")
        desc = v.get("description", "No description")
        cls = "violation-flag"
        st.markdown(f"<div class='{cls}'><strong>[{sev}]</strong> {rule_id} — {desc}</div>", unsafe_allow_html=True)

def display_heatmap_violations(violations: List[Dict[str, Any]]):
    if not violations:
        st.info("No heatmap data available")
        return
    # Aggregate by rule_id for demonstration
    counts = {}
    for v in violations:
        rid = v.get("rule_id", "UNKNOWN")
        counts[rid] = counts.get(rid, 0) + 1
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    df = pd.DataFrame(items, columns=["Rule", "Count"])
    plt.figure(figsize=(8, 4))
    sns.barplot(data=df, x="Count", y="Rule")
    st.pyplot(plt.gcf())
    plt.clf()

# ---------------------------------------------------
# SIDEBAR: Navigation + optional auth
# ---------------------------------------------------
with st.sidebar:
    # Display Logo
    logo_path = Path(__file__).parent / "assets" / "image-wm (3).png"
    if logo_path.exists():
        st.image(str(logo_path), width='stretch')
        st.markdown("---")
    
    st.markdown(
        """
        <div class="sidebar-header">
            <div style="font-size:12px; font-weight:700;">🇮🇳 Government of India</div>
            <div class="sidebar-app-title">भारत Vision · Legal Metrology</div>
            <div style="font-size:11px; margin-top:6px;">E-Commerce Compliance Console</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # If AuthManager exists, show login controls (non-blocking)
    if AuthManager:
        try:
            auth = AuthManager()
            user = auth.get_current_user()
            if user:
                st.markdown(f"**Signed in:** {user.get('name')} ({user.get('role')})")
            else:
                if st.button("Sign In"):
                    auth.start_login_flow()  # implement as non-blocking in your backend
        except Exception:
            # don't break if auth backend has issues
            pass

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Ingest",
            "Extraction",
            "Validation",
            "Analytics",
            "User Dashboard",
            "Admin Dashboard",
            "Help",
            "ERP",
            "Web Crawler",
            "Search",
        ],
        index=0,
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Ministry of Consumer Affairs · Legal Metrology")

# ---------------------------------------------------
# SAMPLE STATIC DATA (same as original, kept locally)
# ---------------------------------------------------
session_stats = {
    "today_scans": 332,
    "compliance_rate": 92.5,
    "violations_flagged": 156,
}

recent_scans = pd.DataFrame(
    [
        ["75521466", "Dharan", "Foodgrains", "28-03-2024", "Compliant"],
        ["21562728", "Myatique", "Personal Care", "28-03-2024", "Violation"],
        ["21564729", "Cataris", "Food Fiscal", "28-03-2024", "Compliant"],
        ["21589728", "Tanygue", "Purchasing", "28-03-2024", "Compliant"],
    ],
    columns=["Product ID", "Brand", "Category", "Scan Date", "Status"],
)

violations_over_time = pd.DataFrame({
    "Date": pd.date_range("2024-04-01", periods=30, freq="D"),
    "Violations": [90, 120, 110, 130, 140, 150, 160, 170, 155, 165,
                   180, 185, 190, 200, 210, 215, 220, 210, 205, 215,
                   220, 225, 230, 225, 220, 215, 230, 235, 240, 238],
})

violations_by_category = pd.DataFrame({
    "Category": ["Food", "Beverages", "Cosmetics", "Household", "Pharma"],
    "Violations": [210, 130, 90, 60, 39],
})

state_wise = pd.DataFrame({
    "State": ["Maharashtra", "Uttar Pradesh", "Delhi", "Tamil Nadu", "Gujarat"],
    "Violations": [598, 492, 315, 267, 245],
})

devices_df = pd.DataFrame(
    [
        ["PN-001", "New Delhi HQ", "Online", "5 min ago"],
        ["PN-014", "Mumbai Zone", "Online", "12 min ago"],
        ["PN-021", "Lucknow Zone", "Offline", "2 hours ago"],
        ["PN-033", "Chennai Zone", "Online", "8 min ago"],
    ],
    columns=["Device ID", "Location", "Status", "Last Sync"],
)

# ---------------------------------------------------
# ROUTING: show the section corresponding to `page`
# ---------------------------------------------------
# Dashboard
if page == "🏠 Dashboard":
    st.markdown(
        """
        <div class="top-header">
          <div class="top-header-left">
            <div class="top-header-sub">Government of India · Ministry of Consumer Affairs</div>
            <div class="top-header-title">National Packaging Compliance Dashboard</div>
          </div>
          <div class="top-header-right">
            Today’s Overview<br/><span style="font-weight:600;">Central Command Console</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Total Scans Today</div><div class='metric-value'>{session_stats['today_scans']}</div><div class='metric-sub'>Across all devices</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Compliance Rate</div><div class='metric-value'>{session_stats['compliance_rate']}%</div><div class='metric-sub'>Last 30 days</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Violations Flagged</div><div class='metric-value'>{session_stats['violations_flagged']}</div><div class='metric-sub'>Pending review</div></div>", unsafe_allow_html=True)

    lcol, rcol = st.columns([2, 1])
    with lcol:
        st.markdown('<div class="card"><div class="card-title">Violations Over Time</div>', unsafe_allow_html=True)
        fig = px.line(violations_over_time, x="Date", y="Violations", markers=True)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with rcol:
        st.markdown('<div class="card"><div class="card-title">Overall Compliance</div><div class="card-subtitle">Share of compliant vs non-compliant labels</div>', unsafe_allow_html=True)
        fig2 = px.pie(values=[session_stats["compliance_rate"], 100 - session_stats["compliance_rate"]], names=["Compliant", "Violation"], hole=0.6)
        fig2.update_traces(textinfo="none")
        fig2.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=True)
        st.plotly_chart(fig2, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Recent Scans</div>', unsafe_allow_html=True)
    recent_display = recent_scans.copy()
    recent_display["Status"] = recent_display["Status"].apply(lambda s: "<span class='status-badge-ok'>Compliant</span>" if s.lower().startswith("compliant") else "<span class='status-badge-bad'>Violation</span>")
    st.write(recent_display.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Ingest / Upload Images (redirect to page)
elif page == "Ingest":
    try:
        st.experimental_set_query_params(page="02__Upload_Image")
        st.switch_page("pages/02__Upload_Image.py")
    except Exception:
        st.info("Upload Image page not available.")

# Extraction (Upload Image)
elif page == "Extraction":
    try:
        st.experimental_set_query_params(page="02__Upload_Image")
        st.switch_page("pages/02__Upload_Image.py")
    except Exception:
        st.info("Upload page not available. You can process single images below.")
        # simple fallback upload inline
        uploaded = st.file_uploader("Upload product image (front/back)", type=["jpg", "jpeg", "png"])
        if uploaded is not None:
            st.image(Image.open(uploaded), width='stretch')
            if st.button("Run PackNetra Analysis"):
                if not run_pipeline_for_image:
                    st.error("Backend pipeline not available.")
                else:
                    with st.spinner("Running analysis..."):
                        res = analyze_image(uploaded)
                        st.json(res)

# Validation (Batch)
elif page == "Validation":
    try:
        st.experimental_set_query_params(page="03__Batch_Process")
        st.switch_page("pages/03__Batch_Process.py")
    except Exception:
        st.info("Batch processing page not available. Use Extraction or Upload pages.")

# Analytics
elif page == "Analytics":
    st.markdown('<div class="card"><div class="card-title">State-wise Violations</div>', unsafe_allow_html=True)
    fig = px.bar(state_wise, x="State", y="Violations")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=320)
    st.plotly_chart(fig, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Violations by Category</div>', unsafe_allow_html=True)
    fig2 = px.bar(violations_by_category, x="Category", y="Violations")
    fig2.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=260)
    st.plotly_chart(fig2, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

# User Dashboard
elif page == "User Dashboard":
    st.header("User Dashboard")
    st.info("This area can surfaces user-specific scans, saved reports and notifications.")
    st.dataframe(recent_scans, width='stretch')

# Admin Dashboard
elif page == "Admin Dashboard":
    st.header("Admin Dashboard")
    st.info("Admin tools: rules, web crawler, user management (available in separate pages).")
    st.dataframe(devices_df, width='stretch')

# Help
elif page == "Help":
    st.header("Help & AI Assistance")
    st.markdown("Use the Help page to interact with AI assistant and troubleshooting guides.")
    st.markdown("- Check 'Extraction' to run a single image test.\n- Use 'Validation' for batch runs.\n- For developer help, open console logs.")

# ERP / Web Crawler / Search redirections
elif page == "ERP":
    try:
        st.switch_page("pages/10__ERP_Product_Management.py")
    except Exception:
        st.info("ERP product management page not available here.")

elif page == "Web Crawler":
    try:
        st.switch_page("pages/Web_Crawler.py")
    except Exception:
        st.info("Web Crawler page not available. Ensure backend crawler dependencies are installed (selenium, webdriver).")

elif page == "Search":
    try:
        st.switch_page("pages/18__Search_Products.py")
    except Exception:
        st.info("Search page not available.")

# ---------------------------------------------------
# Additional widgets: flagged results + heatmap previews (local files)
# ---------------------------------------------------
st.markdown("---")
st.subheader("Flagged Results")
flagged_results_path = Path("data/flagged_results.json")
if flagged_results_path.exists():
    try:
        flagged_results = json.loads(flagged_results_path.read_text(encoding="utf-8"))
        st.json(flagged_results)
    except Exception:
        st.warning("Failed to load flagged results JSON.")
else:
    st.info("No flagged results available (data/flagged_results.json missing).")

st.subheader("Violation Heatmap (preview)")
heatmap_data_path = Path("data/heatmap_data.json")
if heatmap_data_path.exists():
    try:
        heatmap_data = json.loads(heatmap_data_path.read_text(encoding="utf-8"))
        # Render with seaborn as a quick preview (expects 2D list or DataFrame-like)
        df_heat = pd.DataFrame(heatmap_data)
        plt.figure(figsize=(10, 5))
        sns.heatmap(df_heat, annot=False, cmap="coolwarm")
        st.pyplot(plt.gcf())
        plt.clf()
    except Exception:
        st.warning("Heatmap data malformed or cannot be plotted.")
else:
    st.info("No heatmap data available (data/heatmap_data.json missing).")

# Footer
st.markdown(
    """
    <footer style="margin-top:18px;">
        <p style="font-size:12px; color: #6B7280;">© 2025 BharatVision. All rights reserved.</p>
    </footer>
    """,
    unsafe_allow_html=True,
)



