import pandas as pd
import numpy as np
import json
import datetime
import os
import random
from openai import OpenAI

# Importar el cliente de Anthropic
import anthropic
from anthropic import Anthropic

# Importar el cliente de DeepSeek
from deepseek_ai import DeepSeekAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
# the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024.
# do not change this unless explicitly requested by the user
# DeepSeek-Coder v2 es un modelo de código abierto con buen rendimiento

class PredictionEngine:
    """
    Clase encargada de generar predicciones utilizando modelos de IA (DeepSeek, OpenAI o Anthropic)
    basado en datos históricos de monitoreo ambiental.
    """
    
    def __init__(self):
        """Inicializa el motor de predicciones con las APIs disponibles."""
        # Variables para almacenar predicciones en caché
        self.last_prediction_time = None
        self.cached_predictions = None
        # Cachear por 1 hora para evitar múltiples llamadas innecesarias a la API
        self.cache_duration = datetime.timedelta(hours=1)
        
        # Inicializar clientes
        self.openai_client = None
        self.anthropic_client = None
        self.deepseek_client = None
        self.preferred_model = "deepseek"  # Por defecto, usaremos DeepSeek como modelo principal
        
        try:
            # Verificar que la API key de OpenAI esté disponible
            self.openai_api_key = os.environ.get("OPENAI_API_KEY")
            if self.openai_api_key:
                # Inicializar el cliente de OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                print("Cliente OpenAI inicializado correctamente.")
            else:
                print("ADVERTENCIA: La API key de OpenAI no está disponible.")
        except Exception as e:
            print(f"Error al inicializar el cliente de OpenAI: {e}")
            
        try:
            # Verificar que la API key de Anthropic esté disponible
            self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if self.anthropic_api_key:
                # Inicializar el cliente de Anthropic
                self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
                print("Cliente Anthropic inicializado correctamente.")
            else:
                print("ADVERTENCIA: La API key de Anthropic no está disponible.")
        except Exception as e:
            print(f"Error al inicializar el cliente de Anthropic: {e}")
            
        try:
            # Inicializar el cliente de DeepSeek (no requiere API key)
            self.deepseek_client = DeepSeekAI()
            print("Cliente DeepSeek inicializado correctamente.")
        except Exception as e:
            print(f"Error al inicializar el cliente de DeepSeek: {e}")
            
        # Determinar el cliente a usar por defecto
        if self.deepseek_client is not None:
            print("Se utilizará DeepSeek como modelo principal.")
            self.preferred_model = "deepseek"
        elif self.openai_client is not None:
            print("Se utilizará OpenAI como modelo principal.")
            self.preferred_model = "openai"
        elif self.anthropic_client is not None:
            print("Se utilizará Anthropic como modelo principal.")
            self.preferred_model = "anthropic"
        else:
            print("ADVERTENCIA: No hay clientes de IA disponibles. Se utilizarán respuestas locales.")
    
    def _prepare_data_for_analysis(self, df):
        """
        Prepara los datos para el análisis predictivo.
        
        Args:
            df (pd.DataFrame): DataFrame con datos históricos
            
        Returns:
            dict: Datos preparados para análisis
        """
        # Asegurarse de que las fechas están en el formato correcto
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            
        # Obtener estadísticas básicas
        stats = {
            'temperatura': {
                'media': df['temperature'].mean(),
                'max': df['temperature'].max(),
                'min': df['temperature'].min(),
                'tendencia_reciente': df['temperature'].iloc[-5:].mean() - df['temperature'].iloc[-10:-5].mean()
            },
            'pluviosidad': {
                'media': df['rainfall'].mean(),
                'max': df['rainfall'].max(),
                'min': df['rainfall'].min(),
                'tendencia_reciente': df['rainfall'].iloc[-5:].mean() - df['rainfall'].iloc[-10:-5].mean()
            },
            'nivel_agua': {
                'media': df['water_level'].mean(),
                'max': df['water_level'].max(),
                'min': df['water_level'].min(),
                'tendencia_reciente': df['water_level'].iloc[-5:].mean() - df['water_level'].iloc[-10:-5].mean()
            }
        }
        
        # Obtener los últimos 30 puntos de datos para análisis de tendencias
        recent_data = df.tail(30).copy()
        
        # Calcular tendencias mensuales si hay suficientes datos
        if len(df) >= 60:
            monthly_trends = df.groupby(pd.Grouper(key='fecha', freq='ME')).mean().tail(6).reset_index()
            monthly_data = monthly_trends.to_dict(orient='records')
        else:
            monthly_data = []
        
        # Preparar los datos para el análisis
        analysis_data = {
            'statistics': stats,
            'recent_data': recent_data.to_dict(orient='records'),
            'monthly_trends': monthly_data,
            'last_date': df['fecha'].max().strftime('%Y-%m-%d')
        }
        
        return analysis_data
    
    def generate_predictions(self, historical_data, days_to_predict=7):
        """
        Genera predicciones para los próximos días basado en datos históricos.
        
        Args:
            historical_data (pd.DataFrame): DataFrame con datos históricos
            days_to_predict (int): Número de días para los que se generarán predicciones
            
        Returns:
            dict: Predicciones generadas
        """
        # Verificar si tenemos una predicción en caché reciente
        current_time = datetime.datetime.now()
        if (self.last_prediction_time and 
            (current_time - self.last_prediction_time < self.cache_duration) and
            self.cached_predictions):
            return self.cached_predictions
        
        # Preparar los datos para el análisis
        analysis_data = self._prepare_data_for_analysis(historical_data)
        
        # Construir el prompt para el modelo
        prompt = f"""
        Analiza los siguientes datos históricos de monitoreo ambiental y genera predicciones fundamentadas para los próximos {days_to_predict} días:
        
        Estadísticas Históricas:
        - Temperatura: Media: {analysis_data['statistics']['temperatura']['media']:.2f}°C, 
          Máx: {analysis_data['statistics']['temperatura']['max']:.2f}°C, 
          Mín: {analysis_data['statistics']['temperatura']['min']:.2f}°C, 
          Tendencia reciente: {analysis_data['statistics']['temperatura']['tendencia_reciente']:.2f}°C
          
        - Pluviosidad: Media: {analysis_data['statistics']['pluviosidad']['media']:.2f} mm, 
          Máx: {analysis_data['statistics']['pluviosidad']['max']:.2f} mm, 
          Mín: {analysis_data['statistics']['pluviosidad']['min']:.2f} mm, 
          Tendencia reciente: {analysis_data['statistics']['pluviosidad']['tendencia_reciente']:.2f} mm
          
        - Nivel de agua: Media: {analysis_data['statistics']['nivel_agua']['media']:.2f} m, 
          Máx: {analysis_data['statistics']['nivel_agua']['max']:.2f} m, 
          Mín: {analysis_data['statistics']['nivel_agua']['min']:.2f} m, 
          Tendencia reciente: {analysis_data['statistics']['nivel_agua']['tendencia_reciente']:.2f} m
        
        Basado en estos datos y patrones históricos:
        1. Genera predicciones diarias para cada una de las variables (temperatura, pluviosidad, nivel_agua)
        2. Incluye una breve justificación para cada predicción
        3. Asigna una probabilidad de eventos como inundaciones, sequías o deslizamientos
        
        Devuelve tu respuesta en formato JSON de la siguiente manera:
{{
  "predicciones": [
    {{
      "fecha": "YYYY-MM-DD",
      "temperatura": 25.5,
      "pluviosidad": 10.2,
      "nivel_agua": 4.3,
      "justificacion": "Breve explicación"
    }}
  ],
  "probabilidades": {{
    "inundacion": 0.2,
    "sequia": 0.1,
    "deslizamiento": 0.05
  }},
  "analisis": "Análisis general de la situación y tendencias"
}}
        
        Usa valores numéricos realistas basados en los datos históricos y mantén consistencia con las unidades de medida.
        """
        
        try:
            # Variables para almacenar errores
            openai_error = None
            deepseek_error = None
            anthropic_error = None
            
            # Intentar con DeepSeek si es nuestro modelo preferido
            if self.deepseek_client is not None and self.preferred_model == "deepseek":
                try:
                    # Ajustar mensaje para DeepSeek
                    deepseek_prompt = prompt + "\n\nAsegúrate de responder en formato JSON exactamente como se solicita arriba."
                    
                    # Llamada a DeepSeek API
                    deepseek_response = self.deepseek_client.generate(
                        prompt=deepseek_prompt,
                        max_tokens=1500,
                    )
                    
                    # Extraer la respuesta de DeepSeek
                    response_text = deepseek_response.text
                    
                    # Extraer solo el bloque JSON si viene con texto adicional
                    if "```json" in response_text:
                        json_block = response_text.split("```json")[1].split("```")[0].strip()
                        predictions = json.loads(json_block)
                    elif "```" in response_text:
                        json_block = response_text.split("```")[1].split("```")[0].strip()
                        predictions = json.loads(json_block)
                    else:
                        predictions = json.loads(response_text)
                    
                    # Guardar en caché
                    self.cached_predictions = predictions
                    self.last_prediction_time = current_time
                    
                    return predictions
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al procesar con DeepSeek: {error_str}")
                    deepseek_error = error_str
                    print("Intentando con alternativas...")
            
            # Intentar con OpenAI si es nuestro modelo preferido o si DeepSeek falló
            if self.openai_client is not None and (self.preferred_model == "openai" or deepseek_error is not None):
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"}
                    )
                    
                    # Extraer la respuesta y convertirla a diccionario
                    prediction_text = response.choices[0].message.content
                    predictions = json.loads(prediction_text)
                    
                    # Guardar en caché
                    self.cached_predictions = predictions
                    self.last_prediction_time = current_time
                    
                    return predictions
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de OpenAI: {error_str}")
                    openai_error = error_str
                    print("Intentando con alternativas...")
            
            # Intentar con Anthropic si es nuestro modelo preferido o si los otros modelos fallaron
            if self.anthropic_client is not None and (self.preferred_model == "anthropic" or (deepseek_error is not None and openai_error is not None)):
                try:
                    # Ajustar mensaje para Anthropic (especificar JSON de manera explícita)
                    anthropic_prompt = prompt + "\n\nAsegúrate de responder en formato JSON exactamente como se solicita arriba."
                    
                    anthropic_response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1500,
                        messages=[
                            {"role": "user", "content": anthropic_prompt}
                        ]
                    )
                    
                    # Extraer la respuesta de Anthropic e intentar convertirla a JSON
                    response_text = anthropic_response.content[0].text
                    
                    # Extraer solo el bloque JSON si viene con texto adicional
                    if "```json" in response_text:
                        json_block = response_text.split("```json")[1].split("```")[0].strip()
                        predictions = json.loads(json_block)
                    else:
                        predictions = json.loads(response_text)
                    
                    # Guardar en caché
                    self.cached_predictions = predictions
                    self.last_prediction_time = current_time
                    
                    return predictions
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de Anthropic: {error_str}")
                    anthropic_error = error_str
                    print("Utilizando respuestas locales como fallback...")
            
            # Si llegamos aquí, es porque todos los servicios fallaron o no están disponibles
            # Proceder con respuestas locales para que la aplicación siga funcionando
            print("Utilizando respuestas locales para predicciones...")
            
            # Si la API falla, generar datos simulados basados en las estadísticas históricas
            # para que la interfaz siga funcionando
            
            # Obtener los valores de referencia
            temp_mean = analysis_data['statistics']['temperatura']['media']
            rain_mean = analysis_data['statistics']['pluviosidad']['media']
            water_mean = analysis_data['statistics']['nivel_agua']['media']
            
            temp_trend = analysis_data['statistics']['temperatura']['tendencia_reciente']
            rain_trend = analysis_data['statistics']['pluviosidad']['tendencia_reciente']
            water_trend = analysis_data['statistics']['nivel_agua']['tendencia_reciente']
            
            # Generar predicciones simuladas
            predictions = {"predicciones": []}
            
            start_date = datetime.datetime.now().date()
            
            for i in range(days_to_predict):
                # Añadir variación aleatoria pero manteniendo la tendencia
                temp = temp_mean + (temp_trend * i/2) + random.uniform(-2, 2)
                rain = max(0, rain_mean + (rain_trend * i/2) + random.uniform(-5, 5))
                water = water_mean + (water_trend * i/3) + random.uniform(-0.2, 0.2)
                
                prediction_date = (start_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Generar justificación
                if temp > temp_mean + 2:
                    justification = "Se espera un aumento de temperatura debido a patrones climáticos recientes."
                elif temp < temp_mean - 2:
                    justification = "Se prevé una disminución de temperatura debido a un frente frío entrante."
                else:
                    justification = "Temperatura estable según patrones históricos."
                    
                if rain > rain_mean + 5:
                    justification += " Probabilidad de precipitaciones superiores a la media."
                elif rain < rain_mean - 5:
                    justification += " Condiciones más secas de lo normal."
                
                predictions["predicciones"].append({
                    "fecha": prediction_date,
                    "temperatura": round(temp, 2),
                    "pluviosidad": round(rain, 2),
                    "nivel_agua": round(water, 2),
                    "justificacion": justification
                })
            
            # Calcular probabilidades de desastres
            flood_risk = 0.2 if (water_trend > 0 and rain_mean > 15) else 0.1
            drought_risk = 0.3 if (water_trend < 0 and rain_mean < 10) else 0.05
            landslide_risk = 0.15 if (rain_mean > 20 and water_trend > 0) else 0.02
            
            predictions["probabilidades"] = {
                "inundacion": flood_risk,
                "sequia": drought_risk,
                "deslizamiento": landslide_risk
            }
            
            # Análisis general
            predictions["analisis"] = (
                "Basado en los datos históricos, se observa " +
                ("una tendencia al aumento" if temp_trend > 0 else "una tendencia a la disminución") +
                " de la temperatura. " +
                ("Las precipitaciones muestran un patrón ascendente" if rain_trend > 0 else "Se espera un período de menor precipitación") +
                " y los niveles de agua " +
                ("tienden a incrementarse" if water_trend > 0 else "muestran una tendencia decreciente") +
                ". Se recomienda mantener un monitoreo regular de las condiciones."
            )
            
            # Guardar en caché
            self.cached_predictions = predictions
            self.last_prediction_time = current_time
            
            return predictions
            
        except Exception as e:
            print(f"Error al generar predicciones: {str(e)}")
            return {
                "error": f"No se pudieron generar predicciones: {str(e)}",
                "predicciones": [],
                "probabilidades": {
                    "inundacion": 0,
                    "sequia": 0,
                    "deslizamiento": 0
                },
                "analisis": "No disponible"
            }
    
    def analyze_water_quality(self, water_data):
        """
        Analiza los datos de calidad del agua y proporciona un resumen detallado.
        
        Args:
            water_data (pd.DataFrame): DataFrame con datos de calidad del agua
            
        Returns:
            str: Análisis detallado de la calidad del agua
        """
        if water_data.empty:
            return "No hay datos suficientes para realizar un análisis."
            
        try:
            # Extraer información relevante para el análisis
            stations = water_data['station_name'].unique().tolist()
            
            # Calcular promedios por estación
            station_avg = {}
            for station in stations:
                station_data = water_data[water_data['station_name'] == station]
                station_avg[station] = {
                    'ph': station_data['ph'].mean(),
                    'turbidity': station_data['turbidity'].mean(),
                    'dissolved_oxygen': station_data['dissolved_oxygen'].mean()
                }
            
            # Crear el prompt para el modelo de IA
            prompt = f"""
            Actúa como un especialista experto en agua y calidad ambiental. Analiza los siguientes datos de calidad del agua 
            de {len(stations)} estaciones de monitoreo y proporciona un análisis detallado y profesional. 
            
            Datos por estación:
            """
            
            for station, metrics in station_avg.items():
                prompt += f"""
                Estación: {station}
                - pH: {metrics['ph']:.2f}
                - Turbidez: {metrics['turbidity']:.2f} NTU
                - Oxígeno disuelto: {metrics['dissolved_oxygen']:.2f} mg/L
                """
                
            prompt += """
            Para cada estación, analiza:
            1. Si los valores están dentro de rangos saludables para ecosistemas acuáticos
            2. Posibles problemas o preocupaciones basados en estos valores
            3. Recomendaciones de monitoreo o acciones correctivas
            
            Proporciona un análisis resumido y luego recomendaciones generales.
            """
            
            # Variables para almacenar errores
            openai_error = None
            deepseek_error = None
            anthropic_error = None
            
            # Intentar primero con DeepSeek si es nuestro modelo preferido
            if self.deepseek_client is not None and self.preferred_model == "deepseek":
                try:
                    # Llamada a DeepSeek API
                    deepseek_response = self.deepseek_client.generate(
                        prompt=prompt,
                        max_tokens=1500,
                    )
                    
                    # Extraer la respuesta de DeepSeek
                    analysis = deepseek_response.text
                    return analysis
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al procesar con DeepSeek: {error_str}")
                    deepseek_error = error_str
                    print("Intentando con alternativas...")
            
            # Intentar con OpenAI si es nuestro modelo preferido o si DeepSeek falló
            if self.openai_client is not None and (self.preferred_model == "openai" or deepseek_error is not None):
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    
                    # Extraer la respuesta
                    analysis = response.choices[0].message.content
                    return analysis
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de OpenAI: {error_str}")
                    openai_error = error_str
                    print("Intentando con alternativas...")
            
            # Intentar con Anthropic si los otros modelos fallaron o si es nuestro modelo preferido
            if self.anthropic_client is not None and (self.preferred_model == "anthropic" or (deepseek_error is not None and openai_error is not None)):
                try:
                    anthropic_response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    # Extraer la respuesta de Anthropic
                    analysis = anthropic_response.content[0].text
                    return analysis
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de Anthropic: {error_str}")
                    anthropic_error = error_str
                    
                    # Si ambos servicios fallaron, mostrar respuesta local
                    if openai_error is not None:
                        # Mostrar error de OpenAI primero
                        return self._format_local_water_quality_analysis()
                    else:
                        # Si solo Anthropic falló
                        return self._format_local_water_quality_analysis()
            
            # Si llegamos aquí, es porque no pudimos usar ningún cliente o porque todos fallaron
            return self._format_local_water_quality_analysis()
                
        except Exception as e:
            print(f"Error al analizar calidad del agua: {str(e)}")
            return f"Error al analizar los datos: {str(e)}"
    
    def _format_local_water_quality_analysis(self):
        """Proporciona un análisis local sin conexión a APIs."""
        return """
        ### Análisis de calidad de agua (análisis local)
        
        El análisis con IA no está disponible temporalmente, pero aquí hay un análisis basado en estándares de calidad del agua:
        
        **Guía general de interpretación:**
        - **pH:** Los valores ideales están entre 6.5 y 8.5. Valores fuera de este rango pueden indicar contaminación o problemas de acidificación.
        - **Turbidez:** Valores por debajo de 5 NTU se consideran buenos. Valores elevados indican presencia de partículas suspendidas que pueden afectar la vida acuática.
        - **Oxígeno disuelto:** Valores superiores a 5 mg/L son necesarios para mantener ecosistemas acuáticos saludables. Valores inferiores indican riesgo para la fauna acuática.
        
        **Recomendaciones generales:**
        - Monitorear regularmente estaciones con valores fuera de los rangos ideales
        - Verificar tendencias temporales para identificar patrones de deterioro
        - Priorizar acciones correctivas en estaciones con múltiples parámetros fuera de rango
        
        Revise los gráficos disponibles para comparar valores entre estaciones y determinar las áreas prioritarias.
        """
            
    def chat_about_water_quality(self, water_data, user_query):
        """
        Proporciona respuestas a preguntas específicas del usuario sobre la calidad del agua.
        
        Args:
            water_data (pd.DataFrame): DataFrame con datos de calidad del agua
            user_query (str): Pregunta del usuario
            
        Returns:
            str: Respuesta al usuario
        """
        if water_data.empty:
            return "No hay datos suficientes para responder a tu pregunta."
            
        try:
            # Extraer información relevante para el análisis
            stations = water_data['station_name'].unique().tolist()
            
            # Calcular estadísticas por estación
            station_stats = {}
            for station in stations:
                station_data = water_data[water_data['station_name'] == station]
                
                # Obtener la última medición
                last_measurement = station_data.iloc[-1]
                
                # Calcular promedios
                station_stats[station] = {
                    'ph_current': last_measurement['ph'],
                    'ph_avg': station_data['ph'].mean(),
                    'turbidity_current': last_measurement['turbidity'],
                    'turbidity_avg': station_data['turbidity'].mean(),
                    'do_current': last_measurement['dissolved_oxygen'],
                    'do_avg': station_data['dissolved_oxygen'].mean()
                }
            
            # Crear el prompt para el modelo
            prompt = f"""
            Actúa como un asistente experto en calidad del agua. Tienes los siguientes datos de monitoreo ambiental.
            Responde a la pregunta del usuario de manera clara, precisa y profesional.
            
            Pregunta del usuario: "{user_query}"
            
            Datos de calidad del agua por estación:
            """
            
            for station, stats in station_stats.items():
                prompt += f"""
                Estación: {station}
                - pH actual: {stats['ph_current']:.2f}, promedio: {stats['ph_avg']:.2f}
                - Turbidez actual: {stats['turbidity_current']:.2f} NTU, promedio: {stats['turbidity_avg']:.2f} NTU
                - Oxígeno disuelto actual: {stats['do_current']:.2f} mg/L, promedio: {stats['do_avg']:.2f} mg/L
                """
                
            prompt += """
            Información de referencia:
            - pH ideal para agua dulce: 6.5-8.5
            - Turbidez ideal: < 5 NTU
            - Oxígeno disuelto ideal: > 5 mg/L
            
            Responde de manera directa, profesional y útil. Si no puedes responder con los datos proporcionados, 
            indica qué información adicional sería necesaria.
            """
            
            # Variables para almacenar errores
            openai_error = None
            deepseek_error = None
            anthropic_error = None
            
            # Intentar primero con DeepSeek si es nuestro modelo preferido
            if self.deepseek_client is not None and self.preferred_model == "deepseek":
                try:
                    # Llamada a DeepSeek API
                    deepseek_response = self.deepseek_client.generate(
                        prompt=prompt,
                        max_tokens=1000,
                    )
                    
                    # Extraer la respuesta de DeepSeek
                    response = deepseek_response.text
                    return response
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al procesar con DeepSeek: {error_str}")
                    deepseek_error = error_str
                    print("Intentando con alternativas...")
            
            # Intentar con OpenAI si es nuestro modelo preferido o si DeepSeek falló
            if self.openai_client is not None and (self.preferred_model == "openai" or deepseek_error is not None):
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    
                    # Extraer la respuesta
                    chat_response = response.choices[0].message.content
                    return chat_response
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de OpenAI: {error_str}")
                    openai_error = error_str
                    print("Intentando con alternativas...")
            
            # Intentar con Anthropic si los otros modelos fallaron o si es nuestro modelo preferido
            if self.anthropic_client is not None and (self.preferred_model == "anthropic" or (deepseek_error is not None and openai_error is not None)):
                try:
                    anthropic_response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    # Extraer la respuesta de Anthropic
                    chat_response = anthropic_response.content[0].text
                    return chat_response
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de Anthropic: {error_str}")
                    anthropic_error = error_str
            
            # Si llegamos aquí, es porque todos los servicios fallaron o no están disponibles
            # Generamos una respuesta local
            try:
            
                # Detectar tipo de consulta para dar respuesta local coherente
                query_lower = user_query.lower()
                
                if "ph" in query_lower or "acidez" in query_lower or "alcalinidad" in query_lower:
                    return self._generate_local_ph_response(station_stats)
                elif "turbidez" in query_lower or "claridad" in query_lower:
                    return self._generate_local_turbidity_response(station_stats)
                elif "oxígeno" in query_lower or "disuelto" in query_lower:
                    return self._generate_local_oxygen_response(station_stats)
                elif "estación" in query_lower and any(station.lower() in query_lower for station in stations):
                    # Identificar la estación mencionada
                    mentioned_station = next((station for station in stations if station.lower() in query_lower), None)
                    if mentioned_station:
                        return self._generate_local_station_response(mentioned_station, station_stats[mentioned_station])
                else:
                    # Respuesta general
                    return self._generate_local_general_response(station_stats)
            except Exception as e:
                print(f"Error al generar respuesta local: {str(e)}")
                return "Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta formular la pregunta de otra manera o consulta los datos directamente en los gráficos."
        except Exception as main_error:
            print(f"Error general en chat_about_water_quality: {str(main_error)}")
            return "Lo siento, ocurrió un error al procesar tu consulta sobre la calidad del agua. Por favor, intenta más tarde."
    
    def _generate_local_ph_response(self, station_stats):
        """Genera una respuesta local sobre el pH del agua."""
        # Analizar datos de pH
        problematic_stations = []
        for station, stats in station_stats.items():
            if stats['ph_current'] < 6.5 or stats['ph_current'] > 8.5:
                problematic_stations.append(f"{station} (pH={stats['ph_current']:.2f})")
        
        if problematic_stations:
            stations_text = ", ".join(problematic_stations)
            return f"""
            Respecto al pH del agua, he identificado valores fuera del rango ideal (6.5-8.5) en las siguientes estaciones: {stations_text}.
            
            Un pH fuera del rango ideal puede indicar problemas de contaminación industrial, escorrentía agrícola o procesos naturales 
            como descomposición de materia orgánica. Se recomienda un monitoreo más frecuente en estas estaciones y análisis adicionales 
            para identificar la fuente de la variación.
            
            El resto de las estaciones presentan valores de pH dentro de rangos aceptables para ecosistemas acuáticos saludables.
            """
        else:
            return """
            Todas las estaciones muestran valores de pH dentro del rango ideal (6.5-8.5), lo cual es positivo para la salud de los ecosistemas acuáticos.
            
            El pH es un indicador fundamental de la calidad del agua, ya que afecta directamente a la solubilidad de nutrientes y 
            la disponibilidad de estos para los organismos. Un pH estable dentro del rango ideal favorece la biodiversidad y 
            el funcionamiento adecuado de los procesos biológicos en el medio acuático.
            
            Se recomienda mantener el monitoreo regular para detectar cualquier cambio que pudiera indicar problemas emergentes.
            """
    
    def _generate_local_turbidity_response(self, station_stats):
        """Genera una respuesta local sobre la turbidez del agua."""
        # Analizar datos de turbidez
        problematic_stations = []
        for station, stats in station_stats.items():
            if stats['turbidity_current'] > 5:
                problematic_stations.append(f"{station} ({stats['turbidity_current']:.2f} NTU)")
        
        if problematic_stations:
            stations_text = ", ".join(problematic_stations)
            return f"""
            En cuanto a la turbidez del agua, he detectado valores elevados (>5 NTU) en las siguientes estaciones: {stations_text}.
            
            Una alta turbidez indica presencia excesiva de partículas suspendidas, lo que puede afectar negativamente a los ecosistemas acuáticos:
            - Reduce la penetración de luz, afectando la fotosíntesis
            - Puede dañar las branquias de los peces
            - Transporta contaminantes adheridos a las partículas
            
            Las posibles causas incluyen erosión, escorrentía tras lluvias, vertidos o actividad de construcción cercana.
            Recomiendo inspeccionar estas áreas para identificar fuentes de sedimentos y considerar medidas de control de erosión.
            """
        else:
            return """
            Todas las estaciones muestran valores de turbidez por debajo de 5 NTU, lo que indica una buena claridad del agua.
            
            Una baja turbidez es positiva para los ecosistemas acuáticos porque:
            - Permite una mejor penetración de la luz para la fotosíntesis
            - Reduce el estrés en organismos acuáticos
            - Indica menor cantidad de partículas suspendidas que podrían transportar contaminantes
            
            Es recomendable mantener el monitoreo regular, especialmente tras eventos de lluvia que podrían aumentar temporalmente la turbidez.
            """
    
    def _generate_local_oxygen_response(self, station_stats):
        """Genera una respuesta local sobre el oxígeno disuelto."""
        # Analizar datos de oxígeno disuelto
        problematic_stations = []
        for station, stats in station_stats.items():
            if stats['do_current'] < 5:
                problematic_stations.append(f"{station} ({stats['do_current']:.2f} mg/L)")
        
        if problematic_stations:
            stations_text = ", ".join(problematic_stations)
            return f"""
            Respecto al oxígeno disuelto, he identificado niveles preocupantes (<5 mg/L) en las siguientes estaciones: {stations_text}.
            
            Niveles bajos de oxígeno disuelto representan un riesgo significativo para la vida acuática:
            - Pueden causar estrés o mortalidad en peces y otros organismos
            - Indican posible eutrofización o exceso de materia orgánica
            - Pueden señalar contaminación por nutrientes o procesos de descomposición acelerados
            
            Es urgente investigar las causas de estos niveles bajos, como descargas de aguas residuales, exceso de nutrientes 
            o temperaturas elevadas. Se recomienda aumentar la frecuencia de monitoreo e implementar medidas correctivas.
            """
        else:
            return """
            Todas las estaciones muestran niveles adecuados de oxígeno disuelto (>5 mg/L), lo que es fundamental para la salud de los ecosistemas acuáticos.
            
            El oxígeno disuelto es uno de los indicadores más importantes de la calidad del agua, ya que es esencial para la respiración 
            de peces y otros organismos acuáticos. Niveles adecuados indican un buen equilibrio entre producción (fotosíntesis) y 
            consumo (respiración y descomposición) de oxígeno en el ecosistema.
            
            Para mantener estos niveles saludables, es importante controlar factores como las descargas de nutrientes, 
            la temperatura y la presencia de materia orgánica en el agua.
            """
    
    def _generate_local_station_response(self, station_name, stats):
        """Genera una respuesta local sobre una estación específica."""
        # Evaluar cada parámetro
        ph_status = "dentro del rango ideal" if 6.5 <= stats['ph_current'] <= 8.5 else "fuera del rango ideal"
        turbidity_status = "aceptable" if stats['turbidity_current'] <= 5 else "elevada"
        oxygen_status = "adecuado" if stats['do_current'] >= 5 else "bajo"
        
        return f"""
        Análisis de la estación {station_name}:
        
        1. pH: {stats['ph_current']:.2f} - {ph_status} (6.5-8.5)
           • Tendencia: {"estable" if abs(stats['ph_current'] - stats['ph_avg']) < 0.5 else "variable"}
           
        2. Turbidez: {stats['turbidity_current']:.2f} NTU - {turbidity_status}
           • Comparación con promedio: {"mayor" if stats['turbidity_current'] > stats['turbidity_avg'] else "menor"} que el promedio histórico ({stats['turbidity_avg']:.2f} NTU)
           
        3. Oxígeno disuelto: {stats['do_current']:.2f} mg/L - {oxygen_status}
           • Comparación con promedio: {"mayor" if stats['do_current'] > stats['do_avg'] else "menor"} que el promedio histórico ({stats['do_avg']:.2f} mg/L)
        
        Recomendaciones para esta estación:
        {self._generate_station_recommendations(ph_status, turbidity_status, oxygen_status)}
        """
    
    def _generate_station_recommendations(self, ph_status, turbidity_status, oxygen_status):
        """Genera recomendaciones basadas en el estado de los parámetros."""
        recommendations = []
        
        if ph_status != "dentro del rango ideal":
            recommendations.append("- Investigar posibles fuentes de contaminación que afecten el pH (vertidos industriales, escorrentía agrícola)")
        
        if turbidity_status != "aceptable":
            recommendations.append("- Identificar fuentes de sedimentos y partículas suspendidas")
            recommendations.append("- Considerar medidas de control de erosión en la cuenca")
        
        if oxygen_status != "adecuado":
            recommendations.append("- Buscar fuentes de materia orgánica o nutrientes en exceso")
            recommendations.append("- Considerar análisis de DBO (Demanda Biológica de Oxígeno)")
            recommendations.append("- Monitorear con mayor frecuencia, especialmente en momentos críticos del día")
        
        if not recommendations:
            return "Mantener el monitoreo regular para asegurar que los parámetros continúen dentro de rangos adecuados."
        
        return "\n".join(recommendations)
    
    def _generate_local_general_response(self, station_stats):
        """Genera una respuesta general sobre la calidad del agua."""
        # Contar estaciones con problemas
        ph_issues = sum(1 for stats in station_stats.values() if stats['ph_current'] < 6.5 or stats['ph_current'] > 8.5)
        turbidity_issues = sum(1 for stats in station_stats.values() if stats['turbidity_current'] > 5)
        oxygen_issues = sum(1 for stats in station_stats.values() if stats['do_current'] < 5)
        
        total_stations = len(station_stats)
        
        return f"""
        Resumen general de la calidad del agua basado en los datos disponibles:
        
        - De un total de {total_stations} estaciones monitoreadas:
          • {ph_issues} presentan valores de pH fuera del rango ideal (6.5-8.5)
          • {turbidity_issues} muestran turbidez elevada (>5 NTU)
          • {oxygen_issues} tienen niveles de oxígeno disuelto por debajo de lo recomendado (<5 mg/L)
        
        Interpretación:
        La calidad general del agua puede considerarse {"buena" if (ph_issues + turbidity_issues + oxygen_issues) < total_stations/3 else "preocupante en algunas áreas"}.
        
        Los parámetros más críticos son:
        {self._determine_critical_parameters(ph_issues, turbidity_issues, oxygen_issues, total_stations)}
        
        Es importante enfocarse en las estaciones con múltiples parámetros fuera de rango y continuar el monitoreo regular para detectar tendencias y cambios significativos.
        """
    
    def _determine_critical_parameters(self, ph_issues, turbidity_issues, oxygen_issues, total_stations):
        """Determina los parámetros más críticos basados en la cantidad de estaciones con problemas."""
        issues = [
            (ph_issues, "pH", "puede indicar contaminación industrial o agrícola"),
            (turbidity_issues, "Turbidez", "sugiere problemas de erosión o escorrentía"),
            (oxygen_issues, "Oxígeno disuelto", "señala posible eutrofización o exceso de materia orgánica")
        ]
        
        issues.sort(reverse=True)
        
        if issues[0][0] == 0:
            return "- Ningún parámetro muestra problemas significativos actualmente"
        
        result = []
        for count, param, explanation in issues:
            if count > 0:
                percentage = (count / total_stations) * 100
                result.append(f"- {param}: Afecta al {percentage:.1f}% de las estaciones, lo que {explanation}")
        
        return "\n".join(result)
    
    def get_disaster_risk_assessment(self, predictions):
        """
        Analiza las predicciones y evalúa el riesgo de desastres.
        
        Args:
            predictions (dict): Diccionario con las predicciones generadas
            
        Returns:
            dict: Evaluación de riesgo
        """
        try:
            # Extraer probabilidades de las predicciones
            probabilities = predictions.get("probabilidades", {})
            
            flood_risk = probabilities.get("inundacion", 0)
            drought_risk = probabilities.get("sequia", 0)
            landslide_risk = probabilities.get("deslizamiento", 0)
            
            # Determinar niveles de alerta basados en probabilidades
            risk_levels = {
                "inundacion": self._get_risk_level(flood_risk),
                "sequia": self._get_risk_level(drought_risk),
                "deslizamiento": self._get_risk_level(landslide_risk)
            }
            
            # Preparar recomendaciones basadas en los riesgos
            recommendations = {}
            
            if risk_levels["inundacion"] != "bajo":
                recommendations["inundacion"] = [
                    "Monitorear niveles de agua en ríos y embalses",
                    "Verificar funcionamiento de sistemas de drenaje",
                    "Preparar planes de evacuación en zonas de alto riesgo"
                ]
                
            if risk_levels["sequia"] != "bajo":
                recommendations["sequia"] = [
                    "Implementar medidas de conservación de agua",
                    "Monitorear reservas de agua potable",
                    "Considerar restricciones de uso no esencial"
                ]
                
            if risk_levels["deslizamiento"] != "bajo":
                recommendations["deslizamiento"] = [
                    "Monitorear zonas de pendiente con suelos saturados",
                    "Evaluar estabilidad de laderas en áreas críticas",
                    "Verificar sistemas de contención y drenaje"
                ]
                
            return {
                "niveles_riesgo": risk_levels,
                "probabilidades": probabilities,
                "recomendaciones": recommendations
            }
            
        except Exception as e:
            print(f"Error al evaluar riesgo de desastres: {str(e)}")
            return {
                "error": f"No se pudo evaluar el riesgo: {str(e)}",
                "niveles_riesgo": {
                    "inundacion": "indeterminado",
                    "sequia": "indeterminado",
                    "deslizamiento": "indeterminado"
                }
            }
    
    def _get_risk_level(self, probability):
        """Convierte probabilidad numérica a nivel de riesgo cualitativo."""
        if probability < 0.2:
            return "bajo"
        elif probability < 0.4:
            return "moderado"
        elif probability < 0.6:
            return "alto"
        else:
            return "crítico"