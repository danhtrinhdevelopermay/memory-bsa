import streamlit as st
import time
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import os
from database import DatabaseMonitor
from utils import format_bytes, format_duration, get_status_color
from plotly.subplots import make_subplots
import io
import base64
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="PostgreSQL Performance Monitor",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database monitor
@st.cache_resource
def get_db_monitor():
    # Use the provided Neon database connection string
    db_url = "postgresql://neondb_owner:npg_CeoRpbVaU05q@ep-holy-mud-a5j0jeek.us-east-2.aws.neon.tech/neondb?sslmode=require"
    
    return DatabaseMonitor(db_url)

def create_dashboard_image(db_monitor):
    """Create a comprehensive dashboard image in 9:16 aspect ratio using matplotlib"""
    
    # Get all data
    connection_status = db_monitor.test_connection()
    db_info = db_monitor.get_database_info()
    performance_metrics = db_monitor.get_performance_metrics()
    query_performance = db_monitor.get_query_performance()
    active_connections = db_monitor.get_active_connections()
    table_sizes = db_monitor.get_table_sizes()
    
    # Create figure with 9:16 aspect ratio and modern styling
    plt.style.use('default')
    fig = plt.figure(figsize=(5.4, 9.6), facecolor='#f8f9fa')
    
    # Create a grid layout with more spacing
    gs = fig.add_gridspec(9, 2, height_ratios=[0.6, 1.0, 0.2, 1.0, 0.2, 1.5, 0.2, 1.5, 0.6], 
                         hspace=0.3, wspace=0.4, left=0.12, right=0.88, top=0.93, bottom=0.07)
    
    # Title
    title_ax = fig.add_subplot(gs[0, :])
    title_ax.text(0.5, 0.5, 'PostgreSQL Monitor Report', 
                 ha='center', va='center', fontsize=16, fontweight='bold', color='#2c3e50')
    title_ax.text(0.5, 0.1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 ha='center', va='center', fontsize=10, color='#7f8c8d')
    title_ax.axis('off')
    
    # Connection Status Card
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.set_facecolor('#e8f5e8')
    connection_color = '#27ae60' if connection_status['connected'] else '#e74c3c'
    status_text = 'CONNECTED' if connection_status['connected'] else 'DISCONNECTED'
    
    ax1.text(0.5, 0.75, status_text, ha='center', va='center', 
             fontsize=12, fontweight='bold', color=connection_color)
    
    ping_text = f"{connection_status['ping_ms']:.1f} ms" if connection_status['ping_ms'] else "N/A"
    ax1.text(0.5, 0.45, 'Ping Time', ha='center', va='center', fontsize=10, color='#34495e')
    ax1.text(0.5, 0.25, ping_text, ha='center', va='center', fontsize=14, fontweight='bold', color='#2c3e50')
    
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis('off')
    ax1.set_title('Connection Status', fontsize=11, fontweight='bold', pad=10, color='#2c3e50')
    
    # Database Info Card
    ax2 = fig.add_subplot(gs[1, 1])
    ax2.set_facecolor('#e8f4f8')
    
    if db_info:
        info_items = [
            f"Size: {format_bytes(db_info.get('database_size', 0))}",
            f"Connections: {db_info.get('active_connections', 0)}/{db_info.get('max_connections', 0)}",
            f"Uptime: {format_duration(db_info.get('uptime_seconds', 0))}",
            f"Timezone: {db_info.get('timezone', 'N/A')}"
        ]
        
        for i, item in enumerate(info_items):
            ax2.text(0.1, 0.8 - i*0.2, item, ha='left', va='center', 
                    fontsize=9, color='#2c3e50', fontweight='500')
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')
    ax2.set_title('Database Info', fontsize=11, fontweight='bold', pad=10, color='#2c3e50')
    
    # Performance Metrics Cards
    metrics_data = [
        ('Cache Hit Ratio', f"{performance_metrics.get('cache_hit_ratio', 0):.1f}%", '#27ae60'),
        ('Active Locks', str(performance_metrics.get('locks', 0)), '#e67e22'),
        ('Deadlocks', str(performance_metrics.get('deadlocks', 0)), '#e74c3c'),
        ('Temp Files', str(performance_metrics.get('temp_files', 0)), '#9b59b6')
    ]
    
    for i, (title, value, color) in enumerate(metrics_data):
        row = 3 + i // 2 * 2  # Skip spacer rows
        col = i % 2
        ax = fig.add_subplot(gs[row, col])
        ax.set_facecolor('#ffffff')
        
        # Add subtle border with rounded corners effect
        for spine in ax.spines.values():
            spine.set_color('#ecf0f1')
            spine.set_linewidth(2)
        
        # Add padding around content
        ax.text(0.5, 0.7, value, ha='center', va='center', 
                fontsize=20, fontweight='bold', color=color)
        ax.text(0.5, 0.25, title, ha='center', va='center', 
                fontsize=9, color='#34495e', fontweight='500')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    
    # Query Performance Chart
    ax_query = fig.add_subplot(gs[5, :])
    ax_query.set_facecolor('#ffffff')
    
    if query_performance:
        successful_queries = {k: v for k, v in query_performance.items() if v['success']}
        if successful_queries:
            query_names = [name.replace(' ', '\n') for name in list(successful_queries.keys())[:5]]
            execution_times = [v['execution_time'] * 1000 for v in list(successful_queries.values())[:5]]
            
            bars = ax_query.bar(range(len(query_names)), execution_times, 
                               color='#3498db', alpha=0.8, edgecolor='#2980b9', linewidth=1.5,
                               width=0.6)
            
            # Add value labels on bars with better positioning
            for bar, time in zip(bars, execution_times):
                height = bar.get_height()
                ax_query.text(bar.get_x() + bar.get_width()/2., height + max(execution_times) * 0.02,
                             f'{time:.1f}ms', ha='center', va='bottom', fontsize=8, 
                             color='#2c3e50', fontweight='bold')
            
            ax_query.set_xticks(range(len(query_names)))
            ax_query.set_xticklabels(query_names, fontsize=8, color='#34495e')
            ax_query.set_ylabel('Execution Time (ms)', fontsize=9, color='#34495e')
            ax_query.tick_params(axis='y', labelsize=8, colors='#34495e')
            ax_query.grid(True, alpha=0.3, axis='y')
            ax_query.set_title('Query Performance', fontsize=12, fontweight='bold', pad=15, color='#2c3e50')
            ax_query.set_ylim(0, max(execution_times) * 1.15)
    
    # Table Sizes Chart
    ax_tables = fig.add_subplot(gs[7, :])
    ax_tables.set_facecolor('#ffffff')
    
    if table_sizes:
        top_tables = table_sizes[:5]
        table_names = [t['table_name'] for t in top_tables]
        table_sizes_mb = [t['size_bytes'] / (1024*1024) for t in top_tables]
        
        bars = ax_tables.bar(range(len(table_names)), table_sizes_mb, 
                            color='#e67e22', alpha=0.8, edgecolor='#d35400', linewidth=1.5,
                            width=0.6)
        
        # Add value labels on bars with better positioning
        for bar, size in zip(bars, table_sizes_mb):
            height = bar.get_height()
            if height > 0:
                ax_tables.text(bar.get_x() + bar.get_width()/2., height + max(table_sizes_mb) * 0.02,
                              f'{size:.1f}MB', ha='center', va='bottom', fontsize=8, 
                              color='#2c3e50', fontweight='bold')
        
        ax_tables.set_xticks(range(len(table_names)))
        ax_tables.set_xticklabels(table_names, fontsize=8, color='#34495e', rotation=45, ha='right')
        ax_tables.set_ylabel('Size (MB)', fontsize=9, color='#34495e')
        ax_tables.tick_params(axis='y', labelsize=8, colors='#34495e')
        ax_tables.grid(True, alpha=0.3, axis='y')
        ax_tables.set_title('Largest Tables', fontsize=12, fontweight='bold', pad=15, color='#2c3e50')
        if table_sizes_mb:
            ax_tables.set_ylim(0, max(table_sizes_mb) * 1.15)
    
    # Footer
    footer_ax = fig.add_subplot(gs[8, :])
    footer_ax.text(0.5, 0.5, 'Generated by PostgreSQL Monitor', 
                  ha='center', va='center', fontsize=8, color='#7f8c8d', style='italic')
    footer_ax.axis('off')
    
    # Save to bytes
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', 
                facecolor='#f8f9fa', edgecolor='none')
    buf.seek(0)
    img_bytes = buf.read()
    plt.close()
    
    return img_bytes

