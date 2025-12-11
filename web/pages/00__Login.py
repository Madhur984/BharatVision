"""
Login Page - First Page for Streamlit App
Handles user authentication with database storage
"""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
import sys
import base64
import textwrap

# Add parent directory to path for imports
web_root = Path(__file__).parent.parent
sys.path.insert(0, str(web_root))

# Import database manager with robust handling
try:
    from common import get_database
    db = get_database()
except ImportError:
    # Fallback direct import
    try:
        from database import db
    except (ImportError, KeyError):
        from web.database import db

def get_image_base64(image_path):
    """Convert image to base64 string"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Set page config
st.set_page_config(
    page_title="Login - Legal Metrology OCR Pipeline",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# CSS STYLING (Updated to fix layout issues)
# -----------------------------------------------------------------------------
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- Global & Reset --- */
        * { font-family: 'Inter', sans-serif; }
        
        /* Slightly darkened original gradient hues (keep original colors, increase contrast minimally) */
        .stApp {
            background:
                radial-gradient(800px 400px at 6% 14%, rgba(45,126,246,0.12), transparent 12%),
                radial-gradient(700px 350px at 90% 18%, rgba(255,200,150,0.12), transparent 14%),
                linear-gradient(135deg, #d7e9ff 0%, #eef6ff 46%, #fff2ea 100%);
            color: #000000; /* changed to pitch black as requested */
            background-attachment: fixed;
        }
        
        /* Hide default Streamlit elements except keep header visible and styled */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* Style the top header strip to match the page gradient and show black text */
        header {
            visibility: visible;
            background: linear-gradient(135deg, rgba(215,233,255,0.95), rgba(255,242,234,0.95));
            color: #000000 !important;
            border-bottom: 1px solid rgba(0,0,0,0.03);
            box-shadow: 0 4px 12px rgba(2,6,23,0.04);
        }
        [data-testid="stSidebar"] { display: none; }
        
        /* Remove default padding from top of block container to center things better */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Ensure Streamlit columns don't have conflicting backgrounds */
        [data-testid="column"] {
            background-color: transparent;
        }

        /* --- Custom Classes from Design --- */
        .page-header { text-align: center; margin-bottom: 40px; }
        .page-header h1 { font-size: 28px; font-weight: 700; color: #000000; margin: 0; }

        /* Left Panel Styles */
        .left-panel-container { padding-top: 20px; }
        /* Center left-panel content vertically to align with right login card */
        .left-panel-container { display:flex; flex-direction:column; justify-content:center; min-height:520px; }
        .left-panel-container .floating-pill { margin-top:36px; }
        .left-panel-container .secure-ocr-badge { margin-top:12px; }
        .left-panel-container img { display:block; margin: 14px auto 0 auto; max-width: 92%; }
        
        .floating-pill {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.04);
            backdrop-filter: blur(6px);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 13px;
            color: rgba(230,238,251,0.95);
            display: inline-block;
            margin-bottom: 10px;
            box-shadow: 0 6px 28px rgba(2,6,23,0.45);
        }
        
        .secure-ocr-badge {
            background: linear-gradient(90deg, rgba(99,102,241,0.9), rgba(236,72,153,0.85));
            color: white;
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 500;
            display: inline-block;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(99,102,241,0.18);
        }

        .section-label { font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 15px; }

        .info-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 18px 60px rgba(2,6,23,0.6);
            border: 1px solid rgba(255,255,255,0.04);
            backdrop-filter: blur(6px);
        }

        .card-header { display: flex; gap: 20px; margin-bottom: 20px; }
        
        .flag-icon {
            width: 60px; height: 60px;
            background-color: #f8fafc;
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
        }
        .flag-img { width: 40px; height: 40px; object-fit: contain; }

        .card-title-group h2 { font-size: 20px; font-weight: 700; color: #0f172a; margin: 0 0 4px 0; }
        .card-title-group h3 { font-size: 16px; font-weight: 600; color: #334155; margin: 0 0 8px 0; }
        
        .gradient-line {
            height: 4px; width: 100px;
            background: linear-gradient(90deg, #22c55e, #f97316);
            border-radius: 2px;
        }

        .feature-tags { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tag {
            background-color: #eff6ff; color: #2563eb;
            font-size: 12px; font-weight: 600;
            padding: 6px 12px; border-radius: 6px;
        }

        .card-desc { font-size: 14px; line-height: 1.6; color: #64748b; margin: 0; }
        .footer-note { margin-top: 30px; font-size: 13px; color: #94a3b8; }

        /* --- Right Panel (Form) Styles --- */
        /* TARGETING THE STREAMLIT COLUMN DIRECTLY to apply card styles */
        /* This targets the 3rd column block (col1, spacer, col2) and styles its internal container */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) > [data-testid="stVerticalBlock"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.97), rgba(255,255,255,0.92));
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 18px 60px rgba(2,6,23,0.18);
            gap: 0px; /* Reduce gap between streamlit elements inside the card */
            min-height:520px; /* match left column height to center align */
            border: 1px solid rgba(2,6,23,0.06);
        }
        
        .form-header h2 { font-size: 24px; margin: 0 0 8px 0; color: #1e293b; }
        .form-header p { color: #64748b; font-size: 14px; margin: 0 0 25px 0; }

        /* Custom Label Styling for Streamlit Inputs */
        .custom-label-row { display: flex; justify-content: space-between; margin-bottom: 6px; margin-top: 15px;}
        .custom-label { font-size: 13px; font-weight: 600; color: #475569; }
        .custom-helper { font-size: 12px; color: #64748b; }

        /* Overriding Streamlit Input Widgets */
        /* Very light blue input background and subtle border; text in black */
        div[data-testid="stTextInput"] input {
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid #e6f3ff;
            background-color: #f7fbff; /* very very light blue */
            font-size: 14px;
            color: #000000;
            box-shadow: inset 0 -1px 0 rgba(0,0,0,0.02);
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #dbeeff; /* slightly stronger light blue on focus */
            box-shadow: 0 6px 18px rgba(59,130,246,0.04);
            outline: none;
        }
        
        /* Hide the default Streamlit labels since we are using custom HTML ones */
        div[data-testid="stTextInput"] label { display: none; }

        /* Toggle Button Styling (using Streamlit columns) */
        .stButton button {
            background-color: transparent;
            border: none;
            color: #64748b;
            font-weight: 600;
            width: 100%;
        }
        .stButton button:hover {
            color: #1d4ed8;
            border: none;
            background-color: #f1f5f9;
        }
        
        /* Submit Button Styling */
        /* Solid blue buttons (no gradient) */
        div[data-testid="stFormSubmitButton"] button {
            background: #1d4ed8 !important; /* solid blue */
            color: white !important;
            border: none !important;
            padding: 14px !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            margin-top: 10px;
            box-shadow: 0 8px 28px rgba(29,78,216,0.15) !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background: #1e40af !important;
            transform: translateY(-1px);
            box-shadow: 0 12px 40px rgba(29,78,216,0.18) !important;
        }

        /* Checkbox styling */
        .stCheckbox label span { font-size: 13px; color: #475569; }
        .stCheckbox { padding-top: 5px; }

        /* Footer */
        .copyright { margin-top: 30px; text-align: center; font-size: 12px; color: #94a3b8; }
        .version { margin-top: 5px; text-align: center; font-size: 11px; color: #cbd5e1; }
        
        /* Active Tab indicator simulation */
        .active-tab {
            background-color: #1d4ed8;
            color: white;
            padding: 8px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 2px 5px rgba(29, 78, 216, 0.2);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.login_time = None

if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Demo credentials - use these to populate database if they don't exist
DEMO_USERS = {
    "admin": {
        "password": "admin@123",
        "role": "Administrator",
        "email": "admin@metrology.gov.in"
    },
    "user": {
        "password": "user@123",
        "role": "Inspector",
        "email": "inspector@metrology.gov.in"
    },
    "guest": {
        "password": "guest",
        "role": "Guest",
        "email": "guest@metrology.gov.in"
    }
}

# Initialize demo users in database (only if they don't exist)
@st.cache_resource
def initialize_demo_users():
    """Add demo users to database if they don't exist"""
    for username, user_data in DEMO_USERS.items():
        existing = db.get_user(username)
        if not existing:
            db.register_user(
                username=username,
                email=user_data['email'],
                password=user_data['password'],
                role=user_data['role']
            )
    return True

