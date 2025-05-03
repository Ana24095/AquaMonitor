import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.constants import COLORS, PARAMETER_DESCRIPTIONS

def render_water_quality(filtered_data):
    """
    Render the water quality view with detailed metrics and visualizations.
    
    Parameters:
    - filtered_data: DataFrame with filtered environmental data
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Water Quality Analysis</h1>
    """, unsafe_allow_html=True)
    
    # Get the latest data for each station
    latest_data = filtered_data.sort_values('timestamp').groupby('station_id').last().reset_index()
    
    # Create tabs for different water quality parameters
    tab1, tab2, tab3, tab4 = st.tabs(["pH", "Turbidity", "Dissolved Oxygen", "Summary"])
    
    with tab1:
        st.subheader("pH Levels Analysis")
        st.markdown("""
        pH measures how acidic or basic water is. The pH scale ranges from 0 to 14, with 7 being neutral.
        A pH less than 7 indicates acidity, whereas a pH greater than 7 indicates a base.
        
        - **Ideal range**: 6.5 - 8.5
        - **Below 6.5**: Too acidic, can be harmful to aquatic life
        - **Above 8.5**: Too alkaline, can be harmful to aquatic life
        """)
        
        # Create pH bar chart by station
        fig = px.bar(
            latest_data,
            x='station_name',
            y='ph',
            color='ph',
            color_continuous_scale=['red', 'green', 'red'],
            range_color=[4, 10],
            labels={'ph': 'pH Level', 'station_name': 'Station'},
            title='Current pH Levels by Station'
        )
        
        # Add reference lines for ideal pH range
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=6.5,
            x1=len(latest_data) - 0.5,
            y1=6.5,
            line=dict(color="green", width=2, dash="dash"),
        )
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=8.5,
            x1=len(latest_data) - 0.5,
            y1=8.5,
            line=dict(color="green", width=2, dash="dash"),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # pH time series
        try:
            # Asegurarse de que hay datos suficientes para crear el pivot
            if 'timestamp' in filtered_data.columns and 'station_name' in filtered_data.columns and 'ph' in filtered_data.columns:
                # Comprobar que no hay valores nulos en las columnas clave
                valid_data = filtered_data.dropna(subset=['timestamp', 'station_name', 'ph'])
                
                if not valid_data.empty:
                    # Reorganizar los datos para el gráfico
                    ph_data = valid_data.pivot(index='timestamp', columns='station_name', values='ph')
                    
                    # Crear el gráfico solo si tenemos datos válidos
                    if not ph_data.empty and len(ph_data.index) > 0 and len(ph_data.columns) > 0:
                        # Convertir el dataframe pivotado a formato largo para plotly
                        ph_data_long = ph_data.reset_index().melt(
                            id_vars='timestamp', 
                            value_vars=ph_data.columns, 
                            var_name='station_name', 
                            value_name='pH'
                        )
                        
                        ph_fig = px.line(
                            ph_data_long,
                            x='timestamp',
                            y='pH',
                            color='station_name',
                            labels={"timestamp": "Time", "pH": "pH Level"},
                            title="pH Level Over Time"
                        )
                    else:
                        # Crear un gráfico vacío con mensaje
                        ph_fig = px.line(
                            x=[],
                            y=[],
                            title="pH Level Over Time (No data available)"
                        )
                else:
                    # Crear un gráfico vacío con mensaje
                    ph_fig = px.line(
                        x=[],
                        y=[],
                        title="pH Level Over Time (No data available)"
                    )
            else:
                # Crear un gráfico vacío con mensaje si faltan columnas
                ph_fig = px.line(
                    x=[],
                    y=[],
                    title="pH Level Over Time (Required columns missing)"
                )
        except Exception as e:
            st.error(f"Error creating pH chart: {str(e)}")
            # Crear un gráfico vacío en caso de error
            ph_fig = px.line(
                x=[],
                y=[],
                title="pH Level Over Time (Error generating chart)"
            )
        
        # Add reference lines for ideal pH range if we have data
        try:
            if 'ph_data' in locals() and not ph_data.empty and len(ph_data.index) > 0:
                min_date = ph_data.index.min()
                max_date = ph_data.index.max()
                
                ph_fig.add_shape(
                    type="line",
                    x0=min_date,
                    y0=6.5,
                    x1=max_date,
                    y1=6.5,
                    line=dict(color="green", width=2, dash="dash"),
                )
                ph_fig.add_shape(
                    type="line",
                    x0=min_date,
                    y0=8.5,
                    x1=max_date,
                    y1=8.5,
                    line=dict(color="green", width=2, dash="dash"),
                )
            else:
                # Si no hay datos, aún queremos mostrar las líneas de referencia en un rango razonable
                ph_fig.add_shape(
                    type="line",
                    x0=0,
                    y0=6.5,
                    x1=1,
                    y1=6.5,
                    line=dict(color="green", width=2, dash="dash"),
                )
                ph_fig.add_shape(
                    type="line",
                    x0=0,
                    y0=8.5,
                    x1=1,
                    y1=8.5,
                    line=dict(color="green", width=2, dash="dash"),
                )
        except Exception as e:
            st.warning(f"No se pudieron agregar líneas de referencia al gráfico de pH: {str(e)}")
        
        st.plotly_chart(ph_fig, use_container_width=True)
    
    with tab2:
        st.subheader("Turbidity Analysis")
        st.markdown("""
        Turbidity measures the cloudiness or haziness of water caused by suspended particles.
        Higher turbidity can indicate erosion, runoff, or other disturbances.
        
        - **Ideal level**: Below 5 NTU (Nephelometric Turbidity Units)
        - **Above 5 NTU**: May affect aquatic ecosystems and water treatment efficacy
        """)
        
        # Create turbidity bar chart by station
        fig = px.bar(
            latest_data,
            x='station_name',
            y='turbidity',
            color='turbidity',
            color_continuous_scale=['green', 'yellow', 'red'],
            range_color=[0, 10],
            labels={'turbidity': 'Turbidity (NTU)', 'station_name': 'Station'},
            title='Current Turbidity Levels by Station'
        )
        
        # Add reference line for ideal turbidity
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=5,
            x1=len(latest_data) - 0.5,
            y1=5,
            line=dict(color="red", width=2, dash="dash"),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Turbidity time series
        try:
            # Asegurarse de que hay datos suficientes para crear el pivot
            if 'timestamp' in filtered_data.columns and 'station_name' in filtered_data.columns and 'turbidity' in filtered_data.columns:
                # Comprobar que no hay valores nulos en las columnas clave
                valid_data = filtered_data.dropna(subset=['timestamp', 'station_name', 'turbidity'])
                
                if not valid_data.empty:
                    # Reorganizar los datos para el gráfico
                    turbidity_data = valid_data.pivot(index='timestamp', columns='station_name', values='turbidity')
                    
                    # Crear el gráfico solo si tenemos datos válidos
                    if not turbidity_data.empty and len(turbidity_data.index) > 0 and len(turbidity_data.columns) > 0:
                        # Convertir el dataframe pivotado a formato largo para plotly
                        turbidity_data_long = turbidity_data.reset_index().melt(
                            id_vars='timestamp', 
                            value_vars=turbidity_data.columns, 
                            var_name='station_name', 
                            value_name='turbidity'
                        )
                        
                        turbidity_fig = px.line(
                            turbidity_data_long,
                            x='timestamp',
                            y='turbidity',
                            color='station_name',
                            labels={"timestamp": "Time", "turbidity": "Turbidity (NTU)"},
                            title="Turbidity Over Time"
                        )
                            
                        # Agregar línea de referencia para la turbidez ideal
                        turbidity_fig.add_shape(
                            type="line",
                            x0=turbidity_data.index.min(),
                            y0=5,
                            x1=turbidity_data.index.max(),
                            y1=5,
                            line=dict(color="red", width=2, dash="dash"),
                        )
                    else:
                        # Crear un gráfico vacío con mensaje
                        turbidity_fig = px.line(
                            x=[],
                            y=[],
                            title="Turbidity Over Time (No data available)"
                        )
                else:
                    # Crear un gráfico vacío con mensaje
                    turbidity_fig = px.line(
                        x=[],
                        y=[],
                        title="Turbidity Over Time (No data available)"
                    )
            else:
                # Crear un gráfico vacío con mensaje si faltan columnas
                turbidity_fig = px.line(
                    x=[],
                    y=[],
                    title="Turbidity Over Time (Required columns missing)"
                )
                
                # Agregar línea de referencia en un rango razonable
                turbidity_fig.add_shape(
                    type="line",
                    x0=0,
                    y0=5,
                    x1=1,
                    y1=5,
                    line=dict(color="red", width=2, dash="dash"),
                )
        except Exception as e:
            st.error(f"Error creating turbidity chart: {str(e)}")
            # Crear un gráfico vacío en caso de error
            turbidity_fig = px.line(
                x=[],
                y=[],
                title="Turbidity Over Time (Error generating chart)"
            )
        
        st.plotly_chart(turbidity_fig, use_container_width=True)
    
    with tab3:
        st.subheader("Dissolved Oxygen Analysis")
        st.markdown("""
        Dissolved oxygen (DO) is the amount of oxygen present in water, crucial for aquatic life.
        Low levels can stress or kill aquatic organisms.
        
        - **Ideal level**: Above 5 mg/L
        - **Below 5 mg/L**: Stressful for most aquatic organisms
        - **Below 2 mg/L**: Fatal to most fish species
        """)
        
        # Create dissolved oxygen bar chart by station
        fig = px.bar(
            latest_data,
            x='station_name',
            y='dissolved_oxygen',
            color='dissolved_oxygen',
            color_continuous_scale=['red', 'yellow', 'green'],
            range_color=[0, 10],
            labels={'dissolved_oxygen': 'Dissolved Oxygen (mg/L)', 'station_name': 'Station'},
            title='Current Dissolved Oxygen Levels by Station'
        )
        
        # Add reference line for minimum DO
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=5,
            x1=len(latest_data) - 0.5,
            y1=5,
            line=dict(color="red", width=2, dash="dash"),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # DO time series
        try:
            # Asegurarse de que hay datos suficientes para crear el pivot
            if 'timestamp' in filtered_data.columns and 'station_name' in filtered_data.columns and 'dissolved_oxygen' in filtered_data.columns:
                # Comprobar que no hay valores nulos en las columnas clave
                valid_data = filtered_data.dropna(subset=['timestamp', 'station_name', 'dissolved_oxygen'])
                
                if not valid_data.empty:
                    # Reorganizar los datos para el gráfico
                    do_data = valid_data.pivot(index='timestamp', columns='station_name', values='dissolved_oxygen')
                    
                    # Crear el gráfico solo si tenemos datos válidos
                    if not do_data.empty and len(do_data.index) > 0 and len(do_data.columns) > 0:
                        # Convertir el dataframe pivotado a formato largo para plotly
                        do_data_long = do_data.reset_index().melt(
                            id_vars='timestamp', 
                            value_vars=do_data.columns, 
                            var_name='station_name', 
                            value_name='dissolved_oxygen'
                        )
                        
                        do_fig = px.line(
                            do_data_long,
                            x='timestamp',
                            y='dissolved_oxygen',
                            color='station_name',
                            labels={"timestamp": "Time", "dissolved_oxygen": "Dissolved Oxygen (mg/L)"},
                            title="Dissolved Oxygen Over Time"
                        )
                            
                        # Agregar línea de referencia para DO mínimo
                        do_fig.add_shape(
                            type="line",
                            x0=do_data.index.min(),
                            y0=5,
                            x1=do_data.index.max(),
                            y1=5,
                            line=dict(color="red", width=2, dash="dash"),
                        )
                    else:
                        # Crear un gráfico vacío con mensaje
                        do_fig = px.line(
                            x=[],
                            y=[],
                            title="Dissolved Oxygen Over Time (No data available)"
                        )
                else:
                    # Crear un gráfico vacío con mensaje
                    do_fig = px.line(
                        x=[],
                        y=[],
                        title="Dissolved Oxygen Over Time (No data available)"
                    )
            else:
                # Crear un gráfico vacío con mensaje si faltan columnas
                do_fig = px.line(
                    x=[],
                    y=[],
                    title="Dissolved Oxygen Over Time (Required columns missing)"
                )
                
                # Agregar línea de referencia en un rango razonable
                do_fig.add_shape(
                    type="line",
                    x0=0,
                    y0=5,
                    x1=1,
                    y1=5,
                    line=dict(color="red", width=2, dash="dash"),
                )
        except Exception as e:
            st.error(f"Error creating dissolved oxygen chart: {str(e)}")
            # Crear un gráfico vacío en caso de error
            do_fig = px.line(
                x=[],
                y=[],
                title="Dissolved Oxygen Over Time (Error generating chart)"
            )
        
        st.plotly_chart(do_fig, use_container_width=True)
    
    with tab4:
        st.subheader("Water Quality Overview")
        
        # Create a heatmap of water quality parameters by station
        # Reshape data for heatmap
        heatmap_data = latest_data.copy()
        
        # Normalize values between 0 and 1 for comparison
        # pH: optimal is 7, so normalize based on distance from 7
        heatmap_data['ph_norm'] = 1 - abs(heatmap_data['ph'] - 7) / 7
        
        # Turbidity: lower is better (0-10 scale)
        heatmap_data['turbidity_norm'] = 1 - heatmap_data['turbidity'] / 10
        
        # Dissolved oxygen: higher is better (0-10 scale)
        heatmap_data['do_norm'] = heatmap_data['dissolved_oxygen'] / 10
        
        # Create columns for parameters and values
        param_data = []
        for _, row in heatmap_data.iterrows():
            param_data.append({
                'Station': row['station_name'],
                'Parameter': 'pH',
                'Normalized Value': row['ph_norm'],
                'Actual Value': row['ph']
            })
            param_data.append({
                'Station': row['station_name'],
                'Parameter': 'Turbidity',
                'Normalized Value': row['turbidity_norm'],
                'Actual Value': row['turbidity']
            })
            param_data.append({
                'Station': row['station_name'],
                'Parameter': 'Dissolved Oxygen',
                'Normalized Value': row['do_norm'],
                'Actual Value': row['dissolved_oxygen']
            })
        
        param_df = pd.DataFrame(param_data)
        
        # Create heatmap
        fig = px.imshow(
            param_df.pivot(index='Parameter', columns='Station', values='Normalized Value'),
            color_continuous_scale=['red', 'yellow', 'green'],
            labels=dict(x="Station", y="Parameter", color="Quality Score"),
            title="Water Quality Parameters by Station (Normalized)"
        )
        
        # Add actual values as text annotations
        values_matrix = param_df.pivot(index='Parameter', columns='Station', values='Actual Value').values
        for i in range(len(fig.data[0].z)):
            for j in range(len(fig.data[0].z[0])):
                fig.add_annotation(
                    x=j,
                    y=i,
                    text=f"{values_matrix[i][j]:.1f}",
                    showarrow=False,
                    font=dict(color="black")
                )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Overall water quality score by station
        st.subheader("Overall Water Quality Score")
        
        # Calculate an overall water quality score (average of normalized values)
        quality_scores = []
        for station in heatmap_data['station_name'].unique():
            station_data = heatmap_data[heatmap_data['station_name'] == station]
            score = (station_data['ph_norm'].values[0] + 
                     station_data['turbidity_norm'].values[0] + 
                     station_data['do_norm'].values[0]) / 3 * 100
            quality_scores.append({
                'Station': station,
                'Quality Score': score
            })
        
        quality_df = pd.DataFrame(quality_scores)
        
        # Create a gauge chart for each station
        cols = st.columns(len(quality_df))
        for i, (_, row) in enumerate(quality_df.iterrows()):
            with cols[i]:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=row['Quality Score'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': row['Station']},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': COLORS['primary']},
                        'steps': [
                            {'range': [0, 50], 'color': "red"},
                            {'range': [50, 75], 'color': "yellow"},
                            {'range': [75, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': row['Quality Score']
                        }
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)
        
        # Agregar un separador visual
        st.markdown("---")
        
        # Sección de chatbot de análisis de calidad del agua
        st.subheader("💬 Water Quality Assistant")
        
        # Inicializar la engine de predicción para usar el chatbot
        from utils.deepseek_engine import PredictionEngine
        
        # Creamos una instancia de PredictionEngine solo si no existe en la session_state
        if 'prediction_engine' not in st.session_state:
            st.session_state.prediction_engine = PredictionEngine()
        
        # Columnas para análisis automático y chat
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Automatic Analysis")
            
            if st.button("Generate Water Quality Analysis"):
                with st.spinner("Analyzing water quality data..."):
                    analysis = st.session_state.prediction_engine.analyze_water_quality(filtered_data)
                    st.session_state.last_analysis = analysis
            
            # Mostrar el último análisis generado si existe
            if 'last_analysis' in st.session_state:
                st.markdown(st.session_state.last_analysis)
            else:
                st.info("Click the button above to generate an expert analysis of the current water quality data.")
        
        with col2:
            st.subheader("Ask About Water Quality")
            
            # Inicializar el historial de chat si no existe
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Mostrar historial de chat
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_history:
                    if message['role'] == 'user':
                        st.markdown(f"<div style='background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>Assistant:</strong> {message['content']}</div>", unsafe_allow_html=True)
            
            # Input para nuevas preguntas
            user_query = st.text_input("Ask a question about water quality", key="water_quality_query")
            
            # Botón para enviar la pregunta
            if st.button("Send", key="send_water_quality_query"):
                if user_query:
                    # Agregar la pregunta al historial
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': user_query
                    })
                    
                    # Obtener respuesta del modelo
                    with st.spinner("Generating response..."):
                        response = st.session_state.prediction_engine.chat_about_water_quality(filtered_data, user_query)
                    
                    # Agregar la respuesta al historial
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    
                    # Recargar la página para mostrar la respuesta
                    st.rerun()
            
            # Botón para limpiar el historial
            if st.button("Clear Chat History", key="clear_water_quality_chat"):
                st.session_state.chat_history = []
                st.rerun()
