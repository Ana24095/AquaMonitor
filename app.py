import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd

from components.sidebar import render_sidebar
from components.dashboard import render_dashboard
from components.water_quality import render_water_quality
from components.alerts import render_alerts
from components.predictions import render_predictions
from components.reports import render_reports
from components.api_connections import render_api_connections
from components.settings import render_settings
from components.login import render_login
from utils.data_generator import generate_latest_data, get_station_data_by_timeframe
from utils.api_client import get_realtime_data, integrate_realtime_data_with_historical

# Page configuration
st.set_page_config(
    page_title="Environmental Monitoring Platform",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS 
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 1rem;
    }
    
    /* Cards and sections */
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Streamlit Elements */
    [data-testid="stVerticalBlock"] {
        gap: 1rem;
    }
    
    /* Buttons styling */
    .stButton > button {
        background-color: #00b8a9;
        color: white;
        border: none;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #007f75;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #262730;
    }
    
    h1 {
        font-weight: bold;
        font-size: 1.8rem;
    }
    
    h2 {
        font-size: 1.4rem;
        margin-top: 1.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #00b8a9;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: white;
    }
    
    /* Navbar styling */
    .navbar-container {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Style the notification bell and user avatar buttons */
    .navbar-button > button {
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 !important;
    }
    
    /* Expander for notifications and profile */
    .streamlit-expanderHeader {
        font-weight: bold;
        background-color: #f8f9fa;
    }
    
    /* Search box styling */
    [data-testid="stTextInput"] {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'current_view' not in st.session_state:
    st.session_state.current_view = "dashboard"
if 'selected_station' not in st.session_state:
    st.session_state.selected_station = "All Stations"
if 'timeframe' not in st.session_state:
    st.session_state.timeframe = "5m"  # Default to last 5 minutes
if 'alert_threshold' not in st.session_state:
    st.session_state.alert_threshold = {
        "water_level": 80,  # percentage of max level
        "ph": [6.5, 8.5],   # normal pH range
        "turbidity": 5,     # NTU
        "dissolved_oxygen": 5,  # mg/L
    }
if 'active_parameters' not in st.session_state:
    st.session_state.active_parameters = {
        "water_level": True,
        "ph": True,
        "turbidity": True,
        "dissolved_oxygen": True,
        "soil_moisture": True,
        "rainfall": True,
        "flood_risk": True,
        "drought_risk": True,
        "landslide_risk": True
    }
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = datetime.now()
if 'data' not in st.session_state:
    # Initialize with some data
    st.session_state.data = generate_latest_data()
if 'username' not in st.session_state:
    st.session_state.username = ""

# Check if user is authenticated
if not st.session_state.authenticated:
    render_login()
else:
    # Render sidebar navigation
    render_sidebar()

    # Generate new data periodically (for real-time updates)
    current_time = datetime.now()
    
    # Define force_update flag to force data refresh on full refresh cycles
    force_update = False
    if 'last_full_refresh' in st.session_state:
        # If we're within 5 seconds of a full refresh cycle, force update the data
        if (current_time - st.session_state.last_full_refresh).total_seconds() < 5:
            force_update = True
    
    # Update data if 5 seconds have passed since last update or if force_update is true
    if force_update or (current_time - st.session_state.last_update_time).total_seconds() >= 5:
        # Get data from both the generator and API client
        generated_data = generate_latest_data()
        
        # Option to use API data if it's available and enabled
        if 'use_api_data' not in st.session_state:
            st.session_state.use_api_data = True
        
        if st.session_state.use_api_data:
            try:
                # Try to get data from APIs
                api_data = get_realtime_data(refresh=force_update)  # Force API refresh when doing a full update
                
                if not api_data.empty:
                    # If we have API data, integrate it with generated data
                    st.session_state.data = integrate_realtime_data_with_historical(generated_data, api_data)
                else:
                    # If API data is not available, fall back to generated data
                    st.session_state.data = generated_data
            except Exception as e:
                # Log error and fall back to generated data
                print(f"Error getting API data: {str(e)}")
                st.session_state.data = generated_data
        else:
            # If API data is disabled, just use generated data
            st.session_state.data = generated_data
        
        # If it was a forced update, display a message
        if force_update:
            print("Performing complete data refresh as part of the 10-minute cycle...")
        
        st.session_state.last_update_time = current_time

    # Get filtered data based on timeframe and selected station
    filtered_data = get_station_data_by_timeframe(
        st.session_state.data, 
        st.session_state.timeframe,
        st.session_state.selected_station
    )

    # Add a last updated indicator
    st.sidebar.markdown("---")
    st.sidebar.text(f"Last updated: {st.session_state.last_update_time.strftime('%H:%M:%S')}")

    # Initialize notification and profile states
    if 'show_notifications' not in st.session_state:
        st.session_state.show_notifications = False
    if 'show_profile' not in st.session_state:
        st.session_state.show_profile = False
    if 'notifications' not in st.session_state:
        st.session_state.notifications = [
            {"type": "alert", "message": "High water level detected at Station 3", "time": "10 mins ago"},
            {"type": "warning", "message": "pH out of normal range at Station 2", "time": "25 mins ago"},
            {"type": "info", "message": "System update completed successfully", "time": "1 hour ago"}
        ]
        
    # Create the main layout with interactive top navigation bar
    st.markdown('<div class="navbar-container">', unsafe_allow_html=True)
    top_container = st.container()
    with top_container:
        col1, col2, col3, col4, col5 = st.columns([3, 7, 1, 2, 1])
        
        with col1:
            # Usar el nombre de la empresa junto con el logo en el sidebar
            try:
                # Insertar logo a través del componente de imagen de Streamlit
                st.image("new-logo.png", width=60)
            except Exception as e:
                # Si hay algún error, mostrar solo el texto
                st.markdown("<div style='font-size: 1.2rem; font-weight: bold; padding-top: 0.4rem;'>Environmental Monitoring</div>", unsafe_allow_html=True)
        
        with col2:
            search = st.text_input("Search", placeholder="Search...", label_visibility="collapsed")
        
        with col3:
            # Notification bell with badge
            st.markdown('<div class="navbar-button">', unsafe_allow_html=True)
            if st.button("🔔", help="Notifications"):
                st.session_state.show_notifications = not st.session_state.show_notifications
                st.session_state.show_profile = False
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show notification count badge
            if len(st.session_state.notifications) > 0:
                st.markdown(f"""
                <div style="position: relative; top: -34px; left: 25px; z-index: 1000;">
                    <span style="background-color: #ef476f; color: white; font-size: 0.7rem; border-radius: 50%; width: 18px; height: 18px; display: flex; justify-content: center; align-items: center;">{len(st.session_state.notifications)}</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"<div style='color: #0c6271; font-weight: 500; padding-top: 0.4rem;'>{st.session_state.username}</div>", unsafe_allow_html=True)
        
        with col5:
            # User avatar
            initials = st.session_state.username[0].upper() if st.session_state.username else "U"
            st.markdown('<div class="navbar-button">', unsafe_allow_html=True)
            if st.button(initials, help="User profile"):
                st.session_state.show_profile = not st.session_state.show_profile
                st.session_state.show_notifications = False
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close the navbar-container div
    
    # Notification panel
    if st.session_state.show_notifications:
        with st.expander("Notifications", expanded=True):
            if not st.session_state.notifications:
                st.info("No new notifications")
            else:
                for idx, notification in enumerate(st.session_state.notifications):
                    icon = "🔴" if notification["type"] == "alert" else "🟠" if notification["type"] == "warning" else "🔵"
                    st.markdown(f"""
                    <div style="padding: 0.5rem; margin-bottom: 0.5rem; border-bottom: 1px solid #e9ecef;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>{icon} {notification["message"]}</span>
                            <small style="color: #6c757d;">{notification["time"]}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add a mark as read button for each notification
                    col1, col2 = st.columns([4, 1])
                    with col2:
                        if st.button("Mark as read", key=f"read_{idx}"):
                            st.session_state.notifications.pop(idx)
                            st.rerun()
                
                # Clear all button
                if st.button("Clear all notifications"):
                    st.session_state.notifications = []
                    st.rerun()
    
    # User profile panel
    if st.session_state.show_profile:
        with st.expander("User Profile", expanded=True):
            st.write(f"**Username:** {st.session_state.username}")
            st.write("**Role:** Environmental Monitoring Technician")
            st.write("**Last login:** Today at 09:45 AM")
            
            # Quick settings
            st.subheader("Quick Settings")
            st.checkbox("Dark Mode")
            st.checkbox("Receive email notifications", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Profile"):
                    st.session_state.current_view = "settings"
                    st.rerun()
            with col2:
                if st.button("Log Out"):
                    st.session_state.authenticated = False
                    st.session_state.username = ""
                    st.rerun()

    # Render the selected view
    if st.session_state.current_view == "dashboard":
        render_dashboard(filtered_data)
    elif st.session_state.current_view == "water_quality":
        render_water_quality(filtered_data)
    elif st.session_state.current_view == "alerts":
        render_alerts(filtered_data)
    elif st.session_state.current_view == "predictions":
        render_predictions()
    elif st.session_state.current_view == "reports":
        render_reports()
    elif st.session_state.current_view == "api_connections":
        render_api_connections()
    elif st.session_state.current_view == "settings":
        render_settings()

# Auto-refresh the data every 10 minutes but don't refresh the entire app (invisible to user)
if 'last_full_refresh' not in st.session_state:
    st.session_state.last_full_refresh = datetime.now()

# Check if 10 minutes have passed since the last refresh
current_time = datetime.now()
if (current_time - st.session_state.last_full_refresh).total_seconds() >= 600:  # 600 seconds = 10 minutes
    # Only update the data, not the entire app
    st.session_state.last_full_refresh = current_time
    st.session_state.last_update_time = current_time
    
    # Get data from both the generator and API client for the update
    generated_data = generate_latest_data()
    if st.session_state.use_api_data:
        try:
            api_data = get_realtime_data(refresh=True)
            if not api_data.empty:
                st.session_state.data = integrate_realtime_data_with_historical(generated_data, api_data)
            else:
                st.session_state.data = generated_data
        except Exception as e:
            st.session_state.data = generated_data
    else:
        st.session_state.data = generated_data
