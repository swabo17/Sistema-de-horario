"""
Motor de optimización de horarios usando PuLP
Resuelve el Problema de Satisfacción de Restricciones (CSP)
"""
import pulp
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta
from models import (
    SchedulingRequestData, Employee, SpecialDay, 
    DayOfWeek, ShiftCode
)


class ScheduleOptimizer:
    """
    Optimizador de horarios usando PuLP
    Variables de decisión: x[employee_id][day][shift_code] ∈ {0, 1}
    """

    def __init__(self, request_data: SchedulingRequestData):
        self.request_data = request_data
        self.month_config = request_data.month_config
        self.store_config = request_data.store_config
        self.employees = request_data.employees
        
        # Crear calendario del mes
        self.calendar = self._generate_calendar()
        self.days_range = range(1, self.month_config.days_in_month + 1)
        
        # Identificar días de la semana
        self.sundays = self._get_sundays()
        self.special_days = self._parse_special_days()
        
        # Crear modelo PuLP
        self.model = pulp.LpProblem("Schedule_Optimization", pulp.LpMinimize)
        
        # Variables de decisión
        self.x = {}  # x[emp_id][day][shift_code]
        
        # Resultados
        self.schedule = {}
        self.summary = {}

    def _generate_calendar(self) -> List[Tuple[int, str]]:
        """Genera el calendario del mes indicando día y día de semana"""
        calendar = []
        
        # Mapear nombre del día a índice (0=Monday, 6=Sunday)
        day_index = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }
        
        start_day_index = day_index[self.month_config.starting_day_of_week]
        
        for day in range(1, self.month_config.days_in_month + 1):
            # Calcular el índice del día de semana
            day_of_week_index = (start_day_index + day - 1) % 7
            
            # Invertir índice a nombre
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = day_names[day_of_week_index]
            
            calendar.append((day, day_name))
        
        return calendar

    def _get_sundays(self) -> Set[int]:
        """Retorna los días que son domingo en el mes"""
        sundays = set()
        for day, day_name in self.calendar:
            if day_name == "Sunday":
                sundays.add(day)
        return sundays

    def _parse_special_days(self) -> Dict[int, str]:
        """Parsea días especiales (feriados, cierres) desde config"""
        special = {}
        for special_day in self.store_config.special_days:
            special[special_day.day] = special_day.type  # "FI" o "C"
        return special

    def _get_prior_exceptions(self, employee: Employee) -> Dict[int, str]:
        """Extrae excepciones previas del empleado (vacaciones, licencias)"""
        exceptions = {}
        for exc in employee.prior_exceptions:
            exceptions[exc.day] = exc.type  # "V" o "LM"
        return exceptions

    def _is_eligible_day(self, day: int, employee_id: str) -> bool:
        """Verifica si un día es elegible para trabajar (no es feriado/cierre) en sentido general"""
        # Un día es NO elegible si es FI o C (excepto que pueda trabajar compensado en FI)
        if day in self.special_days:
            return self.special_days[day] != "FI" and self.special_days[day] != "C"
        return True

    def _create_variables(self):
        """
        Crea variables de decisión:
        x[emp_id][day][shift_code] ∈ {0, 1}
        """
        shift_codes = ["T", "DT", "L", "LC", "V", "LM"]
        
        for emp in self.employees:
            self.x[emp.employee_id] = {}
            
            for day in self.days_range:
                self.x[emp.employee_id][day] = {}
                
                for code in shift_codes:
                    var_name = f"x_{emp.employee_id}_d{day}_{code}"
                    self.x[emp.employee_id][day][code] = pulp.LpVariable(
                        var_name, cat='Binary'
                    )

    def _add_constraint_one_assignment_per_day(self):
        """
        Restricción: Cada empleado tiene exactamente una asignación por día
        ∑_{code} x[e][d][code] = 1, ∀e, d
        """
        for emp in self.employees:
            for day in self.days_range:
                codes = ["T", "DT", "L", "LC", "V", "LM", "C", "FI"]
                constraint = pulp.lpSum([
                    self.x[emp.employee_id][day].get(code, 0)
                    for code in codes
                    if code in self.x[emp.employee_id][day]
                ]) == 1
                
                self.model += constraint, f"one_assign_{emp.employee_id}_d{day}"

    def _add_constraint_fixed_exceptions(self):
        """
        Restricción: Aplicar pre-asignaciones fijas (V, LM, FI, C)
        """
        for emp in self.employees:
            exceptions = self._get_prior_exceptions(emp)
            
            for day, exc_type in exceptions.items():
                if day <= self.month_config.days_in_month:
                    # Forzar la asignación
                    if exc_type in self.x[emp.employee_id][day]:
                        self.model += (
                            self.x[emp.employee_id][day][exc_type] == 1,
                            f"fixed_{emp.employee_id}_d{day}_{exc_type}"
                        )
        
        # Aplicar días especiales de tienda (FI, C)
        for day, day_type in self.special_days.items():
            if day <= self.month_config.days_in_month:
                for emp in self.employees:
                    if day_type in self.x[emp.employee_id][day]:
                        self.model += (
                            self.x[emp.employee_id][day][day_type] == 1,
                            f"fixed_store_{emp.employee_id}_d{day}_{day_type}"
                        )

    def _add_constraint_max_hours_per_month(self):
        """
        Restricción 1: Límite de horas mensuales
        ∑_{d} h_d * (x_T[e][d] + x_DT[e][d]) ≤ H_max[e]
        """
        for emp in self.employees:
            hours_sum = pulp.lpSum([
                emp.hours_per_day * self.x[emp.employee_id][day]["T"] +
                emp.hours_per_day * self.x[emp.employee_id][day]["DT"]
                for day in self.days_range
            ])
            
            self.model += (
                hours_sum <= emp.max_hours_per_month,
                f"max_hours_{emp.employee_id}"
            )

    def _add_constraint_max_consecutive_work_days(self):
        """
        Restricción 2: Máximo días consecutivos trabajando
        ∑_{j=0}^{6} (x_T[e][d+j] + x_DT[e][d+j]) ≤ 6, ∀e,d
        """
        for emp in self.employees:
            max_days = emp.max_consecutive_work_days
            
            # Ventanas de 7 días consecutivos
            for start_day in range(1, self.month_config.days_in_month - 5):
                work_hours_in_window = pulp.lpSum([
                    self.x[emp.employee_id][start_day + offset]["T"] +
                    self.x[emp.employee_id][start_day + offset]["DT"]
                    for offset in range(7)
                    if start_day + offset <= self.month_config.days_in_month
                ])
                
                self.model += (
                    work_hours_in_window <= max_days,
                    f"max_consecutive_{emp.employee_id}_d{start_day}"
                )

    def _add_constraint_coverage_requirements(self):
        """
        Restricción: Cobertura mínima de empleados por día
        ∑_e (x_T[e][d] + x_DT[e][d]) ≥ C_min[d]
        """
        min_per_day = self.store_config.min_employees_per_day
        min_on_sunday = self.store_config.min_employees_on_sunday
        
        for day in self.days_range:
            # Saltar si es local cerrado o feriado
            if day in self.special_days and self.special_days[day] in ["C", "FI"]:
                continue
            
            working_employees = pulp.lpSum([
                self.x[emp.employee_id][day]["T"] +
                self.x[emp.employee_id][day]["DT"]
                for emp in self.employees
            ])
            
            if day in self.sundays:
                min_coverage = min_on_sunday
            else:
                min_coverage = min_per_day
            
            self.model += (
                working_employees >= min_coverage,
                f"coverage_d{day}"
            )

    def _add_constraint_minimum_rest_days(self):
        """
        Restricción: Mínimo días de descanso por semana
        """
        pass  # Opcional para fase inicial

    def _add_objective_function(self):
        """
        Función objetivo ficticia (CSP = satisfacción de restricciones)
        Minimizar: Z = 0 (o suma pequeña)
        """
        # Dado que es un CSP, la función objetivo es ficticia
        # Podemos dejar vacía o minimizar una constante
        self.model += 0, "objective"

    def optimize(self) -> bool:
        """
        Ejecuta la optimización
        Retorna: True si encontró solución, False en caso contrario
        """
        print("[SCHEDULER] Creando variables de decisión...")
        self._create_variables()
        
        print("[SCHEDULER] Agregando restricción: una asignación por día...")
        self._add_constraint_one_assignment_per_day()
        
        print("[SCHEDULER] Agregando restricción: excepciones fijas...")
        self._add_constraint_fixed_exceptions()
        
        print("[SCHEDULER] Agregando restricción 1: límite de horas...")
        self._add_constraint_max_hours_per_month()
        
        print("[SCHEDULER] Agregando restricción 2: máximo días consecutivos...")
        self._add_constraint_max_consecutive_work_days()
        
        print("[SCHEDULER] Agregando restricción: cobertura mínima...")
        self._add_constraint_coverage_requirements()
        
        print("[SCHEDULER] Agregando función objetivo...")
        self._add_objective_function()
        
        print("[SCHEDULER] Resolviendo modelo...")
        # Usar solver predeterminado (CBC en Linux, PULP_CBC_CMD)
        status = self.model.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if status != pulp.LpStatusOptimal:
            print(f"[SCHEDULER] ERROR: No se encontró solución óptima. Status: {pulp.LpStatus[status]}")
            return False
        
        print("[SCHEDULER] Solución encontrada: ÓPTIMA")
        self._extract_solution()
        return True

    def _extract_solution(self):
        """
        Extrae la solución del modelo y la dumpa en estructuras de datos
        """
        self.schedule = {}
        self.summary = {}
        
        for emp in self.employees:
            self.schedule[emp.employee_id] = {}
            self.summary[emp.employee_id] = {
                "T": 0, "DT": 0, "L": 0, "LC": 0,
                "V": 0, "LM": 0, "FI": 0, "C": 0
            }
            
            for day in self.days_range:
                for code in self.x[emp.employee_id][day]:
                    var = self.x[emp.employee_id][day][code]
                    if var.varValue == 1:
                        self.schedule[emp.employee_id][day] = code
                        self.summary[emp.employee_id][code] += 1
                        break

    def get_schedule(self) -> Dict:
        """Retorna el horario generado"""
        return self.schedule

    def get_summary(self) -> Dict:
        """Retorna el resumen de glosas por empleado"""
        return self.summary

    def get_calendar(self) -> List[Tuple[int, str]]:
        """Retorna el calendario del mes"""
        return self.calendar
