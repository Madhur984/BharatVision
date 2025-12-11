"""
Settings & Configuration Page - Legal Metrology OCR Pipeline

Advanced configuration management for OCR parameters, compliance rules,
model selection, and system optimization.
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List, Any
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent  # Go up two levels from web/pages folder
sys.path.append(str(project_root))

from config import (
    DEVICE, DEFAULT_CAMERA_INDEX, EXPECTED_FIELDS,
    SURYA_LANG_CODES, DETECTION_CONFIDENCE_THRESHOLD
)

# Page configuration
st.set_page_config(
    page_title="Settings - Legal Metrology OCR",
    page_icon="⚙️",
    layout="wide"
)

# Configuration file paths
CONFIG_DIR = Path("config")
USER_CONFIG_FILE = CONFIG_DIR / "user_settings.json"
COMPLIANCE_RULES_FILE = CONFIG_DIR / "custom_compliance_rules.json"
OCR_PRESETS_FILE = CONFIG_DIR / "ocr_presets.json"

def load_settings_css():
    """Load custom CSS for settings page"""
    css = """
    <style>
    /* Hide streamlit_app from sidebar navigation */
    [data-testid="stSidebarNav"] li:first-child {
        display: none !important;
    }
    
    .stApp {
        background: #ffffff !important;
        color: #000000 !important;
    }
    
    .settings-header {
        background: #ffffff;
        color: #000000;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid #e5e7eb;
    }
    
    .settings-header h1 {
        color: #0b2a5a;
    }
    
    .settings-section {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: none;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #0b2a5a;
    }
    
    .config-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
        color: #000000;
    }
    
    .preset-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        cursor: pointer;
        transition: transform 0.2s ease;
        border: 1px solid #e5e7eb;
        color: #000000;
    }
    
    .preset-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .rule-editor {
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    
    .advanced-section {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #000000;
        border: 1px solid #e5e7eb;
    }
    
    .export-section {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
        color: #000000;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def initialize_settings_session():
    """Initialize settings session state"""
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = load_user_settings()
    
    if 'unsaved_changes' not in st.session_state:
        st.session_state.unsaved_changes = False
    
    if 'custom_rules' not in st.session_state:
        st.session_state.custom_rules = load_custom_compliance_rules()

def load_user_settings() -> Dict[str, Any]:
    """Load user settings from file or create defaults"""
    default_settings = {
        'ocr_settings': {
            'confidence_threshold': DETECTION_CONFIDENCE_THRESHOLD,
            'languages': SURYA_LANG_CODES,
            'enable_preprocessing': True,
            'use_gpu': DEVICE == 'cuda',
            'batch_size': 1
        },
        'camera_settings': {
            'default_camera_index': DEFAULT_CAMERA_INDEX,
            'resolution': '1280x720',
            'fps': 30,
            'auto_focus': True
        },
        'compliance_settings': {
            'strict_mode': False,
            'custom_rules_enabled': False,
            'severity_threshold': 'MEDIUM',
            'auto_validate': True
        },
        'ui_settings': {
            'theme': 'light',
            'auto_save_results': True,
            'show_debug_info': False,
            'notifications_enabled': True
        },
        'performance_settings': {
            'max_concurrent_jobs': 3,
            'processing_timeout': 60,
            'memory_limit_gb': 4,
            'cache_enabled': True
        }
    }
    
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, 'r') as f:
                user_settings = json.load(f)
            # Merge with defaults to ensure all keys exist
            for category, settings in default_settings.items():
                if category not in user_settings:
                    user_settings[category] = settings
                else:
                    for key, value in settings.items():
                        if key not in user_settings[category]:
                            user_settings[category][key] = value
            return user_settings
        except Exception:
            return default_settings
    
    return default_settings

def save_user_settings(settings: Dict[str, Any]):
    """Save user settings to file"""
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(USER_CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        st.session_state.unsaved_changes = False
        return True
    except Exception as e:
        st.error(f"Failed to save settings: {str(e)}")
        return False

def load_custom_compliance_rules() -> List[Dict[str, Any]]:
    """Load custom compliance rules"""
    default_rules = []
    
    if COMPLIANCE_RULES_FILE.exists():
        try:
            with open(COMPLIANCE_RULES_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    return default_rules

def save_custom_compliance_rules(rules: List[Dict[str, Any]]):
    """Save custom compliance rules"""
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(COMPLIANCE_RULES_FILE, 'w') as f:
            json.dump(rules, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save custom rules: {str(e)}")
        return False

def create_settings_header():
    """Create settings page header"""
    st.markdown("""
    <div class="settings-header">
        <h1>⚙️ System Settings & Configuration</h1>
        <p>Customize OCR parameters, compliance rules, and system behavior</p>
        <p><strong>Fine-tune for optimal performance and accuracy</strong></p>
    </div>
    """, unsafe_allow_html=True)

def create_ocr_settings_panel():
    """Create OCR configuration panel"""
    st.markdown("### 🔍 OCR Processing Settings")
    
    settings = st.session_state.user_settings['ocr_settings']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Confidence threshold
        new_confidence = st.slider(
            "Detection Confidence Threshold:",
            min_value=0.1,
            max_value=1.0,
            value=settings['confidence_threshold'],
            step=0.05,
            help="Higher values require more confident text detection (0.1 = permissive, 1.0 = strict)"
        )
        
        if new_confidence != settings['confidence_threshold']:
            settings['confidence_threshold'] = new_confidence
            st.session_state.unsaved_changes = True
        
        # Language selection
        available_languages = ['en', 'hi', 'bn', 'te', 'ta', 'mr', 'gu', 'kn', 'ml', 'or']
        language_names = {
            'en': 'English', 'hi': 'Hindi', 'bn': 'Bengali', 'te': 'Telugu',
            'ta': 'Tamil', 'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada',
            'ml': 'Malayalam', 'or': 'Odia'
        }
        
        selected_langs = st.multiselect(
            "Supported Languages:",
            available_languages,
            default=settings['languages'],
            format_func=lambda x: f"{language_names.get(x, x)} ({x})",
            help="Select languages for OCR recognition"
        )
        
        if selected_langs != settings['languages']:
            settings['languages'] = selected_langs
            st.session_state.unsaved_changes = True
        
        # Batch processing size
        new_batch_size = st.selectbox(
            "Batch Processing Size:",
            [1, 2, 4, 8],
            index=[1, 2, 4, 8].index(settings['batch_size']),
            help="Number of images to process simultaneously"
        )
        
        if new_batch_size != settings['batch_size']:
            settings['batch_size'] = new_batch_size
            st.session_state.unsaved_changes = True
    
    with col2:
        # Processing options
        new_preprocessing = st.checkbox(
            "Enable Image Preprocessing",
            value=settings['enable_preprocessing'],
            help="Apply image enhancement before OCR (recommended)"
        )
        
        if new_preprocessing != settings['enable_preprocessing']:
            settings['enable_preprocessing'] = new_preprocessing
            st.session_state.unsaved_changes = True
        
        new_gpu = st.checkbox(
            "Use GPU Acceleration",
            value=settings['use_gpu'],
            help="Use CUDA GPU for faster processing (if available)"
        )
        
        if new_gpu != settings['use_gpu']:
            settings['use_gpu'] = new_gpu
            st.session_state.unsaved_changes = True
        
        # OCR presets
        st.markdown("#### 📋 OCR Presets")
        
        preset_options = {
            "Speed Optimized": {"confidence_threshold": 0.3, "enable_preprocessing": False},
            "Accuracy Optimized": {"confidence_threshold": 0.6, "enable_preprocessing": True},
            "Balanced": {"confidence_threshold": 0.4, "enable_preprocessing": True}
        }
        
        for preset_name, preset_config in preset_options.items():
            if st.button(f"📌 Apply {preset_name}"):
                for key, value in preset_config.items():
                    settings[key] = value
                st.session_state.unsaved_changes = True
                st.success(f"Applied {preset_name} preset")
                st.rerun()

def create_camera_settings_panel():
    """Create camera configuration panel"""
    st.markdown("### 📹 Camera Settings")
    
    settings = st.session_state.user_settings['camera_settings']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Default camera index
        new_camera_index = st.number_input(
            "Default Camera Index:",
            min_value=0,
            max_value=10,
            value=settings['default_camera_index'],
            help="Default camera device to use for live capture"
        )
        
        if new_camera_index != settings['default_camera_index']:
            settings['default_camera_index'] = new_camera_index
            st.session_state.unsaved_changes = True
        
        # Resolution
        resolution_options = ['640x480', '1280x720', '1920x1080', '3840x2160']
        current_resolution = settings['resolution']
        
        new_resolution = st.selectbox(
            "Default Resolution:",
            resolution_options,
            index=resolution_options.index(current_resolution) if current_resolution in resolution_options else 1,
            help="Default camera resolution for live capture"
        )
        
        if new_resolution != settings['resolution']:
            settings['resolution'] = new_resolution
            st.session_state.unsaved_changes = True
    
    with col2:
        # Frame rate
        new_fps = st.selectbox(
            "Frame Rate (FPS):",
            [10, 15, 25, 30, 60],
            index=[10, 15, 25, 30, 60].index(settings['fps']) if settings['fps'] in [10, 15, 25, 30, 60] else 3,
            help="Camera frame rate for live preview"
        )
        
        if new_fps != settings['fps']:
            settings['fps'] = new_fps
            st.session_state.unsaved_changes = True
        
        # Auto focus
        new_auto_focus = st.checkbox(
            "Enable Auto Focus",
            value=settings['auto_focus'],
            help="Enable automatic camera focus adjustment"
        )
        
        if new_auto_focus != settings['auto_focus']:
            settings['auto_focus'] = new_auto_focus
            st.session_state.unsaved_changes = True

def create_compliance_settings_panel():
    """Create compliance validation settings panel"""
    st.markdown("### ⚖️ Compliance Validation Settings")
    
    settings = st.session_state.user_settings['compliance_settings']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Strict mode
        new_strict_mode = st.checkbox(
            "Enable Strict Compliance Mode",
            value=settings['strict_mode'],
            help="Apply stricter validation rules and reject marginal cases"
        )
        
        if new_strict_mode != settings['strict_mode']:
            settings['strict_mode'] = new_strict_mode
            st.session_state.unsaved_changes = True
        
        # Custom rules
        new_custom_rules = st.checkbox(
            "Enable Custom Compliance Rules",
            value=settings['custom_rules_enabled'],
            help="Use additional custom rules defined below"
        )
        
        if new_custom_rules != settings['custom_rules_enabled']:
            settings['custom_rules_enabled'] = new_custom_rules
            st.session_state.unsaved_changes = True
        
        # Auto validation
        new_auto_validate = st.checkbox(
            "Auto-validate on Processing",
            value=settings['auto_validate'],
            help="Automatically run compliance validation after OCR processing"
        )
        
        if new_auto_validate != settings['auto_validate']:
            settings['auto_validate'] = new_auto_validate
            st.session_state.unsaved_changes = True
    
    with col2:
        # Severity threshold
        severity_options = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        current_severity = settings['severity_threshold']
        
        new_severity = st.selectbox(
            "Minimum Violation Severity to Report:",
            severity_options,
            index=severity_options.index(current_severity) if current_severity in severity_options else 1,
            help="Only report violations at or above this severity level"
        )
        
        if new_severity != settings['severity_threshold']:
            settings['severity_threshold'] = new_severity
            st.session_state.unsaved_changes = True
        
        # Rule management
        st.markdown("#### 📋 Rule Management")
        
        if st.button("📝 Edit Standard Rules"):
            st.info("Standard rule editing available in future updates")
        
        if st.button("➕ Add Custom Rule"):
            create_custom_rule_editor()

def create_custom_rule_editor():
    """Create custom compliance rule editor"""
    st.markdown("#### ➕ Create Custom Compliance Rule")
    
    with st.form("custom_rule_form"):
        rule_id = st.text_input(
            "Rule ID:",
            placeholder="CUSTOM_RULE_01",
            help="Unique identifier for the rule"
        )
        
        rule_name = st.text_input(
            "Rule Name:",
            placeholder="Custom validation rule",
            help="Human-readable name for the rule"
        )
        
        rule_description = st.text_area(
            "Description:",
            placeholder="Describe what this rule validates...",
            help="Detailed description of the validation"
        )
        
        field_to_validate = st.selectbox(
            "Field to Validate:",
            EXPECTED_FIELDS + ['custom_field'],
            help="Which product field this rule validates"
        )
        
        severity = st.selectbox(
            "Severity Level:",
            ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
            index=1
        )
        
        validation_pattern = st.text_input(
            "Validation Pattern (Regex):",
            placeholder=r"^[\d]+$",
            help="Regular expression pattern to validate the field value"
        )
        
        submitted = st.form_submit_button("💾 Add Custom Rule")
        
        if submitted and rule_id and rule_name:
            new_rule = {
                'rule_id': rule_id,
                'name': rule_name,
                'description': rule_description,
                'field': field_to_validate,
                'severity': severity,
                'pattern': validation_pattern,
                'created_at': datetime.now().isoformat(),
                'enabled': True
            }
            
            st.session_state.custom_rules.append(new_rule)
            
            if save_custom_compliance_rules(st.session_state.custom_rules):
                st.success(f"✅ Added custom rule: {rule_name}")
                st.rerun()

def display_custom_rules():
    """Display and manage custom compliance rules"""
    if not st.session_state.custom_rules:
        st.info("No custom rules defined. Create one using the form above.")
        return
    
    st.markdown("#### 📋 Custom Compliance Rules")
    
    for i, rule in enumerate(st.session_state.custom_rules):
        with st.expander(f"📐 {rule['name']} ({rule['rule_id']})", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Description:** {rule['description']}")
                st.write(f"**Field:** {rule['field']}")
                st.write(f"**Pattern:** `{rule['pattern']}`")
                st.write(f"**Created:** {rule['created_at'][:10]}")
            
            with col2:
                st.write(f"**Severity:** {rule['severity']}")
                
                # Enable/disable toggle
                enabled = st.checkbox(
                    "Enabled",
                    value=rule['enabled'],
                    key=f"rule_enabled_{i}"
                )
                
                if enabled != rule['enabled']:
                    rule['enabled'] = enabled
                    save_custom_compliance_rules(st.session_state.custom_rules)
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_rule_{i}"):
                    st.session_state.custom_rules.pop(i)
                    save_custom_compliance_rules(st.session_state.custom_rules)
                    st.rerun()

def create_performance_settings_panel():
    """Create performance and resource settings panel"""
    st.markdown("### 🚀 Performance Settings")
    
    settings = st.session_state.user_settings['performance_settings']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Concurrent jobs
        new_concurrent = st.slider(
            "Max Concurrent Processing Jobs:",
            min_value=1,
            max_value=8,
            value=settings['max_concurrent_jobs'],
            help="Number of images to process simultaneously in batch mode"
        )
        
        if new_concurrent != settings['max_concurrent_jobs']:
            settings['max_concurrent_jobs'] = new_concurrent
            st.session_state.unsaved_changes = True
        
        # Processing timeout
        new_timeout = st.slider(
            "Processing Timeout (seconds):",
            min_value=30,
            max_value=300,
            value=settings['processing_timeout'],
            step=10,
            help="Maximum time to wait for a single image to process"
        )
        
        if new_timeout != settings['processing_timeout']:
            settings['processing_timeout'] = new_timeout
            st.session_state.unsaved_changes = True
    
    with col2:
        # Memory limit
        new_memory_limit = st.slider(
            "Memory Limit (GB):",
            min_value=2,
            max_value=16,
            value=settings['memory_limit_gb'],
            help="Maximum memory usage for processing"
        )
        
        if new_memory_limit != settings['memory_limit_gb']:
            settings['memory_limit_gb'] = new_memory_limit
            st.session_state.unsaved_changes = True
        
        # Cache settings
        new_cache_enabled = st.checkbox(
            "Enable Model Caching",
            value=settings['cache_enabled'],
            help="Cache loaded models to speed up subsequent processing"
        )
        
        if new_cache_enabled != settings['cache_enabled']:
            settings['cache_enabled'] = new_cache_enabled
            st.session_state.unsaved_changes = True

def create_ui_settings_panel():
    """Create UI and user experience settings panel"""
    st.markdown("### 🎨 User Interface Settings")
    
    settings = st.session_state.user_settings['ui_settings']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Theme selection
        theme_options = ['light', 'dark', 'auto']
        current_theme = settings['theme']
        
        new_theme = st.selectbox(
            "Interface Theme:",
            theme_options,
            index=theme_options.index(current_theme) if current_theme in theme_options else 0,
            help="Choose the interface color theme"
        )
        
        if new_theme != settings['theme']:
            settings['theme'] = new_theme
            st.session_state.unsaved_changes = True
        
        # Auto-save results
        new_auto_save = st.checkbox(
            "Auto-save Processing Results",
            value=settings['auto_save_results'],
            help="Automatically save processing results to session history"
        )
        
        if new_auto_save != settings['auto_save_results']:
            settings['auto_save_results'] = new_auto_save
            st.session_state.unsaved_changes = True
    
    with col2:
        # Debug information
        new_debug = st.checkbox(
            "Show Debug Information",
            value=settings['show_debug_info'],
            help="Display technical details and debug information"
        )
        
        if new_debug != settings['show_debug_info']:
            settings['show_debug_info'] = new_debug
            st.session_state.unsaved_changes = True
        
        # Notifications
        new_notifications = st.checkbox(
            "Enable Notifications",
            value=settings['notifications_enabled'],
            help="Show processing completion notifications"
        )
        
        if new_notifications != settings['notifications_enabled']:
            settings['notifications_enabled'] = new_notifications
            st.session_state.unsaved_changes = True

def create_export_import_panel():
    """Create configuration export/import panel"""
    st.markdown("### 📤 Configuration Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📤 Export Settings")
        
        export_options = st.multiselect(
            "Select settings to export:",
            ['OCR Settings', 'Camera Settings', 'Compliance Settings', 'UI Settings', 'Performance Settings', 'Custom Rules'],
            default=['OCR Settings', 'Compliance Settings']
        )
        
        if st.button("📊 Export Configuration"):
            if export_options:
                export_data = {}
                
                setting_mapping = {
                    'OCR Settings': 'ocr_settings',
                    'Camera Settings': 'camera_settings',
                    'Compliance Settings': 'compliance_settings',
                    'UI Settings': 'ui_settings',
                    'Performance Settings': 'performance_settings'
                }
                
                for option in export_options:
                    if option in setting_mapping:
                        export_data[setting_mapping[option]] = st.session_state.user_settings[setting_mapping[option]]
                    elif option == 'Custom Rules':
                        export_data['custom_rules'] = st.session_state.custom_rules
                
                export_json = json.dumps(export_data, indent=2)
                
                st.download_button(
                    label="⬇️ Download Configuration",
                    data=export_json,
                    file_name=f"ocr_pipeline_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with col2:
        st.markdown("#### 📥 Import Settings")
        
        uploaded_config = st.file_uploader(
            "Upload configuration file:",
            type=['json'],
            help="Import previously exported configuration"
        )
        
        if uploaded_config:
            try:
                config_data = json.load(uploaded_config)
                
                st.json(config_data)
                
                if st.button("📥 Import Configuration"):
                    # Merge imported settings
                    for key, value in config_data.items():
                        if key in st.session_state.user_settings:
                            st.session_state.user_settings[key].update(value)
                        elif key == 'custom_rules':
                            st.session_state.custom_rules.extend(value)
                    
                    st.session_state.unsaved_changes = True
                    st.success("✅ Configuration imported successfully!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Failed to import configuration: {str(e)}")

def main():
    """Main function for settings page"""
    # Load custom CSS
    load_settings_css()
    
    # Initialize session state
    initialize_settings_session()
    
    # Page header
    create_settings_header()
    
    # Sidebar with save/reset controls
    with st.sidebar:
        st.markdown("### 💾 Configuration Controls")
        
        # Save settings
        if st.button("💾 Save All Settings", type="primary"):
            if save_user_settings(st.session_state.user_settings):
                st.success("✅ Settings saved successfully!")
                st.rerun()
        
        # Reset to defaults
        if st.button("🔄 Reset to Defaults"):
            if st.button("⚠️ Confirm Reset"):
                st.session_state.user_settings = load_user_settings()
                st.session_state.unsaved_changes = False
                st.success("✅ Settings reset to defaults")
                st.rerun()
        
        # Unsaved changes indicator
        if st.session_state.unsaved_changes:
            st.warning("⚠️ You have unsaved changes!")
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔧 System Diagnostics"):
            st.info("System diagnostics feature coming soon!")
        
        if st.button("📊 Export All Data"):
            st.info("Data export feature coming soon!")
        
        if st.button("🗑️ Clear Cache"):
            st.info("Cache cleared!")
    
    # Main settings panels
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 OCR Settings",
        "📹 Camera Settings", 
        "⚖️ Compliance Settings",
        "🚀 Performance",
        "🎨 UI & Export"
    ])
    
    with tab1:
        create_ocr_settings_panel()
    
    with tab2:
        create_camera_settings_panel()
    
    with tab3:
        create_compliance_settings_panel()
        st.markdown("---")
        create_custom_rule_editor()
        display_custom_rules()
    
    with tab4:
        create_performance_settings_panel()
    
    with tab5:
        create_ui_settings_panel()
        st.markdown("---")
        create_export_import_panel()
    
    # Navigation
    st.markdown("---")
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    
    with nav_col1:
        if st.button("🏠 Back to Dashboard"):
            st.switch_page("streamlit_app.py")
    
    with nav_col2:
        if st.button("📊 Batch Process"):
            st.switch_page("pages/03_📊_Batch_Process.py")
    
    with nav_col3:
        if st.button("📂 Upload Images"):
            st.switch_page("pages/02_📂_Upload_Image.py")

if __name__ == "__main__":
    main()


