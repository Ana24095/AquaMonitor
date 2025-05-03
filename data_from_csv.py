import pandas as pd
import streamlit as st
from datetime import datetime

def load_csv_data():
    """
    Carga los datos desde el archivo CSV y los formatea para su uso en el dashboard.
    """
    try:
        # Cargar el dataset
        df = pd.read_csv('data.csv')
        
        # Convertir la columna fecha a datetime
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Ordenar por fecha
        df = df.sort_values('fecha')
        
        # Renombrar columnas para consistencia
        df_renamed = df.rename(columns={
            'temperatura': 'temperature',
            'pluviosidad': 'rainfall',
            'nivel_agua': 'water_level'
        })
        
        return df_renamed
    except Exception as e:
        st.error(f"Error al cargar los datos CSV: {str(e)}")
        return None

def get_last_data_point():
    """
    Obtiene el último punto de datos del CSV.
    """
    df = load_csv_data()
    if df is not None and not df.empty:
        return df.iloc[-1].to_dict()
    return None

def get_data_for_timeframe(timeframe='1m'):
    """
    Filtra los datos basados en el timeframe especificado.
    
    Parameters:
    - timeframe: string que representa el rango de tiempo ('1m', '15m', '1h', '1d', '1w', '1M')
    
    Returns:
    - DataFrame filtrado
    """
    df = load_csv_data()
    if df is None or df.empty:
        return None
    
    now = datetime.now()
    
    # Determinar el punto de corte basado en el timeframe
    if timeframe == '1d':
        # Últimas 24 horas
        cutoff = now - pd.Timedelta(days=1)
    elif timeframe == '1w':
        # Última semana
        cutoff = now - pd.Timedelta(days=7)
    elif timeframe == '1M':
        # Último mes
        cutoff = now - pd.Timedelta(days=30)
    elif timeframe == '3M':
        # Últimos 3 meses
        cutoff = now - pd.Timedelta(days=90)
    elif timeframe == '6M':
        # Últimos 6 meses
        cutoff = now - pd.Timedelta(days=180)
    elif timeframe == '1y':
        # Último año
        cutoff = now - pd.Timedelta(days=365)
    else:
        # Por defecto, todo el dataset
        return df
    
    # Filtrar los datos
    filtered_df = df[df['fecha'] >= cutoff]
    
    return filtered_df

def integrate_csv_with_generated_data(generated_data):
    """
    Integra los datos del CSV con los datos generados.
    
    Parameters:
    - generated_data: DataFrame con los datos generados actualmente
    
    Returns:
    - DataFrame combinado
    """
    csv_data = load_csv_data()
    if csv_data is None:
        return generated_data
    
    # Aquí podrías implementar lógica adicional para combinar los datasets
    # Por ejemplo, usar los datos históricos del CSV para tendencias a largo plazo
    # y los datos generados para actualizaciones en tiempo real
    
    # Por ahora, simplemente agregamos una columna que indique la fuente de los datos
    generated_data['data_source'] = 'real-time'
    csv_data['data_source'] = 'historical'
    
    # Combinar los datasets
    combined_data = pd.concat([csv_data, generated_data], ignore_index=True)
    
    return combined_data