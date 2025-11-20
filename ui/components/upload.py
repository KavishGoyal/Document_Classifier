"""
Upload and process component for Streamlit UI
"""

import streamlit as st
import requests
from typing import Dict, Any
import os


def render_upload_section(api_url: str):
    """Render upload and process section"""
    st.header("📤 Upload & Process Documents")
    
    tab1, tab2 = st.tabs(["📄 Single Document", "📁 Batch Processing"])
    
    with tab1:
        render_single_upload(api_url)
    
    with tab2:
        render_batch_upload(api_url)


def render_single_upload(api_url: str):
    """Render single document upload"""
    st.subheader("Process Single Document")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document for automatic classification",
        key="single_file_upload"
    )
    
    if uploaded_file is not None:
        # Show file info
        file_size = len(uploaded_file.getvalue())
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📄 **File:** {uploaded_file.name}")
        with col2:
            st.info(f"📊 **Size:** {format_size(file_size)}")
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            process_btn = st.button(
                "🚀 Process Document",
                type="primary",
                use_container_width=True
            )
        
        if process_btn:
            process_single_document(api_url, uploaded_file)


def process_single_document(api_url: str, uploaded_file):
    """Process a single document"""
    with st.spinner("Processing document..."):
        try:
            # Step 1: Upload file
            st.info("📤 Uploading file...")
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            upload_response = requests.post(f"{api_url}/documents/upload", files=files)
            
            if upload_response.status_code != 200:
                st.error(f"Upload failed: {upload_response.text}")
                return
            
            upload_result = upload_response.json()
            document_id = upload_result.get("document_id")
            
            st.success(f"✅ File uploaded! Document ID: {document_id}")
            
            # Step 2: Process document
            st.info("🤖 Processing with AI agents...")
            process_response = requests.post(
                f"{api_url}/documents/{document_id}/process-sync"
            )
            
            if process_response.status_code != 200:
                st.error(f"Processing failed: {process_response.text}")
                return
            
            result = process_response.json()
            
            # Display results
            if result.get("success"):
                st.balloons()
                st.success("🎉 Processing Complete!")
                
                # Results card
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Classification Results")
                    domain = result.get('domain', 'Unknown')
                    confidence = result.get('confidence', 0)
                    
                    st.metric("Domain", domain.capitalize())
                    st.metric("Confidence", f"{confidence:.2%}")
                
                with col2:
                    st.markdown("### 📁 Output Information")
                    output_path = result.get('output_path', 'N/A')
                    st.text_area("Output Path", output_path, height=100)
                
                # Show detailed results in expander
                with st.expander("🔍 View Detailed Analysis"):
                    st.json(result)
            else:
                st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def render_batch_upload(api_url: str):
    """Render batch processing section"""
    st.subheader("Batch Processing")
    st.info("Process multiple PDF files from a folder at once")
    
    # Input folder path
    folder_path = st.text_input(
        "Folder Path",
        value=os.getenv("INPUT_FOLDER", "./input_pdfs"),
        help="Path to folder containing PDF files",
        key="batch_folder_path"
    )
    
    # Batch name
    batch_name = st.text_input(
        "Batch Name (optional)",
        placeholder="e.g., Q4_Financial_Reports_2024",
        help="Optional name to identify this batch",
        key="batch_name_input"
    )
    
    # File pattern
    file_pattern = st.text_input(
        "File Pattern",
        value="*.pdf",
        help="Pattern to match files (e.g., *.pdf, report_*.pdf)",
        key="file_pattern_input"
    )
    
    # Process button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        process_batch_btn = st.button(
            "🚀 Process Batch",
            type="primary",
            use_container_width=True,
            key="process_batch_btn"
        )
    
    if process_batch_btn:
        process_batch(api_url, folder_path, batch_name, file_pattern)


def process_batch(api_url: str, folder_path: str, batch_name: str, file_pattern: str):
    """Process batch of documents"""
    with st.spinner("Queuing batch for processing..."):
        try:
            payload = {
                "folder_path": folder_path,
                "batch_name": batch_name if batch_name else None,
                "file_patterns": [file_pattern]
            }
            
            response = requests.post(
                f"{api_url}/batch/process",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.success("✅ Batch Queued Successfully!")
                
                # Display batch info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Batch ID", result.get("batch_id"))
                    st.metric("Total Documents", result.get("total_documents"))
                
                with col2:
                    st.metric("Batch Name", result.get("batch_name"))
                    task_id = result.get("task_id", "N/A")
                    st.text(f"Task ID: {task_id}")
                
                st.info("📊 Monitor progress in the Dashboard tab")
                
            else:
                st.error(f"❌ Batch processing failed: {response.text}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def format_size(size_bytes: int) -> str:
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def render_upload_tips():
    """Render tips for uploading"""
    with st.expander("💡 Tips for Best Results"):
        st.markdown("""
        **For better classification accuracy:**
        
        1. **Clear Content**: Ensure PDFs have clear, readable text
        2. **Good Quality**: Higher quality scans work better
        3. **Domain-Specific**: Documents with domain-specific terminology classify better
        4. **File Size**: Keep files under 50MB for optimal processing
        5. **Page Count**: Documents with 1-50 pages process fastest
        
        **Supported Domains:**
        - 📊 Finance - Financial reports, banking, investments
        - ⚖️ Law - Legal documents, contracts
        - 🔬 Science - Research papers, studies
        - 💻 Technology - Technical documentation
        - 🏥 Healthcare - Medical records
        - 🎓 Education - Academic materials
        - 💼 Business - Business plans, reports
        - ⚙️ Engineering - Technical designs
        - 🎨 Arts - Creative works
        - 📄 General - Miscellaneous documents
        """)