"""
Streamlit UI for Document Classification System
"""

import streamlit as st
import requests
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Document Classification System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def get_statistics():
    """Fetch statistics from API"""
    try:
        response = requests.get(f"{API_URL}/api/statistics")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching statistics: {e}")
        return None


def get_documents(limit=50):
    """Fetch documents list"""
    try:
        response = requests.get(f"{API_URL}/api/documents", params={"limit": limit})
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return None


def process_document_sync(file_path):
    """Process document synchronously"""
    try:
        response = requests.post(
            f"{API_URL}/api/process-sync",
            json={"file_path": file_path}
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def upload_file(uploaded_file):
    """Upload file to server"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        response = requests.post(f"{API_URL}/api/upload", files=files)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=DocClassifier", width=150)
    st.title("🤖 Multi-Agent System")
    
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📤 Upload & Process", "📊 Analytics", "⚙️ System Status"]
    )
    
    st.divider()
    
    st.markdown("### About")
    st.info("""
    **Multi-Agent Document Classifier**
    
    Powered by:
    - 🚀 Groq Ultra-Fast Inference
    - 🔗 Model Context Protocol (MCP)
    - 🧠 LangChain & LangGraph
    - 👁️ Multi-Modal AI (Text + Vision)
    
    5 Specialized Agents:
    1. Document Intake
    2. Vision Analysis
    3. Text Classification
    4. Domain Router
    5. File Organization
    """)


# Main Content
st.markdown('<h1 class="main-header">📄 Intelligent Document Classification System</h1>', unsafe_allow_html=True)

if page == "🏠 Dashboard":
    st.header("Dashboard Overview")
    
    # Fetch statistics
    stats = get_statistics()
    
    if stats:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📄 Total Documents",
                value=stats.get("total_documents", 0),
                delta=None
            )
        
        with col2:
            st.metric(
                label="✅ Completed",
                value=stats.get("completed", 0),
                delta=None
            )
        
        with col3:
            st.metric(
                label="⏳ Pending",
                value=stats.get("pending", 0),
                delta=None
            )
        
        with col4:
            st.metric(
                label="❌ Failed",
                value=stats.get("failed", 0),
                delta=None
            )
        
        st.divider()
        
        # Domain distribution
        if stats.get("domain_distribution"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 Domain Distribution")
                
                domain_data = stats["domain_distribution"]
                df_domains = pd.DataFrame(list(domain_data.items()), columns=["Domain", "Count"])
                
                fig = px.bar(
                    df_domains,
                    x="Domain",
                    y="Count",
                    title="Documents by Domain",
                    color="Count",
                    color_continuous_scale="viridis"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🥧 Distribution Pie")
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(domain_data.keys()),
                    values=list(domain_data.values()),
                    hole=.3
                )])
                fig_pie.update_layout(title="Domain Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Recent documents
    st.subheader("📋 Recent Documents")
    docs_data = get_documents(limit=10)
    
    if docs_data and docs_data.get("documents"):
        df = pd.DataFrame(docs_data["documents"])
        
        # Format dataframe
        display_df = df[[col for col in ["filename", "status", "domain", "confidence", "created_at"] if col in df.columns]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No documents found. Upload and process documents to see them here.")


elif page == "📤 Upload & Process":
    st.header("Upload & Process Documents")
    
    tab1, tab2 = st.tabs(["📄 Single Document", "📁 Batch Processing"])
    
    with tab1:
        st.subheader("Process Single Document")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a PDF document for classification"
        )
        
        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.button("🚀 Process Document", type="primary"):
                    with st.spinner("Processing document..."):
                        # Upload file
                        upload_result = upload_file(uploaded_file)
                        
                        if upload_result.get("success"):
                            file_path = os.path.join(
                                os.getenv("INPUT_FOLDER", "./input_pdfs"),
                                uploaded_file.name
                            )
                            
                            # Process document
                            result = process_document_sync(file_path)
                            
                            if result.get("success"):
                                st.markdown(f"""
                                <div class="success-message">
                                    <h4>✅ Processing Complete!</h4>
                                    <p><strong>Domain:</strong> {result.get('domain', 'Unknown')}</p>
                                    <p><strong>Confidence:</strong> {result.get('confidence', 0):.2%}</p>
                                    <p><strong>Output:</strong> {result.get('output_path', 'File Saved Successfully')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error(f"Processing failed: {result.get('error')}")
                        else:
                            st.error(f"Upload failed: {upload_result.get('error')}")
    
    with tab2:
        st.subheader("Batch Processing")
        
        folder_path = st.text_input(
            "Folder Path",
            value=os.getenv("INPUT_FOLDER", "./input_pdfs"),
            help="Path to folder containing PDF files"
        )
        
        batch_name = st.text_input(
            "Batch Name (optional)",
            placeholder="e.g., Q4_Reports_2024"
        )
        
        if st.button("🚀 Process Batch", type="primary"):
            with st.spinner("Queuing batch for processing..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/batch-process",
                        json={
                            "folder_path": folder_path,
                            "batch_name": batch_name
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Batch queued: {result.get('total_documents')} documents")
                        st.info(f"Task ID: {result.get('task_id')}")
                    else:
                        st.error(f"Batch processing failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


elif page == "📊 Analytics":
    st.header("Analytics & Insights")
    
    stats = get_statistics()
    docs_data = get_documents(limit=100)
    
    if stats and docs_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Processing Success Rate")
            
            total = stats.get("total_documents", 1)
            completed = stats.get("completed", 0)
            success_rate = (completed / total * 100) if total > 0 else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=success_rate,
                title={'text': "Success Rate (%)"},
                delta={'reference': 90},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "gray"},
                        {'range': [75, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Confidence Distribution")
            
            if docs_data.get("documents"):
                df = pd.DataFrame(docs_data["documents"])
                
                if "confidence" in df.columns and not df["confidence"].isna().all():
                    fig = px.histogram(
                        df[df["confidence"].notna()],
                        x="confidence",
                        nbins=20,
                        title="Confidence Score Distribution",
                        labels={"confidence": "Confidence Score"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No confidence data available yet")
    
    st.divider()
    
    # Document timeline
    st.subheader("📅 Processing Timeline")
    
    if docs_data and docs_data.get("documents"):
        df = pd.DataFrame(docs_data["documents"])
        
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
            df["date"] = df["created_at"].dt.date
            
            timeline = df.groupby("date").size().reset_index(name="count")
            
            fig = px.line(
                timeline,
                x="date",
                y="count",
                title="Documents Processed Over Time",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)


elif page == "⚙️ System Status":
    st.header("System Status & Configuration")
    
    # Health check
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success("✅ API Server: Online")
        else:
            st.error("❌ API Server: Offline")
    except:
        st.error("❌ API Server: Cannot connect")
    
    st.divider()
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Configuration")
        st.code(f"""
API URL: {API_URL}
Input Folder: {os.getenv("INPUT_FOLDER", "./input_pdfs")}
Output Folder: {os.getenv("OUTPUT_BASE_FOLDER", "./output")}
        """)
    
    with col2:
        st.subheader("🤖 Agent Information")
        st.info("""
        **Active Agents:**
        1. Document Intake Agent
        2. Vision Analysis Agent (Groq Vision)
        3. Text Classification Agent (Groq LLM)
        4. Domain Router Agent
        5. File Organization Agent (MCP)
        """)
    
    st.divider()
    
    # Available domains
    st.subheader("📂 Available Domains")
    domains = [
        "finance", "law", "science", "technology",
        "healthcare", "education", "business",
        "engineering", "arts", "general"
    ]
    
    cols = st.columns(5)
    for i, domain in enumerate(domains):
        with cols[i % 5]:
            st.button(f"📁 {domain.capitalize()}", disabled=True)


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 2rem;'>
    <p>🤖 Multi-Agent Document Classification System</p>
    <p>Powered by Groq | LangChain | LangGraph | MCP | FastAPI | Streamlit</p>
</div>
""", unsafe_allow_html=True)