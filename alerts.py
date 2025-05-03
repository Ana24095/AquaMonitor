import streamlit as st
import pandas as pd
import plotly.express as px
from utils.constants import STATION_INFO, COLORS

def render_alerts(filtered_data):
    """
    Render the alerts and notifications view.
    
    Parameters:
    - filtered_data: DataFrame with filtered environmental data
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Alerts</h1>
    """, unsafe_allow_html=True)
    
    # Get the latest data point for each station
    latest_data = filtered_data.sort_values('timestamp').groupby('station_id').last().reset_index()
    
    # Check for alerts
    water_level_alerts = latest_data[latest_data['water_level_alert'] == 'high']
    ph_alerts = latest_data[latest_data['ph_alert'] == 'high']
    turbidity_alerts = latest_data[latest_data['turbidity_alert'] == 'high']
    do_alerts = latest_data[latest_data['dissolved_oxygen_alert'] == 'high']
    flood_alerts = latest_data[latest_data['flood_risk'] > 0.7]
    drought_alerts = latest_data[latest_data['drought_risk'] > 0.7]
    landslide_alerts = latest_data[latest_data['landslide_risk'] > 0.7]
    
    total_alerts = (
        len(water_level_alerts) + 
        len(ph_alerts) + 
        len(turbidity_alerts) + 
        len(do_alerts) + 
        len(flood_alerts) + 
        len(drought_alerts) + 
        len(landslide_alerts)
    )
    
    # Create columns for alert summary and details
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <h3 style="font-size: 1.2rem; margin-bottom: 1rem;">Alert Summary</h3>
        """, unsafe_allow_html=True)
        
        if total_alerts == 0:
            st.markdown("""
            <div style="background-color: #d4edda; color: #155724; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
                <h4 style="margin-bottom: 0.5rem;">All systems normal</h4>
                <p style="margin: 0;">No active alerts at the moment.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #f8d7da; color: #721c24; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
                <h4 style="margin-bottom: 0.5rem;">{total_alerts} Active Alerts</h4>
                <p style="margin: 0;">Attention required at multiple stations.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a pie chart for alert distribution
            alert_counts = {
                'Water Level': len(water_level_alerts),
                'pH': len(ph_alerts),
                'Turbidity': len(turbidity_alerts),
                'Dissolved Oxygen': len(do_alerts),
                'Flood': len(flood_alerts),
                'Drought': len(drought_alerts),
                'Landslide': len(landslide_alerts)
            }
            
            # Filter out categories with zero alerts
            alert_counts = {k: v for k, v in alert_counts.items() if v > 0}
            
            if alert_counts:
                alert_df = pd.DataFrame({
                    'Type': list(alert_counts.keys()),
                    'Count': list(alert_counts.values())
                })
                
                fig = px.pie(
                    alert_df,
                    values='Count',
                    names='Type',
                    color='Type',
                    color_discrete_sequence=[
                        '#ef476f', '#ffd166', '#06d6a0', 
                        '#118ab2', '#073b4c', '#9d4edd', '#ff8fa3'
                    ],
                    hole=0.4
                )
                
                fig.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", y=-0.2),
                    font=dict(size=12),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("""
        <h3 style="font-size: 1.2rem; margin-bottom: 1rem;">Recent Notifications</h3>
        """, unsafe_allow_html=True)
        
        # Create alert components
        def create_alert_card(station_name, alert_type, value, threshold, timestamp, severity):
            # Determine color based on severity
            if severity == "high":
                bg_color = "#f8d7da"
                border_color = "#f5c2c7"
                text_color = "#721c24"
                icon = "⚠️"
            elif severity == "medium":
                bg_color = "#fff3cd"
                border_color = "#ffecb5"
                text_color = "#856404"
                icon = "⚠️"
            else:
                bg_color = "#d1e7dd"
                border_color = "#badbcc"
                text_color = "#0f5132"
                icon = "✓"
            
            # Format timestamp
            time_str = timestamp.strftime("%H:%M:%S")
            date_str = timestamp.strftime("%d/%m/%Y")
            
            # Create HTML for the alert card
            return f"""
            <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 10px; padding: 15px; margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <div>
                        <span style="font-size: 1.5rem; margin-right: 10px;">{icon}</span>
                        <span style="font-weight: bold; color: {text_color};">{alert_type}</span>
                    </div>
                    <div style="color: #6c757d; font-size: 0.8rem; text-align: right;">
                        <div>{time_str}</div>
                        <div>{date_str}</div>
                    </div>
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>Station:</strong> {station_name}
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                    <span>Current value: <strong>{value}</strong></span>
                    <span>Threshold: <strong>{threshold}</strong></span>
                </div>
            </div>
            """
        
        # Generate alert cards based on the data
        alerts_shown = 0
        
        # Function to format threshold based on alert type
        def format_threshold(alert_type, thresholds):
            if alert_type == "Water Level":
                return f">{thresholds['water_level']}%"
            elif alert_type == "pH":
                return f"<{thresholds['ph'][0]} or >{thresholds['ph'][1]}"
            elif alert_type == "Turbidity":
                return f">{thresholds['turbidity']} NTU"
            elif alert_type == "Dissolved Oxygen":
                return f"<{thresholds['dissolved_oxygen']} mg/L"
            elif alert_type in ["Flood", "Drought", "Landslide"]:
                return ">70%"
            return "N/A"
        
        # Show water level alerts
        for _, row in water_level_alerts.iterrows():
            station_name = STATION_INFO[row['station_id']]['name']
            st.markdown(
                create_alert_card(
                    station_name=station_name,
                    alert_type="High Water Level",
                    value=f"{row['water_level']:.1f}%",
                    threshold=format_threshold("Water Level", st.session_state.alert_threshold),
                    timestamp=row['timestamp'],
                    severity="high"
                ),
                unsafe_allow_html=True
            )
            alerts_shown += 1
        
        # Show pH alerts
        for _, row in ph_alerts.iterrows():
            station_name = STATION_INFO[row['station_id']]['name']
            st.markdown(
                create_alert_card(
                    station_name=station_name,
                    alert_type="pH Out of Range",
                    value=f"{row['ph']:.1f}",
                    threshold=format_threshold("pH", st.session_state.alert_threshold),
                    timestamp=row['timestamp'],
                    severity="high"
                ),
                unsafe_allow_html=True
            )
            alerts_shown += 1
        
        # Show flood risk alerts
        for _, row in flood_alerts.iterrows():
            station_name = STATION_INFO[row['station_id']]['name']
            st.markdown(
                create_alert_card(
                    station_name=station_name,
                    alert_type="Flood Risk",
                    value=f"{row['flood_risk']*100:.1f}%",
                    threshold=format_threshold("Flood", st.session_state.alert_threshold),
                    timestamp=row['timestamp'],
                    severity="high"
                ),
                unsafe_allow_html=True
            )
            alerts_shown += 1
        
        # Show no alerts message if no alerts are displayed
        if alerts_shown == 0:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #6c757d;">
                <p>No recent alerts to display.</p>
                <p>All stations are reporting normal readings.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Alert settings section
    st.markdown("""
    <h3 style="font-size: 1.2rem; margin: 1.5rem 0 1rem 0;">Alert Settings</h3>
    """, unsafe_allow_html=True)
    
    # Create two columns for the settings
    cols = st.columns(2)
    
    with cols[0]:
        st.subheader("Alert Thresholds", anchor=False)
        
        # Water level threshold
        water_level_threshold = st.slider(
            "Water Level (%)",
            min_value=50,
            max_value=100,
            value=st.session_state.alert_threshold["water_level"],
            step=5,
            help="Alert when water level exceeds this percentage"
        )
        if water_level_threshold != st.session_state.alert_threshold["water_level"]:
            st.session_state.alert_threshold["water_level"] = water_level_threshold
        
        # pH range
        ph_min, ph_max = st.slider(
            "pH Range",
            min_value=0.0,
            max_value=14.0,
            value=(st.session_state.alert_threshold["ph"][0], st.session_state.alert_threshold["ph"][1]),
            step=0.1,
            help="Alert when pH is outside this range"
        )
        if (ph_min, ph_max) != tuple(st.session_state.alert_threshold["ph"]):
            st.session_state.alert_threshold["ph"] = [ph_min, ph_max]
        
        # Turbidity threshold
        turbidity_threshold = st.slider(
            "Turbidity (NTU)",
            min_value=1.0,
            max_value=20.0,
            value=float(st.session_state.alert_threshold["turbidity"]),
            step=0.5,
            help="Alert when turbidity exceeds this value"
        )
        if turbidity_threshold != st.session_state.alert_threshold["turbidity"]:
            st.session_state.alert_threshold["turbidity"] = turbidity_threshold
        
        # Dissolved oxygen threshold
        do_threshold = st.slider(
            "Dissolved Oxygen (mg/L)",
            min_value=1.0,
            max_value=10.0,
            value=float(st.session_state.alert_threshold["dissolved_oxygen"]),
            step=0.5,
            help="Alert when dissolved oxygen falls below this value"
        )
        if do_threshold != st.session_state.alert_threshold["dissolved_oxygen"]:
            st.session_state.alert_threshold["dissolved_oxygen"] = do_threshold
    
    with cols[1]:
        st.subheader("Notification Channels", anchor=False)
        
        # Email notifications
        email_notify = st.checkbox("Receive email alerts", value=True)
        if email_notify:
            email = st.text_input("Email address", value="user@example.com")
        
        # SMS notifications
        sms_notify = st.checkbox("Receive SMS alerts", value=False)
        if sms_notify:
            phone = st.text_input("Phone number", value="+1 XXX XXX XXXX")
        
        # Push notifications
        app_notify = st.checkbox("Receive push notifications in app", value=True)
        
        # Webhook
        webhook_notify = st.checkbox("Send alerts to a webhook", value=False)
        if webhook_notify:
            webhook_url = st.text_input("Webhook URL", value="https://example.com/webhook")
        
        # Save button
        st.button("Save Settings", type="primary", use_container_width=True)

