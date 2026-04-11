"""
API Flask - Backend principal
Recibe solicitudes de programación, las procesa y devuelve resultados
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
from pathlib import Path

from models import (
    SchedulingRequest, SchedulingRequestData, ScheduleResult
)
from scheduler_simple import SimpleScheduleOptimizer
from excel_generator import ExcelScheduleGenerator


app = Flask(__name__)
CORS(app)

# Directorio para archivos generados
OUTPUT_DIR = Path("./generated_schedules")
OUTPUT_DIR.mkdir(exist_ok=True)


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({
        'status': 'ok',
        'service': 'Schedule Optimizer Backend',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/schedule/generate', methods=['POST'])
def generate_schedule():
    """
    Endpoint principal: Genera horarios basado en los parámetros enviados
    
    Body esperado: JSON con estructura SchedulingRequest
    Retorna: JSON con ScheduleResult
    """
    try:
        # Validar y parsear entrada
        raw_data = request.get_json()
        
        if not raw_data:
            return jsonify({
                'success': False,
                'message': 'Body vacío',
                'errors': ['No se recibió JSON válido']
            }), 400
        
        # Parsear con modelo SchedulingRequest (V2.0) - acepta wrapper
        try:
            request_wrapper = SchedulingRequest(**raw_data)
            request_data = request_wrapper.scheduling_request
        except Exception as e:
            print(f"[ERROR] Fallo validación: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error en validación de datos',
                'errors': [str(e)]
            }), 400
        
        print(f"[API] Solicitud recibida de tienda: {request_data.store_config.store_name}")
        print(f"[API] Empleados: {len(request_data.employees)}")
        print(f"[API] Mes: {request_data.month_config.month}/{request_data.month_config.year}")
        
        # Crear optimizador SIMPLE (funcional)
        optimizer = SimpleScheduleOptimizer(
            month_config=request_data.month_config,
            store_config=request_data.store_config,
            employees=request_data.employees
        )
        
        # Ejecutar optimización
        success = optimizer.optimize()
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'No se pudo encontrar una solución válida para los parámetros especificados',
                'errors': ['El modelo PuLP no encontró solución factible']
            }), 422
        
        # Extraer resultados
        schedule = optimizer.get_schedule()
        summary = optimizer.get_summary()
        calendar = {}  # El scheduler simple no necesita calendar
        
        # Generar archivo Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"horario_{request_data.store_config.store_name.replace(' ', '_')}_{timestamp}.xlsx"
        excel_path = OUTPUT_DIR / excel_filename
        
        employees_data = [
            {
                'employee_id': emp.employee_id,
                'name': emp.name,
                'contract_type': emp.contract_type
            }
            for emp in request_data.employees
        ]
        
        generator = ExcelScheduleGenerator(str(excel_path))
        generator.generate(
            schedule=schedule,
            summary=summary,
            calendar=calendar,
            employees_data=employees_data,
            store_name=request_data.store_config.store_name,
            month_name=_get_month_name(request_data.month_config.month),
            year=request_data.month_config.year
        )
        
        # Retornar resultado exitoso
        return jsonify({
            'success': True,
            'message': 'Horarios generados exitosamente',
            'schedule': {k: {str(d): v for d, v in days.items()} for k, days in schedule.items()},
            'summary': summary,
            'file_path': str(excel_path),
            'file_name': excel_filename,
            'errors': []
        }), 200

    except Exception as e:
        print(f"[ERROR] Excepción no capturada: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'errors': [str(e)]
        }), 500


@app.route('/api/schedule/download/<filename>', methods=['GET'])
def download_schedule(filename: str):
    """
    Descarga un archivo de horario generado
    """
    try:
        file_path = OUTPUT_DIR / filename
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'message': 'Archivo no encontrado',
                'errors': ['El archivo especificado no existe']
            }), 404
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al descargar archivo',
            'errors': [str(e)]
        }), 500


@app.route('/api/schedule/list', methods=['GET'])
def list_schedules():
    """
    Lista los archivos de horarios generados
    """
    try:
        files = list(OUTPUT_DIR.glob('*.xlsx'))
        file_list = [
            {
                'filename': f.name,
                'size': f.stat().st_size,
                'created': datetime.fromtimestamp(f.stat().st_ctime).isoformat()
            }
            for f in sorted(files, key=lambda x: x.stat().st_ctime, reverse=True)
        ]
        
        return jsonify({
            'success': True,
            'files': file_list
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Error al listar archivos',
            'errors': [str(e)]
        }), 500


def _get_month_name(month: int) -> str:
    """Convierte número de mes a nombre en español"""
    months = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre'
    }
    return months.get(month, 'Mes Desconocido')


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║     SISTEMA DE GENERACIÓN DE HORARIOS - BACKEND INICIADO      ║
    ║                      Puerto: 5000                             ║
    ║                 URL: http://localhost:5000                    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
