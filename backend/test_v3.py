import json
from scheduler_v3 import ScheduleOptimizerV3

# Datos de prueba
employees = [
    {
        'employee_id': 'EMP001',
        'name': 'Juan Pérez',
        'contract_type': 'Full Time'
    },
    {
        'employee_id': 'EMP002',
        'name': 'Karla Maldonado',
        'contract_type': 'Full Time'
    }
]

# Crear y ejecutar
try:
    print("[TEST] Creando optimizador...")
    optimizer = ScheduleOptimizerV3(employees=employees, days_in_month=30, min_coverage=1)
    
    print("[TEST] Ejecutando optimize()...")
    result = optimizer.optimize()
    
    print(f"[TEST] Status: {result['status']}")
    print(f"[TEST] Empleados en schedule: {list(result['schedule'].keys())}")
    print(f"[TEST] OK - No hay errores")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
