COLORS = {
    "primary": "#00b8a9", # Aqua green
    "text": "#262730", # Dark gray, almost black
    "background": "#ffffff", # White
    "background_secondary": "#f0f2f6", # Light gray
    "alert": "#ef476f", # Red
    "warning": "#ffd166", # Yellow
    "success": "#06d6a0", # Green
}

# Station information
STATION_INFO = {
    "station_1": {
        "name": "Río Ebro",
        "water_type": "Río",
        "image_url": "https://via.placeholder.com/100x100.png?text=Rio+Ebro",
        "lat": 40.6913, 
        "lon": -0.8777,
        "latitude": 40.6913,
        "longitude": -0.8777,
        "base_water_level": 65,
        "base_ph": 7.2,
        "base_turbidity": 3.5,
        "base_dissolved_oxygen": 7.8,
        "base_soil_moisture": 58,
        "base_rainfall": 2.3
    },
    "station_2": {
        "name": "Lago Valencia",
        "water_type": "Lago",
        "image_url": "https://via.placeholder.com/100x100.png?text=Lago+Valencia",
        "lat": 39.5475, 
        "lon": -0.4750,
        "latitude": 39.5475,
        "longitude": -0.4750,
        "base_water_level": 72,
        "base_ph": 7.5,
        "base_turbidity": 2.8,
        "base_dissolved_oxygen": 8.2,
        "base_soil_moisture": 62,
        "base_rainfall": 1.8
    },
    "station_3": {
        "name": "Río Tajo",
        "water_type": "Río",
        "image_url": "https://via.placeholder.com/100x100.png?text=Rio+Tajo",
        "lat": 39.8560, 
        "lon": -4.0248,
        "latitude": 39.8560,
        "longitude": -4.0248,
        "base_water_level": 58,
        "base_ph": 6.9,
        "base_turbidity": 4.2,
        "base_dissolved_oxygen": 6.5,
        "base_soil_moisture": 45,
        "base_rainfall": 3.1
    },
    "station_4": {
        "name": "Laguna Verde",
        "water_type": "Laguna",
        "image_url": "https://via.placeholder.com/100x100.png?text=Laguna+Verde",
        "lat": 40.1120, 
        "lon": -3.0917,
        "latitude": 40.1120,
        "longitude": -3.0917,
        "base_water_level": 81,
        "base_ph": 8.1,
        "base_turbidity": 5.6,
        "base_dissolved_oxygen": 5.3,
        "base_soil_moisture": 70,
        "base_rainfall": 4.5
    }
}

# Timeframe options for filtering data
TIMEFRAME_OPTIONS = ["5m", "15m", "30m", "1h", "1d"]

# Parameter descriptions for water quality
PARAMETER_DESCRIPTIONS = {
    "ph": {
        "title": "pH",
        "description": "Mide la acidez o alcalinidad del agua. Un pH de 7 es neutro, por debajo es ácido y por encima es alcalino.",
        "unit": "",
        "ideal_range": [6.5, 8.5],
        "warning_range": [6.0, 9.0],
        "critical_range": [5.0, 10.0]
    },
    "turbidity": {
        "title": "Turbidez",
        "description": "Mide la claridad del agua. Los valores altos indican agua turbia con partículas suspendidas.",
        "unit": "NTU",
        "ideal_range": [0, 5],
        "warning_range": [5, 10],
        "critical_range": [10, 20]
    },
    "dissolved_oxygen": {
        "title": "Oxígeno Disuelto",
        "description": "Cantidad de oxígeno disponible en el agua. Vital para la vida acuática.",
        "unit": "mg/L",
        "ideal_range": [6, 10],
        "warning_range": [4, 6],
        "critical_range": [0, 4]
    },
    "water_level": {
        "title": "Nivel de Agua",
        "description": "Porcentaje del nivel máximo de agua.",
        "unit": "%",
        "ideal_range": [30, 70],
        "warning_range": [15, 85],
        "critical_range": [0, 100]
    },
    "soil_moisture": {
        "title": "Humedad del Suelo",
        "description": "Cantidad de agua presente en el suelo.",
        "unit": "%",
        "ideal_range": [30, 70],
        "warning_range": [15, 85],
        "critical_range": [0, 100]
    },
    "rainfall": {
        "title": "Pluviosidad",
        "description": "Cantidad de lluvia caída en un día.",
        "unit": "mm/día",
        "ideal_range": [0, 15],
        "warning_range": [15, 30],
        "critical_range": [30, 50]
    }
}