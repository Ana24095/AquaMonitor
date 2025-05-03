import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime
import json
import os
from utils.constants import PARAMETER_DESCRIPTIONS, STATION_INFO
from utils.data_from_csv import load_csv_data
import io

def render_reports():
    """
    Render the report generation and export view.
    
    This component allows users to:
    1. Select data for specific stations and time periods
    2. Generate data reports with various metrics
    3. Export reports in different formats (CSV, Excel, PDF, JSON)
    4. Schedule automatic report generation
    """
    st.markdown("""
    <h1 style="font-size: 1.8rem; font-weight: bold;">Generación de Informes</h1>
    """, unsafe_allow_html=True)
    
    # Create tabs for different report types
    report_tabs = st.tabs([
        "Informe de Estación", 
        "Informe de Calidad de Agua", 
        "Informe de Riesgos",
        "Programar Informes"
    ])
    
    # Tab 1: Station Report
    with report_tabs[0]:
        st.subheader("Informe de Estación")
        
        # Report options
        col1, col2 = st.columns(2)
        
        with col1:
            # Station selection
            station_options = [station["name"] for station in STATION_INFO.values()]
            selected_station = st.selectbox(
                "Seleccionar Estación",
                options=station_options
            )
            
            # Time period selection
            time_period = st.selectbox(
                "Período de Tiempo",
                options=["Últimas 24 horas", "Última semana", "Último mes", "Año completo", "Datos históricos"]
            )
            
        with col2:
            # Report format
            report_format = st.selectbox(
                "Formato de Exportación",
                options=["CSV", "Excel", "PDF", "JSON"]
            )
            
            # Report sections
            sections = st.multiselect(
                "Secciones a incluir",
                options=["Datos básicos", "Datos de calidad de agua", "Métricas de riesgo", "Gráficos"],
                default=["Datos básicos", "Datos de calidad de agua"]
            )
        
        # Get data for the report
        if "Datos históricos" in time_period:
            data = load_csv_data()
        else:
            data = st.session_state.data
        
        # Filter data for selected station
        selected_station_id = None
        for station_id, station_info in STATION_INFO.items():
            if station_info["name"] == selected_station:
                selected_station_id = station_id
                break
        
        if selected_station_id and not data.empty:
            station_data = data[data['station_id'] == selected_station_id].copy()
            
            # Calculate metrics for the report
            if not station_data.empty:
                st.markdown("### Vista previa del informe")
                
                # Generate a preview table
                st.dataframe(
                    station_data[['timestamp', 'water_level', 'ph', 'turbidity', 'dissolved_oxygen', 'rainfall']].tail(10),
                    hide_index=True,
                    use_container_width=True
                )
                
                # Calculate averages for metrics
                avg_water_level = station_data['water_level'].mean()
                avg_ph = station_data['ph'].mean()
                avg_turbidity = station_data['turbidity'].mean()
                avg_do = station_data['dissolved_oxygen'].mean()
                
                # Display summary metrics
                st.markdown("### Resumen de métricas")
                
                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.metric("Nivel de Agua Promedio", f"{avg_water_level:.1f}%")
                with metric_cols[1]:
                    st.metric("pH Promedio", f"{avg_ph:.1f}")
                with metric_cols[2]:
                    st.metric("Turbidez Promedio", f"{avg_turbidity:.1f} NTU")
                with metric_cols[3]:
                    st.metric("Oxígeno Disuelto Promedio", f"{avg_do:.1f} mg/L")
                
                # Generate graph for the report preview
                if "Gráficos" in sections:
                    st.markdown("### Gráficos incluidos en el informe")
                    
                    # Time series chart of water level
                    fig = px.line(
                        station_data, 
                        x='timestamp', 
                        y='water_level',
                        labels={'water_level': 'Nivel de Agua (%)', 'timestamp': 'Fecha'},
                        title=f'Nivel de Agua en {selected_station}',
                        color_discrete_sequence=['#00b8a9']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export data button
                st.markdown("### Exportar informe")
                
                if st.button("Generar Informe", type="primary", use_container_width=True):
                    with st.spinner(f"Generando informe en formato {report_format}..."):
                        # Export based on selected format
                        if report_format == "CSV":
                            csv = station_data.to_csv(index=False)
                            b64 = base64.b64encode(csv.encode()).decode()
                            href = f'<a href="data:file/csv;base64,{b64}" download="informe_{selected_station.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv">Descargar Informe CSV</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                        elif report_format == "Excel":
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                station_data.to_excel(writer, sheet_name='Datos', index=False)
                                
                                # Add an extra sheet with summary statistics
                                summary_df = pd.DataFrame({
                                    'Métrica': ['Nivel de Agua', 'pH', 'Turbidez', 'Oxígeno Disuelto'],
                                    'Promedio': [avg_water_level, avg_ph, avg_turbidity, avg_do],
                                    'Mínimo': [
                                        station_data['water_level'].min(),
                                        station_data['ph'].min(),
                                        station_data['turbidity'].min(),
                                        station_data['dissolved_oxygen'].min()
                                    ],
                                    'Máximo': [
                                        station_data['water_level'].max(),
                                        station_data['ph'].max(),
                                        station_data['turbidity'].max(),
                                        station_data['dissolved_oxygen'].max()
                                    ]
                                })
                                summary_df.to_excel(writer, sheet_name='Resumen', index=False)
                                
                                # Format cells
                                workbook = writer.book
                                
                                # Add chart if requested
                                if "Gráficos" in sections:
                                    chart_sheet = workbook.add_worksheet('Gráficos')
                                    writer.sheets['Gráficos'] = chart_sheet
                                    
                                    # Create a chart for water level
                                    chart = workbook.add_chart({'type': 'line'})
                                    
                                    # Configure the chart
                                    chart.add_series({
                                        'name': 'Nivel de Agua',
                                        'categories': ['Datos', 1, 0, len(station_data), 0],
                                        'values': ['Datos', 1, 3, len(station_data), 3],
                                    })
                                    
                                    chart.set_title({'name': f'Nivel de Agua en {selected_station}'})
                                    chart.set_x_axis({'name': 'Fecha'})
                                    chart.set_y_axis({'name': 'Nivel (%)'})
                                    
                                    chart_sheet.insert_chart('B2', chart, {'x_scale': 2, 'y_scale': 1})
                                    
                            excel_data = output.getvalue()
                            b64 = base64.b64encode(excel_data).decode()
                            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="informe_{selected_station.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.xlsx">Descargar Informe Excel</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                        elif report_format == "JSON":
                            # Convert timestamps to string format for JSON
                            json_data = station_data.copy()
                            json_data['timestamp'] = json_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Create a structured JSON report
                            report = {
                                "station_name": selected_station,
                                "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "time_period": time_period,
                                "summary": {
                                    "avg_water_level": float(f"{avg_water_level:.2f}"),
                                    "avg_ph": float(f"{avg_ph:.2f}"),
                                    "avg_turbidity": float(f"{avg_turbidity:.2f}"),
                                    "avg_dissolved_oxygen": float(f"{avg_do:.2f}")
                                },
                                "data": json_data.to_dict(orient='records')
                            }
                            
                            # Convert to JSON string
                            json_str = json.dumps(report, indent=4)
                            b64 = base64.b64encode(json_str.encode()).decode()
                            href = f'<a href="data:application/json;base64,{b64}" download="informe_{selected_station.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.json">Descargar Informe JSON</a>'
                            st.markdown(href, unsafe_allow_html=True)
                            
                        elif report_format == "PDF":
                            st.warning("La generación de PDFs necesita configuración adicional. Por favor seleccione otro formato de exportación por ahora.")
            else:
                st.warning("No hay datos disponibles para la estación seleccionada.")
    
    # Tab 2: Water Quality Report
    with report_tabs[1]:
        st.subheader("Informe de Calidad de Agua")
        
        # Quality report options
        col1, col2 = st.columns(2)
        
        with col1:
            # Parameter selection
            parameter = st.selectbox(
                "Parámetro de Calidad",
                options=["pH", "Turbidez", "Oxígeno Disuelto", "Todos"]
            )
            
            # Threshold configuration
            include_thresholds = st.checkbox("Incluir análisis de umbrales", value=True)
        
        with col2:
            # Time period
            quality_time_period = st.selectbox(
                "Período de Análisis",
                options=["Última semana", "Último mes", "Trimestre", "Año completo"],
                key="quality_time_period"
            )
            
            # Report format
            quality_format = st.selectbox(
                "Formato de Exportación",
                options=["Excel", "CSV", "JSON"],
                key="quality_format"
            )
        
        # Display warning levels
        if include_thresholds:
            st.markdown("### Niveles de alerta configurados")
            
            # Get thresholds for parameters
            threshold_cols = st.columns(3)
            
            with threshold_cols[0]:
                st.markdown("""
                **pH**
                - Normal: 6.5 - 8.5
                - Alerta: < 6.0 o > 9.0
                - Crítico: < 5.0 o > 10.0
                """)
            
            with threshold_cols[1]:
                st.markdown("""
                **Turbidez**
                - Normal: 0 - 5 NTU
                - Alerta: 5 - 10 NTU
                - Crítico: > 10 NTU
                """)
            
            with threshold_cols[2]:
                st.markdown("""
                **Oxígeno Disuelto**
                - Normal: > 6 mg/L
                - Alerta: 4 - 6 mg/L
                - Crítico: < 4 mg/L
                """)
        
        # Generate water quality report button
        if st.button("Generar Informe de Calidad", type="primary", use_container_width=True):
            with st.spinner("Generando informe de calidad de agua..."):
                # This would be implemented to generate the specific water quality report
                st.success("Informe de calidad de agua generado exitosamente.")
                
                # For demonstration purposes, we'll create a download link for a placeholder file
                data = {
                    "Estación": [],
                    "Parámetro": [],
                    "Promedio": [],
                    "Máximo": [],
                    "Mínimo": [],
                    "% Tiempo en Rango Normal": [],
                    "% Tiempo en Alerta": [],
                    "% Tiempo en Crítico": []
                }
                
                # Add some sample data for demonstration
                for station_id, station_info in STATION_INFO.items():
                    # Add pH data
                    data["Estación"].append(station_info["name"])
                    data["Parámetro"].append("pH")
                    data["Promedio"].append(station_info["base_ph"])
                    data["Máximo"].append(station_info["base_ph"] + 0.5)
                    data["Mínimo"].append(station_info["base_ph"] - 0.5)
                    
                    # Calculate some random percentages that sum to 100%
                    normal_pct = 85
                    alert_pct = 10
                    critical_pct = 5
                    
                    data["% Tiempo en Rango Normal"].append(normal_pct)
                    data["% Tiempo en Alerta"].append(alert_pct)
                    data["% Tiempo en Crítico"].append(critical_pct)
                    
                    # Add Turbidity data
                    data["Estación"].append(station_info["name"])
                    data["Parámetro"].append("Turbidez")
                    data["Promedio"].append(station_info["base_turbidity"])
                    data["Máximo"].append(station_info["base_turbidity"] * 1.2)
                    data["Mínimo"].append(station_info["base_turbidity"] * 0.8)
                    
                    # Calculate some random percentages that sum to 100%
                    normal_pct = 90
                    alert_pct = 8
                    critical_pct = 2
                    
                    data["% Tiempo en Rango Normal"].append(normal_pct)
                    data["% Tiempo en Alerta"].append(alert_pct)
                    data["% Tiempo en Crítico"].append(critical_pct)
                    
                    # Add Dissolved Oxygen data
                    data["Estación"].append(station_info["name"])
                    data["Parámetro"].append("Oxígeno Disuelto")
                    data["Promedio"].append(station_info["base_dissolved_oxygen"])
                    data["Máximo"].append(station_info["base_dissolved_oxygen"] * 1.1)
                    data["Mínimo"].append(station_info["base_dissolved_oxygen"] * 0.9)
                    
                    # Calculate some random percentages that sum to 100%
                    normal_pct = 95
                    alert_pct = 4
                    critical_pct = 1
                    
                    data["% Tiempo en Rango Normal"].append(normal_pct)
                    data["% Tiempo en Alerta"].append(alert_pct)
                    data["% Tiempo en Crítico"].append(critical_pct)
                
                # Create a DataFrame from the data
                quality_df = pd.DataFrame(data)
                
                # Filter based on selected parameter
                if parameter != "Todos":
                    quality_df = quality_df[quality_df["Parámetro"] == parameter]
                
                # Export based on selected format
                if quality_format == "CSV":
                    csv = quality_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    download_filename = f"informe_calidad_{parameter.lower() if parameter != 'Todos' else 'todos'}_{datetime.now().strftime('%Y%m%d')}.csv"
                    href = f'<a href="data:file/csv;base64,{b64}" download="{download_filename}">Descargar Informe de Calidad (CSV)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                elif quality_format == "Excel":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        quality_df.to_excel(writer, sheet_name='Calidad de Agua', index=False)
                        
                        # Add a chart sheet if there's enough data
                        if len(quality_df) > 1:
                            workbook = writer.book
                            chart_sheet = workbook.add_worksheet('Gráficos')
                            writer.sheets['Gráficos'] = chart_sheet
                            
                            # Create a chart showing normal/alert/critical percentages
                            chart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
                            
                            # Configure the chart data ranges
                            for i, param in enumerate(quality_df['Parámetro'].unique()):
                                param_data = quality_df[quality_df['Parámetro'] == param]
                                chart.add_series({
                                    'name': f'Normal - {param}',
                                    'categories': ['Calidad de Agua', 1, 0, len(param_data), 0],  # Estación column
                                    'values': ['Calidad de Agua', 1, 5, len(param_data), 5],  # Normal column
                                    'fill': {'color': '#00b8a9'}
                                })
                                chart.add_series({
                                    'name': f'Alerta - {param}',
                                    'categories': ['Calidad de Agua', 1, 0, len(param_data), 0],
                                    'values': ['Calidad de Agua', 1, 6, len(param_data), 6],  # Alert column
                                    'fill': {'color': '#ffd166'}
                                })
                                chart.add_series({
                                    'name': f'Crítico - {param}',
                                    'categories': ['Calidad de Agua', 1, 0, len(param_data), 0],
                                    'values': ['Calidad de Agua', 1, 7, len(param_data), 7],  # Critical column
                                    'fill': {'color': '#ef476f'}
                                })
                            
                            chart.set_title({'name': 'Distribución de Calidad de Agua por Estación'})
                            chart.set_x_axis({'name': 'Porcentaje'})
                            chart.set_y_axis({'name': 'Estación'})
                            
                            chart_sheet.insert_chart('B2', chart, {'x_scale': 1.5, 'y_scale': 1.5})
                    
                    excel_data = output.getvalue()
                    b64 = base64.b64encode(excel_data).decode()
                    download_filename = f"informe_calidad_{parameter.lower() if parameter != 'Todos' else 'todos'}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{download_filename}">Descargar Informe de Calidad (Excel)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                elif quality_format == "JSON":
                    # Create a structured JSON report
                    report = {
                        "report_type": "Water Quality Report",
                        "parameter": parameter,
                        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "time_period": quality_time_period,
                        "data": quality_df.to_dict(orient='records')
                    }
                    
                    # Convert to JSON string
                    json_str = json.dumps(report, indent=4)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    download_filename = f"informe_calidad_{parameter.lower() if parameter != 'Todos' else 'todos'}_{datetime.now().strftime('%Y%m%d')}.json"
                    href = f'<a href="data:application/json;base64,{b64}" download="{download_filename}">Descargar Informe de Calidad (JSON)</a>'
                    st.markdown(href, unsafe_allow_html=True)
    
    # Tab 3: Risk Report
    with report_tabs[2]:
        st.subheader("Informe de Riesgos")
        
        # Risk assessment options
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk type selection
            risk_type = st.selectbox(
                "Tipo de Riesgo",
                options=["Inundación", "Sequía", "Deslizamiento", "Todos los riesgos"]
            )
            
            # Risk level filter
            risk_level = st.selectbox(
                "Nivel de Riesgo",
                options=["Todos los niveles", "Solo alto riesgo (>70%)", "Solo riesgo medio (>30%)"]
            )
        
        with col2:
            # Time period for risk assessment
            risk_time_period = st.selectbox(
                "Período de Análisis",
                options=["Última semana", "Último mes", "Trimestre", "Año completo"],
                key="risk_time_period"
            )
            
            # Report format
            risk_format = st.selectbox(
                "Formato de Exportación",
                options=["Excel", "CSV", "JSON", "PDF"],
                key="risk_format"
            )
        
        # Generate sample risk distribution charts
        risk_metrics = {
            "Inundación": [0.25, 0.42, 0.18, 0.65],
            "Sequía": [0.12, 0.35, 0.22, 0.48],
            "Deslizamiento": [0.08, 0.17, 0.32, 0.22]
        }
        
        # Show risk distribution by station
        st.markdown("### Distribución de riesgos por estación")
        
        # Create a DataFrame for the risk metrics
        risk_df = pd.DataFrame({
            "Estación": [info["name"] for info in STATION_INFO.values()],
            "Inundación": risk_metrics["Inundación"],
            "Sequía": risk_metrics["Sequía"],
            "Deslizamiento": risk_metrics["Deslizamiento"]
        })
        
        # Display the data in a table
        st.dataframe(risk_df, hide_index=True, use_container_width=True)
        
        # Create a chart visualization
        if risk_type != "Todos los riesgos":
            # Bar chart for single risk type
            fig = px.bar(
                risk_df,
                x="Estación",
                y=risk_type,
                color=risk_type,
                color_continuous_scale=["green", "yellow", "red"],
                labels={risk_type: f"Probabilidad de {risk_type} (0-1)"},
                title=f"Probabilidad de {risk_type} por Estación"
            )
        else:
            # Grouped bar chart for all risk types
            fig = px.bar(
                risk_df.melt(id_vars=["Estación"], value_vars=["Inundación", "Sequía", "Deslizamiento"], 
                            var_name="Tipo de Riesgo", value_name="Probabilidad"),
                x="Estación",
                y="Probabilidad",
                color="Tipo de Riesgo",
                barmode="group",
                title="Probabilidad de riesgos por estación"
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Generate risk report button
        if st.button("Generar Informe de Riesgos", type="primary", use_container_width=True):
            with st.spinner("Generando informe de riesgos..."):
                # Generate a report file in the selected format
                if risk_format == "CSV":
                    # For CSV, just export the dataframe
                    if risk_type != "Todos los riesgos":
                        export_df = risk_df[["Estación", risk_type]]
                    else:
                        export_df = risk_df
                    
                    csv = export_df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    download_filename = f"informe_riesgos_{risk_type.lower().replace(' ', '_') if risk_type != 'Todos los riesgos' else 'todos'}_{datetime.now().strftime('%Y%m%d')}.csv"
                    href = f'<a href="data:file/csv;base64,{b64}" download="{download_filename}">Descargar Informe de Riesgos (CSV)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                elif risk_format == "Excel":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        if risk_type != "Todos los riesgos":
                            export_df = risk_df[["Estación", risk_type]]
                            export_df.to_excel(writer, sheet_name=f'Riesgo de {risk_type}', index=False)
                        else:
                            risk_df.to_excel(writer, sheet_name='Todos los Riesgos', index=False)
                        
                        # Add a chart
                        workbook = writer.book
                        chart_sheet = workbook.add_worksheet('Gráficos de Riesgo')
                        writer.sheets['Gráficos de Riesgo'] = chart_sheet
                        
                        chart = workbook.add_chart({'type': 'column'})
                        
                        if risk_type != "Todos los riesgos":
                            chart.add_series({
                                'name': risk_type,
                                'categories': [f'Riesgo de {risk_type}', 1, 0, len(export_df), 0],
                                'values': [f'Riesgo de {risk_type}', 1, 1, len(export_df), 1],
                            })
                        else:
                            for i, risk in enumerate(["Inundación", "Sequía", "Deslizamiento"]):
                                chart.add_series({
                                    'name': risk,
                                    'categories': ['Todos los Riesgos', 1, 0, len(risk_df), 0],
                                    'values': ['Todos los Riesgos', 1, i+1, len(risk_df), i+1],
                                })
                        
                        chart.set_title({'name': 'Probabilidad de Riesgos por Estación'})
                        chart.set_x_axis({'name': 'Estación'})
                        chart.set_y_axis({'name': 'Probabilidad (0-1)'})
                        
                        chart_sheet.insert_chart('B2', chart, {'x_scale': 1.5, 'y_scale': 1.5})
                    
                    excel_data = output.getvalue()
                    b64 = base64.b64encode(excel_data).decode()
                    download_filename = f"informe_riesgos_{risk_type.lower().replace(' ', '_') if risk_type != 'Todos los riesgos' else 'todos'}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{download_filename}">Descargar Informe de Riesgos (Excel)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                elif risk_format == "JSON":
                    # Create a more detailed JSON structure
                    if risk_type != "Todos los riesgos":
                        data_to_export = risk_df[["Estación", risk_type]].to_dict(orient='records')
                    else:
                        data_to_export = risk_df.to_dict(orient='records')
                    
                    report = {
                        "report_type": "Risk Assessment Report",
                        "risk_type": risk_type,
                        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "time_period": risk_time_period,
                        "risk_level_filter": risk_level,
                        "data": data_to_export
                    }
                    
                    # Add risk level classifications
                    report["risk_classifications"] = {
                        "high_risk": "Probabilidad > 0.7",
                        "medium_risk": "Probabilidad entre 0.3 y 0.7",
                        "low_risk": "Probabilidad < 0.3"
                    }
                    
                    # Convert to JSON string
                    json_str = json.dumps(report, indent=4)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    download_filename = f"informe_riesgos_{risk_type.lower().replace(' ', '_') if risk_type != 'Todos los riesgos' else 'todos'}_{datetime.now().strftime('%Y%m%d')}.json"
                    href = f'<a href="data:application/json;base64,{b64}" download="{download_filename}">Descargar Informe de Riesgos (JSON)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                elif risk_format == "PDF":
                    st.warning("La generación de PDFs necesita configuración adicional. Por favor seleccione otro formato de exportación por ahora.")
    
    # Tab 4: Schedule Reports
    with report_tabs[3]:
        st.subheader("Programar Informes Automáticos")
        
        # Report scheduling options
        st.markdown("""
        Esta función permite programar la generación y envío automático de informes a los destinatarios designados.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Report type
            scheduled_report_type = st.selectbox(
                "Tipo de Informe",
                options=["Informe de Estación", "Informe de Calidad de Agua", "Informe de Riesgos"]
            )
            
            # Report frequency
            frequency = st.selectbox(
                "Frecuencia",
                options=["Diario", "Semanal", "Mensual"]
            )
            
            # Recipients
            recipients = st.text_area(
                "Destinatarios (correos electrónicos separados por comas)",
                placeholder="ejemplo@correo.com, otro@correo.com"
            )
        
        with col2:
            # Format
            scheduled_format = st.selectbox(
                "Formato",
                options=["Excel", "CSV", "PDF"]
            )
            
            # Time of day (for daily reports)
            if frequency == "Diario":
                scheduled_time = st.time_input("Hora de envío", value=datetime.strptime("08:00", "%H:%M").time())
            
            # Day of week (for weekly reports)
            elif frequency == "Semanal":
                day_of_week = st.selectbox(
                    "Día de la semana",
                    options=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                )
                scheduled_time = st.time_input("Hora de envío", value=datetime.strptime("08:00", "%H:%M").time())
            
            # Day of month (for monthly reports)
            elif frequency == "Mensual":
                day_of_month = st.number_input("Día del mes", min_value=1, max_value=28, value=1)
                scheduled_time = st.time_input("Hora de envío", value=datetime.strptime("08:00", "%H:%M").time())
        
        # Schedule button
        if st.button("Programar Informe Automático", type="primary"):
            # In a full implementation, this would save the schedule to a database
            st.success(f"Informe programado correctamente. Se enviará {frequency.lower()} a los destinatarios especificados.")
            
            # Display the schedule details
            st.markdown("### Detalles de la programación")
            
            schedule_details = {
                "Tipo de informe": scheduled_report_type,
                "Frecuencia": frequency,
                "Formato": scheduled_format,
                "Destinatarios": recipients
            }
            
            if frequency == "Diario":
                schedule_details["Hora de envío"] = scheduled_time.strftime("%H:%M")
            elif frequency == "Semanal":
                schedule_details["Día de la semana"] = day_of_week
                schedule_details["Hora de envío"] = scheduled_time.strftime("%H:%M")
            elif frequency == "Mensual":
                schedule_details["Día del mes"] = day_of_month
                schedule_details["Hora de envío"] = scheduled_time.strftime("%H:%M")
            
            # Display the schedule details in a table
            schedule_df = pd.DataFrame({"Parámetro": schedule_details.keys(), "Valor": schedule_details.values()})
            st.dataframe(schedule_df, hide_index=True, use_container_width=True)
            
            # Show a note about email configuration
            st.info("""
            Nota: Para que los informes automáticos se envíen por correo electrónico, es necesario configurar 
            un servidor SMTP en la configuración del sistema. En una implementación real, esto requeriría acceso
            a un servidor de correo o un servicio como SendGrid, Mailchimp, etc.
            """)

def to_excel(df):
    """
    Convert a DataFrame to an Excel file and return as bytes.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    return output.getvalue()

def get_table_download_link(df, filename, linktext="Download CSV"):
    """
    Generate a link to download a dataframe as a CSV file.
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{linktext}</a>'
    return href