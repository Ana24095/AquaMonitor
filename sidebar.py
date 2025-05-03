import streamlit as st
from utils.constants import STATION_INFO, TIMEFRAME_OPTIONS, COLORS
import base64

def render_sidebar():
    """Render the sidebar navigation and controls."""
    
    # Add logo at the top of the sidebar
    try:
        # Display the custom logo image
        st.sidebar.image("new-logo.png", width=150)
        st.sidebar.markdown("<h3 style='text-align: center; color: white; margin-top: 0px;'>Aqua Nova</h3>", unsafe_allow_html=True)
    except Exception as e:
        # Fallback to text if image not available
        st.sidebar.error(f"Error loading logo: {str(e)}")
        st.sidebar.markdown("<h2 style='text-align: center; color: white;'>Aqua Nova</h2>", unsafe_allow_html=True)
    
    # Navigation menu
    nav_options = {
        "dashboard": "📊 Dashboard",
        "water_quality": "💧 Water Quality",
        "alerts": "🚨 Alerts",
        "predictions": "🔮 AI Predictions",
        "reports": "📝 Reports",
        "api_connections": "🔌 API Connections",
        "settings": "⚙️ Settings"
    }
    
    st.sidebar.markdown("---")
    
    # Create navigation buttons
    for nav_key, nav_label in nav_options.items():
        if st.sidebar.button(
            nav_label, 
            key=f"nav_{nav_key}",
            use_container_width=True,
            type="primary" if st.session_state.current_view == nav_key else "secondary"
        ):
            st.session_state.current_view = nav_key
            # Don't use st.rerun() here as we have auto-refresh in the main app
    
    st.sidebar.markdown("---")
    
    # Station selector
    st.sidebar.subheader("Station Filter")
    station_options = ["All Stations"] + [station["name"] for station in STATION_INFO.values()]
    selected_station = st.sidebar.selectbox(
        "Select Station",
        options=station_options,
        index=station_options.index(st.session_state.selected_station)
    )
    if selected_station != st.session_state.selected_station:
        st.session_state.selected_station = selected_station
    
    # Timeframe selector
    st.sidebar.subheader("Time Range")
    timeframe_labels = {
        "5m": "Last 5 minutes",
        "15m": "Last 15 minutes",
        "30m": "Last 30 minutes",
        "1h": "Last hour",
        "1d": "Last 24 hours"
    }
    selected_timeframe = st.sidebar.radio(
        "Select Range",
        options=TIMEFRAME_OPTIONS,
        format_func=lambda x: timeframe_labels[x],
        index=TIMEFRAME_OPTIONS.index(st.session_state.timeframe),
        horizontal=True
    )
    if selected_timeframe != st.session_state.timeframe:
        st.session_state.timeframe = selected_timeframe
    
    # Alert indicators
    st.sidebar.markdown("---")
    st.sidebar.subheader("Alert Status")
    
    # Get counts of alerts from current data
    alert_data = st.session_state.data.iloc[-len(STATION_INFO):]  # Get latest readings for each station
    
    # Count alerts by type
    water_level_alerts = sum(alert_data['water_level_alert'] == 'high')
    ph_alerts = sum(alert_data['ph_alert'] == 'high')
    turbidity_alerts = sum(alert_data['turbidity_alert'] == 'high')
    do_alerts = sum(alert_data['dissolved_oxygen_alert'] == 'high')
    
    total_alerts = water_level_alerts + ph_alerts + turbidity_alerts + do_alerts
    
    # Display alert summary
    if total_alerts == 0:
        st.sidebar.success("All systems normal")
    else:
        st.sidebar.error(f"{total_alerts} active alerts")
        
        # Show alert details
        if water_level_alerts > 0:
            st.sidebar.warning(f"⚠️ Water Level: {water_level_alerts} stations")
        if ph_alerts > 0:
            st.sidebar.warning(f"⚠️ pH Level: {ph_alerts} stations")
        if turbidity_alerts > 0:
            st.sidebar.warning(f"⚠️ Turbidity: {turbidity_alerts} stations")
        if do_alerts > 0:
            st.sidebar.warning(f"⚠️ Dissolved Oxygen: {do_alerts} stations")
            
    # Logout button at the bottom
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.sidebar.info("In a real implementation, this would log you out of the system.")
