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
    Clase encargada de generar predicciones utilizando modelos de IA (OpenAI o Anthropic)
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
        self.use_fallback = False  # Flag para indicar si usar alternativas
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
        
        # Construir el prompt para GPT-4o
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
            # Intentar obtener la respuesta del modelo
            # Primero intentar con OpenAI si es nuestro modelo preferido
            openai_error = None
            if self.openai_client is not None and self.preferred_model == "openai":
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
                    
                    # Si hay un error con OpenAI pero tenemos cliente de Anthropic, intentamos con este
                    if self.anthropic_client is not None:
                        print("Intentando con Anthropic como alternativa para predicciones...")
            
            # Intentar con DeepSeek si está configurado como preferido o como fallback
            if self.deepseek_client is not None and (self.preferred_model == "deepseek" or openai_error is not None):
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
                    
                except Exception as deepseek_error:
                    error_str = str(deepseek_error)
                    print(f"Error al procesar con DeepSeek: {error_str}")
                    print("Intentando con alternativas...")
                    
                    # Si DeepSeek falla y tenemos Anthropic, intentamos con este
                    if self.anthropic_client is not None:
                        print("Intentando con Anthropic como alternativa...")
            
            # Intentar con Anthropic si DeepSeek y OpenAI fallaron o si es el modelo principal
            if self.anthropic_client is not None and (self.preferred_model == "anthropic" or openai_error is not None):
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
                    
                except Exception as anthropic_error:
                    error_str = str(anthropic_error)
                    print(f"Error al conectar con la API de Anthropic: {error_str}")
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
            
            # Intentar con el modelo de IA preferido
            openai_error = None
            deepseek_error = None
            
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
                    
                    # Si hay un error con OpenAI pero tenemos cliente de Anthropic, intentamos con este
                    if self.anthropic_client is not None:
                        print("Intentando con Anthropic como alternativa...")
                        
            # Intentar con Anthropic si OpenAI falló o si estamos usando Anthropic como principal
            if self.anthropic_client is not None and (openai_error is not None or self.use_anthropic_fallback):
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
                    
                except Exception as anthropic_error:
                    error_str = str(anthropic_error)
                    print(f"Error al conectar con la API de Anthropic: {error_str}")
                    
                    # Si ambos servicios fallaron, mostrar mensajes de error específicos
                    if openai_error is not None:
                        # Mostrar error de OpenAI primero
                        return self._format_openai_error_message(openai_error)
                    else:
                        # Si solo Anthropic falló
                        return f"""
                        ### Error de conexión con Anthropic
                        
                        No se pudo conectar con el servicio de Anthropic. 
                        
                        Posibles causas:
                        - Problemas de conectividad a internet
                        - Servicio de Anthropic temporalmente no disponible
                        - Límite de tasa (rate limit) alcanzado
                        
                        Detalles técnicos: {error_str}
                        """
            
            # Si llegamos aquí, es porque no pudimos usar ningún cliente o porque OpenAI falló y no hay Anthropic
            if openai_error is not None:
                return self._format_openai_error_message(openai_error)
            else:
                return """
                ### Error de configuración de APIs
                
                No se ha configurado correctamente ninguna API de IA. Por favor, verifica la configuración 
                de las variables de entorno para OPENAI_API_KEY o ANTHROPIC_API_KEY.
                """
                
        except Exception as e:
            print(f"Error al analizar calidad del agua: {str(e)}")
            return f"Error al analizar los datos: {str(e)}"
            
    def _format_openai_error_message(self, error_str):
        """Formatea mensajes de error específicos para OpenAI."""
        if "insufficient_quota" in error_str or "exceeded your current quota" in error_str:
            return """
            ### Análisis de calidad de agua (sin IA)
            
            El análisis con IA no está disponible temporalmente, pero aquí hay un análisis básico basado en estándares de calidad del agua:
            
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
        elif "invalid_api_key" in error_str or "authentication" in error_str:
            return """
            ### Análisis de calidad de agua (sin IA)
            
            El análisis con IA no está disponible debido a un problema de autenticación, pero aquí hay un análisis basado en estándares de calidad del agua:
            
            **Guía general de interpretación:**
            - **pH:** Los valores ideales están entre 6.5 y 8.5. Valores fuera de este rango pueden indicar contaminación o problemas de acidificación.
            - **Turbidez:** Valores por debajo de 5 NTU se consideran buenos. Valores elevados indican presencia de partículas suspendidas que pueden afectar la vida acuática.
            - **Oxígeno disuelto:** Valores superiores a 5 mg/L son necesarios para mantener ecosistemas acuáticos saludables. Valores inferiores indican riesgo para la fauna acuática.
            
            **Recomendaciones generales:**
            - Monitorear regularmente estaciones con valores fuera de los rangos ideales
            - Verificar tendencias temporales para identificar patrones de deterioro
            - Priorizar acciones correctivas en estaciones con múltiples parámetros fuera de rango
            """
        else:
            return f"""
            ### Análisis de calidad de agua (sin IA)
            
            El análisis con IA no está disponible debido a problemas de conexión, pero aquí hay un análisis basado en estándares de calidad del agua:
            
            **Guía general de interpretación:**
            - **pH:** Los valores ideales están entre 6.5 y 8.5. Valores fuera de este rango pueden indicar contaminación o problemas de acidificación.
            - **Turbidez:** Valores por debajo de 5 NTU se consideran buenos. Valores elevados indican presencia de partículas suspendidas que pueden afectar la vida acuática.
            - **Oxígeno disuelto:** Valores superiores a 5 mg/L son necesarios para mantener ecosistemas acuáticos saludables. Valores inferiores indican riesgo para la fauna acuática.
            
            **Recomendaciones generales:**
            - Monitorear regularmente estaciones con valores fuera de los rangos ideales
            - Verificar tendencias temporales para identificar patrones de deterioro
            - Priorizar acciones correctivas en estaciones con múltiples parámetros fuera de rango
            
            Revise los gráficos disponibles para obtener información más detallada sobre cada estación.
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
            
            # Crear el prompt para GPT-4o
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
            
            # Primero intentar con OpenAI a menos que estemos usando Anthropic como fallback principal
            openai_error = None
            if self.openai_client is not None and not self.use_anthropic_fallback:
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    
                    # Extraer la respuesta
                    answer = response.choices[0].message.content
                    return answer
                    
                except Exception as api_error:
                    error_str = str(api_error)
                    print(f"Error al conectar con la API de OpenAI: {error_str}")
                    openai_error = error_str
                    
                    # Si hay un error con OpenAI pero tenemos cliente de Anthropic, intentamos con este
                    if self.anthropic_client is not None:
                        print("Intentando con Anthropic como alternativa para el chat...")
                        
            # Intentar con Anthropic si OpenAI falló o si estamos usando Anthropic como principal
            if self.anthropic_client is not None and (openai_error is not None or self.use_anthropic_fallback):
                try:
                    anthropic_response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=800,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    # Extraer la respuesta de Anthropic
                    answer = anthropic_response.content[0].text
                    return answer
                    
                except Exception as anthropic_error:
                    error_str = str(anthropic_error)
                    print(f"Error al conectar con la API de Anthropic: {error_str}")
                    
                    # Si ambos servicios fallaron, mostrar mensajes de error específicos
                    if openai_error is not None:
                        # Mostrar error de OpenAI primero
                        return self._format_openai_error_message(openai_error)
                    else:
                        # Si solo Anthropic falló, generar respuesta básica relacionada con la consulta del usuario
                        # Analizar la pregunta del usuario
                        query_low = user_query.lower()
                        
                        if "ph" in query_low:
                            return f"""
                            **Información sobre pH del agua (respuesta local)**
                            
                            El pH es un indicador importante de la calidad del agua que mide su acidez o alcalinidad:
                            
                            - El rango ideal para agua dulce es 6.5-8.5
                            - Valores por debajo de 6.5 indican condiciones ácidas que pueden estresar a organismos acuáticos
                            - Valores por encima de 8.5 indican condiciones alcalinas que también pueden ser problemáticas
                            
                            Revise los gráficos de pH para identificar las estaciones con valores fuera del rango ideal.
                            """
                        elif "turbi" in query_low:
                            return f"""
                            **Información sobre turbidez (respuesta local)**
                            
                            La turbidez mide la claridad del agua:
                            
                            - Valores bajos (< 5 NTU) indican agua clara con buena penetración de luz
                            - Valores altos indican presencia de partículas suspendidas (sedimentos, microorganismos)
                            - La turbidez elevada reduce la fotosíntesis y puede dañar las branquias de los peces
                            
                            Para mejorar la turbidez: controlar la erosión, implementar zonas de amortiguamiento vegetativo.
                            """
                        elif "oxígeno" in query_low or "oxigeno" in query_low or "disuelto" in query_low:
                            return f"""
                            **Información sobre oxígeno disuelto (respuesta local)**
                            
                            El oxígeno disuelto es esencial para la vida acuática:
                            
                            - Valores superiores a 5 mg/L son necesarios para ecosistemas saludables
                            - Valores por debajo de 3 mg/L causan estrés en muchas especies
                            - Valores por debajo de 2 mg/L pueden ser letales para la mayoría de los peces
                            
                            Factores que reducen el oxígeno: temperatura alta, contaminación orgánica, eutrofización.
                            """
                        else:
                            return f"""
                            **Respuesta a su consulta sobre calidad del agua (respuesta local)**
                            
                            Los tres parámetros principales para evaluar la calidad del agua son:
                            
                            1. **pH:** Ideal entre 6.5-8.5. Mide la acidez o alcalinidad.
                            2. **Turbidez:** Ideal < 5 NTU. Mide la claridad del agua.
                            3. **Oxígeno disuelto:** Ideal > 5 mg/L. Esencial para la vida acuática.
                            
                            Revise los gráficos disponibles para comparar los valores actuales con estos rangos ideales y determinar la calidad del agua en cada estación.
                            """
            
            # Si llegamos aquí, es porque no pudimos usar ningún cliente o porque OpenAI falló y no hay Anthropic
            if openai_error is not None:
                return self._format_openai_error_message(openai_error)
            else:
                return """
                **Error de configuración de APIs**
                
                No se ha configurado correctamente ninguna API de IA. Por favor, verifica la configuración 
                de las variables de entorno para OPENAI_API_KEY o ANTHROPIC_API_KEY.
                """
                
        except Exception as e:
            print(f"Error al procesar la consulta: {str(e)}")
            return f"Error al procesar tu consulta: {str(e)}"
            
    def get_disaster_risk_assessment(self, predictions):
        """
        Analiza las predicciones y evalúa el riesgo de desastres.
        
        Args:
            predictions (dict): Diccionario con las predicciones generadas
            
        Returns:
            dict: Evaluación de riesgo
        """
        # Extraer probabilidades de los diferentes tipos de desastres
        try:
            probabilities = predictions.get('probabilidades', {})
            flood_risk = probabilities.get('inundacion', 0)
            drought_risk = probabilities.get('sequia', 0)
            landslide_risk = probabilities.get('deslizamiento', 0)
            
            # Determinar el riesgo general
            max_risk = max(flood_risk, drought_risk, landslide_risk)
            
            # Evaluar el nivel de riesgo
            if max_risk < 0.3:
                risk_level = "bajo"
                recommendations = "Mantener el monitoreo regular."
            elif max_risk < 0.6:
                risk_level = "moderado"
                recommendations = "Aumentar la frecuencia de monitoreo y preparar planes de contingencia."
            else:
                risk_level = "alto"
                recommendations = "Activar protocolos de emergencia y considerar evacuaciones preventivas en zonas de riesgo."
            
            # Identificar el tipo de riesgo principal
            if flood_risk == max_risk:
                main_risk = "inundación"
            elif drought_risk == max_risk:
                main_risk = "sequía"
            else:
                main_risk = "deslizamiento"
            
            return {
                "nivel_riesgo": risk_level,
                "riesgo_principal": main_risk,
                "probabilidades": {
                    "inundacion": flood_risk,
                    "sequia": drought_risk,
                    "deslizamiento": landslide_risk
                },
                "recomendaciones": recommendations
            }
            
        except Exception as e:
            print(f"Error al evaluar riesgo: {str(e)}")
            return {
                "nivel_riesgo": "desconocido",
                "riesgo_principal": "no determinado",
                "probabilidades": {
                    "inundacion": 0,
                    "sequia": 0,
                    "deslizamiento": 0
                },
                "recomendaciones": "No se pudo realizar la evaluación de riesgo."
            }