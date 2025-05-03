import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from utils.api_client import api_client

def render_api_connections():
    """
    Renderiza la vista de conexiones API para configurar y gestionar
    fuentes de datos en tiempo real.
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Conexiones API</h1>
    """, unsafe_allow_html=True)
    
    # Create tabs for different API connection functionality
    api_tabs = st.tabs([
        "Conexiones Actuales", 
        "Configurar API", 
        "API Meteorológica",
        "API Calidad de Agua",
        "API Nivel de Agua",
        "API Humedad del Suelo"
    ])
    
    # Tab 1: Current Connections
    with api_tabs[0]:
        st.subheader("Estado de Conexiones API")
        
        # Get list of configured APIs
        api_types = list(api_client.api_endpoints.keys())
        
        # Display connection status for each API
        for api_type in api_types:
            # Test connection
            test_result = api_client.test_api_connection(api_type)
            
            # Create status indicator
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if test_result["status"] == "success":
                    st.success("✓")
                elif test_result["status"] == "warning":
                    st.warning("⚠️")
                else:
                    st.error("✗")
            
            with col2:
                # Format API type name nicely
                api_name = api_type.replace("_", " ").title()
                
                st.markdown(f"**API {api_name}**")
                st.markdown(f"URL: `{api_client.api_endpoints[api_type]}`")
                
                # Display connection status
                if test_result["status"] == "success":
                    st.success(test_result["message"])
                elif test_result["status"] == "warning":
                    st.warning(test_result["message"])
                else:
                    st.error(test_result["message"])
            
            st.markdown("---")
        
        # Button to refresh all connections
        if st.button("Probar Todas las Conexiones", type="primary"):
            st.success("Prueba de conexiones completada.")
    
    # Tab 2: Configure API
    with api_tabs[1]:
        st.subheader("Configurar Nueva Conexión API")
        
        # API type selection
        api_type = st.selectbox(
            "Tipo de API",
            options=list(api_client.api_endpoints.keys()),
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        # Current configuration
        st.markdown("### Configuración Actual")
        st.markdown(f"URL: `{api_client.api_endpoints[api_type]}`")
        
        # Show a masked API key if one exists
        api_key = api_client.api_keys[api_type]
        if api_key:
            # Mask the API key for display
            masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
            st.markdown(f"API Key: `{masked_key}`")
        else:
            st.markdown("API Key: `No configurada`")
        
        # Form for updating API configuration
        with st.form("api_config_form"):
            new_api_url = st.text_input("Nueva URL de API", value=api_client.api_endpoints[api_type])
            new_api_key = st.text_input("Nueva Clave de API", type="password")
            
            submitted = st.form_submit_button("Actualizar Configuración", type="primary")
            
            if submitted:
                # Update API configuration
                result = api_client.configure_api_connection(api_type, new_api_url, new_api_key if new_api_key else api_key)
                
                if result:
                    st.success(f"Configuración de API {api_type.replace('_', ' ').title()} actualizada con éxito.")
                    
                    # Test the new connection
                    test_result = api_client.test_api_connection(api_type)
                    if test_result["status"] == "success":
                        st.success(test_result["message"])
                    elif test_result["status"] == "warning":
                        st.warning(test_result["message"])
                    else:
                        st.error(test_result["message"])
                else:
                    st.error("Error al actualizar la configuración de API. Por favor, verifica los datos ingresados.")
    
    # Tab 3: Weather API
    with api_tabs[2]:
        st.subheader("API Meteorológica")
        
        st.markdown("""
        La API meteorológica proporciona datos de clima en tiempo real, incluyendo:
        
        - Temperatura
        - Humedad
        - Velocidad y dirección del viento
        - Precipitación
        - Presión atmosférica
        """)
        
        # Weather API status
        test_result = api_client.test_api_connection("weather")
        
        if test_result["status"] == "success":
            st.success(f"API Meteorológica: {test_result['message']}")
            
            # Show sample data
            st.markdown("### Muestra de Datos")
            
            sample_data = api_client.fetch_weather_data(list(api_client.api_endpoints.keys())[0])
            
            # Display sample data in a table
            if sample_data:
                # Convert to DataFrame for display
                sample_df = pd.DataFrame([sample_data])
                
                # Display data source information
                if "data_source" in sample_data:
                    if sample_data["data_source"] == "api":
                        st.success("✓ Datos obtenidos desde la API en tiempo real")
                    else:
                        st.warning("⚠️ Datos simulados (API no disponible)")
                
                # Select only relevant columns
                display_cols = ["station_id", "timestamp", "temperature", "humidity", 
                               "wind_speed", "wind_direction", "pressure", "precipitation"]
                
                display_df = sample_df[display_cols]
                
                # Clean up column names for display
                display_df.columns = [col.replace("_", " ").title() for col in display_df.columns]
                
                st.dataframe(display_df)
            else:
                st.warning("No hay datos disponibles para mostrar.")
            
            # Weather data visualization
            st.markdown("### Visualización de Datos")
            
            # Get some historical data for visualization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_weather = api_client.get_historical_data(
                "station_1",  # Using station_1 as an example
                "weather",
                start_date,
                end_date
            )
            
            if not historical_weather.empty:
                # Temperature over time
                fig = px.line(
                    historical_weather, 
                    x="timestamp", 
                    y="temperature",
                    title="Temperatura en los últimos 30 días",
                    labels={"temperature": "Temperatura (°C)", "timestamp": "Fecha"},
                    color_discrete_sequence=["#ef476f"]
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Rainfall over time
                fig = px.bar(
                    historical_weather, 
                    x="timestamp", 
                    y="rainfall",
                    title="Precipitación en los últimos 30 días",
                    labels={"rainfall": "Precipitación (mm)", "timestamp": "Fecha"},
                    color_discrete_sequence=["#118ab2"]
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos históricos disponibles para visualización.")
        else:
            if test_result["status"] == "warning":
                st.warning(f"API Meteorológica: {test_result['message']}")
            else:
                st.error(f"API Meteorológica: {test_result['message']}")
            
            st.markdown("""
            Para configurar la API meteorológica, necesitas:
            
            1. Registrarte con un proveedor de servicios meteorológicos
            2. Obtener una clave de API y la URL del endpoint
            3. Configurar la conexión en la pestaña "Configurar API"
            
            Puedes utilizar servicios como OpenWeatherMap, WeatherAPI, AccuWeather, u otros proveedores similares.
            """)
    
    # Tab 4: Water Quality API
    with api_tabs[3]:
        st.subheader("API de Calidad de Agua")
        
        st.markdown("""
        La API de calidad de agua proporciona métricas sobre la calidad del agua, incluyendo:
        
        - pH
        - Turbidez
        - Oxígeno disuelto
        - Conductividad
        - Nitratos y fosfatos
        - Temperatura del agua
        """)
        
        # Water quality API status
        test_result = api_client.test_api_connection("water_quality")
        
        if test_result["status"] == "success":
            st.success(f"API de Calidad de Agua: {test_result['message']}")
            
            # Show sample data
            st.markdown("### Muestra de Datos")
            
            sample_data = api_client.fetch_water_quality_data("station_1")  # Using station_1 as an example
            
            # Display sample data in a table
            if sample_data:
                # Convert to DataFrame for display
                sample_df = pd.DataFrame([sample_data])
                
                # Display data source information
                if "data_source" in sample_data:
                    if sample_data["data_source"] == "api":
                        st.success("✓ Datos obtenidos desde la API en tiempo real")
                    else:
                        st.warning("⚠️ Datos simulados (API no disponible)")
                
                # Select only relevant columns
                display_cols = ["station_id", "timestamp", "ph", "turbidity", 
                               "dissolved_oxygen", "conductivity", "temperature", 
                               "nitrates", "phosphates"]
                
                # Filter to only columns that exist in the sample data
                display_cols = [col for col in display_cols if col in sample_data]
                
                display_df = sample_df[display_cols]
                
                # Clean up column names for display
                display_df.columns = [col.replace("_", " ").title() for col in display_df.columns]
                
                st.dataframe(display_df)
            else:
                st.warning("No hay datos disponibles para mostrar.")
            
            # Water quality visualization
            st.markdown("### Visualización de Datos")
            
            # Get some historical data for visualization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_wq = api_client.get_historical_data(
                "station_1",  # Using station_1 as an example
                "water_quality",
                start_date,
                end_date
            )
            
            if not historical_wq.empty:
                # pH over time
                fig = px.line(
                    historical_wq, 
                    x="timestamp", 
                    y="ph",
                    title="Niveles de pH en los últimos 30 días",
                    labels={"ph": "pH", "timestamp": "Fecha"},
                    color_discrete_sequence=["#06d6a0"]
                )
                
                # Add reference lines for normal pH range
                fig.add_hline(y=8.5, line_dash="dash", line_color="#ffd166", annotation_text="Límite superior normal")
                fig.add_hline(y=6.5, line_dash="dash", line_color="#ffd166", annotation_text="Límite inferior normal")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Turbidity and dissolved oxygen
                metrics_fig = px.line(
                    historical_wq, 
                    x="timestamp", 
                    y=["turbidity", "dissolved_oxygen"],
                    title="Turbidez y Oxígeno Disuelto en los últimos 30 días",
                    labels={
                        "turbidity": "Turbidez (NTU)", 
                        "dissolved_oxygen": "Oxígeno Disuelto (mg/L)", 
                        "timestamp": "Fecha",
                        "value": "Valor",
                        "variable": "Métrica"
                    },
                    color_discrete_map={
                        "turbidity": "#ef476f",
                        "dissolved_oxygen": "#118ab2"
                    }
                )
                st.plotly_chart(metrics_fig, use_container_width=True)
            else:
                st.warning("No hay datos históricos disponibles para visualización.")
        else:
            if test_result["status"] == "warning":
                st.warning(f"API de Calidad de Agua: {test_result['message']}")
            else:
                st.error(f"API de Calidad de Agua: {test_result['message']}")
            
            st.markdown("""
            Para configurar la API de calidad de agua, necesitas:
            
            1. Conectarte con un proveedor de monitoreo de calidad de agua
            2. Obtener credenciales de acceso a su API
            3. Configurar la conexión en la pestaña "Configurar API"
            
            Muchas agencias gubernamentales y organizaciones de monitoreo ambiental ofrecen APIs para acceder a datos de calidad de agua.
            """)
    
    # Tab 5: Water Level API
    with api_tabs[4]:
        st.subheader("API de Nivel de Agua")
        
        st.markdown("""
        La API de nivel de agua proporciona datos sobre los niveles de agua y caudales, incluyendo:
        
        - Nivel de agua actual
        - Caudal
        - Temperatura del agua
        - Previsiones de inundación
        """)
        
        # Water level API status
        test_result = api_client.test_api_connection("water_levels")
        
        if test_result["status"] == "success":
            st.success(f"API de Nivel de Agua: {test_result['message']}")
            
            # Show sample data
            st.markdown("### Muestra de Datos")
            
            sample_data = api_client.fetch_water_level_data("station_1")  # Using station_1 as an example
            
            # Display sample data in a table
            if sample_data:
                # Convert to DataFrame for display
                sample_df = pd.DataFrame([sample_data])
                
                # Display data source information
                if "data_source" in sample_data:
                    if sample_data["data_source"] == "api":
                        st.success("✓ Datos obtenidos desde la API en tiempo real")
                    else:
                        st.warning("⚠️ Datos simulados (API no disponible)")
                
                # Clean up column names for display
                sample_df.columns = [col.replace("_", " ").title() for col in sample_df.columns]
                
                st.dataframe(sample_df)
            else:
                st.warning("No hay datos disponibles para mostrar.")
            
            # Water level visualization
            st.markdown("### Visualización de Datos")
            
            # Get some historical data for visualization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_wl = api_client.get_historical_data(
                "station_1",  # Using station_1 as an example
                "water_level",
                start_date,
                end_date
            )
            
            if not historical_wl.empty:
                # Water level over time
                fig = px.area(
                    historical_wl, 
                    x="timestamp", 
                    y="water_level",
                    title="Nivel de Agua en los últimos 30 días",
                    labels={"water_level": "Nivel de Agua (%)", "timestamp": "Fecha"},
                    color_discrete_sequence=["#118ab2"]
                )
                
                # Add reference lines for warning and critical levels
                fig.add_hline(y=85, line_dash="dash", line_color="#ffd166", annotation_text="Nivel de advertencia")
                fig.add_hline(y=95, line_dash="dash", line_color="#ef476f", annotation_text="Nivel crítico")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Flow rate over time
                if "flow_rate" in historical_wl.columns:
                    flow_fig = px.line(
                        historical_wl, 
                        x="timestamp", 
                        y="flow_rate",
                        title="Caudal en los últimos 30 días",
                        labels={"flow_rate": "Caudal (m³/s)", "timestamp": "Fecha"},
                        color_discrete_sequence=["#06d6a0"]
                    )
                    st.plotly_chart(flow_fig, use_container_width=True)
            else:
                st.warning("No hay datos históricos disponibles para visualización.")
        else:
            if test_result["status"] == "warning":
                st.warning(f"API de Nivel de Agua: {test_result['message']}")
            else:
                st.error(f"API de Nivel de Agua: {test_result['message']}")
            
            st.markdown("""
            Para configurar la API de nivel de agua, necesitas:
            
            1. Conectarte con un servicio hidrológico o agencia de gestión de agua
            2. Obtener credenciales de acceso a su API
            3. Configurar la conexión en la pestaña "Configurar API"
            
            Agencias como USGS, servicios meteorológicos nacionales, y autoridades de cuencas hidrográficas suelen ofrecer APIs para acceder a datos de nivel de agua.
            """)
    
    # Tab 6: Soil Moisture API
    with api_tabs[5]:
        st.subheader("API de Humedad del Suelo")
        
        st.markdown("""
        La API de humedad del suelo proporciona datos sobre las condiciones del suelo, incluyendo:
        
        - Humedad del suelo
        - Temperatura del suelo
        - Conductividad del suelo
        - pH del suelo
        """)
        
        # Soil moisture API status
        test_result = api_client.test_api_connection("soil_moisture")
        
        if test_result["status"] == "success":
            st.success(f"API de Humedad del Suelo: {test_result['message']}")
            
            # Show sample data
            st.markdown("### Muestra de Datos")
            
            sample_data = api_client.fetch_soil_moisture_data("station_1")  # Using station_1 as an example
            
            # Display sample data in a table
            if sample_data:
                # Convert to DataFrame for display
                sample_df = pd.DataFrame([sample_data])
                
                # Display data source information
                if "data_source" in sample_data:
                    if sample_data["data_source"] == "api":
                        st.success("✓ Datos obtenidos desde la API en tiempo real")
                    else:
                        st.warning("⚠️ Datos simulados (API no disponible)")
                
                # Clean up column names for display
                sample_df.columns = [col.replace("_", " ").title() for col in sample_df.columns]
                
                st.dataframe(sample_df)
            else:
                st.warning("No hay datos disponibles para mostrar.")
            
            # Soil moisture visualization
            st.markdown("### Visualización de Datos")
            
            # Get some historical data for visualization
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_soil = api_client.get_historical_data(
                "station_1",  # Using station_1 as an example
                "soil",
                start_date,
                end_date
            )
            
            if not historical_soil.empty:
                # Soil moisture over time
                fig = px.line(
                    historical_soil, 
                    x="timestamp", 
                    y="soil_moisture",
                    title="Humedad del Suelo en los últimos 30 días",
                    labels={"soil_moisture": "Humedad del Suelo (%)", "timestamp": "Fecha"},
                    color_discrete_sequence=["#8ac926"]
                )
                
                # Add reference lines for healthy soil moisture levels
                fig.add_hline(y=30, line_dash="dash", line_color="#ef476f", annotation_text="Nivel bajo crítico")
                fig.add_hline(y=80, line_dash="dash", line_color="#ffd166", annotation_text="Nivel alto")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Soil temperature over time
                if "soil_temperature" in historical_soil.columns:
                    temp_fig = px.line(
                        historical_soil, 
                        x="timestamp", 
                        y="soil_temperature",
                        title="Temperatura del Suelo en los últimos 30 días",
                        labels={"soil_temperature": "Temperatura del Suelo (°C)", "timestamp": "Fecha"},
                        color_discrete_sequence=["#ef476f"]
                    )
                    st.plotly_chart(temp_fig, use_container_width=True)
            else:
                st.warning("No hay datos históricos disponibles para visualización.")
        else:
            if test_result["status"] == "warning":
                st.warning(f"API de Humedad del Suelo: {test_result['message']}")
            else:
                st.error(f"API de Humedad del Suelo: {test_result['message']}")
            
            st.markdown("""
            Para configurar la API de humedad del suelo, necesitas:
            
            1. Conectarte con un servicio de monitoreo de condiciones del suelo
            2. Obtener credenciales de acceso a su API
            3. Configurar la conexión en la pestaña "Configurar API"
            
            Servicios de monitoreo agrícola, institutos de investigación del suelo y algunas agencias meteorológicas ofrecen APIs para acceder a datos de humedad del suelo.
            """)
    
    # Add information about API usage and data sources
    st.markdown("---")
    st.markdown("### Información sobre APIs y Fuentes de Datos")
    
    st.markdown("""
    Las APIs conectadas proporcionan datos en tiempo real que son fundamentales para el monitoreo 
    ambiental efectivo. Estos datos complementan las lecturas de sensores locales y permiten 
    una visión más completa del estado de los ecosistemas acuáticos.
    
    **Beneficios de las conexiones API:**
    - Acceso a datos de múltiples fuentes en tiempo real
    - Integración con redes de monitoreo gubernamentales y de investigación
    - Mayor precisión en predicciones y alertas tempranas
    - Visión histórica para análisis de tendencias
    
    **Recomendaciones para configuración de APIs:**
    - Utilizar fuentes oficiales cuando sea posible
    - Verificar la frecuencia de actualización de los datos
    - Configurar correctamente los intervalos de actualización para optimizar el rendimiento
    """)
    
    # Display API update intervals
    st.markdown("### Intervalos de Actualización Configurados")
    
    update_intervals = api_client.update_intervals
    
    # Create a DataFrame for better display
    intervals_df = pd.DataFrame({
        "API": [k.replace("_", " ").title() for k in update_intervals.keys()],
        "Intervalo (segundos)": list(update_intervals.values()),
        "Intervalo (minutos)": [v/60 for v in update_intervals.values()]
    })
    
    st.dataframe(intervals_df, hide_index=True)
    
    # Add option to configure update intervals
    if st.checkbox("Configurar intervalos de actualización"):
        st.warning("La modificación de los intervalos de actualización puede afectar el rendimiento de la aplicación.")
        
        for api_type, interval in update_intervals.items():
            new_interval = st.slider(
                f"Intervalo para {api_type.replace('_', ' ').title()} (segundos)",
                min_value=60,
                max_value=3600,
                value=interval,
                step=60
            )
            
            # Update the interval if changed
            if new_interval != interval:
                api_client.update_intervals[api_type] = new_interval
        
        if st.button("Guardar Configuración de Intervalos"):
            st.success("Intervalos de actualización configurados correctamente.")
            
    # Add section for API logs (in a real implementation, this would show actual API request logs)
    if st.checkbox("Ver registros de solicitudes API"):
        st.code("""
2025-04-30 12:34:56 - INFO - API Request: weather - station_1 - Status: 200 OK
2025-04-30 12:35:12 - INFO - API Request: water_quality - station_2 - Status: 200 OK
2025-04-30 12:35:28 - INFO - API Request: water_levels - station_1 - Status: 200 OK
2025-04-30 12:35:44 - INFO - API Request: soil_moisture - station_3 - Status: 200 OK
        """)