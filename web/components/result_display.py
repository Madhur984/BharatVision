"""
Result Display Components - Legal Metrology OCR Pipeline

Specialized components for displaying OCR results, compliance reports,
and processing analytics with professional formatting.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from PIL import Image
import numpy as np

from .ui_components import (
    create_status_badge, create_compliance_indicator, 
    create_violation_details_table, create_data_field_display,
    PRIMARY_COLOR, SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR
)

class ResultDisplayManager:
    """Manages the display of processing results across different result types"""
    
    def __init__(self):
        self.result_types = {
            'ocr': self.display_ocr_results,
            'compliance': self.display_compliance_results,
            'analytics': self.display_analytics_results,
            'comparison': self.display_comparison_results
        }
    
    def display_result(self, result: Dict[str, Any], display_type: str = 'full'):
        """Main method to display results based on type"""
        if display_type == 'summary':
            self.display_result_summary(result)
        elif display_type == 'detailed':
            self.display_detailed_results(result)
        else:  # full
            self.display_full_results(result)
    
    def display_result_summary(self, result: Dict[str, Any]):
        """Display a compact summary of results"""
        st.markdown("### 📊 Processing Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            processing_time = result.get('processing_time', 0)
            st.metric("⏱️ Processing Time", f"{processing_time:.2f}s")
        
        with col2:
            violations = result.get('violations', [])
            st.metric("⚖️ Violations", len(violations))
        
        with col3:
            compliance_status = result.get('compliance_status', 'UNKNOWN')
            status_color = SUCCESS_COLOR if compliance_status == 'COMPLIANT' else ERROR_COLOR
            st.markdown(f"**Status:** {create_status_badge(compliance_status)}", unsafe_allow_html=True)
        
        with col4:
            extracted_fields = len([k for k, v in result.get('refined_data', {}).items() if v])
            st.metric("📝 Fields Extracted", extracted_fields)
    
    def display_detailed_results(self, result: Dict[str, Any]):
        """Display detailed results with all information"""
        st.markdown("### 🔍 Detailed Results")
        
        # Tabbed interface for detailed view
        tab1, tab2, tab3 = st.tabs(["📋 Extracted Data", "⚖️ Compliance Report", "🔧 Technical Details"])
        
        with tab1:
            self.display_extracted_data_tab(result)
        
        with tab2:
            self.display_compliance_tab(result)
        
        with tab3:
            self.display_technical_tab(result)
    
    def display_full_results(self, result: Dict[str, Any]):
        """Display comprehensive results with all tabs and details"""
        # Summary first
        self.display_result_summary(result)
        
        st.markdown("---")
        
        # Full tabbed interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🖼️ Image", "🔍 OCR Output", "📋 Structured Data", 
            "⚖️ Compliance", "📊 Analytics"
        ])
        
        with tab1:
            self.display_image_tab(result)
        
        with tab2:
            self.display_ocr_tab(result)
        
        with tab3:
            self.display_extracted_data_tab(result)
        
        with tab4:
            self.display_compliance_tab(result)
        
        with tab5:
            self.display_analytics_tab(result)
    
    def display_image_tab(self, result: Dict[str, Any]):
        """Display image-related information"""
        st.markdown("#### 🖼️ Image Information")
        
        # Image metadata
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Image Details:**")
            filename = result.get('filename', 'Unknown')
            st.write(f"• **Filename:** {filename}")
            
            file_size = result.get('file_size', 0)
            if file_size > 0:
                st.write(f"• **File Size:** {file_size / 1024:.1f} KB")
            
            dimensions = result.get('image_dimensions', (0, 0))
            if dimensions[0] > 0:
                st.write(f"• **Dimensions:** {dimensions[0]} × {dimensions[1]} pixels")
            
            timestamp = result.get('timestamp', 'Unknown')
            st.write(f"• **Processed:** {timestamp}")
        
        with col2:
            st.markdown("**Processing Method:**")
            method = result.get('method', 'Unknown')
            st.write(f"• **Source:** {method}")
            
            if 'camera_index' in result:
                st.write(f"• **Camera:** Device {result['camera_index']}")
            
            processing_time = result.get('processing_time', 0)
            st.write(f"• **Processing Time:** {processing_time:.2f} seconds")
        
        # Display image if available
        if 'original_image' in result:
            st.markdown("**Original Image:**")
            st.image(result['original_image'], caption="Captured Image", width='stretch')
    
    def display_ocr_tab(self, result: Dict[str, Any]):
        """Display OCR processing results"""
        st.markdown("#### 🔍 OCR Processing Results")
        
        ocr_result = result.get('ocr_result', {})
        
        if isinstance(ocr_result, dict) and 'contents' in ocr_result:
            # Raw text extraction
            st.markdown("**Raw Extracted Text:**")
            st.text_area(
                "OCR Output:",
                ocr_result['contents'],
                height=200,
                help="Raw text extracted by the OCR engine",
                disabled=True
            )
            
            # OCR confidence and statistics
            col1, col2 = st.columns(2)
            
            with col1:
                if 'confidence' in ocr_result:
                    confidence = ocr_result['confidence']
                    st.metric("🎯 OCR Confidence", f"{confidence:.1%}")
                
                # Text statistics
                text_content = ocr_result['contents']
                word_count = len(text_content.split())
                char_count = len(text_content)
                
                st.metric("📝 Word Count", word_count)
                st.metric("🔤 Character Count", char_count)
            
            with col2:
                # Detection statistics
                if 'detection_stats' in ocr_result:
                    stats = ocr_result['detection_stats']
                    st.write("**Detection Statistics:**")
                    for key, value in stats.items():
                        st.write(f"• {key.replace('_', ' ').title()}: {value}")
        
        else:
            # Simple text output
            st.text_area(
                "Raw OCR Output:",
                str(ocr_result),
                height=200,
                disabled=True
            )
    
    def display_extracted_data_tab(self, result: Dict[str, Any]):
        """Display structured data extraction results"""
        st.markdown("#### 📋 Structured Product Data")
        
        refined_data = result.get('refined_data', {})
        
        if not refined_data:
            st.warning("No structured data was extracted from the image.")
            return
        
        # Expected fields from config
        from config import EXPECTED_FIELDS
        create_data_field_display(refined_data, EXPECTED_FIELDS)
        
        # JSON view
        st.markdown("---")
        with st.expander("🔧 Raw JSON Data", expanded=False):
            st.json(refined_data)
        
        # Field extraction statistics
        st.markdown("---")
        st.markdown("**📊 Extraction Statistics:**")
        
        total_fields = len(EXPECTED_FIELDS)
        extracted_fields = len([k for k, v in refined_data.items() if v and str(v).strip()])
        extraction_rate = (extracted_fields / total_fields) * 100 if total_fields > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📝 Total Expected", total_fields)
        
        with col2:
            st.metric("✅ Successfully Extracted", extracted_fields)
        
        with col3:
            st.metric("📊 Extraction Rate", f"{extraction_rate:.1f}%")
    
    def display_compliance_tab(self, result: Dict[str, Any]):
        """Display compliance validation results"""
        st.markdown("#### ⚖️ Legal Metrology Compliance Report")
        
        violations = result.get('violations', [])
        compliance_status = result.get('compliance_status', 'UNKNOWN')
        
        # Compliance indicator
        create_compliance_indicator(violations, show_details=True)
        
        # Detailed violation table
        if violations:
            create_violation_details_table(violations)
            
            # Violation analysis
            st.markdown("---")
            self.display_violation_analysis(violations)
        
        # Compliance recommendations
        st.markdown("---")
        self.display_compliance_recommendations(violations, compliance_status)
    
    def display_analytics_tab(self, result: Dict[str, Any]):
        """Display analytics and insights"""
        st.markdown("#### 📊 Processing Analytics")
        
        # Processing performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**⚡ Performance Metrics:**")
            
            processing_time = result.get('processing_time', 0)
            st.write(f"• **Total Processing Time:** {processing_time:.2f}s")
            
            # Breakdown if available
            if 'processing_breakdown' in result:
                breakdown = result['processing_breakdown']
                for step, time_taken in breakdown.items():
                    st.write(f"• **{step.title()}:** {time_taken:.2f}s")
        
        with col2:
            st.markdown("**📈 Quality Metrics:**")
            
            violations = result.get('violations', [])
            refined_data = result.get('refined_data', {})
            
            quality_score = self.calculate_quality_score(violations, refined_data)
            st.write(f"• **Overall Quality Score:** {quality_score:.1f}/100")
            
            extraction_completeness = self.calculate_extraction_completeness(refined_data)
            st.write(f"• **Data Completeness:** {extraction_completeness:.1f}%")
            
            compliance_score = 100 if not violations else max(0, 100 - len(violations) * 10)
            st.write(f"• **Compliance Score:** {compliance_score:.1f}/100")
    
    def display_technical_tab(self, result: Dict[str, Any]):
        """Display technical processing details"""
        st.markdown("#### 🔧 Technical Processing Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**System Information:**")
            st.write(f"• **Processing Method:** {result.get('method', 'Unknown')}")
            st.write(f"• **Timestamp:** {result.get('timestamp', 'Unknown')}")
            
            if 'processing_options' in result:
                options = result['processing_options']
                st.write("• **Processing Options:**")
                for key, value in options.items():
                    st.write(f"  - {key.replace('_', ' ').title()}: {value}")
        
        with col2:
            st.markdown("**Error Information:**")
            
            if 'error' in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                st.success("✅ No errors detected")
            
            if 'warnings' in result:
                st.warning(f"⚠️ Warnings: {len(result['warnings'])}")
                for warning in result['warnings']:
                    st.write(f"• {warning}")
        
        # Raw result data
        with st.expander("🔍 Raw Result Data", expanded=False):
            # Filter out large binary data
            filtered_result = {k: v for k, v in result.items() 
                             if k not in ['original_image', 'processed_image']}
            st.json(filtered_result)
    
    def display_violation_analysis(self, violations: List[Dict]):
        """Display detailed violation analysis"""
        st.markdown("#### 📊 Violation Analysis")
        
        if not violations:
            return
        
        # Severity distribution
        severity_counts = {}
        rule_counts = {}
        
        for violation in violations:
            severity = violation.get('severity', 'MEDIUM').upper()
            rule_id = violation.get('rule_id', 'UNKNOWN')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Severity pie chart
            if severity_counts:
                severity_df = pd.DataFrame(
                    list(severity_counts.items()),
                    columns=['Severity', 'Count']
                )
                
                fig_severity = px.pie(
                    severity_df,
                    values='Count',
                    names='Severity',
                    title="Violations by Severity",
                    color_discrete_map={
                        'CRITICAL': ERROR_COLOR,
                        'HIGH': WARNING_COLOR,
                        'MEDIUM': '#17a2b8',
                        'LOW': '#6c757d'
                    }
                )
                
                st.plotly_chart(fig_severity, width='stretch')
        
        with col2:
            # Most frequent violations
            if rule_counts:
                rule_df = pd.DataFrame(
                    list(rule_counts.items()),
                    columns=['Rule ID', 'Count']
                ).sort_values('Count', ascending=True)
                
                fig_rules = px.bar(
                    rule_df.tail(5),  # Top 5 most frequent
                    x='Count',
                    y='Rule ID',
                    orientation='h',
                    title="Most Frequent Violations"
                )
                
                st.plotly_chart(fig_rules, width='stretch')
    
    def display_compliance_recommendations(self, violations: List[Dict], compliance_status: str):
        """Display compliance recommendations"""
        st.markdown("#### 💡 Compliance Recommendations")
        
        if not violations:
            st.success("🎉 **Excellent!** This product is fully compliant with Legal Metrology requirements.")
            return
        
        # Critical recommendations
        critical_violations = [v for v in violations if v.get('severity', '').upper() == 'CRITICAL']
        
        if critical_violations:
            st.error("""
            🚨 **Critical Action Required:**
            This product has critical compliance violations that must be resolved before it can be legally sold.
            """)
        
        # General recommendations
        st.markdown("**📋 Action Items:**")
        
        priority_actions = []
        for violation in violations:
            severity = violation.get('severity', 'MEDIUM').upper()
            rule_id = violation.get('rule_id', 'UNKNOWN')
            
            if severity == 'CRITICAL':
                priority_actions.append(f"🔴 **{rule_id}**: Immediate action required")
            elif severity == 'HIGH':
                priority_actions.append(f"🟡 **{rule_id}**: High priority fix needed")
            else:
                priority_actions.append(f"🔵 **{rule_id}**: Recommended improvement")
        
        for action in priority_actions[:5]:  # Show top 5 actions
            st.write(action)
        
        # Legal compliance note
        st.info("""
        📚 **Legal Reference:** These recommendations are based on the Legal Metrology 
        (Packaged Commodities) Rules, 2011. Consult with legal experts for critical compliance issues.
        """)
    
    def calculate_quality_score(self, violations: List[Dict], refined_data: Dict) -> float:
        """Calculate overall quality score"""
        # Base score
        base_score = 100.0
        
        # Deduct points for violations
        for violation in violations:
            severity = violation.get('severity', 'MEDIUM').upper()
            if severity == 'CRITICAL':
                base_score -= 20
            elif severity == 'HIGH':
                base_score -= 10
            elif severity == 'MEDIUM':
                base_score -= 5
            else:  # LOW
                base_score -= 2
        
        # Deduct points for missing data
        from config import EXPECTED_FIELDS
        missing_fields = len([f for f in EXPECTED_FIELDS if not refined_data.get(f)])
        base_score -= missing_fields * 2
        
        return max(0, base_score)
    
    def calculate_extraction_completeness(self, refined_data: Dict) -> float:
        """Calculate data extraction completeness percentage"""
        from config import EXPECTED_FIELDS
        
        if not EXPECTED_FIELDS:
            return 100.0
        
        extracted_count = len([f for f in EXPECTED_FIELDS if refined_data.get(f)])
        return (extracted_count / len(EXPECTED_FIELDS)) * 100


def display_batch_results_summary(results: List[Dict[str, Any]]):
    """Display summary for batch processing results"""
    if not results:
        st.info("No results to display")
        return
    
    st.markdown("### 📊 Batch Processing Summary")
    
    # Overall statistics
    total_files = len(results)
    successful_files = len([r for r in results if 'error' not in r])
    compliant_files = len([r for r in results if r.get('compliance_status') == 'COMPLIANT'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Total Files", total_files)
    
    with col2:
        success_rate = (successful_files / total_files) * 100 if total_files > 0 else 0
        st.metric("✅ Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        compliance_rate = (compliant_files / successful_files) * 100 if successful_files > 0 else 0
        st.metric("⚖️ Compliance Rate", f"{compliance_rate:.1f}%")
    
    with col4:
        avg_time = sum(r.get('processing_time', 0) for r in results) / len(results) if results else 0
        st.metric("⏱️ Avg Time", f"{avg_time:.2f}s")
    
    # Processing time chart
    if len(results) > 1:
        st.markdown("### 📈 Processing Performance")
        
        processing_times = [r.get('processing_time', 0) for r in results]
        filenames = [r.get('filename', f'File {i+1}') for i, r in enumerate(results)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(results))),
            y=processing_times,
            mode='lines+markers',
            name='Processing Time',
            text=filenames,
            hovertemplate='<b>%{text}</b><br>Time: %{y:.2f}s<extra></extra>'
        ))
        
        fig.update_layout(
            title="Processing Time Trend",
            xaxis_title="File Order",
            yaxis_title="Time (seconds)",
            hovermode='closest'
        )
        
        st.plotly_chart(fig, width='stretch')


    def create_results_comparison(results: List[Dict[str, Any]], comparison_field: str = 'compliance_status'):
        """Create a comparison view of multiple results"""
        if len(results) < 2:
            st.info("Need at least 2 results for comparison")
            return

        st.markdown("### 🔍 Results Comparison")

        # Create comparison table
        comparison_data = []
        for i, result in enumerate(results):
            filename = result.get('filename', f'Result {i+1}')
            comparison_data.append({
                'File': filename,
                'Compliance': result.get('compliance_status', 'UNKNOWN'),
                'Violations': len(result.get('violations', [])),
                'Processing Time': f"{result.get('processing_time', 0):.2f}s",
                'Fields Extracted': len([k for k, v in result.get('refined_data', {}).items() if v])
            })

        df = pd.DataFrame(comparison_data)

        # Style the comparison table
        def highlight_compliance(val):
            if val == 'COMPLIANT':
                return f'background-color: {SUCCESS_COLOR}; color: white'
            elif val == 'NON_COMPLIANT':
                return f'background-color: {ERROR_COLOR}; color: white'
            return ''

        styled_df = df.style.applymap(highlight_compliance, subset=['Compliance'])

        st.dataframe(styled_df, width='stretch', hide_index=True, key="results_comparison_table")
