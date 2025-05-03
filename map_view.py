import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
from utils.constants import STATION_INFO, COLORS

def render_map(data):
    """
    Render an interactive map showing monitoring stations and their data.
    
    Parameters:
    - data: DataFrame with environmental data
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Localización</h1>
    """, unsafe_allow_html=True)
    
    # Get the latest data point for each station
    latest_data = data.sort_values('timestamp').groupby('station_id').last().reset_index()
    
    # Create a map centered on the average of all station coordinates
    avg_lat = sum(station["lat"] for station in STATION_INFO.values()) / len(STATION_INFO)
    avg_lon = sum(station["lon"] for station in STATION_INFO.values()) / len(STATION_INFO)
    
    # Create columns for the interactive map and station list
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create Folium map
        m = folium.Map(
            location=[avg_lat, avg_lon], 
            zoom_start=10, 
            tiles="CartoDB positron",
            control_scale=True
        )
        
        # Add a marker for each station
        for station_id, station_info in STATION_INFO.items():
            station_data = latest_data[latest_data['station_id'] == station_id]
            
            if not station_data.empty:
                # Get the station's data
                water_level = station_data['water_level'].values[0]
                
                # Determine marker color based on water level
                if water_level > 90:
                    color = '#ef476f'  # Critical (red)
                elif water_level > 75:
                    color = '#ffd166'  # Warning (yellow)
                else:
                    color = '#00b8a9'  # Normal (aqua)
                
                # Create a popup with station information
                popup_html = f"""
                <div style="width: 200px; font-family: sans-serif;">
                    <h4 style="color: #333; margin-bottom: 10px;">{station_info['name']}</h4>
                    <div style="background-color: {color}; color: white; padding: 5px; border-radius: 5px; margin-bottom: 10px; text-align: center;">
                        <b>Nivel de Agua: {water_level:.1f}%</b>
                    </div>
                    <table style="width: 100%;">
                        <tr>
                            <td><b>Tipo:</b></td>
                            <td>{station_info['water_type']}</td>
                        </tr>
                        <tr>
                            <td><b>pH:</b></td>
                            <td>{station_data['ph'].values[0]:.1f}</td>
                        </tr>
                        <tr>
                            <td><b>Turbidez:</b></td>
                            <td>{station_data['turbidity'].values[0]:.1f} NTU</td>
                        </tr>
                        <tr>
                            <td><b>Oxígeno:</b></td>
                            <td>{station_data['dissolved_oxygen'].values[0]:.1f} mg/L</td>
                        </tr>
                        <tr>
                            <td><b>Humedad:</b></td>
                            <td>{station_data['soil_moisture'].values[0]:.1f}%</td>
                        </tr>
                        <tr>
                            <td><b>Pluviosidad:</b></td>
                            <td>{station_data['rainfall'].values[0]:.1f} mm/día</td>
                        </tr>
                    </table>
                </div>
                """
                
                # Create a custom icon for better visibility
                icon = folium.DivIcon(
                    icon_size=(40, 40),
                    icon_anchor=(20, 40),
                    html=f"""
                    <div style="background-color: {color}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px #333;">
                    </div>
                    """
                )
                
                # Add marker to map
                folium.Marker(
                    location=[station_info['lat'], station_info['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=station_info['name'],
                    icon=icon
                ).add_to(m)
        
        # Add additional map layers
        folium.TileLayer('CartoDB dark_matter', name='Dark Mode').add_to(m)
        folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
        folium.TileLayer('Stamen Terrain', name='Terrain').add_to(m)
        
        # Add layer control
        folium.LayerControl(position='topright').add_to(m)
        
        # Display the map
        st.markdown("""
        <div style="border-radius: 10px; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        folium_static(m, width=800, height=500)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <h3 style="font-size: 1.2rem; margin-bottom: 1rem;">Estaciones de Monitoreo</h3>
        """, unsafe_allow_html=True)
        
        # Display station cards
        for station_id, station_info in STATION_INFO.items():
            station_data = latest_data[latest_data['station_id'] == station_id]
            
            if not station_data.empty:
                water_level = station_data['water_level'].values[0]
                
                # Determine color based on water level
                if water_level > 90:
                    color = '#ef476f'  # Critical
                    status = "Crítico"
                elif water_level > 75:
                    color = '#ffd166'  # Warning
                    status = "Alerta"
                else:
                    color = '#00b8a9'  # Normal
                    status = "Normal"
                
                # Create a styled card for this station
                st.markdown(f"""
                <div style="background-color: white; border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 0 5px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #333;">{station_info['name']}</h4>
                        <span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.8rem;">{status}</span>
                    </div>
                    <p style="color: #666; margin-bottom: 8px; font-size: 0.9rem;">Tipo: {station_info['water_type']}</p>
                    <div style="background-color: #f8f9fa; height: 10px; border-radius: 5px; margin-bottom: 5px;">
                        <div style="width: {water_level}%; background-color: {color}; height: 10px; border-radius: 5px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                        <span>Nivel de Agua</span>
                        <span style="font-weight: bold;">{water_level:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Add a data table with more detailed information
    st.markdown("""
    <h3 style="font-size: 1.2rem; margin: 1.5rem 0 1rem 0;">Datos Detallados</h3>
    """, unsafe_allow_html=True)
    
    # Join station info to the data
    station_data_df = latest_data.copy()
    station_data_df['station_name'] = station_data_df['station_id'].apply(
        lambda x: STATION_INFO[x]['name'] if x in STATION_INFO else "Unknown"
    )
    station_data_df['water_type'] = station_data_df['station_id'].apply(
        lambda x: STATION_INFO[x]['water_type'] if x in STATION_INFO else "Unknown"
    )
    
    # Select columns for display
    display_cols = [
        'station_name', 'water_type', 'water_level', 'ph', 'turbidity', 
        'dissolved_oxygen', 'soil_moisture', 'rainfall'
    ]
    
    # Rename columns for Spanish display
    rename_dict = {
        'station_name': 'Estación',
        'water_type': 'Tipo',
        'water_level': 'Nivel de Agua (%)',
        'ph': 'pH',
        'turbidity': 'Turbidez (NTU)',
        'dissolved_oxygen': 'Oxígeno Disuelto (mg/L)',
        'soil_moisture': 'Humedad del Suelo (%)',
        'rainfall': 'Pluviosidad (mm/día)'
    }
    
    display_df = station_data_df[display_cols].sort_values('station_name').rename(columns=rename_dict)
    
    # Apply styling to the dataframe
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True
    )