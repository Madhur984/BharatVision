"""
UI Components Module - Legal Metrology OCR Pipeline

Reusable UI components for the Streamlit web interface.
Provides consistent styling and behavior across all pages.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64
import io

# Color scheme constants
PRIMARY_COLOR = "#1f4037"
SECONDARY_COLOR = "#99f2c8"
SUCCESS_COLOR = "#28a745"
WARNING_COLOR = "#ffc107"
ERROR_COLOR = "#dc3545"
INFO_COLOR = "#17a2b8"

def create_status_badge(status: str, text: str = None) -> str:
    """Create a colored status badge"""
    if text is None:
        text = status
    
    color_map = {
        'COMPLIANT': SUCCESS_COLOR,
        'NON_COMPLIANT': ERROR_COLOR,
        'PROCESSING': WARNING_COLOR,
        'ERROR': ERROR_COLOR,
        'QUEUED': INFO_COLOR,
        'COMPLETED': SUCCESS_COLOR
    }
    
    color = color_map.get(status.upper(), INFO_COLOR)
    
    return f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: bold;
        text-transform: uppercase;
    ">{text}</span>
    """

def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal") -> None:
    """Create a styled metric card"""
    delta_html = ""
    if delta:
        delta_colors = {
            "normal": "#666",
            "inverse": "#666", 
            "off": "transparent"
        }
        delta_html = f'<p style="color: {delta_colors.get(delta_color, "#666")}; font-size: 0.875rem; margin: 0;">{delta}</p>'
    
    card_html = f"""
    <div style="
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid {PRIMARY_COLOR};
        margin: 0.5rem 0;
    ">
        <h3 style="margin: 0; color: {PRIMARY_COLOR}; font-size: 1.5rem; font-weight: bold;">{value}</h3>
        <p style="margin: 0.25rem 0 0 0; color: #666; font-size: 0.875rem;">{title}</p>
        {delta_html}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def create_progress_ring(percentage: float, size: int = 100, color: str = PRIMARY_COLOR) -> str:
    """Create an animated progress ring SVG"""
    radius = (size - 10) // 2
    circumference = 2 * 3.14159 * radius
    stroke_dasharray = circumference
    stroke_dashoffset = circumference - (percentage / 100) * circumference
    
    return f"""
    <div style="display: flex; align-items: center; justify-content: center;">
        <svg width="{size}" height="{size}" style="transform: rotate(-90deg);">
            <circle
                cx="{size//2}"
                cy="{size//2}"
                r="{radius}"
                stroke="#e6e6e6"
                stroke-width="8"
                fill="transparent"
            />
            <circle
                cx="{size//2}"
                cy="{size//2}"
                r="{radius}"
                stroke="{color}"
                stroke-width="8"
                fill="transparent"
                stroke-dasharray="{stroke_dasharray}"
                stroke-dashoffset="{stroke_dashoffset}"
                style="transition: stroke-dashoffset 0.5s ease-in-out;"
            />
            <text
                x="{size//2}"
                y="{size//2}"
                dy="0.3em"
                text-anchor="middle"
                style="font-size: {size//4}px; font-weight: bold; fill: {color}; transform: rotate(90deg); transform-origin: {size//2}px {size//2}px;"
            >{int(percentage)}%</text>
        </svg>
    </div>
    """

def create_compliance_indicator(violations: List[Dict], show_details: bool = True) -> None:
    """Create a comprehensive compliance status indicator"""
    total_violations = len(violations)
    
    if total_violations == 0:
        # Fully compliant
        st.markdown(f"""
        <div style="
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            margin: 1rem 0;
        ">
            <h3 style="margin: 0; color: #155724;">🎉 FULLY COMPLIANT</h3>
            <p style="margin: 0.5rem 0 0 0;">This product meets all Legal Metrology requirements!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Count violations by severity
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for violation in violations:
        severity = violation.get('severity', 'MEDIUM').upper()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Determine overall status
    if severity_counts['CRITICAL'] > 0:
        status_color = ERROR_COLOR
        status_text = "CRITICAL VIOLATIONS"
        status_icon = "🚨"
    elif severity_counts['HIGH'] > 0:
        status_color = WARNING_COLOR
        status_text = "HIGH PRIORITY VIOLATIONS"
        status_icon = "⚠️"
    else:
        status_color = INFO_COLOR
        status_text = "MINOR VIOLATIONS"
        status_icon = "ℹ️"
    
    # Main status banner
    st.markdown(f"""
    <div style="
        background: {status_color};
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 1rem 0;
    ">
        <h3 style="margin: 0; color: white;">{status_icon} {status_text}</h3>
        <p style="margin: 0.5rem 0 0 0;">Found {total_violations} compliance violation(s)</p>
    </div>
    """, unsafe_allow_html=True)
    
    if show_details:
        # Severity breakdown
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if severity_counts['CRITICAL'] > 0:
                create_metric_card("Critical", str(severity_counts['CRITICAL']))
        
        with col2:
            if severity_counts['HIGH'] > 0:
                create_metric_card("High Priority", str(severity_counts['HIGH']))
        
        with col3:
            if severity_counts['MEDIUM'] > 0:
                create_metric_card("Medium", str(severity_counts['MEDIUM']))
        
        with col4:
            if severity_counts['LOW'] > 0:
                create_metric_card("Low Priority", str(severity_counts['LOW']))