# Initialize demo users
initialize_demo_users()

def register_new_user(username, email, password, confirm_password):
    """Register a new user in database"""
    
    # Validation
    if not username or not email or not password or not confirm_password:
        return False, " All fields are required"
    
    if len(username) < 3:
        return False, " Username must be at least 3 characters"
    
    if len(password) < 6:
        return False, " Password must be at least 6 characters"
    
    if password != confirm_password:
        return False, " Passwords do not match"
    
    # Check if user exists in database
    existing_user = db.get_user(username)
    if existing_user:
        return False, " Username already exists"
    
    if '@' not in email or '.' not in email:
        return False, " Please enter a valid email address"
    
    # Register user in database
    success, message = db.register_user(username, email, password, role="Inspector")
    
    if success:
        return True, f"Account created successfully! You can now login with username: {username}"
    else:
        return False, message

def display_login_form():
    """Display the login and register forms with split layout"""
    
    # Page Header
    st.markdown('<div class="page-header"><h1>BharatVision</h1></div>', unsafe_allow_html=True)
    
    # Main Layout Columns
    col1, spacer, col2 = st.columns([1.1, 0.2, 1])
    
    # --- LEFT PANEL (Info) ---
    with col1:
        # Replace the info-card with the project's logo image (image-wm (3).png)
                logo_path = Path(__file__).parent.parent / "assets" / "image-wm (3) (1).png"
                if logo_path.exists():
                        img_b64 = get_image_base64(logo_path)
                        st.markdown(textwrap.dedent(f"""
<div class="left-panel-container" style="display:flex; align-items:center; justify-content:center; min-height:520px;">
    <div style="width:100%; text-align:center;">
        <img src="data:image/png;base64,{img_b64}" style="max-width:92%; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,0.06);" />
    </div>
</div>
"""), unsafe_allow_html=True)
                else:
                        # Fallback: empty centered space so layout stays consistent
                        st.markdown(textwrap.dedent('''
<div class="left-panel-container" style="display:flex; align-items:center; justify-content:center; min-height:520px;">
    <div style="width:100%; text-align:center; color:#64748b; font-size:13px;">BharatVision</div>
</div>
'''), unsafe_allow_html=True)

    # --- RIGHT PANEL (Form) ---
    with col2:
        # Toggle between Login/Register
        st.markdown('<div style="display:flex; gap:10px; margin-bottom:24px;">', unsafe_allow_html=True)
        login_tab, register_tab = st.columns([1, 1])
        with login_tab:
            if not st.session_state.show_register:
                st.markdown('<div class="active-tab">Login</div>', unsafe_allow_html=True)
            else:
                if st.button("Login", key="btn_login_switch"):
                    st.session_state.show_register = False
                    st.rerun()
        with register_tab:
            if st.session_state.show_register:
                st.markdown('<div class="active-tab">Register</div>', unsafe_allow_html=True)
            else:
                if st.button("Register", key="btn_register_switch"):
                    st.session_state.show_register = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True) # End Toggle Wrapper

        # FORM LOGIC
        if not st.session_state.show_register:
            # --- LOGIN FORM ---
            with st.form("login_form"):
                # Username
                st.markdown('<div class="custom-label-row"><span class="custom-label">Username</span><span class="custom-helper">Use official user ID</span></div>', unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
                
                # Password
                st.markdown('<div class="custom-label-row"><span class="custom-label">Password</span><span class="custom-helper">Minimum 6 characters</span></div>', unsafe_allow_html=True)
                password = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="collapsed")
                
                # Checkbox & Forgot Password
                c_col1, c_col2 = st.columns([1.5, 1])
                with c_col1:
                    remember = st.checkbox('Remember me on this device', value=False)
                with c_col2:
                    st.markdown('<div style="text-align:right; padding-top:8px;"><a href="#" style="font-size:13px; color:#2563eb; text-decoration:none; font-weight:500;">Forgot password?</a></div>', unsafe_allow_html=True)

                submit = st.form_submit_button('Login')

                if submit:
                    if not username or not password:
                        st.error('Please enter username and password')
                        db.log_login(username, status='failed', device_info='Invalid input')
                    else:
                        user = db.get_user(username)
                        if not user:
                            st.error('Invalid username')
                            db.log_login(username, status='failed', device_info='User not found')
                        elif user['password'] != password:
                            st.error('Invalid password')
                            db.log_login(username, status='failed', device_info='Wrong password')
                        else:
                            st.session_state.authenticated = True
                            st.session_state.user = {
                                'user_id': user['id'],
                                'username': user['username'],
                                'role': user['role'],
                                'email': user['email'],
                                'login_time': datetime.now()
                            }
                            st.session_state.remember_login = remember
                            db.log_login(username, status='success', device_info='Web Browser')
                            st.success('Login successful! Redirecting...')
                            st.rerun()

                # Guest Login Button
                st.markdown('<div style="text-align: center; margin-top: 15px; font-size: 13px; color: #64748b;">Or</div>', unsafe_allow_html=True)
                if st.button("Continue as Guest", use_container_width=True):
                     guest_user = db.get_user("guest")
                     if guest_user:
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'user_id': guest_user['id'],
                            'username': guest_user['username'],
                            'role': guest_user['role'],
                            'email': guest_user['email'],
                            'login_time': datetime.now()
                        }
                        st.session_state.remember_login = False
                        db.log_login("guest", status='success', device_info='Web Browser (Guest)')
                        st.success('Logged in as Guest! Redirecting...')
                        st.rerun()
                     else:
                        st.error("Guest account not configured.")

        else:
            # --- REGISTER FORM ---
            with st.form('register_form'):
                st.markdown('<div class="custom-label-row"><span class="custom-label">Username</span></div>', unsafe_allow_html=True)
                new_username = st.text_input("Username", placeholder='Choose a username', label_visibility="collapsed")

                st.markdown('<div class="custom-label-row"><span class="custom-label">Email</span></div>', unsafe_allow_html=True)
                new_email = st.text_input("Email", placeholder='Enter your email', label_visibility="collapsed")

                st.markdown('<div class="custom-label-row"><span class="custom-label">Password</span></div>', unsafe_allow_html=True)
                new_password = st.text_input("Password", type='password', placeholder='Create a password', label_visibility="collapsed")

                st.markdown('<div class="custom-label-row"><span class="custom-label">Confirm Password</span></div>', unsafe_allow_html=True)
                confirm_password = st.text_input("Confirm", type='password', placeholder='Confirm your password', label_visibility="collapsed")

                st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
                agree_terms = st.checkbox('I agree to the Terms & Conditions', value=False)

                register_submit = st.form_submit_button('Create Account')

                if register_submit:
                    if not agree_terms:
                        st.error('Please agree to Terms & Conditions')
                    else:
                        success, message = register_new_user(new_username, new_email, new_password, confirm_password)
                        if success:
                            st.success(message)
                            st.info('Switching to login tab...')
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(message)

        # Footer inside card
        st.markdown('<div class="copyright">© 2025 BharatVision - All rights reserved</div>', unsafe_allow_html=True)
        st.markdown('<div class="version">v1.0 - Public Preview</div>', unsafe_allow_html=True)
        

# Main page logic
if st.session_state.authenticated:
    # User is logged in - show protected content
    st.switch_page("pages/02__Upload_Image.py")
else:
    # Show login form
    display_login_form()