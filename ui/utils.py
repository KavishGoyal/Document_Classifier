"""
Utility functions for Streamlit UI
"""

import streamlit as st
import requests
from typing import Dict, Any, Optional
import time


def get_api_url() -> str:
    """Get API URL from environment or default"""
    import os
    return os.getenv("API_URL", "http://localhost:8000")


def api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    files: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """
    Make API request with error handling
    
    Args:
        endpoint: API endpoint (e.g., "/api/statistics")
        method: HTTP method (GET, POST, etc.)
        data: JSON data for request body
        files: Files to upload
    
    Returns:
        Response JSON or None if error
    """
    api_url = get_api_url()
    full_url = f"{api_url}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(full_url, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(full_url, files=files, timeout=60)
            else:
                response = requests.post(full_url, json=data, timeout=60)
        elif method == "DELETE":
            response = requests.delete(full_url, timeout=30)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to API server. Please check if services are running.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def show_success_message(message: str, icon: str = "✅"):
    """Show success message with custom styling"""
    st.markdown(f"""
    <div style="padding: 1rem; background-color: #d4edda; 
                border: 1px solid #c3e6cb; border-radius: 0.5rem; 
                color: #155724; margin: 1rem 0;">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)


def show_error_message(message: str, icon: str = "❌"):
    """Show error message with custom styling"""
    st.markdown(f"""
    <div style="padding: 1rem; background-color: #f8d7da; 
                border: 1px solid #f5c6cb; border-radius: 0.5rem; 
                color: #721c24; margin: 1rem 0;">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)


def show_info_message(message: str, icon: str = "ℹ️"):
    """Show info message with custom styling"""
    st.markdown(f"""
    <div style="padding: 1rem; background-color: #d1ecf1; 
                border: 1px solid #bee5eb; border-radius: 0.5rem; 
                color: #0c5460; margin: 1rem 0;">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)


def format_confidence(confidence: float) -> str:
    """Format confidence score as percentage with color"""
    if confidence >= 0.8:
        color = "#28a745"  # Green
    elif confidence >= 0.6:
        color = "#ffc107"  # Yellow
    else:
        color = "#dc3545"  # Red
    
    return f'<span style="color: {color}; font-weight: bold;">{confidence:.2%}</span>'


def format_status(status: str) -> str:
    """Format status with color and icon"""
    status_config = {
        "completed": {"icon": "✅", "color": "#28a745"},
        "processing": {"icon": "⏳", "color": "#17a2b8"},
        "pending": {"icon": "⏸️", "color": "#ffc107"},
        "failed": {"icon": "❌", "color": "#dc3545"}
    }
    
    config = status_config.get(status.lower(), {"icon": "❓", "color": "#6c757d"})
    
    return f'{config["icon"]} <span style="color: {config["color"]};">{status.capitalize()}</span>'


def create_download_button(data: bytes, filename: str, label: str = "Download"):
    """Create download button for file"""
    st.download_button(
        label=label,
        data=data,
        file_name=filename,
        mime="application/pdf"
    )


def show_loading_spinner(message: str = "Loading..."):
    """Show loading spinner with message"""
    return st.spinner(message)


def create_metric_card(title: str, value: Any, delta: Optional[str] = None):
    """Create styled metric card"""
    st.markdown(f"""
    <div style="padding: 1rem; background-color: #f8f9fa; 
                border-radius: 0.5rem; border-left: 4px solid #007bff;">
        <div style="color: #6c757d; font-size: 0.9rem;">{title}</div>
        <div style="font-size: 2rem; font-weight: bold; color: #212529;">{value}</div>
        {f'<div style="color: #28a745; font-size: 0.9rem;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def auto_refresh(interval: int = 30):
    """Auto-refresh page at specified interval"""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh > interval:
        st.session_state.last_refresh = current_time
        st.rerun()


def add_custom_css():
    """Add custom CSS styles"""
    st.markdown("""
    <style>
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Custom styles */
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .stButton>button {
            width: 100%;
        }
        
        /* Metric cards */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
        }
        
        /* Tables */
        .dataframe {
            font-size: 0.9rem;
        }
        
        /* Success messages */
        .success-box {
            padding: 1rem;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 0.5rem;
            color: #155724;
        }
        
        /* Error messages */
        .error-box {
            padding: 1rem;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 0.5rem;
            color: #721c24;
        }
    </style>
    """, unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if API is healthy"""
    try:
        response = requests.get(f"{get_api_url()}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def display_system_status():
    """Display system status in sidebar"""
    st.sidebar.markdown("### 🔧 System Status")
    
    api_healthy = check_api_health()
    
    if api_healthy:
        st.sidebar.success("✅ API Server: Online")
    else:
        st.sidebar.error("❌ API Server: Offline")
    
    # Show API URL
    st.sidebar.text(f"API: {get_api_url()}")


def paginate_data(data: list, page: int, per_page: int = 10):
    """Paginate list data"""
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    total_pages = (len(data) + per_page - 1) // per_page
    
    return data[start_idx:end_idx], total_pages


def create_pagination_controls(current_page: int, total_pages: int, key: str = "pagination"):
    """Create pagination controls"""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ First", key=f"{key}_first", disabled=current_page == 1):
            st.session_state[f"{key}_page"] = 1
    
    with col2:
        if st.button("◀️ Prev", key=f"{key}_prev", disabled=current_page == 1):
            st.session_state[f"{key}_page"] = current_page - 1
    
    with col3:
        st.markdown(f"<center>Page {current_page} of {total_pages}</center>", unsafe_allow_html=True)
    
    with col4:
        if st.button("Next ▶️", key=f"{key}_next", disabled=current_page == total_pages):
            st.session_state[f"{key}_page"] = current_page + 1
    
    with col5:
        if st.button("Last ⏭️", key=f"{key}_last", disabled=current_page == total_pages):
            st.session_state[f"{key}_page"] = total_pages