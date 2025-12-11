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
    page_title="ERP Product Management - BharatVision",
    page_icon="assets/logo.png",
    layout="wide",
)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.auth import AuthManager, UserRole

# Load BharatVision CSS
with open(STYLE_PATH, "r", encoding="utf-8") as f:    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Hide streamlit_app from sidebar navigation
st.markdown("""
<style>
    /* Hide streamlit_app from sidebar navigation */
    [data-testid="stSidebarNav"] li:first-child {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Header with Logo
st.markdown(
    """
    <div class="header">
        <img src="../assets/logo.png" alt="BharatVision Logo" class="logo">
        <h1>ERP Product Management - Legal Metrology Compliance</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ERP Product Management Content
st.subheader("Manage Products in ERP")
st.info("This page allows managing products in the ERP system for compliance.")

# Check authentication
if "user" not in st.session_state:
    st.error("Please login first")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Add Product",
    "📊 Product Inventory",
    "✏️ Edit Product",
    "📈 Analytics"
])

# Initialize session state
if "products" not in st.session_state:
    st.session_state.products = []

# TAB 1: Add Product
with tab1:
    st.subheader("➕ Add New Product")
    
    with st.form("product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product Name", placeholder="e.g., Premium Coffee Blend")
            product_code = st.text_input("Product Code/SKU", placeholder="e.g., PROD-2024-001")
            mrp = st.number_input("Maximum Retail Price (MRP)", min_value=0.0, step=0.01)
        
        with col2:
            category = st.selectbox("Product Category", [
                "Food & Beverage",
                "Electronics",
                "Pharmaceuticals",
                "Chemicals",
                "Textiles",
                "Other"
            ])
            quantity = st.number_input("Initial Quantity", min_value=0, step=1)
            unit = st.selectbox("Unit", ["kg", "liters", "pieces", "boxes", "tons"])
        
        manufacturer = st.text_input("Manufacturer Name", placeholder="Company name")
        compliance_status = st.selectbox("Initial Compliance Status", ["Draft", "Pending Review", "Compliant", "Non-Compliant"])
        
        notes = st.text_area("Additional Notes", placeholder="Product-specific compliance notes")
        
        submit = st.form_submit_button("📤 Add Product", type="primary")
        
        if submit:
            if product_name and product_code and mrp > 0:
                new_product = {
                    "id": product_code,
                    "name": product_name,
                    "category": category,
                    "mrp": mrp,
                    "quantity": quantity,
                    "unit": unit,
                    "manufacturer": manufacturer,
                    "status": compliance_status,
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "notes": notes
                }
                
                st.session_state.products.append(new_product)
                st.success(f"✅ Product added: {product_name} ({product_code})")
            else:
                st.error("Please fill in all required fields")

# TAB 2: Product Inventory
with tab2:
    st.subheader("📊 Product Inventory")
    
    if st.session_state.products:
        products_df = pd.DataFrame(st.session_state.products)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Products", len(st.session_state.products))
        
        with col2:
            compliant = len([p for p in st.session_state.products if p["status"] == "Compliant"])
            st.metric("Compliant", compliant)
        
        with col3:
            non_compliant = len([p for p in st.session_state.products if p["status"] == "Non-Compliant"])
            st.metric("Non-Compliant", non_compliant)
        
        with col4:
            pending = len([p for p in st.session_state.products if p["status"] == "Pending Review"])
            st.metric("Pending", pending)
        
        st.markdown("---")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            filter_status = st.multiselect("Filter by Status", ["Draft", "Pending Review", "Compliant", "Non-Compliant"], default=["Compliant"])
        
        with col2:
            filter_category = st.multiselect("Filter by Category", products_df["category"].unique())
        
        # Apply filters
        filtered_products = [
            p for p in st.session_state.products
            if p["status"] in filter_status and (not filter_category or p["category"] in filter_category)
        ]
        
        if filtered_products:
            # Display as table
            display_df = pd.DataFrame(filtered_products)[["id", "name", "category", "mrp", "quantity", "unit", "status", "last_updated"]]
            st.dataframe(display_df, width='stretch')
            
            # Category distribution
            st.subheader("Products by Category")
            category_counts = products_df["category"].value_counts()
            st.bar_chart(category_counts)
        else:
            st.info("No products match the selected filters")
    else:
        st.info("No products added yet")

# TAB 3: Edit Product
with tab3:
    st.subheader("✏️ Edit Product Information")
    
    if st.session_state.products:
        product_ids = [p["id"] for p in st.session_state.products]
        selected_id = st.selectbox("Select Product to Edit", product_ids)
        
        # Find product
        product = next((p for p in st.session_state.products if p["id"] == selected_id), None)
        
        if product:
            with st.form("edit_product_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    product["name"] = st.text_input("Product Name", value=product["name"])
                    product["mrp"] = st.number_input("MRP", value=product["mrp"], min_value=0.0, step=0.01)
                    product["quantity"] = st.number_input("Quantity", value=product["quantity"], min_value=0)
                
                with col2:
                    product["category"] = st.selectbox("Category", ["Food & Beverage", "Electronics", "Pharmaceuticals", "Chemicals", "Textiles", "Other"], index=["Food & Beverage", "Electronics", "Pharmaceuticals", "Chemicals", "Textiles", "Other"].index(product["category"]))
                    product["status"] = st.selectbox("Compliance Status", ["Draft", "Pending Review", "Compliant", "Non-Compliant"], index=["Draft", "Pending Review", "Compliant", "Non-Compliant"].index(product["status"]))
                    product["unit"] = st.selectbox("Unit", ["kg", "liters", "pieces", "boxes", "tons"], index=["kg", "liters", "pieces", "boxes", "tons"].index(product["unit"]))
                
                product["notes"] = st.text_area("Notes", value=product["notes"])
                
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    product["last_updated"] = datetime.now().strftime("%Y-%m-%d")
                    st.success("✅ Product updated successfully")
    else:
        st.info("No products to edit")

# TAB 4: Analytics
with tab4:
    st.subheader("📈 Product Analytics")
    
    if st.session_state.products:
        products_df = pd.DataFrame(st.session_state.products)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Status Distribution")
            status_counts = products_df["status"].value_counts()
            st.bar_chart(status_counts)
        
        with col2:
            st.subheader("Products by Category")
            category_counts = products_df["category"].value_counts()
            st.bar_chart(category_counts)
        
        # Compliance rate
        st.subheader("Compliance Rate")
        compliant_count = len([p for p in st.session_state.products if p["status"] == "Compliant"])
        total_count = len(st.session_state.products)
        compliance_rate = (compliant_count / total_count * 100) if total_count > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Compliance Rate", f"{compliance_rate:.1f}%")
        with col2:
            st.metric("Total Value", f"₹{sum(p['mrp'] * p['quantity'] for p in st.session_state.products):,.2f}")
        with col3:
            st.metric("Total Quantity", sum(p["quantity"] for p in st.session_state.products))
    else:
        st.info("No analytics available yet")

# Footer
st.markdown(
    """
    <footer>
        <p>© 2025 BharatVision. All rights reserved.</p>
    </footer>
    """,
    unsafe_allow_html=True,
)



