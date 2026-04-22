import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import time
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.activity_store import (
    fetch_recent_events, get_alerts, get_event_count, init_db,
    get_risk_distribution, get_top_processes, get_process_events
)
from utils import export_suspicious_events_csv, export_alert_summary, get_recent_exports

# Ensure database exists before querying
init_db()

st.set_page_config(page_title="UBNAD Monitor", layout="wide", page_icon="🛡️")

st.title("🛡️ UBNAD Privacy Monitor")
st.caption("Unauthorized Background Network Activity Detector - Windows Edition")

# Sidebar controls
st.sidebar.header("⚙️ Controls & Settings")
refresh_rate = st.sidebar.slider("Auto-Refresh Rate (sec)", 1, 10, 2, step=1)
tab_select = st.sidebar.radio("Select View", ["📊 Dashboard", "🚨 Alerts", "📈 Analysis", "💾 Export"])

st.sidebar.divider()

# Auto-refresh trigger
if "page_load_time" not in st.session_state:
    st.session_state.page_load_time = time.time()

st.sidebar.success(f"📡 Refreshing every {refresh_rate} seconds")
st.sidebar.info("Status: ✅ Live Monitoring Active")

# Fetch data from database
try:
    events = fetch_recent_events(limit=100)
    alerts = get_alerts(limit=20)
    total_count = get_event_count()
    risk_dist = get_risk_distribution()
    top_processes = get_top_processes(limit=10)
    df = pd.DataFrame(events) if events else pd.DataFrame()
except Exception as e:
    st.error(f"Database error: {e}")
    df = pd.DataFrame()
    alerts = []
    total_count = 0
    risk_dist = {}
    top_processes = []

# ===== DASHBOARD TAB =====
if tab_select == "📊 Dashboard":
    
    # Live metrics - Real-time statistics
    st.subheader("📊 Live Statistics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if len(df) > 0:
        # Using new risk level definitions (0-100 scale)
        critical = len(df[df["suspicion_score"] >= 76])
        high = len(df[(df["suspicion_score"] >= 51) & (df["suspicion_score"] < 76)])
        medium = len(df[(df["suspicion_score"] >= 26) & (df["suspicion_score"] < 51)])
        safe = len(df[df["suspicion_score"] < 26])
        unique_processes = df["process_name"].nunique()
        
        col1.metric("📈 Total Events", total_count)
        col2.metric("🟢 Safe", safe)
        col3.metric("🟡 Medium", medium)
        col4.metric("🔴 High", high)
        col5.metric("🔴 Critical", critical)
    else:
        col1.metric("📈 Total Events", 0)
        col2.metric("🟢 Safe", 0)
        col3.metric("🟡 Medium", 0)
        col4.metric("🔴 High", 0)
        col5.metric("🔴 Critical", 0)
    
    st.divider()
    
    # Visualizations
    if len(df) > 0:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("🎯 Risk Distribution")
            if risk_dist:
                fig_risk = px.pie(
                    names=list(risk_dist.keys()),
                    values=list(risk_dist.values()),
                    color_discrete_map={
                        'CRITICAL': '#991b1b',
                        'HIGH': '#ea580c',
                        'MEDIUM': '#ea8317',
                        'SAFE': '#10b981'
                    }
                )
                st.plotly_chart(fig_risk, use_container_width=True)
        
        with col_chart2:
            st.subheader("🔝 Top Processes")
            if top_processes:
                df_top = pd.DataFrame(top_processes)
                fig_proc = px.bar(
                    df_top,
                    x='count',
                    y='process',
                    orientation='h',
                    labels={'count': 'Events', 'process': 'Process'}
                )
                fig_proc.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_proc, use_container_width=True)
        
        st.divider()
    
    # Live network activity table
    st.subheader("📡 Live Network Activity")
    
    if len(df) == 0:
        st.info("⏳ Waiting for network activity...")
    else:
        # Format for display
        df_display = df.copy()
        df_display["suspicion_score"] = df_display["suspicion_score"].round(2)
        
        # Select columns (include reason if available)
        cols_to_show = ["timestamp", "process_name", "dest_ip", "dest_port", 
                       "suspicion_score", "severity"]
        available_cols = [c for c in cols_to_show if c in df_display.columns]
        df_display = df_display[available_cols]
        
        # Color styling based on severity
        def highlight(row):
            try:
                severity = row.get("severity", "SAFE")
                if severity == "CRITICAL":
                    return ["background-color: #991b1b; color: white"] * len(row)
                elif severity == "HIGH":
                    return ["background-color: #ea580c; color: white"] * len(row)
                elif severity == "MEDIUM":
                    return ["background-color: #ea8317; color: white"] * len(row)
                else:
                    return ["background-color: #10b981; color: white"] * len(row)
            except:
                return [""] * len(row)
        
        st.dataframe(df_display.style.apply(highlight, axis=1), use_container_width=True, height=400)

