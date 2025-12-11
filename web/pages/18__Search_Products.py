import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import json
import sys
import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # goes up to /web
STYLE_PATH = BASE_DIR / "assets" / "style.css"

# BharatVision Theme Setup
st.set_page_config(
    page_title="Search Products - BharatVision",
    page_icon="assets/logo.png",
    layout="wide",
)

# Load BharatVision CSS
with open(STYLE_PATH, "r", encoding="utf-8") as f:    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header with Logo
st.markdown(
    """
    <div class="header">
        <img src="../assets/logo.png" alt="BharatVision Logo" class="logo">
        <h1>Search Products - Legal Metrology Compliance</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Enhanced Custom CSS
st.markdown("""
<style>
    /* Hide streamlit_app from sidebar navigation */
    [data-testid="stSidebarNav"] li:first-child {
        display: none !important;
    }
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: #FFFFFF !important;
    }
    
    .main {
        font-family: 'Inter', sans-serif;
        background: #FFFFFF;
        color: #000000;
    }
    
    .search-header {
        background: #3866D5;
        padding: 1.5rem;
        border-radius: 16px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .search-header h1, .search-header p {
        color: #FFFFFF !important;
    }
    
    .product-result {
        background: #FFFFFF;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: none;
        margin: 0.75rem 0;
        color: #000000;
    }
    
    .verification-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .verified {
        background: #e8f5e9;
        color: #388e3c;
    }
    
    .unverified {
        background: #ffebee;
        color: #c62828;
    }
    
    .partial {
        background: #fff3e0;
        color: #f57c00;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
if "user" not in st.session_state:
    st.error("Please login first")
    st.stop()

# Header
st.markdown("""
<div class="search-header">
    <h1>🔍 Product Search & Verification</h1>
    <p>Search and verify products for compliance and authenticity</p>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs([
    "🔎 Search Products",
    "✅ Verification Results",
    "📊 Search Analytics"
])

# Initialize session state
if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "verified_products" not in st.session_state:
    st.session_state.verified_products = []

# Sample product database
SAMPLE_PRODUCTS = [
    {"id": "PROD-001", "name": "Premium Coffee Blend", "category": "Food & Beverage", "mrp": 450, "verified": True, "compliance_status": "Compliant"},
    {"id": "PROD-002", "name": "Organic Tea", "category": "Food & Beverage", "mrp": 320, "verified": True, "compliance_status": "Compliant"},
    {"id": "PROD-003", "name": "Spice Mix", "category": "Food & Beverage", "mrp": 150, "verified": False, "compliance_status": "Unverified"},
    {"id": "PROD-004", "name": "Electronics Adapter", "category": "Electronics", "mrp": 599, "verified": True, "compliance_status": "Compliant"},
    {"id": "PROD-005", "name": "USB Cable", "category": "Electronics", "mrp": 299, "verified": True, "compliance_status": "Compliant"},
]

# TAB 1: Search Products
with tab1:
    st.subheader("🔎 Search Products")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("Search by Product ID, Name, or Category", placeholder="e.g., PROD-001 or Coffee")
    
    with col2:
        search_by = st.selectbox("Search By", ["All", "Product ID", "Name", "Category"])
    
    with col3:
        if st.button("🔍 Search", type="primary"):
            st.session_state.search_triggered = True
    
    # Perform search
    if st.session_state.get("search_triggered", False):
        results = []
        
        for product in SAMPLE_PRODUCTS:
            match = False
            
            if search_by == "All":
                match = (search_query.lower() in product["id"].lower() or
                        search_query.lower() in product["name"].lower() or
                        search_query.lower() in product["category"].lower())
            elif search_by == "Product ID":
                match = search_query.lower() in product["id"].lower()
            elif search_by == "Name":
                match = search_query.lower() in product["name"].lower()
            elif search_by == "Category":
                match = search_query.lower() in product["category"].lower()
            
            if match:
                results.append(product)
        
        # Add to search history
        search_record = {
            "query": search_query,
            "results_count": len(results),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "search_by": search_by
        }
        st.session_state.search_history.append(search_record)
        
        # Display results
        if results:
            st.success(f"✅ Found {len(results)} product(s)")
            st.markdown("---")
            
            for product in results:
                st.markdown(f"""
                <div class="product-result">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4>{product['name']}</h4>
                            <p><strong>Product ID:</strong> {product['id']} | <strong>Category:</strong> {product['category']}</p>
                            <p><strong>MRP:</strong> ₹{product['mrp']} | <strong>Compliance:</strong> {product['compliance_status']}</p>
                        </div>
                        <span class="verification-badge {'verified' if product['verified'] else 'unverified'}">
                            {'✅ Verified' if product['verified'] else '❌ Unverified'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"📋 View Details - {product['id']}", key=f"details_{product['id']}"):
                        st.json(product)
                
                with col2:
                    if st.button(f"✅ Verify - {product['id']}", key=f"verify_{product['id']}"):
                        st.session_state.verified_products.append({
                            "product": product,
                            "verified_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "verified_by": st.session_state.user.get("username", "Unknown") if isinstance(st.session_state.user, dict) else "Unknown"
                        })
                        st.success(f"✅ Product verified: {product['id']}")
                
                with col3:
                    if st.button(f"📝 Flag - {product['id']}", key=f"flag_{product['id']}"):
                        st.warning(f"⚠️ Product flagged for review: {product['id']}")
                
                st.markdown("---")
        else:
            st.warning("❌ No products found matching your search")
        
        st.session_state.search_triggered = False

# TAB 2: Verification Results
with tab2:
    st.subheader("✅ Verification Results")
    
    if st.session_state.verified_products:
        st.write(f"**Total Verified:** {len(st.session_state.verified_products)}")
        st.markdown("---")
        
        for record in st.session_state.verified_products:
            product = record["product"]
            
            st.markdown(f"""
            <div class="product-result">
                <div>
                    <h4>{product['name']}</h4>
                    <p><strong>Product ID:</strong> {product['id']}</p>
                    <p><strong>Verified by:</strong> {record['verified_by']} on {record['verified_date']}</p>
                    <p><strong>Compliance Status:</strong> {product['compliance_status']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🗑️ Remove {product['id']}", key=f"remove_verified_{product['id']}"):
                st.session_state.verified_products.remove(record)
                st.rerun()
            
            st.markdown("---")
    else:
        st.info("No verified products yet. Search and verify products from the search tab.")
    
    # Export verified products
    if st.session_state.verified_products:
        st.markdown("---")
        
        export_df = pd.DataFrame([
            {
                "Product ID": r["product"]["id"],
                "Product Name": r["product"]["name"],
                "Category": r["product"]["category"],
                "MRP": r["product"]["mrp"],
                "Compliance Status": r["product"]["compliance_status"],
                "Verified Date": r["verified_date"],
                "Verified By": r["verified_by"]
            }
            for r in st.session_state.verified_products
        ])
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="verified_products.csv",
            mime="text/csv"
        )

# TAB 3: Search Analytics
with tab3:
    st.subheader("📊 Search Analytics")
    
    if st.session_state.search_history:
        history_df = pd.DataFrame(st.session_state.search_history)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Searches", len(st.session_state.search_history))
        
        with col2:
            total_results = history_df["results_count"].sum()
            st.metric("Total Results Found", total_results)
        
        with col3:
            avg_results = history_df["results_count"].mean()
            st.metric("Avg Results per Search", f"{avg_results:.1f}")
        
        st.markdown("---")
        
        # Display search history
        st.subheader("Search History")
        st.dataframe(history_df, width='stretch')
        
        # Search analytics
        st.subheader("Search Type Distribution")
        search_type_counts = history_df["search_by"].value_counts()
        st.bar_chart(search_type_counts)
    else:
        st.info("No search history yet")

# Footer
st.markdown(
    """
    <footer>
        <p>© 2025 BharatVision. All rights reserved.</p>
    </footer>
    """,
    unsafe_allow_html=True,
)



