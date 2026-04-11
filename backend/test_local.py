"""
Script de prueba local - Sin necesidad de hacer requests HTTP
"""
import json
from pathlib import Path
from models import SchedulingRequestData
from scheduler import ScheduleOptimizer
from excel_generator import ExcelScheduleGenerator


def main():
    print("\n" + "="*70)
    print("PRUEBA LOCAL DE GENERADOR DE HORARIOS")
    print("="*70 + "\n")
    
    # Cargar datos de prueba
    with open('test_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Parsear datos
    request_data = SchedulingRequestData(**raw_data['scheduling_request'])
    
    print(f"[TEST] Tienda: {request_data.store_config.store_name}")
    print(f"[TEST] Empleados: {len(request_data.employees)}")
    print(f"[TEST] Mes: {request_data.month_config.month}/{request_data.month_config.year}")
    print(f"[TEST] Días especiales: {len(request_data.store_config.special_days)}\n")
    
    # Listar empleados
    print("EMPLEADOS:")
    for emp in request_data.employees:
        print(f"  - {emp.name:20} ({emp.contract_type:12}) - {emp.max_hours_per_month} hrs/mes")
    print()
    
    # Crear optimizador
    print("[OPTIMIZER] Inicializando optimizador...")
    optimizer = ScheduleOptimizer(request_data)
    
    # Ejecutar optimización
    print("[OPTIMIZER] Ejecutando optimización...")
    success = optimizer.optimize()
    
    if not success:
        print("[ERROR] No se encontró solución factible")
        return
    
    print("[SUCCESS] Optimización completada exitosamente!\n")
    
    # Obtener resultados
    schedule = optimizer.get_schedule()
    summary = optimizer.get_summary()
    calendar = optimizer.get_calendar()
    
    # Mostrar resumen
    print("RESUMEN DE ASIGNACIONES:")
    print("-" * 70)
    for emp_id, counts in summary.items():
        emp_name = next((e.name for e in request_data.employees if e.employee_id == emp_id), emp_id)
        print(f"\n{emp_name}:")
        for code, count in sorted(counts.items()):
            if count > 0:
                print(f"  {code}: {count:2d} días")
    
    # Generar Excel
    print("\n" + "-" * 70)
    print("[EXCEL] Generando archivo Excel...")
    
    output_dir = Path("./generated_schedules")
    output_dir.mkdir(exist_ok=True)
    
    excel_path = output_dir / "horario_ejemplo.xlsx"
    
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
        month_name="Abril",
        year=2026
    )
    
    print(f"[SUCCESS] Excel guardado en: {excel_path}")
    print("\n" + "="*70)
    print("PRUEBA COMPLETADA EXITOSAMENTE")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
