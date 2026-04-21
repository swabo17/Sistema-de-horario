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
        # Identificar feriados normales (que generan compensación)
        self.feriados_normales = [day for day, d_type in self.special_days.items() if d_type == "Holiday_Normal"] # Ajusta según tu lógica real de modelos
        
        # Calcular semanas (agrupar los días de 7 en 7 para las restricciones semanales)
        self.weeks = []
        current_week = []
        for day, _ in self.calendar:
            current_week.append(day)
            if len(current_week) == 7 or day == self.month_config.days_in_month:
                self.weeks.append(current_week)
                current_week = []
        
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
        # AQUÍ DEFINES TODOS LOS CÓDIGOS POSIBLES
        self.all_codes = ["T8", "T9", "T10", "DT", "L", "LC", "V", "LM", "FI", "C"]
        self.work_codes = ["T8", "T9", "T10", "DT"] # Solo los de trabajo
        
        for emp in self.employees:
            self.x[emp.employee_id] = {}
            for day in self.days_range:
                self.x[emp.employee_id][day] = {}
                for code in self.all_codes:
                    var_name = f"x_{emp.employee_id}_d{day}_{code}"
                    self.x[emp.employee_id][day][code] = pulp.LpVariable(var_name, cat='Binary')

    def _add_constraint_one_assignment_per_day(self):
        for emp in self.employees:
            for day in self.days_range:
                # Sumar todas las variables posibles y obligar a que sea 1
                constraint = pulp.lpSum([self.x[emp.employee_id][day][code] for code in self.all_codes]) == 1
                self.model += constraint, f"one_assign_{emp.employee_id}_d{day}"

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
        for emp in self.employees:
            # Evaluar ventanas de 6 días, la suma de trabajo no puede ser 6
            for start_day in range(1, self.month_config.days_in_month - 4):
                work_days_in_window = pulp.lpSum([
                    self.x[emp.employee_id][start_day + offset][s]
                    for offset in range(6)
                    for s in self.work_shift_codes # todos los códigos de turno de trabajo
                    if start_day + offset <= self.month_config.days_in_month
                ])
                self.model += (work_days_in_window <= 5, f"max_5_consecutive_{emp.employee_id}_d{start_day}")

    def _add_constraint_free_weekends(self):
        """Considerar 1 sábado y domingo libre por trabajador exceptuando a Sofía y Joaquín"""
        # Encontrar todos los pares de (Sábado, Domingo) del mes
        weekend_pairs = []
        for i in range(len(self.calendar) - 1):
            if self.calendar[i][1] == "Saturday" and self.calendar[i+1][1] == "Sunday":
                weekend_pairs.append((self.calendar[i][0], self.calendar[i+1][0]))

        for emp in self.employees:
            # Tu regla específica: omitir a estos trabajadores
            if emp.name.lower() in ["sofia", "joaquin", "sofía", "joaquín"]:
                continue
                
            # Crear una lista de variables binarias auxiliares que valen 1 SOLO si el Sab y Dom son Libres
            # Como PuLP no permite variables auxiliares dinámicas fácilmente sin crearlas en el __init__, 
            # un truco matemático es sumar los 'L' de cada par. Si L_sab + L_dom == 2, el fin de semana es libre.
            # Hacemos que la suma del "puntaje" de todos los fines de semana sea >= 2 (lo que equivale a 1 fin de semana completo)
            
            puntuacion_fines_de_semana = []
            for sab, dom in weekend_pairs:
                # Una variable continua entre 0 y 1 que solo llega a 1 si Sab(L) + Dom(L) == 2
                we_libre = pulp.LpVariable(f"we_libre_{emp.employee_id}_{sab}_{dom}", 0, 1)
                self.model += we_libre <= self.x[emp.employee_id][sab]["L"]
                self.model += we_libre <= self.x[emp.employee_id][dom]["L"]
                puntuacion_fines_de_semana.append(we_libre)
                
            # Exigir al menos 1 fin de semana completamente libre
            self.model += pulp.lpSum(puntuacion_fines_de_semana) >= 1, f"min_1_we_libre_{emp.employee_id}"

    def _add_constraint_monthly_free_days(self):
        for emp in self.employees:
            total_libres = pulp.lpSum([self.x[emp.employee_id][day]["L"] + self.x[emp.employee_id][day]["LC"] for day in self.days_range])
            
            feriados_trabajados = pulp.lpSum([self.x[emp.employee_id][f_day][s] 
                                            for f_day in self.feriados_normales 
                                            for s in self.work_shift_codes])
            
            # Base de libres (ej: 8 o 9 dependiendo de las semanas del mes) + los compensados
            base_libres = self.base_free_days_in_month
            self.model += (total_libres == base_libres + feriados_trabajados)

    def _constraint_dt_only_on_sundays(self):
        for emp in self.employees:
            for day, day_name in self.calendar:
                if day_name != "Sunday":
                    # Forzar a 0 la variable DT en cualquier día que no sea domingo
                    self.model += self.x[emp.employee_id][day]["DT"] == 0, f"No_DT_on_{day}_{emp.employee_id}"
    
    def _constraint_part_time_weekends(self):
        for emp in self.employees:
            if emp.contract_type == "Part Time":
                for day, day_name in self.calendar:
                    if day_name not in ["Saturday", "Sunday"]:
                        # No pueden tener turnos de trabajo de lunes a viernes
                        for shift in ["T8", "T9", "T10", "DT"]: # Agrega aquí tus códigos de trabajo
                            self.model += self.x[emp.employee_id][day][shift] == 0
                    else:
                        # En fin de semana, si trabajan, DEBE ser el turno de 10 horas
                        self.model += self.x[emp.employee_id][day]["T10"] <= 1 # Lógica base para T10

    def _constraint_full_time_weekly_structure(self):
        # Asumiendo que defines self.weeks como una lista de listas de días, ej: [[1,2,3,4,5,6,7], ...]
        for emp in self.employees:
            if emp.contract_type == "Full Time":
                for week_index, week_days in enumerate(self.weeks):
                    # 1. Exactamente 2 días libres por semana
                    self.model += pulp.lpSum([self.x[emp.employee_id][day]["L"] for day in week_days]) == 2
                    
                    # 2. Exactamente 3 turnos de 8 horas
                    self.model += pulp.lpSum([self.x[emp.employee_id][day]["T8"] for day in week_days]) == 3
                    
                    # 3. Exactamente 2 turnos de 9 horas (Puedes incluir DT aquí si el DT dura 9 horas)
                    self.model += pulp.lpSum([self.x[emp.employee_id][day]["T9"] + 
                                            self.x[emp.employee_id][day]["DT"] for day in week_days]) == 2
    
    def _constraint_max_5_consecutive_days(self):
        work_shifts = ["T8", "T9", "T10", "DT"]
        for emp in self.employees:
            for start_day in range(1, self.month_config.days_in_month - 4):
                # En cualquier ventana de 6 días, la suma de días trabajados no puede superar 5
                worked_in_window = pulp.lpSum([
                    self.x[emp.employee_id][start_day + offset][s]
                    for offset in range(6)
                    for s in work_shifts
                    if start_day + offset <= self.month_config.days_in_month
                ])
                self.model += worked_in_window <= 5

    def _constraint_min_sundays_ft(self):
        sundays = [day for day, name in self.calendar if name == "Sunday"]
        for emp in self.employees:
            if emp.contract_type == "Full Time":
                # La suma de DT en todos los domingos del mes debe ser >= 2
                self.model += pulp.lpSum([self.x[emp.employee_id][sun]["DT"] for sun in sundays]) >= 2

    def _constraint_one_free_weekend(self):
        # Identificar los pares de (Sábado, Domingo) del mes
        weekend_pairs = self._get_weekend_pairs() # Método que debes crear que retorne ej: [(6,7), (13,14)...]
        
        for emp in self.employees:
            # Excepciones específicas del equipo
            if emp.name.lower() in ["sofia", "joaquin", "sofía", "joaquín"]:
                continue 
                
            # Para el resto, deben tener al menos un par (Sab, Dom) donde ambos sean "L"
            # Esto requiere crear una variable binaria auxiliar por fin de semana en PuLP
            # ...

    def _constraint_holiday_compensation(self):
        for emp in self.employees:
            total_libres = pulp.lpSum([self.x[emp.employee_id][day]["L"] for day in self.days_range])
            
            # Contar cuántos feriados normales trabajó este empleado
            feriados_trabajados = pulp.lpSum([
                self.x[emp.employee_id][h_day]["T8"] + self.x[emp.employee_id][h_day]["T9"]
                for h_day in self.feriados_normales
            ])
            
            # Días libres base (ej: 4 semanas = 8 libres) + compensación
            dias_libres_base = self.calcular_libres_base_del_mes() 
            self.model += total_libres == dias_libres_base + feriados_trabajados

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

        print("[SCHEDULER] Agregando reglas de negocio V2.0...")
        self._constraint_dt_only_on_sundays()
        self._constraint_part_time_weekends()
        self._constraint_full_time_weekly_structure()
        self._constraint_max_5_consecutive_days()
        self._constraint_min_sundays_ft()
        self._constraint_holiday_compensation()

        print("[SCHEDULER] Agregando restricción: cobertura mínima...")
        self._add_constraint_coverage_requirements()
        
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