def create_violation_details_table(violations: List[Dict]) -> None:
    """Create a detailed table of violations"""
    if not violations:
        return
    
    st.markdown("#### 📋 Violation Details")
    
    table_data = []
    for i, violation in enumerate(violations, 1):
        table_data.append({
            '#': i,
            'Rule ID': violation.get('rule_id', 'UNKNOWN'),
            'Severity': violation.get('severity', 'MEDIUM').title(),
            'Field': violation.get('violating_field', 'N/A'),
            'Description': violation.get('description', 'No description available')
        })
    
    df = pd.DataFrame(table_data)
    
    # Style the dataframe
    def highlight_severity(val):
        if val == 'Critical':
            return f'background-color: {ERROR_COLOR}; color: white'
        elif val == 'High':
            return f'background-color: {WARNING_COLOR}; color: black'
        elif val == 'Medium':
            return f'background-color: {INFO_COLOR}; color: white'
        return ''
    
    styled_df = df.style.applymap(highlight_severity, subset=['Severity'])
    
    st.dataframe(styled_df, width='stretch', hide_index=True, key="violation_details_table")

def create_processing_timeline(steps: List[Dict]) -> None:
    """Create a visual processing timeline"""
    st.markdown("#### ⏱️ Processing Timeline")
    
    for i, step in enumerate(steps):
        is_last = i == len(steps) - 1
        
        # Timeline connector
        if not is_last:
            connector = "│"
        else:
            connector = ""
        
        # Step status
        status = step.get('status', 'completed')
        if status == 'completed':
            icon = "✅"
            color = SUCCESS_COLOR
        elif status == 'processing':
            icon = "🔄"
            color = WARNING_COLOR
        elif status == 'error':
            icon = "❌"
            color = ERROR_COLOR
        else:
            icon = "⏳"
            color = INFO_COLOR
        
        # Step card
        st.markdown(f"""
        <div style="
            display: flex;
            margin: 0.5rem 0;
        ">
            <div style="
                width: 30px;
                text-align: center;
                margin-right: 1rem;
            ">
                <div style="
                    background: {color};
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.875rem;
                ">{icon}</div>
                <div style="
                    height: 20px;
                    width: 2px;
                    background: #ddd;
                    margin: 5px auto;
                ">{connector}</div>
            </div>
            <div style="
                flex: 1;
                background: white;
                padding: 0.75rem;
                border-radius: 0.375rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border-left: 3px solid {color};
            ">
                <h4 style="margin: 0 0 0.25rem 0; color: {PRIMARY_COLOR};">{step.get('name', 'Unknown Step')}</h4>
                <p style="margin: 0; color: #666; font-size: 0.875rem;">{step.get('description', '')}</p>
                <small style="color: #999;">Duration: {step.get('duration', 'N/A')}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

def create_image_comparison(original_image, processed_image=None, annotations=None) -> None:
    """Create a side-by-side image comparison"""
    if processed_image is None:
        # Single image display
        st.image(original_image, caption="Original Image", width='stretch')
        return
    
    # Side-by-side comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original Image**")
        st.image(original_image, width='stretch')
    
    with col2:
        st.markdown("**Processed Image**")
        st.image(processed_image, width='stretch')
    
    if annotations:
        st.markdown("**Image Annotations:**")
        for annotation in annotations:
            st.write(f"• {annotation}")

def create_data_field_display(data: Dict[str, Any], expected_fields: List[str]) -> None:
    """Create a structured display of extracted data fields"""
    st.markdown("#### 📋 Extracted Data Fields")
    
    # Organize fields by status
    found_fields = {}
    missing_fields = []
    
    for field in expected_fields:
        value = data.get(field)
        if value and str(value).strip():
            found_fields[field] = value
        else:
            missing_fields.append(field)
    
    # Display found fields
    if found_fields:
        st.markdown("**✅ Successfully Extracted:**")
        
        for field, value in found_fields.items():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write(f"**{field.replace('_', ' ').title()}:**")
            
            with col2:
                # Truncate long values
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                
                st.code(display_value)
    
    # Display missing fields
    if missing_fields:
        st.markdown("**❌ Missing Fields:**")
        
        missing_cols = st.columns(min(len(missing_fields), 3))
        for i, field in enumerate(missing_fields):
            col_idx = i % len(missing_cols)
            with missing_cols[col_idx]:
                st.markdown(f"• {field.replace('_', ' ').title()}")

def create_analytics_chart(data: List[Dict], chart_type: str = "line") -> None:
    """Create analytics charts from processing data"""
    if not data:
        st.info("No data available for analytics")
        return
    
    df = pd.DataFrame(data)
    
    if chart_type == "line":
        # Processing time trend
        if 'processing_time' in df.columns:
            fig = px.line(
                df,
                y='processing_time',
                title="Processing Time Trend",
                labels={'processing_time': 'Time (seconds)', 'index': 'Processing Order'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')
    
    elif chart_type == "pie":
        # Compliance distribution
        if 'compliance_status' in df.columns:
            status_counts = df['compliance_status'].value_counts()
            
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Compliance Distribution",
                color_discrete_map={
                    'COMPLIANT': SUCCESS_COLOR,
                    'NON_COMPLIANT': ERROR_COLOR
                }
            )
            st.plotly_chart(fig, width='stretch')
    
    elif chart_type == "bar":
        # Violation frequency
        if 'violations' in df.columns:
            violation_counts = df['violations'].apply(len)
            
            fig = px.histogram(
                x=violation_counts,
                title="Violation Count Distribution",
                labels={'x': 'Number of Violations', 'y': 'Frequency'}
            )
            st.plotly_chart(fig, width='stretch')

def create_export_button(data: Any, filename: str, file_type: str = "json") -> None:
    """Create a styled export button with download functionality"""
    if file_type == "json":
        import json
        file_data = json.dumps(data, indent=2, ensure_ascii=False)
        mime_type = "application/json"
    elif file_type == "csv":
        if isinstance(data, pd.DataFrame):
            file_data = data.to_csv(index=False)
        else:
            df = pd.DataFrame(data)
            file_data = df.to_csv(index=False)
        mime_type = "text/csv"
    else:
        st.error(f"Unsupported file type: {file_type}")
        return
    
    st.download_button(
        label=f"📥 Export {file_type.upper()}",
        data=file_data,
        file_name=f"{filename}.{file_type}",
        mime=mime_type,
        width='stretch'
    )

def create_loading_spinner(text: str = "Processing...") -> None:
    """Create a custom loading spinner"""
    spinner_html = f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
    ">
        <div style="
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid {PRIMARY_COLOR};
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        "></div>
        <p style="
            color: {PRIMARY_COLOR};
            font-weight: bold;
            margin: 0;
        ">{text}</p>
    </div>
    
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """
    
    st.markdown(spinner_html, unsafe_allow_html=True)

def create_help_tooltip(text: str, help_text: str) -> None:
    """Create text with a help tooltip"""
    tooltip_html = f"""
    <div style="display: inline-block; position: relative;">
        <span>{text}</span>
        <span style="
            margin-left: 0.5rem;
            color: {INFO_COLOR};
            cursor: help;
            font-size: 0.875rem;
        " title="{help_text}">ℹ️</span>
    </div>
    """
    
    st.markdown(tooltip_html, unsafe_allow_html=True)

def create_alert_box(message: str, alert_type: str = "info") -> None:
    """Create a styled alert box"""
    color_map = {
        'info': INFO_COLOR,
        'success': SUCCESS_COLOR,
        'warning': WARNING_COLOR,
        'error': ERROR_COLOR
    }
    
    icon_map = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }
    
    color = color_map.get(alert_type, INFO_COLOR)
    icon = icon_map.get(alert_type, 'ℹ️')
    
    alert_html = f"""
    <div style="
        background: {color}22;
        border: 1px solid {color};
        border-left: 4px solid {color};
        color: {color};
        padding: 1rem;
        border-radius: 0.375rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
    ">
        <span style="margin-right: 0.5rem; font-size: 1.2rem;">{icon}</span>
        <span>{message}</span>
    </div>
    """
    
    st.markdown(alert_html, unsafe_allow_html=True)
