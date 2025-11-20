"""
Dashboard component for Streamlit UI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any


def render_dashboard(stats: Dict[str, Any], docs_data: Dict[str, Any]):
    """Render main dashboard"""
    
    # Header
    st.header("📊 Dashboard Overview")
    
    # Metrics row
    render_metrics_row(stats)
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        render_domain_distribution(stats)
    
    with col2:
        render_status_pie_chart(stats)
    
    st.divider()
    
    # Recent documents
    render_recent_documents(docs_data)


def render_metrics_row(stats: Dict[str, Any]):
    """Render metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📄 Total Documents",
            value=stats.get("total_documents", 0),
            help="Total number of documents processed"
        )
    
    with col2:
        completed = stats.get("completed", 0)
        st.metric(
            label="✅ Completed",
            value=completed,
            delta=None,
            help="Successfully processed documents"
        )
    
    with col3:
        pending = stats.get("pending", 0)
        st.metric(
            label="⏳ Pending",
            value=pending,
            delta=None,
            help="Documents waiting to be processed"
        )
    
    with col4:
        success_rate = stats.get("success_rate", 0)
        st.metric(
            label="📈 Success Rate",
            value=f"{success_rate:.1f}%",
            delta=None,
            help="Percentage of successfully processed documents"
        )


def render_domain_distribution(stats: Dict[str, Any]):
    """Render domain distribution bar chart"""
    st.subheader("📊 Documents by Domain")
    
    domain_data = stats.get("domain_distribution", {})
    
    if not domain_data:
        st.info("No classified documents yet")
        return
    
    # Create DataFrame
    df = pd.DataFrame(
        list(domain_data.items()),
        columns=["Domain", "Count"]
    )
    
    # Sort by count
    df = df.sort_values("Count", ascending=False)
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Domain",
        y="Count",
        title="Document Distribution by Domain",
        color="Count",
        color_continuous_scale="viridis",
        text="Count"
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Domain",
        yaxis_title="Number of Documents",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_status_pie_chart(stats: Dict[str, Any]):
    """Render processing status pie chart"""
    st.subheader("🥧 Processing Status")
    
    # Prepare data
    labels = []
    values = []
    colors = []
    
    if stats.get("completed", 0) > 0:
        labels.append("Completed")
        values.append(stats["completed"])
        colors.append("#28a745")
    
    if stats.get("pending", 0) > 0:
        labels.append("Pending")
        values.append(stats["pending"])
        colors.append("#ffc107")
    
    if stats.get("processing", 0) > 0:
        labels.append("Processing")
        values.append(stats["processing"])
        colors.append("#17a2b8")
    
    if stats.get("failed", 0) > 0:
        labels.append("Failed")
        values.append(stats["failed"])
        colors.append("#dc3545")
    
    if not labels:
        st.info("No documents processed yet")
        return
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=.3,
        textinfo='label+percent+value',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Document Processing Status",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_recent_documents(docs_data: Dict[str, Any]):
    """Render recent documents table"""
    st.subheader("📋 Recent Documents")
    
    if not docs_data or not docs_data.get("documents"):
        st.info("No documents found. Upload and process documents to see them here.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(docs_data["documents"])
    
    # Format columns
    display_columns = ["filename", "status", "domain", "confidence", "created_at"]
    display_df = df[[col for col in display_columns if col in df.columns]].copy()
    
    # Rename columns
    display_df.columns = ["Filename", "Status", "Domain", "Confidence", "Created"]
    
    # Format confidence
    if "Confidence" in display_df.columns:
        display_df["Confidence"] = display_df["Confidence"].apply(
            lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
        )
    
    # Format created date
    if "Created" in display_df.columns:
        display_df["Created"] = pd.to_datetime(display_df["Created"]).dt.strftime("%Y-%m-%d %H:%M")
    
    # Display table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Processing status"
            ),
            "Domain": st.column_config.TextColumn(
                "Domain",
                help="Classified domain"
            ),
            "Confidence": st.column_config.TextColumn(
                "Confidence",
                help="Classification confidence score"
            )
        }
    )


def render_quick_stats(stats: Dict[str, Any]):
    """Render quick statistics in sidebar"""
    st.sidebar.markdown("### 📊 Quick Stats")
    
    total = stats.get("total_documents", 0)
    completed = stats.get("completed", 0)
    
    st.sidebar.metric("Total Docs", total)
    st.sidebar.metric("Completed", completed)
    
    if total > 0:
        success_rate = (completed / total) * 100
        st.sidebar.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Most common domain
    domain_dist = stats.get("domain_distribution", {})
    if domain_dist:
        top_domain = max(domain_dist, key=domain_dist.get)
        st.sidebar.metric("Top Domain", top_domain.capitalize())