# ===== ALERTS TAB =====
elif tab_select == "🚨 Alerts":
    
    st.subheader("🚨 Alert History")
    
    if len(alerts) == 0:
        st.success("✅ No high-risk behavior detected")
    else:
        alert_count = len(alerts)
        col1, col2 = st.columns([2, 1])
        col1.info(f"Found {alert_count} alerts (HIGH and CRITICAL severity)")
        
        # Display alerts in collapsible sections
        for i, alert in enumerate(alerts[:20], 1):
            risk = alert.get("severity", alert.get("risk_level", "UNKNOWN"))
            score = round(alert.get("suspicion_score", 0), 1)
            process = alert.get("process_name", "Unknown")
            ip = alert.get("dest_ip", "Unknown")
            port = alert.get("dest_port", 0)
            timestamp = alert.get("timestamp", "")
            reason = alert.get("reason", "No details available")
            
            emoji = "🔴" if risk == "CRITICAL" else "🟠"
            
            with st.expander(f"{emoji} {risk} | {process} → {ip}:{port} | {score}/100 | {timestamp}"):
                st.markdown(f"**Process:** {process}")
                st.markdown(f"**Destination:** {ip}:{port}")
                st.markdown(f"**Score:** {score}/100")
                st.markdown(f"**Severity:** {risk}")
                st.markdown(f"**Time:** {timestamp}")
                st.markdown(f"**Reasoning:**")
                st.text(reason if reason else "No explanation available")

# ===== ANALYSIS TAB =====
elif tab_select == "📈 Analysis":
    
    st.subheader("📈 Detailed Analysis")
    
    if len(df) == 0:
        st.info("No events recorded yet")
    else:
        analysis_col1, analysis_col2 = st.columns(2)
        
        with analysis_col1:
            st.subheader("Score Distribution")
            if len(df) > 0:
                fig_score = px.histogram(
                    df,
                    x='suspicion_score',
                    nbins=20,
                    labels={'suspicion_score': 'Suspicion Score'},
                    title='Score Distribution'
                )
                st.plotly_chart(fig_score, use_container_width=True)
        
        with analysis_col2:
            st.subheader("Activity Timeline")
            if len(df) > 0:
                df_timeline = df.copy()
                df_timeline['hour'] = pd.to_datetime(df_timeline['timestamp']).dt.hour
                timeline_agg = df_timeline.groupby('hour').size()
                fig_timeline = px.line(timeline_agg, title='Events per Hour')
                st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.divider()
        
        # Process-specific analysis
        st.subheader("🔧 Process Details")
        if top_processes and len(top_processes) > 0:
            process_names = [p['process'] for p in top_processes[:10]]
            selected_process = st.selectbox("Select Process:", process_names)
            
            if selected_process:
                process_events = get_process_events(selected_process, limit=20)
                if process_events:
                    st.info(f"Found {len(process_events)} events for {selected_process}")
                    df_proc = pd.DataFrame(process_events)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Avg Score", round(df_proc['suspicion_score'].mean(), 1))
                    with col2:
                        st.metric("Max Score", round(df_proc['suspicion_score'].max(), 1))
                    
                    st.dataframe(df_proc[['timestamp', 'dest_ip', 'dest_port', 'suspicion_score', 'severity']], 
                                use_container_width=True)

# ===== EXPORT TAB =====
elif tab_select == "💾 Export":
    
    st.subheader("💾 Export & Reporting")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.markdown("### 📋 Export Options")
        
        if st.button("📥 Export All Events (CSV)", use_container_width=True):
            with st.spinner("Exporting..."):
                csv_path = export_suspicious_events_csv(limit=1000)
                if csv_path:
                    st.success(f"✅ Exported to: {csv_path}")
                    st.info(f"File: {os.path.basename(csv_path)}")
        
        if st.button("🚨 Export Alerts Only (CSV)", use_container_width=True):
            with st.spinner("Exporting..."):
                csv_path = export_suspicious_events_csv(severity_filter='CRITICAL', limit=1000)
                if csv_path:
                    st.success(f"✅ Exported CRITICAL events to: {csv_path}")
        
        if st.button("📊 Export Alert Summary", use_container_width=True):
            with st.spinner("Exporting..."):
                csv_path = export_alert_summary()
                if csv_path:
                    st.success(f"✅ Alert summary exported: {csv_path}")
    
    with export_col2:
        st.markdown("### 📂 Recent Exports")
        exports = get_recent_exports(limit=5)
        if exports:
            for exp in exports:
                st.caption(f"📄 {exp['name']} | {exp['size']:,} bytes | {exp['modified']}")
        else:
            st.info("No exports yet")

st.divider()

# Live status footer with timestamp
col_time, col_refresh = st.columns([3, 1])
with col_time:
    st.markdown(f"**🕐 Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Auto-Refresh:** Every {refresh_rate}s")
with col_refresh:
    st.caption("UBNAD v2.0 Windows Edition")

# Auto-refresh mechanism
time.sleep(refresh_rate)
st.rerun()
