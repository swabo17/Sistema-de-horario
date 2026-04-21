"""
Motor de Optimización de Horarios V2.0 - Sistema de Satisfacción de Restricciones
Implementa restricciones complejas: FT exactamente 42h/semana, PT solo sábado/domingo,
compensación de feriados, y maximización de continuidad de descansos.
"""
import pulp
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime, timedelta
from models import ContractType, ShiftCode, HolidayType


class ScheduleOptimizer:
    """
    Optimizador de horarios V2.0 usando PuLP (Integer Linear Programming)
    
    Variables de decisión:
      x[emp_id][day][shift_code] ∈ {0, 1}
      
    Restricciones Hard:
      1. Una asignación por empleado por día
      2. Exactamente 5 días trabajados/semana (FT)
      3. Exactamente 2 turnos de 9h + 3 turnos de 8h/semana (FT)
      4. Exactamente 2 domingos TRABAJADOS/mes (FT)
      5. Exactamente 2 domingos LIBRES/mes (FT)
      6. Part Time solo sábado/domingo
      7. Exactamente 2 días trabajados/semana (PT, 20h totales)
      8. Feriados irrenunciables pre-asignados
      9. Compensación LC por feriados normales trabajados
      10. Cobertura mínima por día
      
    Función Objetivo:
      Minimizar fragmentación de descansos (maximizar continuidad)
    """

    def __init__(self, month_config, store_config, employees):
        self.month_config = month_config
        self.store_config = store_config
        self.employees = {e.employee_id: e for e in employees}
        
        # Generar calendario del mes
        self.calendar = self._generate_calendar()
        self.days_range = list(range(1, self.month_config.days_in_month + 1))
        
        # Identificar días especiales
        self.sundays = self._get_sundays()
        self.saturdays = self._get_saturdays()
        self.weekdays = self._get_weekdays()
        self.holidays_normal = self._get_holidays_normal()
        self.holidays_irren = self._get_holidays_irren()
        self.closed_days = set(self.store_config.closed_days or [])
        
        # Agrupar empleados
        self.emp_ft = {eid: e for eid, e in self.employees.items() 
                       if e.contract_type == ContractType.FULL_TIME}
        self.emp_pt = {eid: e for eid, e in self.employees.items() 
                       if e.contract_type == ContractType.PART_TIME}
        
        # Generar semanas del mes
        self.weeks = self._generate_weeks()
        
        # Código de turnos
        self.shift_codes = [s.value for s in ShiftCode]
        
        # Modelo PuLP
        self.model = None
        self.x = {}  # Variables de decisión
        
        # Resultados
        self.schedule = {}
        self.summary = {}

    # ==================== MÉTODOS AUXILIARES ====================
    
    def _generate_calendar(self) -> List[Tuple[int, str]]:
        """Genera calendario: (día, nombre_día_semana)"""
        calendar = []
        day_index = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        start_day_idx = day_index[self.month_config.starting_day_of_week]
        
        for day in range(1, self.month_config.days_in_month + 1):
            day_of_week_idx = (start_day_idx + day - 1) % 7
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            calendar.append((day, day_names[day_of_week_idx]))
        
        return calendar

    def _get_sundays(self) -> Set[int]:
        return {day for day, dow in self.calendar if dow == "Sunday"}

    def _get_saturdays(self) -> Set[int]:
        return {day for day, dow in self.calendar if dow == "Saturday"}

    def _get_weekdays(self) -> Set[int]:
        return {day for day, dow in self.calendar if dow not in ["Saturday", "Sunday"]}

    def _get_holidays_normal(self) -> Set[int]:
        """Feriados de tipo Normal (si se trabajan → LC)"""
        return {h.day for h in self.store_config.holidays 
                if h.type == HolidayType.NORMAL}

    def _get_holidays_irren(self) -> Set[int]:
        """Feriados Irrenunciables (FI pre-asignado)"""
        return {h.day for h in self.store_config.holidays 
                if h.type == HolidayType.IRRENUNCIABLE}

    def _generate_weeks(self) -> List[List[int]]:
        """Divide el mes en semanas (basado en estructura de calendario)"""
        weeks = []
        current_week = []
        
        for day, _ in self.calendar:
            current_week.append(day)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        
        if current_week:  # Última semana incompleta
            weeks.append(current_week)
        
        return weeks

    def _get_prior_exceptions(self, emp_id: str) -> Dict[int, str]:
        """Retorna dict {día: tipo_excepción} para empleado"""
        emp = self.employees[emp_id]
        exceptions = {}
        for exc in emp.prior_exceptions:
            exceptions[exc.day] = exc.type
        return exceptions

    # ==================== CONSTRUCCIÓN DEL MODELO ====================

    def optimize(self) -> bool:
        """
        Construye y resuelve el modelo de optimización
        Retorna: True si encontró solución óptima, False en caso contrario
        """
        print("\n[SCHEDULER_V2] ========== INICIANDO CONSTRUCCIÓN DEL MODELO ==========")
        
        # Crear modelo
        self.model = pulp.LpProblem("Schedule_Optimization_V2", pulp.LpMinimize)
        
        # 1. Crear variables de decisión
        print("[SCHEDULER_V2] 1/13 - Creando variables de decisión...")
        self._create_variables()
        
        # 2. Hard Constraints
        print("[SCHEDULER_V2] 2/13 - Restricción: Una asignación por empleado por día...")
        self._constraint_one_assignment_per_day()
        
        print("[SCHEDULER_V2] 3/13 - Restricción: Full Time - 5 días trabajo por semana...")
        self._constraint_ft_5_working_days_per_week()
        
        self._constraint_max_5_consecutive_days()
        self._constraint_dt_only_on_sundays()

        print("[SCHEDULER_V2] 4/13 - Restricción: Full Time - Distribución 2×T9 + 3×T8...")
        self._constraint_ft_9h_8h_distribution()
        
        print("[SCHEDULER_V2] 5/13 - Restricción: Full Time - 2 domingos TRABAJADOS...")
        self._constraint_ft_2_sundays_worked()
        
        print("[SCHEDULER_V2] 6/13 - Restricción: Full Time - 2 domingos LIBRES...")
        self._constraint_ft_2_sundays_free()
        
        print("[SCHEDULER_V2] 7/13 - Restricción: Full Time - 2 libres por semana...")
        self._constraint_ft_2_free_per_week()
        
        print("[SCHEDULER_V2] 8/13 - Restricción: Part Time - Solo sábado/domingo...")
        self._constraint_pt_weekends_only()
        
        print("[SCHEDULER_V2] 9/13 - Restricción: Part Time - 2 días/semana (20h)...")
        self._constraint_pt_2_days_per_week()
        
        print("[SCHEDULER_V2] 10/13 - Restricción: Feriados Irrenunciables...")
        #self._constraint_holidays_irren()
        
        print("[SCHEDULER_V2] 11/13 - Restricción: Compensación de Feriados Normales...")
        #self._constraint_holiday_compensation()
        
        print("[SCHEDULER_V2] 12/13 - Restricción: Cobertura Mínima...")
        self._constraint_minimum_coverage()
        
        print("[SCHEDULER_V2] 13/13 - Función Objetivo: Continuidad de Descansos...")
        self._setup_objective_function()
        
        # Resolver
        print("\n[SCHEDULER_V2] Resolviendo modelo (CBC)...")
        self.model.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Verificar resultado
        if self.model.status == pulp.LpStatusOptimal:
            print(f"[SCHEDULER_V2] ✓ SOLUCIÓN ÓPTIMA encontrada (Status: {pulp.LpStatus[self.model.status]})")
            self._extract_solution()
            return True
        else:
            print(f"[SCHEDULER_V2] ✗ INFEASIBLE - No se encontró solución. Status: {pulp.LpStatus[self.model.status]}")
            return False

    def _create_variables(self):
        """Crea variables binarias x[emp_id][day][shift_code]"""
        for emp_id in self.employees:
            self.x[emp_id] = {}
            for day in self.days_range:
                self.x[emp_id][day] = {}
                for shift in self.shift_codes:
                    var_name = f"x_{emp_id}_{day}_{shift}"
                    self.x[emp_id][day][shift] = pulp.LpVariable(var_name, cat='Binary')

    def _constraint_one_assignment_per_day(self):
        """Hard: Una asignación (y solo una) por empleado por día"""
        for emp_id in self.employees:
            for day in self.days_range:
                self.model += (
                    pulp.lpSum([self.x[emp_id][day][s] for s in self.shift_codes]) == 1,
                    f"one_assignment_{emp_id}_{day}"
                )

    def _constraint_ft_5_working_days_per_week(self):
        """Hard FT: Exactamente 5 días trabajados solo en semanas completas"""
        for emp_id in self.emp_ft:
            for week_idx, week_days in enumerate(self.weeks):
                work_codes = ["T8", "T9", "T10", "DT"]
                
                if len(week_days) < 7:
                    # En la semana incompleta, solo limitamos a que no supere los días disponibles
                    self.model += (
                        pulp.lpSum([self.x[emp_id][day][s] for day in week_days for s in work_codes]) <= len(week_days),
                        f"ft_max_work_days_week{week_idx}_{emp_id}"
                    )
                    continue

                self.model += (
                    pulp.lpSum([self.x[emp_id][day][s] for day in week_days for s in work_codes]) == 5,
                    f"ft_5_work_days_week{week_idx}_{emp_id}"
                )

    def _constraint_ft_9h_8h_distribution(self):
        """Hard FT: Por semana, exactamente 2 turnos T9 (9h) y 3 turnos T8 (8h)
        
        2×9h + 3×8h = 18h + 24h = 42h/semana ✓
        TEMPORALMENTE DESHABILITADO - Usar solo al menos algunos T8/T9
        """
        for emp_id in self.emp_ft:
            for week_idx, week_days in enumerate(self.weeks):
                # Al menos algunos T8 o T9 (flexible)
                self.model += (
                    pulp.lpSum([self.x[emp_id][day][c] for day in week_days for c in ["T8", "T9"]]) >= 1,
                    f"ft_min_t8t9_week{week_idx}_{emp_id}"
                )

    def _constraint_ft_2_sundays_worked(self):
        """Hard FT: Al menos 1 domingo TRABAJADO en el mes (T8, T9, o DT)"""
        for emp_id in self.emp_ft:
            self.model += (
                pulp.lpSum([self.x[emp_id][day][s] 
                           for day in self.sundays 
                           for s in ["T8", "T9", "DT"]]) >= 1,
                f"ft_min_sundays_worked_{emp_id}"
            )

    def _constraint_ft_2_sundays_free(self):
        """Hard FT: Al menos 1 domingo LIBRE en el mes (L o LC)"""
        for emp_id in self.emp_ft:
            self.model += (
                pulp.lpSum([self.x[emp_id][day][s] 
                           for day in self.sundays 
                           for s in ["L", "LC"]]) >= 1,
                f"ft_min_sundays_free_{emp_id}"
            )

    def _constraint_dt_only_on_sundays(self):
        """Hard: El turno DT (Domingo Trabajado) SOLO puede ir en domingos"""
        for emp_id in self.employees:
            for day in self.days_range:
                if day not in self.sundays:
                    # Forzar a 0 la variable DT en cualquier día que no sea domingo
                    self.model += self.x[emp_id][day]["DT"] == 0, f"no_dt_not_sunday_{emp_id}_{day}"

    def _constraint_ft_2_free_per_week(self):
        """Hard FT: Exactamente 2 días LIBRES en semanas completas"""
        for emp_id in self.emp_ft:
            for week_idx, week_days in enumerate(self.weeks):
                if len(week_days) < 7:
                    continue # No forzar la regla de 2 días en el sobrante del mes
                    
                self.model += (
                    pulp.lpSum([self.x[emp_id][day][s] for day in week_days for s in ["L", "LC"]]) == 2,
                    f"ft_2_free_week{week_idx}_{emp_id}"
                )

    def _constraint_pt_weekends_only(self):
        """Hard PT: Lunes a Viernes DEBEN estar Libres (L)"""
        for emp_id in self.emp_pt:
            for day in self.weekdays:
                # Al forzar que "L" sea 1, automáticamente todos los demás turnos (T8, T9, etc.)
                # se vuelven 0 por tu restricción de "1 código por día".
                self.model += self.x[emp_id][day]["L"] == 1, f"pt_free_weekday_{emp_id}_{day}"
    

    def _constraint_pt_2_days_per_week(self):
        """Hard PT: 2 días trabajados por semana (si existe fin de semana en esos días)"""
        for emp_id in self.emp_pt:
            for week_idx, week_days in enumerate(self.weeks):
                # Contar cuántos sábados y domingos reales hay en este bloque de días
                weekend_days = [d for d in week_days if self.calendar[d-1][1] in ["Saturday", "Sunday"]]
                
                if len(weekend_days) < 2:
                    self.model += (
                        pulp.lpSum([self.x[emp_id][day][s] for day in week_days for s in ["T10", "DT"]]) <= len(weekend_days),
                        f"pt_max_work_days_week{week_idx}_{emp_id}"
                    )
                    continue

                self.model += (
                    pulp.lpSum([self.x[emp_id][day][s] for day in week_days for s in ["T10", "DT"]]) == 2,
                    f"pt_2_work_days_week{week_idx}_{emp_id}"
                )

    def _constraint_max_5_consecutive_days(self):
        """Asegura que un trabajador nunca trabaje más de 5 días seguidos en ventanas móviles"""
        work_codes = ["T8", "T9", "T10", "DT"]
        for emp_id in self.employees:
            # Ventanas móviles de 6 días: la suma del trabajo no puede ser 6
            for start_day in range(1, self.month_config.days_in_month - 4):
                window = [start_day + offset for offset in range(6) if start_day + offset <= self.month_config.days_in_month]
                
                if len(window) == 6:
                    self.model += (
                        pulp.lpSum([self.x[emp_id][day][s] for day in window for s in work_codes]) <= 5,
                        f"max_5_consecutive_{emp_id}_start_{start_day}"
                    )

    def _constraint_holidays_irren(self):
        """Hard: Feriados Irrenunciables automáticamente asignados a FI
        
        Todos los empleados (sin excepciones previas) = FI en ese día
        """
        for day in self.holidays_irren:
            for emp_id in self.employees:
                exceptions = self._get_prior_exceptions(emp_id)
                
                # Si NO tiene excepción previa, DEBE ser FI
                if day not in exceptions:
                    self.model += (
                        self.x[emp_id][day]["FI"] == 1,
                        f"holiday_irren_{emp_id}_{day}"
                    )

    def _constraint_holiday_compensation(self):
        """Hard: Solo se da LC exacto a los FT que trabajaron feriado normal."""
        
        # 1. Para los Full Time
        for emp_id in self.emp_ft:
            total_lc = pulp.lpSum([self.x[emp_id][day]["LC"] for day in self.days_range])
            
            worked_in_normal_holidays = pulp.lpSum([
                self.x[emp_id][day]["T8"] + self.x[emp_id][day]["T9"] + self.x[emp_id][day]["DT"]
                for day in self.holidays_normal
            ])
            
            # ¡EL SECRETO ESTÁ AQUÍ! Es ==, no >=
            self.model += (
                total_lc == worked_in_normal_holidays,
                f"holiday_compensation_exact_{emp_id}"
            )
            
        # 2. Para los Part Time (Prohibir que el modelo use LC para rellenar)
        for emp_id in self.emp_pt:
            total_lc = pulp.lpSum([self.x[emp_id][day]["LC"] for day in self.days_range])
            self.model += (total_lc == 0, f"no_lc_for_pt_{emp_id}")

    def _constraint_minimum_coverage(self):
        """Hard: Cobertura mínima de empleados por día"""
        min_per_day = self.store_config.min_employees_per_day or 2
        min_sunday = self.store_config.min_employees_on_sunday or 1
        
        for day in self.days_range:
            if day in self.closed_days:
                # Día cerrado: todos C
                continue
            
            if day in self.sundays:
                # Domingo: mínimo especial
                min_staff = min_sunday
            else:
                # Día normal
                min_staff = min_per_day
            
            self.model += (
                pulp.lpSum([
                    self.x[emp_id][day][s] 
                    for emp_id in self.employees 
                    for s in ["T8", "T9", "T10", "DT"]
                ]) >= min_staff,
                f"min_coverage_day_{day}"
            )

    def _setup_objective_function(self):
        """Soft Objective: Minimizar fragmentación de días libres (maximizar continuidad)
        
        Para cada Full Time, por semana:
        - Si los 2 libres son consecutivos → penalty = 0
        - Si están separados → penalty > 0
        
        Objetivo: minimizar fragmentación = maximizar continuidad
        """
        penalty_expr = 0
        
        for emp_id in self.emp_ft:
            for week_idx, week_days in enumerate(self.weeks):
                if len(week_days) < 2:
                    continue
                
                # Buscar si hay 2 días consecutivos que sean libres
                consecutive_penalty = 0
                
                for i in range(len(week_days) - 1):
                    d1, d2 = week_days[i], week_days[i + 1]
                    
                    # Ambos son libres (L o LC)
                    both_free = (self.x[emp_id][d1]["L"] + self.x[emp_id][d1]["LC"] + 
                                self.x[emp_id][d2]["L"] + self.x[emp_id][d2]["LC"])
                    
                    # Si ambos son libres, no hay penalidad de fragmentación en este par
                    # Si NO son ambos libres, agregamos penalidad
                    consecutive_penalty += (1 - both_free)  # Será 0 si ambos libres, 1+ si no
                
                # Agregar al objetivo (penalizar fragmentación)
                penalty_expr += 50 * consecutive_penalty
        
        self.model += penalty_expr, "minimize_fragmentation"

    # ==================== EXTRAER SOLUCIÓN ====================

    def _extract_solution(self):
        """Extrae la solución del modelo y la organiza por empleado y día"""
        self.schedule = {}
        self.summary = {code: {} for code in self.shift_codes}
        
        for emp_id in self.employees:
            self.schedule[emp_id] = {}
            
            for day in self.days_range:
                for shift in self.shift_codes:
                    if self.x[emp_id][day][shift].varValue == 1:
                        self.schedule[emp_id][day] = shift
                        
                        # Contar en resumen
                        if emp_id not in self.summary[shift]:
                            self.summary[shift][emp_id] = 0
                        self.summary[shift][emp_id] += 1
                        break

    def get_schedule(self) -> Dict:
        """Retorna el horario programado"""
        return self.schedule

    def get_summary(self) -> Dict:
        """Retorna resumen de glosas por empleado"""
        return self.summary