def main():
    st.title("🐘 PostgreSQL Performance Monitor")
    st.markdown("Real-time monitoring dashboard for PostgreSQL database performance")
    
    # Initialize database monitor
    db_monitor = get_db_monitor()
    
    # Sidebar controls
    st.sidebar.title("⚙️ Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    refresh_interval = st.sidebar.selectbox(
        "Refresh Interval (milliseconds)",
        [25, 30, 35, 40, 50, 100, 200, 500],
        index=3
    )
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_resource.clear()
        st.rerun()
    
    # Download report button
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Báo cáo")
    
    if st.sidebar.button("📥 Tải xuống báo cáo (9:16)"):
        with st.spinner("Đang tạo báo cáo..."):
            try:
                # Create the dashboard image
                img_bytes = create_dashboard_image(db_monitor)
                
                # Create download button
                st.sidebar.download_button(
                    label="💾 Tải xuống PNG",
                    data=img_bytes,
                    file_name=f"postgresql_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png"
                )
                
                st.sidebar.success("✅ Báo cáo đã được tạo!")
                
            except Exception as e:
                st.sidebar.error(f"❌ Lỗi tạo báo cáo: {str(e)}")
    
    # Preview report
    if st.sidebar.button("👀 Xem trước báo cáo"):
        with st.spinner("Đang tạo xem trước..."):
            try:
                img_bytes = create_dashboard_image(db_monitor)
                st.sidebar.image(img_bytes, use_column_width=True)
            except Exception as e:
                st.sidebar.error(f"❌ Lỗi xem trước: {str(e)}")
    
    # Connection status section
    st.header("📡 Connection Status")
    
    # Test connection
    connection_status = db_monitor.test_connection()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if connection_status['connected']:
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
    
    with col2:
        if connection_status['ping_ms'] is not None:
            st.metric("Ping", f"{connection_status['ping_ms']:.2f} ms")
        else:
            st.metric("Ping", "N/A")
    
    with col3:
        if connection_status['connected']:
            st.info(f"🗄️ Database: {connection_status.get('database_name', 'Unknown')}")
        else:
            st.error("Database: Unavailable")
    
    # Show connection error if exists
    if not connection_status['connected'] and connection_status.get('error'):
        st.error(f"Connection Error: {connection_status['error']}")
        return
    
    # Database information section
    st.header("📊 Database Information")
    
    db_info = db_monitor.get_database_info()
    
    if db_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Server Information")
            st.write(f"**Version:** {db_info.get('version', 'Unknown')}")
            st.write(f"**Server Started:** {db_info.get('server_start_time', 'Unknown')}")
            st.write(f"**Current Time:** {db_info.get('current_time', 'Unknown')}")
            st.write(f"**Timezone:** {db_info.get('timezone', 'Unknown')}")
        
        with col2:
            st.subheader("Database Statistics")
            st.write(f"**Database Size:** {format_bytes(db_info.get('database_size', 0))}")
            st.write(f"**Active Connections:** {db_info.get('active_connections', 0)}")
            st.write(f"**Max Connections:** {db_info.get('max_connections', 0)}")
            st.write(f"**Uptime:** {format_duration(db_info.get('uptime_seconds', 0))}")
    
    # Performance metrics section
    st.header("⚡ Performance Metrics")
    
    performance_metrics = db_monitor.get_performance_metrics()
    
    if performance_metrics:
        # Create metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Cache Hit Ratio",
                f"{performance_metrics.get('cache_hit_ratio', 0):.1f}%",
                delta=None,
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Commits/sec",
                f"{performance_metrics.get('commits_per_sec', 0):.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                "Rollbacks/sec",
                f"{performance_metrics.get('rollbacks_per_sec', 0):.2f}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Blocks Read/sec",
                f"{performance_metrics.get('blocks_read_per_sec', 0):.2f}",
                delta=None
            )
        
        # Additional metrics
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                "Locks",
                f"{performance_metrics.get('locks', 0)}",
                delta=None
            )
        
        with col6:
            st.metric(
                "Deadlocks",
                f"{performance_metrics.get('deadlocks', 0)}",
                delta=None
            )
        
        with col7:
            st.metric(
                "Temp Files",
                f"{performance_metrics.get('temp_files', 0)}",
                delta=None
            )
        
        with col8:
            st.metric(
                "Temp Bytes",
                format_bytes(performance_metrics.get('temp_bytes', 0)),
                delta=None
            )
    
    # Query performance section
    st.header("🔍 Query Performance")
    
    query_performance = db_monitor.get_query_performance()
    
    if query_performance:
        # Test query execution times
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Test Query Results")
            for query_name, result in query_performance.items():
                if result['success']:
                    st.success(f"✅ {query_name}: {result['execution_time']:.3f}s")
                else:
                    st.error(f"❌ {query_name}: {result['error']}")
        
        with col2:
            st.subheader("Query Execution Chart")
            
            # Create execution time chart
            successful_queries = {k: v for k, v in query_performance.items() if v['success']}
            
            if successful_queries:
                query_names = list(successful_queries.keys())
                execution_times = [v['execution_time'] for v in successful_queries.values()]
                
                fig = px.bar(
                    x=query_names,
                    y=execution_times,
                    title="Query Execution Times",
                    labels={'x': 'Query Type', 'y': 'Execution Time (seconds)'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Active connections section
    st.header("👥 Active Connections")
    
    active_connections = db_monitor.get_active_connections()
    
    if active_connections:
        df = pd.DataFrame(active_connections)
        
        if not df.empty:
            # Display connection statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Connections", len(df))
            
            with col2:
                if 'state' in df.columns:
                    active_count = len(df[df['state'] == 'active'])
                    st.metric("Active Queries", active_count)
                else:
                    st.metric("Active Queries", "N/A")
            
            with col3:
                if 'application_name' in df.columns:
                    unique_apps = df['application_name'].nunique()
                    st.metric("Unique Applications", unique_apps)
                else:
                    st.metric("Unique Applications", "N/A")
            
            # Show connections table
            st.subheader("Connection Details")
            
            # Select relevant columns for display
            display_columns = []
            for col in ['pid', 'usename', 'application_name', 'client_addr', 'state', 'query_start', 'query']:
                if col in df.columns:
                    display_columns.append(col)
            
            if display_columns:
                display_df = df[display_columns].copy()
                
                # Truncate long queries for better display
                if 'query' in display_df.columns:
                    display_df['query'] = display_df['query'].str[:100] + '...'
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.write("No connection details available")
        else:
            st.info("No active connections found")
    
    # Tables and indexes section
    st.header("📋 Database Objects")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Largest Tables")
        table_sizes = db_monitor.get_table_sizes()
        
        if table_sizes:
            df_tables = pd.DataFrame(table_sizes)
            if not df_tables.empty:
                # Format size for display
                df_tables['formatted_size'] = df_tables['size_bytes'].apply(format_bytes)
                
                # Display top 10 tables
                st.dataframe(
                    df_tables[['table_name', 'formatted_size']].head(10),
                    use_container_width=True
                )
            else:
                st.info("No table information available")
        else:
            st.info("Unable to retrieve table sizes")
    
    with col2:
        st.subheader("Index Usage")
        index_usage = db_monitor.get_index_usage()
        
        if index_usage:
            df_indexes = pd.DataFrame(index_usage)
            if not df_indexes.empty:
                # Display index usage statistics
                st.dataframe(
                    df_indexes[['table_name', 'index_name', 'index_scans', 'index_size']].head(10),
                    use_container_width=True
                )
            else:
                st.info("No index information available")
        else:
            st.info("Unable to retrieve index usage")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval / 1000)  # Convert milliseconds to seconds
        st.rerun()

if __name__ == "__main__":
    main()
