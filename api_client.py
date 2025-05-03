import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import streamlit as st
import os
from utils.constants import STATION_INFO

class ApiClient:
    """
    Cliente API para conectar con diversas fuentes de datos ambientales en tiempo real.
    Esta clase maneja la autenticación, conexión y transformación de datos de APIs externas.
    """
    
    def __init__(self):
        """Inicializa el cliente API con las credenciales necesarias."""
        # URLs de API (estas serían URLs reales en una implementación completa)
        self.api_endpoints = {
            "weather": "https://api.example.com/weather",
            "water_quality": "https://api.example.com/water-quality",
            "water_levels": "https://api.example.com/water-levels",
            "soil_moisture": "https://api.example.com/soil",
        }
        
        # Credenciales de API (normalmente se cargarían desde variables de entorno)
        self.api_keys = {
            "weather": os.environ.get("WEATHER_API_KEY", ""),
            "water_quality": os.environ.get("WATER_QUALITY_API_KEY", ""),
            "water_levels": os.environ.get("WATER_LEVEL_API_KEY", ""),
            "soil_moisture": os.environ.get("SOIL_API_KEY", ""),
        }
        
        # Intervalos de actualización de datos para cada API (en segundos)
        self.update_intervals = {
            "weather": 300,  # 5 minutos
            "water_quality": 600,  # 10 minutos
            "water_levels": 300,  # 5 minutos
            "soil_moisture": 900,  # 15 minutos
        }
        
        # Caché de datos para evitar solicitudes excesivas
        self.data_cache = {}
        self.last_update = {}
        
    def fetch_weather_data(self, station_id):
        """
        Obtiene datos meteorológicos en tiempo real para una estación específica.
        
        Args:
            station_id: ID de la estación de monitoreo
            
        Returns:
            dict: Datos meteorológicos actualizados
        """
        cache_key = f"weather_{station_id}"
        
        # Check if we need to update the cache
        current_time = time.time()
        if (cache_key in self.last_update and 
            current_time - self.last_update.get(cache_key, 0) < self.update_intervals["weather"]):
            return self.data_cache.get(cache_key, {})
        
        try:
            # Get station info for fallback and supplementary data
            station_info = STATION_INFO.get(station_id, {})
            if not station_info:
                return {}
            
            # Check if we have API credentials
            if self.api_keys["weather"] and self.api_endpoints["weather"] != "https://api.example.com/weather":
                # Make real API request
                try:
                    response = requests.get(
                        f"{self.api_endpoints['weather']}",
                        params={"station": station_id, "lat": station_info.get("latitude"), "lon": station_info.get("longitude")},
                        headers={"Authorization": f"Bearer {self.api_keys['weather']}"},
                        timeout=10  # Timeout after 10 seconds
                    )
                    
                    # Check if request was successful
                    if response.status_code == 200:
                        api_data = response.json()
                        
                        # Format the data as needed
                        data = {
                            "station_id": station_id,
                            "timestamp": datetime.now().isoformat(),
                            "temperature": api_data.get("temperature", 0),
                            "humidity": api_data.get("humidity", 0),
                            "wind_speed": api_data.get("wind_speed", 0),
                            "wind_direction": api_data.get("wind_direction", 0),
                            "pressure": api_data.get("pressure", 0),
                            "precipitation": api_data.get("precipitation", 0),
                            "latitude": station_info.get("latitude"),
                            "longitude": station_info.get("longitude"),
                            "data_source": "api"
                        }
                        
                        # Update cache
                        self.data_cache[cache_key] = data
                        self.last_update[cache_key] = current_time
                        
                        return data
                    else:
                        # Log the error but continue to use simulated data as fallback
                        print(f"API request failed with status {response.status_code}: {response.text}")
                        # Fall through to the simulated data path
                    
                except requests.RequestException as req_error:
                    # Log the error but continue to use simulated data as fallback
                    print(f"API request error: {str(req_error)}")
                    # Fall through to the simulated data path
            
            # Fallback: Generate simulated data based on station information
            latitude = station_info.get("latitude")
            longitude = station_info.get("longitude")
            
            # Generate weather data based on location and historical patterns
            data = {
                "station_id": station_id,
                "timestamp": datetime.now().isoformat(),
                "temperature": 22 + np.random.normal(0, 3),  # Celsius
                "humidity": 60 + np.random.normal(0, 10),  # Percentage
                "wind_speed": 5 + np.random.normal(0, 2),  # m/s
                "wind_direction": np.random.randint(0, 360),  # Degrees
                "pressure": 1013 + np.random.normal(0, 5),  # hPa
                "precipitation": max(0, np.random.exponential(scale=1.0)),  # mm
                "latitude": latitude,
                "longitude": longitude,
                "data_source": "simulated"
            }
            
            # Update cache
            self.data_cache[cache_key] = data
            self.last_update[cache_key] = current_time
            
            return data
            
        except Exception as e:
            st.error(f"Error al obtener datos meteorológicos: {str(e)}")
            return {}
    
    def fetch_water_quality_data(self, station_id):
        """
        Obtiene datos de calidad de agua en tiempo real para una estación específica.
        
        Args:
            station_id: ID de la estación de monitoreo
            
        Returns:
            dict: Datos de calidad de agua actualizados
        """
        cache_key = f"water_quality_{station_id}"
        
        # Check if we need to update the cache
        current_time = time.time()
        if (cache_key in self.last_update and 
            current_time - self.last_update.get(cache_key, 0) < self.update_intervals["water_quality"]):
            return self.data_cache.get(cache_key, {})
        
        try:
            # Get station info for fallback and supplementary data
            station_info = STATION_INFO.get(station_id, {})
            if not station_info:
                return {}
            
            # Check if we have API credentials
            if self.api_keys["water_quality"] and self.api_endpoints["water_quality"] != "https://api.example.com/water-quality":
                # Make real API request
                try:
                    response = requests.get(
                        f"{self.api_endpoints['water_quality']}",
                        params={"station": station_id, "lat": station_info.get("latitude"), "lon": station_info.get("longitude")},
                        headers={"Authorization": f"Bearer {self.api_keys['water_quality']}"},
                        timeout=10  # Timeout after 10 seconds
                    )
                    
                    # Check if request was successful
                    if response.status_code == 200:
                        api_data = response.json()
                        
                        # Format the data as needed
                        data = {
                            "station_id": station_id,
                            "timestamp": datetime.now().isoformat(),
                            "ph": api_data.get("ph", 7.0),
                            "turbidity": api_data.get("turbidity", 0),
                            "dissolved_oxygen": api_data.get("dissolved_oxygen", 0),
                            "conductivity": api_data.get("conductivity", 0),
                            "temperature": api_data.get("temperature", 0),
                            "nitrates": api_data.get("nitrates", 0),
                            "phosphates": api_data.get("phosphates", 0),
                            "data_source": "api"
                        }
                        
                        # Update cache
                        self.data_cache[cache_key] = data
                        self.last_update[cache_key] = current_time
                        
                        return data
                    else:
                        # Log the error but continue to use simulated data as fallback
                        print(f"Water quality API request failed with status {response.status_code}: {response.text}")
                        # Fall through to the simulated data path
                    
                except requests.RequestException as req_error:
                    # Log the error but continue to use simulated data as fallback
                    print(f"Water quality API request error: {str(req_error)}")
                    # Fall through to the simulated data path
            
            # Base values from station info
            base_ph = station_info.get("base_ph", 7.0)
            base_turbidity = station_info.get("base_turbidity", 4.0)
            base_do = station_info.get("base_dissolved_oxygen", 7.0)
            
            # Generate water quality data with some normal variation
            data = {
                "station_id": station_id,
                "timestamp": datetime.now().isoformat(),
                "ph": max(min(base_ph + np.random.normal(0, 0.3), 14), 0),
                "turbidity": max(base_turbidity + np.random.normal(0, 0.5), 0),  # NTU
                "dissolved_oxygen": max(base_do + np.random.normal(0, 0.4), 0),  # mg/L
                "conductivity": 300 + np.random.normal(0, 30),  # µS/cm
                "temperature": 18 + np.random.normal(0, 1),  # Celsius
                "nitrates": 2 + np.random.normal(0, 0.5),  # mg/L
                "phosphates": 0.3 + np.random.normal(0, 0.1),  # mg/L
                "data_source": "simulated"
            }
            
            # Update cache
            self.data_cache[cache_key] = data
            self.last_update[cache_key] = current_time
            
            return data
            
        except Exception as e:
            st.error(f"Error al obtener datos de calidad de agua: {str(e)}")
            return {}
    
    def fetch_water_level_data(self, station_id):
        """
        Obtiene datos de nivel de agua en tiempo real para una estación específica.
        
        Args:
            station_id: ID de la estación de monitoreo
            
        Returns:
            dict: Datos de nivel de agua actualizados
        """
        cache_key = f"water_level_{station_id}"
        
        # Check if we need to update the cache
        current_time = time.time()
        if (cache_key in self.last_update and 
            current_time - self.last_update.get(cache_key, 0) < self.update_intervals["water_levels"]):
            return self.data_cache.get(cache_key, {})
        
        try:
            # Get station info for fallback and supplementary data
            station_info = STATION_INFO.get(station_id, {})
            if not station_info:
                return {}
            
            # Check if we have API credentials
            if self.api_keys["water_levels"] and self.api_endpoints["water_levels"] != "https://api.example.com/water-levels":
                # Make real API request
                try:
                    response = requests.get(
                        f"{self.api_endpoints['water_levels']}",
                        params={"station": station_id, "lat": station_info.get("latitude"), "lon": station_info.get("longitude")},
                        headers={"Authorization": f"Bearer {self.api_keys['water_levels']}"},
                        timeout=10  # Timeout after 10 seconds
                    )
                    
                    # Check if request was successful
                    if response.status_code == 200:
                        api_data = response.json()
                        
                        # Format the data as needed
                        data = {
                            "station_id": station_id,
                            "timestamp": datetime.now().isoformat(),
                            "water_level": api_data.get("water_level", 0),
                            "flow_rate": api_data.get("flow_rate", 0),
                            "water_temperature": api_data.get("temperature", 0),
                            "data_source": "api"
                        }
                        
                        # Update cache
                        self.data_cache[cache_key] = data
                        self.last_update[cache_key] = current_time
                        
                        return data
                    else:
                        # Log the error but continue to use simulated data as fallback
                        print(f"Water level API request failed with status {response.status_code}: {response.text}")
                        # Fall through to the simulated data path
                    
                except requests.RequestException as req_error:
                    # Log the error but continue to use simulated data as fallback
                    print(f"Water level API request error: {str(req_error)}")
                    # Fall through to the simulated data path
            
            # Base value from station info
            base_water_level = station_info.get("base_water_level", 60)
            
            # Generate water level data
            data = {
                "station_id": station_id,
                "timestamp": datetime.now().isoformat(),
                "water_level": max(min(base_water_level + np.random.normal(0, 5), 100), 0),  # Percentage
                "flow_rate": 50 + np.random.normal(0, 10),  # m³/s
                "water_temperature": 15 + np.random.normal(0, 2),  # Celsius
                "data_source": "simulated"
            }
            
            # Update cache
            self.data_cache[cache_key] = data
            self.last_update[cache_key] = current_time
            
            return data
            
        except Exception as e:
            st.error(f"Error al obtener datos de nivel de agua: {str(e)}")
            return {}
    
    def fetch_soil_moisture_data(self, station_id):
        """
        Obtiene datos de humedad del suelo en tiempo real para una estación específica.
        
        Args:
            station_id: ID de la estación de monitoreo
            
        Returns:
            dict: Datos de humedad del suelo actualizados
        """
        cache_key = f"soil_moisture_{station_id}"
        
        # Check if we need to update the cache
        current_time = time.time()
        if (cache_key in self.last_update and 
            current_time - self.last_update.get(cache_key, 0) < self.update_intervals["soil_moisture"]):
            return self.data_cache.get(cache_key, {})
        
        try:
            # Get station info for fallback and supplementary data
            station_info = STATION_INFO.get(station_id, {})
            if not station_info:
                return {}
            
            # Check if we have API credentials
            if self.api_keys["soil_moisture"] and self.api_endpoints["soil_moisture"] != "https://api.example.com/soil":
                # Make real API request
                try:
                    response = requests.get(
                        f"{self.api_endpoints['soil_moisture']}",
                        params={"station": station_id, "lat": station_info.get("latitude"), "lon": station_info.get("longitude")},
                        headers={"Authorization": f"Bearer {self.api_keys['soil_moisture']}"},
                        timeout=10  # Timeout after 10 seconds
                    )
                    
                    # Check if request was successful
                    if response.status_code == 200:
                        api_data = response.json()
                        
                        # Format the data as needed
                        data = {
                            "station_id": station_id,
                            "timestamp": datetime.now().isoformat(),
                            "soil_moisture": api_data.get("moisture", 0),
                            "soil_temperature": api_data.get("temperature", 0),
                            "soil_conductivity": api_data.get("conductivity", 0),
                            "soil_ph": api_data.get("ph", 0),
                            "data_source": "api"
                        }
                        
                        # Update cache
                        self.data_cache[cache_key] = data
                        self.last_update[cache_key] = current_time
                        
                        return data
                    else:
                        # Log the error but continue to use simulated data as fallback
                        print(f"Soil moisture API request failed with status {response.status_code}: {response.text}")
                        # Fall through to the simulated data path
                    
                except requests.RequestException as req_error:
                    # Log the error but continue to use simulated data as fallback
                    print(f"Soil moisture API request error: {str(req_error)}")
                    # Fall through to the simulated data path
            
            # Base values from station info
            base_soil_moisture = station_info.get("base_soil_moisture", 50)
            
            # Generate soil moisture data
            data = {
                "station_id": station_id,
                "timestamp": datetime.now().isoformat(),
                "soil_moisture": max(min(base_soil_moisture + np.random.normal(0, 5), 100), 0),  # Percentage
                "soil_temperature": 15 + np.random.normal(0, 2),  # Celsius
                "soil_conductivity": 200 + np.random.normal(0, 20),  # µS/cm
                "soil_ph": 6.5 + np.random.normal(0, 0.3),  # pH
                "data_source": "simulated"
            }
            
            # Update cache
            self.data_cache[cache_key] = data
            self.last_update[cache_key] = current_time
            
            return data
            
        except Exception as e:
            st.error(f"Error al obtener datos de humedad del suelo: {str(e)}")
            return {}
    
    def get_all_station_data(self, station_id=None):
        """
        Obtiene datos completos para una estación o todas las estaciones.
        Combina datos de todas las APIs disponibles.
        
        Args:
            station_id (opcional): ID de la estación específica o None para todas
            
        Returns:
            DataFrame: Datos combinados de todas las fuentes
        """
        all_data = []
        
        # Determine which stations to fetch
        stations_to_fetch = [station_id] if station_id else STATION_INFO.keys()
        
        for station in stations_to_fetch:
            # Fetch data from all sources
            weather_data = self.fetch_weather_data(station)
            water_quality_data = self.fetch_water_quality_data(station)
            water_level_data = self.fetch_water_level_data(station)
            soil_data = self.fetch_soil_moisture_data(station)
            
            # Combine all data sources
            combined_data = {
                "station_id": station,
                "timestamp": datetime.now(),
                "name": STATION_INFO.get(station, {}).get("name", "Unknown Station"),
                "water_type": STATION_INFO.get(station, {}).get("water_type", "Unknown"),
                "latitude": STATION_INFO.get(station, {}).get("latitude", 0),
                "longitude": STATION_INFO.get(station, {}).get("longitude", 0),
            }
            
            # Add weather data
            if weather_data:
                combined_data.update({
                    "temperature": weather_data.get("temperature"),
                    "humidity": weather_data.get("humidity"),
                    "wind_speed": weather_data.get("wind_speed"),
                    "wind_direction": weather_data.get("wind_direction"),
                    "pressure": weather_data.get("pressure"),
                    "rainfall": weather_data.get("precipitation", 0),
                })
            
            # Add water quality data
            if water_quality_data:
                combined_data.update({
                    "ph": water_quality_data.get("ph"),
                    "turbidity": water_quality_data.get("turbidity"),
                    "dissolved_oxygen": water_quality_data.get("dissolved_oxygen"),
                    "conductivity": water_quality_data.get("conductivity"),
                    "water_temperature": water_quality_data.get("temperature"),
                    "nitrates": water_quality_data.get("nitrates"),
                    "phosphates": water_quality_data.get("phosphates"),
                })
            
            # Add water level data
            if water_level_data:
                combined_data.update({
                    "water_level": water_level_data.get("water_level"),
                    "flow_rate": water_level_data.get("flow_rate"),
                })
            
            # Add soil data
            if soil_data:
                combined_data.update({
                    "soil_moisture": soil_data.get("soil_moisture"),
                    "soil_temperature": soil_data.get("soil_temperature"),
                    "soil_conductivity": soil_data.get("soil_conductivity"),
                    "soil_ph": soil_data.get("soil_ph"),
                })
            
            # Add alert levels based on thresholds
            combined_data.update({
                "water_level_alert": "high" if combined_data.get("water_level", 0) > 80 else 
                                    "medium" if combined_data.get("water_level", 0) > 70 else "low",
                
                "ph_alert": "high" if combined_data.get("ph", 7.0) < 6.0 or combined_data.get("ph", 7.0) > 9.0 else 
                          "medium" if combined_data.get("ph", 7.0) < 6.5 or combined_data.get("ph", 7.0) > 8.5 else "low",
                
                "turbidity_alert": "high" if combined_data.get("turbidity", 0) > 10 else 
                                 "medium" if combined_data.get("turbidity", 0) > 5 else "low",
                
                "dissolved_oxygen_alert": "high" if combined_data.get("dissolved_oxygen", 8.0) < 4 else 
                                        "medium" if combined_data.get("dissolved_oxygen", 8.0) < 6 else "low",
            })
            
            # Calculate risk metrics
            water_level = combined_data.get("water_level", 50)
            rainfall = combined_data.get("rainfall", 0)
            soil_moisture = combined_data.get("soil_moisture", 50)
            
            # Simple risk models
            flood_risk = min(1.0, (water_level / 100) * 0.7 + (rainfall / 50) * 0.3)
            drought_risk = min(1.0, max(0, 1 - (water_level / 100) * 0.5 - (soil_moisture / 100) * 0.5))
            landslide_risk = min(1.0, (soil_moisture / 100) * 0.6 + (rainfall / 50) * 0.4)
            
            combined_data.update({
                "flood_risk": flood_risk,
                "drought_risk": drought_risk,
                "landslide_risk": landslide_risk
            })
            
            # Add to the combined dataset
            all_data.append(combined_data)
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(all_data)
        
        return df
    
    def configure_api_connection(self, api_type, api_url, api_key):
        """
        Configura o actualiza los parámetros de conexión para una API específica.
        
        Args:
            api_type: Tipo de API (weather, water_quality, etc.)
            api_url: Nueva URL para la API
            api_key: Nueva clave de API
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        if api_type not in self.api_endpoints:
            return False
        
        # Update API connection details
        self.api_endpoints[api_type] = api_url
        self.api_keys[api_type] = api_key
        
        # Clear cache for this API type
        cache_keys = [k for k in self.data_cache.keys() if k.startswith(f"{api_type}_")]
        for key in cache_keys:
            if key in self.data_cache:
                del self.data_cache[key]
            if key in self.last_update:
                del self.last_update[key]
        
        return True
    
    def test_api_connection(self, api_type):
        """
        Prueba la conexión a una API específica.
        
        Args:
            api_type: Tipo de API a probar
            
        Returns:
            dict: Resultado de la prueba con status y mensaje
        """
        if api_type not in self.api_endpoints:
            return {"status": "error", "message": "Tipo de API no soportado"}
        
        try:
            url = self.api_endpoints[api_type]
            key = self.api_keys[api_type]
            
            if not url or not url.startswith("http"):
                return {"status": "error", "message": "URL de API inválida"}
            
            if not key:
                return {"status": "warning", "message": "Clave de API no configurada"}
            
            # Check if the API is still the example API
            if url.startswith("https://api.example.com"):
                return {"status": "warning", "message": "API no configurada con un endpoint real"}
            
            # Make a real API connection test
            try:
                # Attempt to connect to the API with a simple request
                response = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    params={"test": "connection"},
                    timeout=5
                )
                
                # Check the response status
                if response.status_code == 200:
                    return {"status": "success", "message": "Conexión exitosa a la API"}
                elif response.status_code == 401 or response.status_code == 403:
                    return {"status": "error", "message": f"Error de autenticación (código {response.status_code})"}
                else:
                    return {"status": "error", "message": f"Error en la conexión a la API (código {response.status_code})"}
                
            except requests.ConnectionError:
                return {"status": "error", "message": "No se pudo conectar al servidor de la API"}
            except requests.Timeout:
                return {"status": "error", "message": "Tiempo de espera agotado al conectar con la API"}
            except requests.RequestException:
                return {"status": "error", "message": "Error en la solicitud a la API"}
            
        except Exception as e:
            return {"status": "error", "message": f"Error al probar la conexión: {str(e)}"}
    
    def get_historical_data(self, station_id, data_type, start_date, end_date):
        """
        Obtiene datos históricos para una estación específica y un tipo de datos.
        
        Args:
            station_id: ID de la estación de monitoreo
            data_type: Tipo de datos (weather, water_quality, etc.)
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            DataFrame: Datos históricos
        """
        # Validate inputs
        if not station_id or station_id not in STATION_INFO:
            return pd.DataFrame()
        
        # Convert date strings to datetime objects if necessary
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate number of days
        days = (end_date - start_date).days + 1
        if days <= 0:
            return pd.DataFrame()
        
        # Initialize data structure
        dates = [start_date + timedelta(days=i) for i in range(days)]
        station_info = STATION_INFO[station_id]
        
        # Check if we can get real historical data from the API
        if data_type in self.api_endpoints and self.api_keys[data_type] and not self.api_endpoints[data_type].startswith("https://api.example.com"):
            try:
                # Format dates for API request
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                
                # Make API request for historical data
                response = requests.get(
                    f"{self.api_endpoints[data_type]}/historical",
                    params={
                        "station": station_id,
                        "start_date": start_str,
                        "end_date": end_str,
                        "lat": station_info.get("latitude"),
                        "lon": station_info.get("longitude")
                    },
                    headers={"Authorization": f"Bearer {self.api_keys[data_type]}"},
                    timeout=15  # Give more time for historical data
                )
                
                # Check if request was successful
                if response.status_code == 200:
                    api_data = response.json()
                    
                    # Process the API response into a DataFrame
                    if isinstance(api_data, list) and len(api_data) > 0:
                        df = pd.DataFrame(api_data)
                        
                        # Ensure expected columns and format
                        if 'timestamp' in df.columns:
                            df['timestamp'] = pd.to_datetime(df['timestamp'])
                            
                            # Add station_id if not present
                            if 'station_id' not in df.columns:
                                df['station_id'] = station_id
                                
                            # Sort by timestamp
                            df = df.sort_values('timestamp')
                            
                            # Log successful API data retrieval
                            print(f"Retrieved {len(df)} historical records from API for {data_type}, station {station_id}")
                            
                            return df
                    else:
                        print(f"API returned empty or invalid data for {data_type} historical request")
                else:
                    print(f"Historical API request failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"Error retrieving historical data from API: {str(e)}")
                # Fall through to simulated data
        
        # If API request failed or isn't configured, generate simulated data
        print(f"Generating simulated historical data for {data_type}, station {station_id}")
        
        # Generate historical data based on the data type
        if data_type == "weather":
            # Base values with seasonal and random variations
            base_temp = 22  # Celsius
            base_rainfall = station_info.get("base_rainfall", 2.0)  # mm
            
            data = {
                "station_id": [station_id] * days,
                "timestamp": dates,
                "temperature": [base_temp + 5*np.sin(i/30*np.pi) + np.random.normal(0, 2) for i in range(days)],
                "rainfall": [max(0, base_rainfall + 3*np.sin(i/30*np.pi) + np.random.exponential(1)) for i in range(days)],
                "humidity": [60 + 20*np.sin(i/30*np.pi) + np.random.normal(0, 5) for i in range(days)],
                "data_source": ["simulated"] * days
            }
            
        elif data_type == "water_quality":
            # Base values from station info with some variation over time
            base_ph = station_info.get("base_ph", 7.0)
            base_turbidity = station_info.get("base_turbidity", 4.0)
            base_do = station_info.get("base_dissolved_oxygen", 7.0)
            
            data = {
                "station_id": [station_id] * days,
                "timestamp": dates,
                "ph": [base_ph + 0.5*np.sin(i/45*np.pi) + np.random.normal(0, 0.2) for i in range(days)],
                "turbidity": [max(0, base_turbidity + np.sin(i/30*np.pi) + np.random.normal(0, 0.5)) for i in range(days)],
                "dissolved_oxygen": [max(0, base_do - 0.8*np.sin(i/60*np.pi) + np.random.normal(0, 0.3)) for i in range(days)],
                "data_source": ["simulated"] * days
            }
            
        elif data_type == "water_level":
            # Base water level with seasonal and random variations
            base_level = station_info.get("base_water_level", 60)
            
            data = {
                "station_id": [station_id] * days,
                "timestamp": dates,
                "water_level": [max(min(base_level + 15*np.sin(i/60*np.pi) + np.random.normal(0, 3), 100), 0) for i in range(days)],
                "flow_rate": [max(50 + 20*np.sin(i/45*np.pi) + np.random.normal(0, 5), 0) for i in range(days)],
                "data_source": ["simulated"] * days
            }
            
        elif data_type == "soil":
            # Base soil moisture with seasonal and random variations
            base_moisture = station_info.get("base_soil_moisture", 50)
            
            data = {
                "station_id": [station_id] * days,
                "timestamp": dates,
                "soil_moisture": [max(min(base_moisture + 20*np.sin(i/45*np.pi) + np.random.normal(0, 4), 100), 0) for i in range(days)],
                "soil_temperature": [15 + 8*np.sin(i/60*np.pi) + np.random.normal(0, 1) for i in range(days)],
                "data_source": ["simulated"] * days
            }
            
        else:
            # Unsupported data type
            return pd.DataFrame()
        
        # Convert to DataFrame
        return pd.DataFrame(data)


# Initialize global API client for use across the application
api_client = ApiClient()

def get_realtime_data(refresh=False):
    """
    Obtiene datos en tiempo real de todas las estaciones de monitoreo.
    
    Args:
        refresh: Si es True, fuerza una actualización de los datos
        
    Returns:
        DataFrame: Datos combinados de todas las fuentes y estaciones
    """
    if refresh:
        # Clear cache to force refresh
        api_client.data_cache = {}
        api_client.last_update = {}
    
    # Get data for all stations
    return api_client.get_all_station_data()

def integrate_realtime_data_with_historical(historical_df, realtime_df=None):
    """
    Integra datos históricos con datos en tiempo real.
    
    Args:
        historical_df: DataFrame con datos históricos
        realtime_df: DataFrame con datos en tiempo real (opcional)
        
    Returns:
        DataFrame: Datos combinados
    """
    if realtime_df is None:
        realtime_df = get_realtime_data()
    
    # Ensure timestamps are datetime objects
    historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'])
    realtime_df['timestamp'] = pd.to_datetime(realtime_df['timestamp'])
    
    # Combine the datasets
    combined_df = pd.concat([historical_df, realtime_df], ignore_index=True, sort=False)
    
    # Remove duplicates based on station_id and timestamp
    combined_df = combined_df.drop_duplicates(subset=['station_id', 'timestamp'], keep='last')
    
    # Sort by timestamp
    combined_df = combined_df.sort_values('timestamp')
    
    return combined_df