"""
Analytics component for Streamlit UI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any


def render_analytics(stats: Dict[str, Any], docs_data: Dict[str, Any]):
    """Render analytics page"""
    st.header("📊 Analytics & Insights")
    
    # Performance metrics
    render_performance_section(stats)
    
    st.divider()
    
    # Confidence analysis
    render_confidence_analysis(docs_data)
    
    st.divider()
    
    # Timeline
    render_timeline(docs_data)


def render_performance_section(stats: Dict[str, Any]):
    """Render performance metrics"""
    st.subheader("⚡ Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_success_rate_gauge(stats)
    
    with col2:
        render_domain_performance(stats)


def render_success_rate_gauge(stats: Dict[str, Any]):
    """Render success rate gauge chart"""
    total = stats.get("total_documents", 1)
    completed = stats.get("completed", 0)
    success_rate = (completed / total * 100) if total > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=success_rate,
        title={'text': "Success Rate (%)"},
        delta={'reference': 90, 'relative': False},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "#ffcccc"},
                {'range': [50, 75], 'color': "#ffffcc"},
                {'range': [75, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_domain_performance(stats: Dict[str, Any]):
    """Render domain performance table"""
    st.markdown("#### 📋 Domain Statistics")
    
    domain_dist = stats.get("domain_distribution", {})
    
    if not domain_dist:
        st.info("No domain data available yet")
        return
    
    # Create performance DataFrame
    df = pd.DataFrame([
        {
            "Domain": domain,
            "Documents": count,
            "Percentage": f"{(count / sum(domain_dist.values()) * 100):.1f}%"
        }
        for domain, count in sorted(
            domain_dist.items(),
            key=lambda x: x[1],
            reverse=True
        )
    ])
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Domain": st.column_config.TextColumn("Domain", width="medium"),
            "Documents": st.column_config.NumberColumn("Documents", width="small"),
            "Percentage": st.column_config.TextColumn("Share", width="small")
        }
    )


def render_confidence_analysis(docs_data: Dict[str, Any]):
    """Render confidence score analysis"""
    st.subheader("🎯 Confidence Score Analysis")
    
    if not docs_data or not docs_data.get("documents"):
        st.info("No documents available for analysis")
        return
    
    df = pd.DataFrame(docs_data["documents"])
    
    # Filter out documents without confidence scores
    if "confidence" not in df.columns or df["confidence"].isna().all():
        st.info("No confidence data available yet")
        return
    
    df_with_confidence = df[df["confidence"].notna()].copy()
    
    if df_with_confidence.empty:
        st.info("No confidence data available yet")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_confidence_histogram(df_with_confidence)
    
    with col2:
        render_confidence_stats(df_with_confidence)


def render_confidence_histogram(df: pd.DataFrame):
    """Render confidence score histogram"""
    fig = px.histogram(
        df,
        x="confidence",
        nbins=20,
        title="Confidence Score Distribution",
        labels={"confidence": "Confidence Score", "count": "Number of Documents"},
        color_discrete_sequence=["#1f77b4"]
    )
    
    fig.update_traces(marker_line_width=1, marker_line_color="white")
    fig.update_layout(
        xaxis_title="Confidence Score",
        yaxis_title="Number of Documents",
        bargap=0.1,
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_confidence_stats(df: pd.DataFrame):
    """Render confidence statistics"""
    st.markdown("#### 📈 Confidence Statistics")
    
    avg_confidence = df["confidence"].mean()
    min_confidence = df["confidence"].min()
    max_confidence = df["confidence"].max()
    median_confidence = df["confidence"].median()
    
    # Create metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Average", f"{avg_confidence:.2%}")
        st.metric("Minimum", f"{min_confidence:.2%}")
    
    with col2:
        st.metric("Maximum", f"{max_confidence:.2%}")
        st.metric("Median", f"{median_confidence:.2%}")
    
    # Confidence ranges
    st.markdown("##### Distribution by Range")
    
    ranges = {
        "High (80-100%)": ((df["confidence"] >= 0.8) & (df["confidence"] <= 1.0)).sum(),
        "Medium (60-80%)": ((df["confidence"] >= 0.6) & (df["confidence"] < 0.8)).sum(),
        "Low (0-60%)": (df["confidence"] < 0.6).sum()
    }
    
    for range_name, count in ranges.items():
        percentage = (count / len(df) * 100) if len(df) > 0 else 0
        st.text(f"{range_name}: {count} docs ({percentage:.1f}%)")


def render_timeline(docs_data: Dict[str, Any]):
    """Render processing timeline"""
    st.subheader("📅 Processing Timeline")
    
    if not docs_data or not docs_data.get("documents"):
        st.info("No timeline data available")
        return
    
    df = pd.DataFrame(docs_data["documents"])
    
    if "created_at" not in df.columns:
        st.info("No timeline data available")
        return
    
    # Convert to datetime
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    
    # Group by date
    timeline = df.groupby("date").size().reset_index(name="count")
    
    # Create line chart
    fig = px.line(
        timeline,
        x="date",
        y="count",
        title="Documents Processed Over Time",
        labels={"date": "Date", "count": "Number of Documents"},
        markers=True
    )
    
    fig.update_traces(
        line_color="#1f77b4",
        line_width=3,
        marker=dict(size=8, color="#1f77b4")
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Documents Processed",
        hovermode="x unified",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show daily breakdown
    if not timeline.empty:
        with st.expander("📊 View Daily Breakdown"):
            timeline_display = timeline.copy()
            timeline_display["date"] = timeline_display["date"].astype(str)
            timeline_display.columns = ["Date", "Documents"]
            
            st.dataframe(
                timeline_display.sort_values("Date", ascending=False),
                use_container_width=True,
                hide_index=True
            )


def render_domain_confidence_analysis(docs_data: Dict[str, Any]):
    """Render confidence analysis by domain"""
    st.subheader("🎯 Confidence by Domain")
    
    if not docs_data or not docs_data.get("documents"):
        st.info("No data available")
        return
    
    df = pd.DataFrame(docs_data["documents"])
    
    if "domain" not in df.columns or "confidence" not in df.columns:
        st.info("Insufficient data for domain-confidence analysis")
        return
    
    # Filter valid data
    df_valid = df[(df["domain"].notna()) & (df["confidence"].notna())].copy()
    
    if df_valid.empty:
        st.info("No data available for analysis")
        return
    
    # Create box plot
    fig = px.box(
        df_valid,
        x="domain",
        y="confidence",
        title="Confidence Distribution by Domain",
        labels={"domain": "Domain", "confidence": "Confidence Score"},
        color="domain"
    )
    
    fig.update_layout(
        xaxis_title="Domain",
        yaxis_title="Confidence Score",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)