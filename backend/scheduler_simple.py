"""
Scheduler SIMPLE - Versión minimalista que FUNCIONA
Solo restricciones básicas: una asignación por día, cobertura mínima
"""
import pulp
from typing import Dict, List
from models import Employee, MonthConfig, StoreConfig, ShiftCode


class SimpleScheduleOptimizer:
    def __init__(self, month_config: MonthConfig, store_config: StoreConfig, employees: List[Employee]):
        self.month_config = month_config
        self.store_config = store_config
        self.employees = employees
        self.calendar = {}
        self.schedule = {}
        self.summary = {}
        
        # Variables de decisión
        self.x = {}
        
        # Modelo PuLP
        self.model = pulp.LpProblem("Schedule_Simple", pulp.LpMinimize)
        
        # Configuración
        self.days_range = list(range(1, month_config.days_in_month + 1))
        self.shift_codes = ["T8", "T9", "T10", "DT", "L", "LC", "V", "LM", "FI", "C"]
        self.emp_ids = [e.employee_id for e in employees]
        
        # Separar FT y PT
        self.emp_ft = [e.employee_id for e in employees if "Full Time" in str(e.contract_type)]
        self.emp_pt = [e.employee_id for e in employees if "Part Time" in str(e.contract_type)]
        
        print("[SIMPLE] ========== OPTIMIZADOR SIMPLE ==========")
        print(f"[SIMPLE] Full Time: {len(self.emp_ft)}, Part Time: {len(self.emp_pt)}")

    def optimize(self) -> bool:
        """Ejecuta la optimización"""
        try:
            self._setup_decision_variables()
            self._constraint_one_per_day()
            self._constraint_minimum_coverage()
            self._setup_objective()
            
            # Resolver
            print(f"[SIMPLE] Resolviendo...")
            self.model.solve(pulp.PULP_CBC_CMD(msg=0))
            
            if self.model.status != pulp.LpStatusOptimal:
                print(f"[SIMPLE] ✗ Status: {pulp.LpStatus[self.model.status]}")
                return False
            
            print(f"[SIMPLE] ✓ Solución encontrada")
            self._extract_solution()
            return True
            
        except Exception as e:
            print(f"[SIMPLE] Error: {str(e)}")
            return False

    def _setup_decision_variables(self):
        """Crear variables x[emp][day][shift] = 0/1"""
        for emp_id in self.emp_ids:
            self.x[emp_id] = {}
            for day in self.days_range:
                self.x[emp_id][day] = {}
                for shift in self.shift_codes:
                    var_name = f"x_{emp_id}_{day}_{shift}"
                    self.x[emp_id][day][shift] = pulp.LpVariable(var_name, cat='Binary')

    def _constraint_one_per_day(self):
        """Una asignación por empleado por día"""
        for emp_id in self.emp_ids:
            for day in self.days_range:
                self.model += (
                    pulp.lpSum([self.x[emp_id][day][s] for s in self.shift_codes]) == 1,
                    f"one_{emp_id}_{day}"
                )

    def _constraint_minimum_coverage(self):
        """Cobertura mínima: cierto número de empleados trabajando por día"""
        min_per_day = self.store_config.min_employees_per_day
        work_codes = ["T8", "T9", "T10", "DT"]
        
        for day in self.days_range:
            self.model += (
                pulp.lpSum([self.x[emp_id][day][s] 
                           for emp_id in self.emp_ids 
                           for s in work_codes]) >= min_per_day,
                f"coverage_day{day}"
            )

    def _setup_objective(self):
        """Objetivo: Minimizar nada (solo satisfacer restricciones)"""
        # El objetivo es vacío - solo queremos satisfacer restricciones
        self.model += 0, "dummy_objective"

    def _extract_solution(self):
        """Extrae la solución"""
        self.schedule = {}
        self.summary = {emp_id: {} for emp_id in self.emp_ids}
        
        for emp_id in self.emp_ids:
            self.schedule[emp_id] = {}
            
            for day in self.days_range:
                for shift in self.shift_codes:
                    if self.x[emp_id][day][shift].varValue == 1:
                        self.schedule[emp_id][day] = shift
                        
                        # Contar en resumen: summary[emp_id][shift_code]
                        if shift not in self.summary[emp_id]:
                            self.summary[emp_id][shift] = 0
                        self.summary[emp_id][shift] += 1
                        break

    def get_schedule(self) -> Dict:
        """Retorna el horario"""
        return self.schedule

    def get_summary(self) -> Dict:
        """Retorna resumen"""
        return self.summary
