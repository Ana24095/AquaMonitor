import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.deepseek_engine import PredictionEngine
from utils.data_from_csv import load_csv_data
from utils.constants import COLORS

def render_predictions():
    """
    Renderiza la vista de predicciones y análisis predictivo.
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Predicciones con IA</h1>
    """, unsafe_allow_html=True)
    
    # Cargar datos históricos
    historical_data = load_csv_data()
    
    if historical_data is None or historical_data.empty:
        st.error("No se pudieron cargar los datos históricos para generar predicciones.")
        return
    
    # Crear instancia del motor de predicciones
    prediction_engine = None
    try:
        prediction_engine = PredictionEngine()
    except Exception as e:
        st.error(f"Error al inicializar el motor de predicciones: {str(e)}")
        st.info("Asegúrate de que la API key de OpenAI esté configurada correctamente. Se utilizará el modo simulado.")
    
    # Interfaz para configurar los días de predicción
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <p style="margin-bottom: 1rem;">
            Este módulo utiliza inteligencia artificial para analizar los datos históricos y generar predicciones
            sobre variables ambientales clave y el riesgo de eventos como inundaciones, sequías o deslizamientos.
        </p>
        """, unsafe_allow_html=True)
    
    with col2:
        days_to_predict = st.selectbox(
            "Días a predecir",
            options=[3, 5, 7, 10, 14],
            index=2,  # Default a 7 días
            help="Selecciona cuántos días en el futuro quieres predecir"
        )
    
    # Verificar si el motor de predicciones está inicializado
    if prediction_engine is None:
        # Crear un motor de predicciones de emergencia
        prediction_engine = PredictionEngine()
    
    # Contenedor para mostrar un spinner mientras se generan las predicciones
    with st.spinner("Generando predicciones con IA..."):
        try:
            # Generar predicciones
            predictions = prediction_engine.generate_predictions(historical_data, days_to_predict)
            
            # Obtener evaluación de riesgo
            risk_assessment = prediction_engine.get_disaster_risk_assessment(predictions)
        except Exception as e:
            st.error(f"Error al generar predicciones: {str(e)}")
            return
    
    # Crear columnas para mostrar los resultados
    col_metrics, col_risk = st.columns([3, 1])
    
    # Mostrar análisis general
    with col_metrics:
        if 'analisis' in predictions:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <h3 style="font-size: 1.2rem; margin-bottom: 0.5rem;">Análisis General</h3>
                <p>{predictions['analisis']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Mostrar evaluación de riesgo
    with col_risk:
        # Determinar color basado en el nivel de riesgo
        risk_colors = {
            "bajo": "#00b8a9",     # Verde aqua
            "moderado": "#ffd166",  # Amarillo
            "alto": "#ef476f",      # Rojo
            "desconocido": "#6c757d" # Gris
        }
        
        risk_color = risk_colors.get(risk_assessment['nivel_riesgo'], "#6c757d")
        
        st.markdown(f"""
        <div style="background-color: {risk_color}; color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;">
            <h3 style="font-size: 1.2rem; margin-bottom: 0.5rem;">Nivel de Riesgo</h3>
            <p style="font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem; text-transform: uppercase;">{risk_assessment['nivel_riesgo']}</p>
            <p>Principal riesgo: {risk_assessment['riesgo_principal']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px;">
            <h3 style="font-size: 1.2rem; margin-bottom: 0.5rem;">Recomendaciones</h3>
            <p>{risk_assessment['recomendaciones']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Mostrar predicciones en una tabla
    st.markdown("""
    <h3 style="font-size: 1.2rem; margin: 1.5rem 0 1rem 0;">Predicciones Diarias</h3>
    """, unsafe_allow_html=True)
    
    # Crear el DataFrame de predicciones
    if 'predicciones' in predictions and len(predictions['predicciones']) > 0:
        pred_df = pd.DataFrame(predictions['predicciones'])
        
        # Convertir fechas
        if 'fecha' in pred_df.columns:
            pred_df['fecha'] = pd.to_datetime(pred_df['fecha'])
        
        # Crear gráficos de predicciones
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de temperatura y nivel de agua
            fig = go.Figure()
            
            # Añadir temperatura
            fig.add_trace(go.Scatter(
                x=pred_df['fecha'],
                y=pred_df['temperatura'],
                mode='lines+markers',
                name='Temperatura (°C)',
                line=dict(color=COLORS['primary'], width=3),
                marker=dict(size=8)
            ))
            
            # Crear un eje y secundario para el nivel de agua
            fig.add_trace(go.Scatter(
                x=pred_df['fecha'],
                y=pred_df['nivel_agua'],
                mode='lines+markers',
                name='Nivel de agua (m)',
                line=dict(color='#3a86ff', width=3, dash='dot'),
                marker=dict(size=8),
                yaxis='y2'
            ))
            
            # Configurar el layout
            fig.update_layout(
                title='Predicción de Temperatura y Nivel de Agua',
                xaxis=dict(title='Fecha'),
                yaxis=dict(
                    title=dict(text='Temperatura (°C)', font=dict(color=COLORS['primary'])),
                    tickfont=dict(color=COLORS['primary'])
                ),
                yaxis2=dict(
                    title=dict(text='Nivel de agua (m)', font=dict(color='#3a86ff')),
                    tickfont=dict(color='#3a86ff'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                margin=dict(l=20, r=20, t=50, b=20),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de pluviosidad
            fig = px.bar(
                pred_df,
                x='fecha',
                y='pluviosidad',
                title='Predicción de Pluviosidad',
                labels={'pluviosidad': 'Pluviosidad (mm)', 'fecha': 'Fecha'},
                color_discrete_sequence=['#43aa8b']
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=50, b=20),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla de predicciones
        # Formatear el DataFrame para mostrar
        display_df = pred_df.copy()
        display_df['fecha'] = display_df['fecha'].dt.strftime('%d/%m/%Y')
        display_df.rename(columns={
            'fecha': 'Fecha',
            'temperatura': 'Temperatura (°C)',
            'pluviosidad': 'Pluviosidad (mm)',
            'nivel_agua': 'Nivel de Agua (m)',
            'justificacion': 'Justificación'
        }, inplace=True)
        
        # Mostrar tabla
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("No se pudieron generar predicciones. Inténtalo de nuevo más tarde.")
    
    # Mostrar gráfico de probabilidades de desastres
    st.markdown("""
    <h3 style="font-size: 1.2rem; margin: 1.5rem 0 1rem 0;">Probabilidad de Desastres</h3>
    """, unsafe_allow_html=True)
    
    # Obtener probabilidades
    probabilities = predictions.get('probabilidades', {})
    
    if probabilities:
        # Crear DataFrame para el gráfico
        prob_df = pd.DataFrame({
            'Tipo': ['Inundación', 'Sequía', 'Deslizamiento'],
            'Probabilidad': [
                probabilities.get('inundacion', 0) * 100,
                probabilities.get('sequia', 0) * 100,
                probabilities.get('deslizamiento', 0) * 100
            ]
        })
        
        # Crear gráfico de barras
        fig = px.bar(
            prob_df,
            x='Tipo',
            y='Probabilidad',
            color='Tipo',
            color_discrete_map={
                'Inundación': '#3a86ff',
                'Sequía': '#ff9e00',
                'Deslizamiento': '#ef476f'
            },
            labels={'Probabilidad': 'Probabilidad (%)', 'Tipo': 'Tipo de Desastre'},
            height=400
        )
        
        # Añadir línea para niveles de riesgo
        fig.add_shape(
            type="line",
            x0=-0.5, y0=30, x1=2.5, y1=30,
            line=dict(color="#ffd166", width=2, dash="dash"),
            name="Riesgo Moderado"
        )
        
        fig.add_shape(
            type="line",
            x0=-0.5, y0=60, x1=2.5, y1=60,
            line=dict(color="#ef476f", width=2, dash="dash"),
            name="Riesgo Alto"
        )
        
        # Añadir texto para los niveles de riesgo
        fig.add_annotation(
            x=2.5, y=30,
            text="Riesgo Moderado",
            showarrow=False,
            font=dict(color="#856404", size=12),
            xanchor="right"
        )
        
        fig.add_annotation(
            x=2.5, y=60,
            text="Riesgo Alto",
            showarrow=False,
            font=dict(color="#721c24", size=12),
            xanchor="right"
        )
        
        fig.update_layout(
            margin=dict(l=20, r=100, t=20, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudieron obtener las probabilidades de desastres.")
    
    # Añadir una sección de explicación sobre el modelo
    with st.expander("¿Cómo funciona el modelo predictivo?"):
        st.markdown("""
        ### Acerca del modelo predictivo
        
        Este modelo utiliza inteligencia artificial avanzada para analizar patrones en los datos históricos de monitoreo ambiental y generar predicciones para los próximos días.
        
        **Metodología:**
        
        1. **Análisis de datos históricos**: El sistema examina los datos recopilados por las estaciones de monitoreo, identificando patrones, tendencias y relaciones entre las variables ambientales.
        
        2. **Procesamiento con IA**: Utilizamos modelos avanzados como DeepSeek, GPT-4o de OpenAI, o Claude de Anthropic para analizar estos patrones y generar predicciones contextualizadas, con DeepSeek como nuestra opción principal.
        
        3. **Validación**: Las predicciones se evalúan en función de los rangos históricos y las tendencias recientes para asegurar su coherencia.
        
        4. **Evaluación de riesgo**: El sistema calcula la probabilidad de eventos como inundaciones, sequías o deslizamientos basándose en los valores previstos de las variables ambientales.
        
        **Limitaciones:**
        
        - El modelo se basa en datos históricos, por lo que eventos extremos sin precedentes pueden ser difíciles de predecir con precisión.
        - Las predicciones a largo plazo tienen mayor incertidumbre que las de corto plazo.
        - Este es un sistema de apoyo a la decisión y no reemplaza el juicio de expertos en situaciones críticas.
        
        **Uso responsable:**
        
        Estas predicciones deben utilizarse como una herramienta informativa adicional en conjunto con otras fuentes de información y el criterio profesional.
        """)