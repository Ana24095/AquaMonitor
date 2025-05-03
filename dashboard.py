import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.constants import COLORS, STATION_INFO

def render_dashboard(filtered_data):
    """
    Render the main dashboard view with summary metrics and visualizations.
    
    Parameters:
    - filtered_data: DataFrame with filtered environmental data
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Dashboard</h1>
    """, unsafe_allow_html=True)
    
    # Get the latest data point for each station
    latest_data = filtered_data.sort_values('timestamp').groupby('station_id').last().reset_index()
    
    # Water Level section - water level cards in a row
    st.markdown("""
    <h2 style="font-size: 1.4rem; margin-top: 1rem;">Water Level</h2>
    """, unsafe_allow_html=True)
    
    # Create a row for water level cards
    water_cols = st.columns(len(STATION_INFO))
    
    # Colors for water level indicators
    water_level_colors = {
        "high": "#ef476f",  # Red
        "medium": "#ffd166", # Yellow
        "low": "#00b8a9"  # Green
    }
    
    # Display water level cards for each station
    for i, (station_id, station_info) in enumerate(STATION_INFO.items()):
        station_data = latest_data[latest_data['station_id'] == station_id]
        
        if not station_data.empty:
            water_level = station_data['water_level'].values[0]
            
            # Determine color based on water level
            if water_level > 90:
                color = water_level_colors["high"]
                level_class = "critical"
            elif water_level > 75:
                color = water_level_colors["medium"]
                level_class = "warning"
            else:
                color = water_level_colors["low"]
                level_class = "normal"
            
            # Create a card for this station's water level
            with water_cols[i]:
                st.markdown(f"""
                <div style="background-color: #0d3b49; border-radius: 10px; padding: 1rem; text-align: center;">
                    <h3 style="color: white; font-size: 1rem; margin-bottom: 0.5rem;">{station_info["name"]}</h3>
                    <div style="font-size: 2.5rem; font-weight: bold; color: {color}; margin: 0.5rem 0;">
                        {water_level:.0f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Create two columns for the second row
    col1, col2 = st.columns(2)
    
    # Water quality section
    with col1:
        st.markdown("""
        <h2 style="font-size: 1.4rem; margin-top: 1.5rem;">Water Quality</h2>
        """, unsafe_allow_html=True)
        
        # Create a grouped bar chart for water quality metrics
        quality_data = []
        
        for _, row in latest_data.iterrows():
            quality_data.append({
                "Station": row["station_name"],
                "Parameter": "pH",
                "Value": row["ph"]
            })
            quality_data.append({
                "Station": row["station_name"],
                "Parameter": "Turbidity",
                "Value": row["turbidity"]
            })
            quality_data.append({
                "Station": row["station_name"],
                "Parameter": "Dissolved Oxygen",
                "Value": row["dissolved_oxygen"]
            })
        
        quality_df = pd.DataFrame(quality_data)
        
        fig = px.bar(
            quality_df,
            x="Station",
            y="Value",
            color="Parameter",
            barmode="group",
            color_discrete_sequence=[COLORS["primary"], "#43aa8b", "#f94144"],
            height=300
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#333333"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Disaster probability section
    with col2:
        st.markdown("""
        <h2 style="font-size: 1.4rem; margin-top: 1.5rem;">Disaster Probability</h2>
        """, unsafe_allow_html=True)
        
        # Calculate average risk values
        avg_flood_risk = latest_data['flood_risk'].mean() * 100
        avg_drought_risk = latest_data['drought_risk'].mean() * 100
        avg_landslide_risk = latest_data['landslide_risk'].mean() * 100
        
        # Create a donut chart for disaster risk
        risk_data = pd.DataFrame({
            'Type': ['Flooding', 'Drought', 'Landslide'],
            'Percentage': [avg_flood_risk, avg_drought_risk, avg_landslide_risk]
        })
        
        fig = px.pie(
            risk_data,
            names='Type',
            values='Percentage',
            hole=0.6,
            color='Type',
            color_discrete_map={
                'Flooding': COLORS['primary'],
                'Drought': '#d00000',
                'Landslide': '#ffb703'
            },
            height=300
        )
        
        # Add percentage annotations
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#ffffff', width=2))
        )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#333333"),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Soil moisture section
    st.markdown("""
    <h2 style="font-size: 1.4rem; margin-top: 1.5rem;">Soil Moisture</h2>
    """, unsafe_allow_html=True)
    
    # Create a horizontal bar chart for soil moisture
    soil_moisture_data = latest_data[['station_name', 'soil_moisture']].sort_values('soil_moisture', ascending=True)
    
    # Create bars for each station with colored segments
    soil_cols = st.columns(len(STATION_INFO))
    
    for i, (_, row) in enumerate(soil_moisture_data.iterrows()):
        station_name = row['station_name']
        moisture = row['soil_moisture']
        
        # Determine color based on moisture level
        if moisture < 30:
            color = "#f94144"  # Red
        elif moisture < 60:
            color = "#f8961e"  # Orange
        else:
            color = "#90be6d"  # Green
        
        with soil_cols[i]:
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <p style="margin-bottom: 0.2rem; font-weight: bold;">{station_name}</p>
                <div style="width: 100%; background-color: #e9ecef; border-radius: 5px; height: 10px;">
                    <div style="width: {moisture}%; background-color: {color}; height: 10px; border-radius: 5px;"></div>
                </div>
                <p style="text-align: right; margin-top: 0.2rem;">{moisture:.0f} %</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Rainfall section
    st.markdown("""
    <h2 style="font-size: 1.4rem; margin-top: 1.5rem;">Rainfall</h2>
    """, unsafe_allow_html=True)
    
    # Create a horizontal bar chart for rainfall
    rainfall_data = latest_data[['station_name', 'rainfall']].sort_values('station_name')
    
    fig = px.bar(
        rainfall_data,
        y='station_name',
        x='rainfall',
        orientation='h',
        height=300,
        labels={'rainfall': 'mm/day', 'station_name': 'Station'},
        color='rainfall',
        color_continuous_scale=['#52b69a', '#76c893', '#99d98c', '#b5e48c', '#d9ed92'],
    )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#333333"),
        yaxis={'categoryorder':'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Location section
    st.markdown("""
    <h2 style="font-size: 1.4rem; margin-top: 1.5rem;">Location</h2>
    <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
        <div style="width: 48%; background-color: #f8f9fa; border-radius: 10px; padding: 0.5rem; text-align: center;">
            <img src="https://via.placeholder.com/400x200/e9ecef/333333?text=Stations+Map" style="width: 100%; border-radius: 5px;">
        </div>
        <div style="width: 48%; background-color: #f8f9fa; border-radius: 10px; padding: 0.5rem; text-align: center;">
            <img src="https://via.placeholder.com/400x200/e9ecef/333333?text=Detailed+View" style="width: 100%; border-radius: 5px;">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a button to view all stations
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("View all stations", use_container_width=True):
            st.session_state.current_view = "map"
