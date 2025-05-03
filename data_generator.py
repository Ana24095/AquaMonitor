import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from utils.constants import STATION_INFO

def generate_latest_data():
    """
    Generate a DataFrame with the latest simulated environmental data for all stations.
    Returns a DataFrame with timestamps and environmental metrics.
    """
    data = []
    current_time = datetime.now()
    
    # Generate data for the past hour with 5-minute intervals
    for minutes in range(0, 60, 5):
        timestamp = current_time - timedelta(minutes=minutes)
        
        for station_id, station in STATION_INFO.items():
            # Base values for this station
            base_water_level = station["base_water_level"]
            base_ph = station["base_ph"]
            base_turbidity = station["base_turbidity"]
            base_dissolved_oxygen = station["base_dissolved_oxygen"]
            base_soil_moisture = station["base_soil_moisture"]
            base_rainfall = station["base_rainfall"]
            
            # Add some randomness to simulate fluctuations
            water_level = max(0, min(100, base_water_level + random.uniform(-5, 5)))
            ph = max(0, min(14, base_ph + random.uniform(-0.5, 0.5)))
            turbidity = max(0, base_turbidity + random.uniform(-1, 1))
            dissolved_oxygen = max(0, base_dissolved_oxygen + random.uniform(-0.5, 0.5))
            soil_moisture = max(0, min(100, base_soil_moisture + random.uniform(-3, 3)))
            rainfall = max(0, base_rainfall + random.uniform(-0.5, 0.5))
            
            # Calculate risk factors based on current conditions
            flood_risk = calculate_flood_risk(water_level, rainfall)
            drought_risk = calculate_drought_risk(water_level, soil_moisture)
            landslide_risk = calculate_landslide_risk(soil_moisture, rainfall)
            
            # Determine alert levels
            water_level_alert = "high" if water_level > 80 else "normal"
            ph_alert = "high" if ph < 6.5 or ph > 8.5 else "normal"
            turbidity_alert = "high" if turbidity > 5 else "normal"
            do_alert = "high" if dissolved_oxygen < 5 else "normal"
            
            data.append({
                "timestamp": timestamp,
                "station_id": station_id,
                "station_name": station["name"],
                "latitude": station["latitude"],
                "longitude": station["longitude"],
                "water_type": station["water_type"],
                "water_level": water_level,
                "ph": ph,
                "turbidity": turbidity,
                "dissolved_oxygen": dissolved_oxygen,
                "soil_moisture": soil_moisture,
                "rainfall": rainfall,
                "flood_risk": flood_risk,
                "drought_risk": drought_risk,
                "landslide_risk": landslide_risk,
                "water_level_alert": water_level_alert,
                "ph_alert": ph_alert,
                "turbidity_alert": turbidity_alert,
                "dissolved_oxygen_alert": do_alert
            })
    
    return pd.DataFrame(data)

def get_station_data_by_timeframe(data, timeframe, station_filter="All Stations"):
    """
    Filter data based on the selected timeframe and station.
    
    Parameters:
    - data: DataFrame with all the environmental data
    - timeframe: string representing the time range ('5m', '15m', '30m', '1h', '1d')
    - station_filter: string or ID of the station to filter by
    
    Returns:
    - Filtered DataFrame
    """
    current_time = datetime.now()
    
    # Convert timeframe to minutes
    if timeframe == "5m":
        delta_minutes = 5
    elif timeframe == "15m":
        delta_minutes = 15
    elif timeframe == "30m":
        delta_minutes = 30
    elif timeframe == "1h":
        delta_minutes = 60
    elif timeframe == "1d":
        delta_minutes = 1440
    else:
        delta_minutes = 5  # Default
    
    # Filter by time
    time_threshold = current_time - timedelta(minutes=delta_minutes)
    filtered_data = data[data['timestamp'] >= time_threshold]
    
    # Filter by station if needed
    if station_filter != "All Stations":
        filtered_data = filtered_data[filtered_data['station_name'] == station_filter]
    
    return filtered_data

def calculate_flood_risk(water_level, rainfall):
    """Calculate flood risk based on water level and rainfall."""
    # Simple weighted calculation
    risk = (0.7 * water_level / 100) + (0.3 * min(rainfall / 10, 1))
    return min(1, max(0, risk))  # Ensure value is between 0 and 1

def calculate_drought_risk(water_level, soil_moisture):
    """Calculate drought risk based on water level and soil moisture."""
    # Inverse relationship - lower values indicate higher risk
    water_factor = 1 - (water_level / 100)
    soil_factor = 1 - (soil_moisture / 100)
    risk = (0.6 * water_factor) + (0.4 * soil_factor)
    return min(1, max(0, risk))

def calculate_landslide_risk(soil_moisture, rainfall):
    """Calculate landslide risk based on soil moisture and rainfall."""
    # High soil moisture + high rainfall = higher landslide risk
    soil_factor = soil_moisture / 100  # Normalize to 0-1
    rain_factor = min(rainfall / 10, 1)  # Normalize rainfall (cap at 10mm)
    risk = (0.5 * soil_factor) + (0.5 * rain_factor)
    return min(1, max(0, risk))
