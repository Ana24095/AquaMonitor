import streamlit as st
from utils.constants import PARAMETER_DESCRIPTIONS, STATION_INFO, COLORS, TIMEFRAME_OPTIONS
from utils.api_client import api_client

def render_settings():
    """Render the settings page for configuring the dashboard."""
    st.header("Dashboard Settings")
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["Parameters", "Alert Thresholds", "Station Management", "Data Sources"])
    
    with tab1:
        st.subheader("Parameter Settings")
        st.write("Enable or disable display of specific monitoring parameters.")
        
        # Parameter toggles
        for param, param_info in PARAMETER_DESCRIPTIONS.items():
            # Asegurarse de que help sea una cadena de texto (string)
            help_text = str(param_info["description"]) if isinstance(param_info, dict) and "description" in param_info else ""
            enabled = st.checkbox(
                param.replace('_', ' ').title(),
                value=st.session_state.active_parameters.get(param, True),
                help=help_text,
                key=f"param_{param}"
            )
            st.session_state.active_parameters[param] = enabled
        
        # Save button
        if st.button("Save Parameter Settings"):
            st.success("Parameter settings saved successfully!")
    
    with tab2:
        st.subheader("Alert Thresholds")
        st.write("Configure threshold values for alert triggers.")
        
        # Water level threshold
        st.slider(
            "Water Level Alert Threshold (%)",
            min_value=50,
            max_value=95,
            value=int(st.session_state.alert_threshold["water_level"]),  # Asegurar que sea int
            step=5,
            help="Alert will trigger when water level exceeds this percentage",
            key="threshold_water_level"
        )
        
        # pH thresholds
        st.write("pH Level Alert Thresholds")
        col1, col2 = st.columns(2)
        with col1:
            ph_min = st.number_input(
                "Minimum pH",
                min_value=0.0,
                max_value=14.0,
                value=st.session_state.alert_threshold["ph"][0],
                step=0.1,
                help="Alert will trigger when pH falls below this value",
                key="threshold_ph_min"
            )
        with col2:
            ph_max = st.number_input(
                "Maximum pH",
                min_value=0.0,
                max_value=14.0,
                value=st.session_state.alert_threshold["ph"][1],
                step=0.1,
                help="Alert will trigger when pH exceeds this value",
                key="threshold_ph_max"
            )
        
        # Turbidity threshold
        st.slider(
            "Turbidity Alert Threshold (NTU)",
            min_value=1.0,
            max_value=10.0,
            value=float(st.session_state.alert_threshold["turbidity"]),  # Asegurar que sea float
            step=0.5,
            help="Alert will trigger when turbidity exceeds this value",
            key="threshold_turbidity"
        )
        
        # Dissolved oxygen threshold
        st.slider(
            "Minimum Dissolved Oxygen (mg/L)",
            min_value=1.0,
            max_value=8.0,
            value=float(st.session_state.alert_threshold["dissolved_oxygen"]),  # Asegurar que sea float
            step=0.5,
            help="Alert will trigger when dissolved oxygen falls below this value",
            key="threshold_do"
        )
        
        # Update thresholds
        if st.button("Update Alert Thresholds"):
            st.session_state.alert_threshold = {
                "water_level": st.session_state.threshold_water_level,
                "ph": [st.session_state.threshold_ph_min, st.session_state.threshold_ph_max],
                "turbidity": st.session_state.threshold_turbidity,
                "dissolved_oxygen": st.session_state.threshold_do
            }
            st.success("Alert thresholds updated successfully!")
    
    with tab3:
        st.subheader("Station Management")
        st.write("View and manage monitoring stations.")
        
        # Display stations
        for station_id, station in STATION_INFO.items():
            with st.expander(f"{station['name']} ({station_id})"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(station["image_url"], use_container_width=True)
                
                with col2:
                    st.write(f"**Type:** {station['water_type']}")
                    st.write(f"**Location:** {station['latitude']}, {station['longitude']}")
                    
                    # These would normally save to a database, but are placeholders here
                    st.text_input("Station Name", value=station["name"], key=f"name_{station_id}")
                    
                    # Mapa de traducción de tipos de agua de español a inglés
                    water_type_translation = {
                        "Río": "River",
                        "Lago": "Lake",
                        "Laguna": "Lagoon",
                        "Arroyo": "Stream",
                        "Embalse": "Reservoir"
                    }
                    
                    # Obtener el tipo en inglés o el valor original si no existe traducción
                    current_type_eng = water_type_translation.get(station["water_type"], "River")
                    
                    st.selectbox("Water Type", ["River", "Lake", "Lagoon", "Stream", "Reservoir"], 
                                index=["River", "Lake", "Lagoon", "Stream", "Reservoir"].index(current_type_eng),
                                key=f"type_{station_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.number_input("Latitude", value=station["latitude"], key=f"lat_{station_id}")
                    with col2:
                        st.number_input("Longitude", value=station["longitude"], key=f"lon_{station_id}")
                    
                    st.button("Save Changes", key=f"save_{station_id}")
        
        # Add new station (placeholder)
        with st.expander("Add New Station"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Station ID", placeholder="e.g., ST005", key="new_station_id")
                st.text_input("Station Name", placeholder="e.g., Mountain River Station", key="new_station_name")
                st.selectbox("Water Type", ["River", "Lake", "Lagoon", "Stream", "Reservoir"], key="new_station_type")
            
            with col2:
                st.number_input("Latitude", key="new_station_lat")
                st.number_input("Longitude", key="new_station_lon")
                st.text_input("Image URL", placeholder="Enter image URL", key="new_station_img")
            
            if st.button("Add Station"):
                st.info("In a real implementation, this would add a new station to the database.")
                st.success("Station added successfully!")
        
    with tab4:
        st.subheader("Data Sources")
        st.write("Configure data sources and API connections.")
        
        # Data source options
        if 'use_api_data' not in st.session_state:
            st.session_state.use_api_data = True
            
        data_source = st.radio(
            "Primary Data Source",
            options=["Generated Data Only", "API Data When Available", "Require API Data"],
            index=1 if st.session_state.use_api_data else 0,
            help="Select where the dashboard should get its data from"
        )
        
        # Update session state based on selection
        if data_source == "Generated Data Only":
            st.session_state.use_api_data = False
            st.info("The dashboard will use locally generated data only.")
        else:
            st.session_state.use_api_data = True
            
            # Show API settings if using API data
            st.markdown("### API Connection Settings")
            
            # Weather API
            with st.expander("Weather API"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    api_enabled = st.checkbox(
                        "Enable Weather API", 
                        value=True,
                        key="weather_api_enabled"
                    )
                
                with col2:
                    st.write("Provides real-time weather data including temperature, rainfall, and wind conditions.")
                
                if api_enabled:
                    st.text_input(
                        "API Endpoint URL",
                        value=api_client.api_endpoints.get("weather", "https://api.example.com/weather"),
                        key="weather_api_url"
                    )
                    
                    st.text_input(
                        "API Key",
                        value=api_client.api_keys.get("weather", ""),
                        type="password",
                        key="weather_api_key"
                    )
                    
                    # Update frequency
                    st.slider(
                        "Update Frequency (seconds)",
                        min_value=60,
                        max_value=1800,
                        value=int(api_client.update_intervals.get("weather", 300)),  # Asegurar que sea int
                        step=60,
                        key="weather_api_frequency"
                    )
            
            # Water Quality API
            with st.expander("Water Quality API"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    api_enabled = st.checkbox(
                        "Enable Water Quality API", 
                        value=True,
                        key="water_quality_api_enabled"
                    )
                
                with col2:
                    st.write("Provides real-time water quality data including pH, turbidity, and dissolved oxygen levels.")
                
                if api_enabled:
                    st.text_input(
                        "API Endpoint URL",
                        value=api_client.api_endpoints.get("water_quality", "https://api.example.com/water-quality"),
                        key="water_quality_api_url"
                    )
                    
                    st.text_input(
                        "API Key",
                        value=api_client.api_keys.get("water_quality", ""),
                        type="password",
                        key="water_quality_api_key"
                    )
                    
                    # Update frequency
                    st.slider(
                        "Update Frequency (seconds)",
                        min_value=60,
                        max_value=1800,
                        value=int(api_client.update_intervals.get("water_quality", 600)),  # Asegurar que sea int
                        step=60,
                        key="water_quality_api_frequency"
                    )
            
            # Water Levels API
            with st.expander("Water Levels API"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    api_enabled = st.checkbox(
                        "Enable Water Levels API", 
                        value=True,
                        key="water_levels_api_enabled"
                    )
                
                with col2:
                    st.write("Provides real-time water level and flow rate data for rivers, lakes, and reservoirs.")
                
                if api_enabled:
                    st.text_input(
                        "API Endpoint URL",
                        value=api_client.api_endpoints.get("water_levels", "https://api.example.com/water-levels"),
                        key="water_levels_api_url"
                    )
                    
                    st.text_input(
                        "API Key",
                        value=api_client.api_keys.get("water_levels", ""),
                        type="password",
                        key="water_levels_api_key"
                    )
                    
                    # Update frequency
                    st.slider(
                        "Update Frequency (seconds)",
                        min_value=60,
                        max_value=1800,
                        value=int(api_client.update_intervals.get("water_levels", 300)),  # Asegurar que sea int
                        step=60,
                        key="water_levels_api_frequency"
                    )
            
            # Soil Moisture API
            with st.expander("Soil Moisture API"):
                col1, col2 = st.columns([1, 3])
                with col1:
                    api_enabled = st.checkbox(
                        "Enable Soil Moisture API", 
                        value=True,
                        key="soil_moisture_api_enabled"
                    )
                
                with col2:
                    st.write("Provides real-time soil moisture and composition data for environmental monitoring.")
                
                if api_enabled:
                    st.text_input(
                        "API Endpoint URL",
                        value=api_client.api_endpoints.get("soil_moisture", "https://api.example.com/soil"),
                        key="soil_moisture_api_url"
                    )
                    
                    st.text_input(
                        "API Key",
                        value=api_client.api_keys.get("soil_moisture", ""),
                        type="password",
                        key="soil_moisture_api_key"
                    )
                    
                    # Update frequency
                    st.slider(
                        "Update Frequency (seconds)",
                        min_value=60,
                        max_value=1800,
                        value=int(api_client.update_intervals.get("soil_moisture", 900)),  # Asegurar que sea int
                        step=60,
                        key="soil_moisture_api_frequency"
                    )
            
            # Fallback behavior
            st.markdown("### Fallback Behavior")
            
            fallback_behavior = st.radio(
                "When API data is unavailable:",
                options=[
                    "Use generated data",
                    "Show error message",
                    "Use last available data"
                ],
                index=0,
                key="api_fallback_behavior"
            )
            
            # API Status Indicator
            st.markdown("### API Connection Status")
            
            # Test API connections
            test_results = {
                "weather": api_client.test_api_connection("weather"),
                "water_quality": api_client.test_api_connection("water_quality"),
                "water_levels": api_client.test_api_connection("water_levels"),
                "soil_moisture": api_client.test_api_connection("soil_moisture")
            }
            
            # Create a status table
            status_data = {
                "API": ["Weather", "Water Quality", "Water Levels", "Soil Moisture"],
                "Status": [
                    "✓ Connected" if test_results["weather"]["status"] == "success" else "⚠️ Warning" if test_results["weather"]["status"] == "warning" else "✗ Error",
                    "✓ Connected" if test_results["water_quality"]["status"] == "success" else "⚠️ Warning" if test_results["water_quality"]["status"] == "warning" else "✗ Error",
                    "✓ Connected" if test_results["water_levels"]["status"] == "success" else "⚠️ Warning" if test_results["water_levels"]["status"] == "warning" else "✗ Error",
                    "✓ Connected" if test_results["soil_moisture"]["status"] == "success" else "⚠️ Warning" if test_results["soil_moisture"]["status"] == "warning" else "✗ Error"
                ],
                "Message": [
                    test_results["weather"]["message"],
                    test_results["water_quality"]["message"],
                    test_results["water_levels"]["message"],
                    test_results["soil_moisture"]["message"]
                ]
            }
            
            # Convert to DataFrame for display
            import pandas as pd
            status_df = pd.DataFrame(status_data)
            st.dataframe(status_df, hide_index=True)
            
        # Save API settings button
        if st.button("Save Data Source Settings", type="primary"):
            if st.session_state.use_api_data:
                # Update API client settings
                api_client.configure_api_connection(
                    "weather", 
                    st.session_state.weather_api_url, 
                    st.session_state.weather_api_key
                )
                api_client.configure_api_connection(
                    "water_quality", 
                    st.session_state.water_quality_api_url, 
                    st.session_state.water_quality_api_key
                )
                api_client.configure_api_connection(
                    "water_levels", 
                    st.session_state.water_levels_api_url, 
                    st.session_state.water_levels_api_key
                )
                api_client.configure_api_connection(
                    "soil_moisture", 
                    st.session_state.soil_moisture_api_url, 
                    st.session_state.soil_moisture_api_key
                )
                
                # Update API update intervals
                api_client.update_intervals["weather"] = st.session_state.weather_api_frequency
                api_client.update_intervals["water_quality"] = st.session_state.water_quality_api_frequency
                api_client.update_intervals["water_levels"] = st.session_state.water_levels_api_frequency
                api_client.update_intervals["soil_moisture"] = st.session_state.soil_moisture_api_frequency
                
                st.success("API settings saved successfully!")
            else:
                st.success("Data source set to generated data only.")
    
    # User preferences
    st.header("User Preferences")
    
    # Display preferences
    with st.expander("Display Settings"):
        st.radio("Default View", ["Dashboard", "Water Quality", "Alerts", "Predictions", "Reports"], index=0)
        st.selectbox("Default Timeframe", TIMEFRAME_OPTIONS, index=0)
        st.checkbox("Show alerts in sidebar", value=True)
        st.checkbox("Auto-refresh data", value=True)
        
        if st.button("Save Display Preferences"):
            st.success("Display preferences saved successfully!")
    
    # Account settings (placeholder)
    with st.expander("Account Settings"):
        st.text_input("Name", value="Environmental Technician")
        st.text_input("Email", value="tech@monitoring.org")
        st.text_input("Organization", value="Environmental Monitoring Team")
        
        st.checkbox("Receive email notifications", value=True)
        st.checkbox("Receive SMS alerts", value=False)
        
        if st.button("Update Account Information"):
            st.success("Account information updated successfully!")
    
    # About section
    st.header("About Environmental Monitoring")
    st.write("""
    This environmental monitoring dashboard is designed to provide real-time visualization
    of water levels, quality metrics, and potential environmental risks. The dashboard is designed for use
    by environmental technicians, municipal authorities, researchers, and NGOs working in water resource
    management.
    
    Version: 1.0.0
    """)
    
    # Log out button
    if st.button("Log Out", type="primary"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.info("You have been logged out successfully.")
        st.rerun()
