# MODELADO TÉCNICO: RESTRICCIONES CLAVE V2.0

## Documento Técnico
**Explicación Matemática y Implementación de:**
1. Restricción de distribución de turnos de 9h vs 8h para exactamente 42h/semana (Full Time)
2. Restricción de compensación automática LC por feriados trabajados

---

## 1. RESTRICCIÓN: Distribución T9 vs T8 = 42h/Semana (Full Time)

### 1.1 Problema Matemático

**Objetivo:** Asegurar que todo Full Time trabaja **exactamente 42 horas cada semana**, distribuidas en:
- **2 turnos de 9 horas** (T9)
- **3 turnos de 8 horas** (T8)
- **2 días libres** (L o LC)

**Total:** 2×9 + 3×8 + 2×0 = 18 + 24 = **42 horas exactas ✓**

### 1.2 Formulación Matemática

#### Variables
```
x[e, d, T8] ∈ {0, 1}   for e ∈ E_FT, d ∈ D
x[e, d, T9] ∈ {0, 1}   for e ∈ E_FT, d ∈ D

Interpretación:
  x[e, d, T8] = 1  ⟺  empleado e trabaja 8 horas en día d
  x[e, d, T9] = 1  ⟺  empleado e trabaja 9 horas en día d
```

#### Primera Restricción: Exactamente 3 días de T8 por semana
```
∑_{d ∈ W_i} x[e, d, T8] = 3   ∀e ∈ E_FT, ∀W_i ∈ W

Significado:
  De los 5 días trabajados en la semana W_i, exactamente 3 deben ser T8
  Ejemplo semana: [T9, T9, T8, T8, T8, L, L]
                   lun vie mié jue vie sáb dom
                   ↑  ↑  ↑  ↑  ↑ = 5 días trabajados ✓
```

#### Segunda Restricción: Exactamente 2 días de T9 por semana
```
∑_{d ∈ W_i} x[e, d, T9] = 2   ∀e ∈ E_FT, ∀W_i ∈ W

Significado:
  De los 5 días trabajados, exactamente 2 deben ser T9

Total verificación:
  T8 count + T9 count = 3 + 2 = 5 días ✓
  Horas: 3×8 + 2×9 = 24 + 18 = 42 horas ✓
```

#### Tercera Restricción: Exactamente 5 días trabajados por semana
```
∑_{d ∈ W_i} (x[e, d, T8] + x[e, d, T9]) = 5   ∀e ∈ E_FT, ∀W_i ∈ W

Nota: Esta restricción es redundante si las dos anteriores se cumplen
      (3 + 2 = 5 automáticamente), pero la incluimos para explicititud
```

#### Cuarta Restricción: Exactamente 2 días libres por semana
```
∑_{d ∈ W_i} (x[e, d, L] + x[e, d, LC]) = 2   ∀e ∈ E_FT, ∀W_i ∈ W

Importancia: Garantiza que 5 + 2 = 7 días de la semana están asignados correctamente
```

### 1.3 Implementación en PuLP (Python)

```python
# scheduler_v2.py - Método _constraint_ft_9h_8h_distribution()

def _constraint_ft_9h_8h_distribution(self):
    """
    Hard FT: Por cada semana, exactamente 2 turnos T9 (9h) y 3 turnos T8 (8h)
    
    Esto garantiza: 2×9h + 3×8h = 18h + 24h = 42h/semana
    """
    
    # Iterar sobre cada Full Time
    for emp_id in self.emp_ft:
        
        # Iterar sobre cada semana del mes
        for week_idx, week_days in enumerate(self.weeks):
            
            # =====================================================
            # Restricción 1: Exactamente 2 turnos de T9 por semana
            # =====================================================
            constraint_2_t9 = pulp.lpSum([
                self.x[emp_id][day]["T9"]      # Variable binaria para T9
                for day in week_days            # Todos los días de la semana
            ]) == 2                             # EXACTAMENTE 2
            
            # Agregar restricción al modelo con nombre descriptivo
            self.model += (
                constraint_2_t9,
                f"ft_2_t9_week{week_idx}_{emp_id}"
            )
            
            # =====================================================
            # Restricción 2: Exactamente 3 turnos de T8 por semana
            # =====================================================
            constraint_3_t8 = pulp.lpSum([
                self.x[emp_id][day]["T8"]      # Variable binaria para T8
                for day in week_days            # Todos los días de la semana
            ]) == 3                             # EXACTAMENTE 3
            
            # Agregar restricción al modelo
            self.model += (
                constraint_3_t8,
                f"ft_3_t8_week{week_idx}_{emp_id}"
            )
            
            # Verificación lógica (solo para documentación):
            # T9_count + T8_count = 2 + 3 = 5 trabajados/semana ✓
            # Horas: 2×9 + 3×8 = 18 + 24 = 42 horas ✓


# Ejemplo de salida esperada para una semana:
# Semana 1 (días 1-7):
#
#   Día 1 (Lunes):   x[Juan, 1, T9] = 1   → 9 horas
#   Día 2 (Martes):  x[Juan, 2, T9] = 1   → 9 horas  (2 T9 completados)
#   Día 3 (Miérc):   x[Juan, 3, T8] = 1   → 8 horas
#   Día 4 (Jueves):  x[Juan, 4, T8] = 1   → 8 horas
#   Día 5 (Viernes): x[Juan, 5, T8] = 1   → 8 horas  (3 T8 completados)
#   Día 6 (Sábado):  x[Juan, 6, L]  = 1   → 0 horas
#   Día 7 (Domingo): x[Juan, 7, L]  = 1   → 0 horas
#
#   VERIFICACIÓN:
#   - T9 count: 2 ✓
#   - T8 count: 3 ✓
#   - Libres: 2 ✓
#   - Total horas: 2×9 + 3×8 = 42 ✓
```

### 1.4 Por Qué Esta Formulación es Correcta

| Aspecto | Razón |
|---------|-------|
| **Exactitud de horas** | 2×9 + 3×8 = 42 siempre, no hay variación |
| **Flexibilidad** | Permite combinaciones diferentes de qué días son T9 vs T8 |
| **Humanidad** | No cargar todos los T9 el mismo día (distribuye el esfuerzo) |
| **Compatibilidad con descansos** | Se puede tener exactamente 2 libres sin conflictos |
| **Escalabilidad** | Funciona para qualquier número de semanas del mes |

---

## 2. RESTRICCIÓN: Compensación de Feriados Normales → LC Automático

### 2.1 Problema Matemático

**Requisito:** Si un Full Time trabaja en un **feriado de tipo "Normal"**, el sistema debe:
1. Registrar que trabajó ese feriado especial (T8 o T9)
2. Automáticamente agregarle **mínimo 1 día Libre Compensado (LC)** durante el mismo mes
3. Este LC **no se cuenta** dentro de los 2 libres semanales (es extra)

**Ejemplo:**
```
Escenario: Feriado Normal el 2 de Abril (Jueves Santo)

Opción A - Trabajar el feriado:
  Día 2 (Jueves Santo): x[Juan, 2, T8] = 1  (trabaja 8h)
  ENTONCES: ∃ d' ∈ D tal que x[Juan, d', LC] = 1 en el mismo mes

Opción B - No trabajar el feriado:
  Día 2 (Jueves Santo): x[Juan, 2, L] = 1   (descansa)
  ENTONCES: No se requiere LC automático
```

### 2.2 Formulación Matemática

#### Identificar Feriados Normales
```
HOLIDAYS_NORMAL = {d ∈ D : holiday_type(d) = "Normal"}

Ejemplo: HOLIDAYS_NORMAL = {2, 15, 30}
         (Jueves Santo, Día X, Día Y)
```

#### Variable Auxiliar: Trabajo en Feriado Normal
```
worked_holiday[e, d] ∈ {0, 1}

Definición derivada (NO variable de decisión):
  worked_holiday[e, d] = x[e, d, T8] + x[e, d, T9]   ∀d ∈ HOLIDAYS_NORMAL
  
Interpretación:
  worked_holiday[Juan, 2] = 1
    ⟺ Juan trabajó T8 o T9 el 2 de Abril
```

#### Total de Feriados Normales Trabajados en el Mes
```
total_worked_holidays[e] = ∑_{d ∈ HOLIDAYS_NORMAL} worked_holiday[e, d]

Ejemplo:
  Si HOLIDAYS_NORMAL = {2, 15, 30} y Juan trabaja el 2 y el 30:
  total_worked_holidays[Juan] = 1 + 0 + 1 = 2
```

#### Total de Libres Compensados en el Mes
```
total_lc[e] = ∑_{d ∈ D} x[e, d, LC]

Ejemplo:
  Si Juan tiene LC los días {8, 22}:
  total_lc[Juan] = 2
```

#### LA RESTRICCIÓN PRINCIPAL: Compensación Obligatoria
```
∑_{d ∈ D} x[e, d, LC] ≥ ∑_{d ∈ HOLIDAYS_NORMAL} (x[e, d, T8] + x[e, d, T9])

O equivalentemente:
total_lc[e] ≥ total_worked_holidays[e]

Significado:
  Si trabajó N feriados normales → Debe tener ≥ N LibresCompensados en el mes
  Si no trabajó ningún feriado → Puede tener 0 LC (solo libres normales L)
  
Ejemplo verificación:
  Juan trabajó 2 feriados normales (días 2 y 30)
  Juan tiene 2 LC (días 8 y 22)
  → total_lc = 2 ≥ total_worked_holidays = 2 ✓ VÁLIDO
  
  Si Juan solo tiene 1 LC:
  → total_lc = 1 < total_worked_holidays = 2 ✗ INVÁLIDO (solución infeasible)
```

### 2.3 Implementación en PuLP (Python)

```python
# scheduler_v2.py - Método _constraint_holiday_compensation()

def _constraint_holiday_compensation(self):
    """
    Hard FT: Si trabaja en un feriado NORMAL (T8 o T9),
    DEBE tener mínimo 1 LC en el mes por cada feriado trabajado.
    
    Matemáticamente:
      ∑_{d ∈ D} x[e, d, LC] ≥ ∑_{d ∈ HOLIDAYS_NORMAL} (x[e, d, T8] + x[e, d, T9])
    """
    
    # Iterar sobre cada Full Time
    for emp_id in self.emp_ft:
        
        # ========================================================
        # LADO IZQUIERDO: Total de LC en el mes
        # ========================================================
        # Suma de todos los días del mes que son LC
        total_lc_in_month = pulp.lpSum([
            self.x[emp_id][day]["LC"]    # Variable binaria para LC
            for day in self.days_range   # Todos los días del mes
        ])
        
        # ========================================================
        # LADO DERECHO: Total de feriados normales trabajados
        # ========================================================
        # Suma de (T8 + T9) solo en los días que son feriados normales
        total_worked_in_normal_holidays = pulp.lpSum([
            self.x[emp_id][day]["T8"] + self.x[emp_id][day]["T9"]
            for day in self.holidays_normal  # Solo feriados de tipo "Normal"
        ])
        
        # ========================================================
        # RESTRICCIÓN: LC >= trabajados en feriados normales
        # ========================================================
        constraint = total_lc_in_month >= total_worked_in_normal_holidays
        
        self.model += (
            constraint,
            f"holiday_compensation_{emp_id}"
        )
        
        # DEBUG (recomendado habilitar para ver qué está pasando):
        print(f"[DEBUG] {emp_id}: En feriados normales {self.holidays_normal}")
        print(f"[DEBUG]        Si trabaja N feriados → Necesita ≥ N LC en mes")


# EJEMPLO: Instancia concreta del modelo
# ==========================================
# HOLIDAYS_NORMAL = {2, 15, 30}  # Fechas con feriado tipo "Normal"
# 
# Caso 1: Juan trabaja feriado del 2 de Abril
#   - Día 2: x[Juan, 2, T8] = 1  (trabajó)
#   - Días 15, 30: x[Juan, 15, *] ≠ T8/T9, x[Juan, 30, *] ≠ T8/T9 (no trabajó)
#   - total_worked_holidays = 1
#   
#   RESTRICCIÓN se convierte en: total_lc >= 1
#   Solución válida: Juan tiene x[Juan, 8, LC] = 1  (LC el 8 de Abril)
#                    o cualquier otro día con LC
#
# Caso 2: Juan no trabaja ningún feriado normal
#   - Días 2, 15, 30: No son T8 o T9
#   - total_worked_holidays = 0
#   
#   RESTRICCIÓN se convierte en: total_lc >= 0
#   Solución válida: Juan puede no tener LC (solamente L libres normales)
#                    O puede tener LC de todas formas (sin restricción)
#
# Caso 3: Juan trabaja los 3 feriados normales
#   - Días 2, 15, 30: Todo T8 o T9
#   - total_worked_holidays = 3
#   
#   RESTRICCIÓN se convierte en: total_lc >= 3
#   Juan DEBE tener mínimo 3 días LC en el mes
#   Solución válida: x[Juan, d1, LC] = 1, x[Juan, d2, LC] = 1, x[Juan, d3, LC] = 1
#                   (donde d1, d2, d3 son días diferentes)


# RELACIÓN CON RESTRICCIÓN DE 2 LIBRES/SEMANA:
# =============================================
# Los 2 libres por semana (L o LC) son DISTINTOS de los LC por compensación:
#
# Semana 1:
#   x[Juan, 1, L] = 1    (líbre normal, cuenta para "2 libres/semana")
#   x[Juan, 2, LC] = 1   (líbre compensado por feriado normal trabajado)
#   
#   → Semana tiene: L=1 + LC=1 = 2 "días no trabajados" ✓
#   → Compensa uno de los feriados normales trabajados el mes ✓
#   → Ambas restricciones se satisfacen simultáneamente
```

### 2.4 Por Qué Esta Formulación es Correcta

| Aspecto | Razón |
|---------|-------|
| **Fairness** | Si trabajas feriado → derecho a descanso extra comprobado |
| **Automatización** | Sistema calcula automáticamente sin input manual |
| **Generalización** | Funciona para 0, 1, 2, ... feriados normales en el mes |
| **Segregación** | LC no mezcla con L (tipos de descanso distinguibles en Excel) |
| **Auditoría** | Fácil verificar: #LC_marcados = #feriados_trabajados |

### 2.5 Caso Especial: Feriados Irrenunciables

```
IMPORTANTE: Los feriados IRRENUNCIABLES (FI) NO disparan compensación

Escenario: Feriado Irrenunciable el 25 de Abril (Día del Trabajador)
  
Todos los empleados (excepto con excepciones previas):
  x[*,  25, FI] = 1  (pre-asignado fijo)
  
NO hay restricción de LC para estos, porque:
  - El código usado es FI (no T8/T9)
  - FI no es parte de la suma: ∑ (x[e, d, T8] + x[e, d, T9])
  - Por lo tanto: total_worked_holidays NO incluye días FI
  
Matemáticamente:
  total_worked_holidays[e] = ∑_{d ∈ HOLIDAYS_NORMAL} (T8 o T9)
  # FI no entra en esta suma
```

---

## 3. INTEGRACIÓN AMBAS RESTRICCIONES

### 3.1 Diagrama Conceptual

```
                SEMANA 1
        ┌───────────────────────┐
        │ L1  L2  L3  L4  L5  L6  L7
        ├───────────────────────┤
Turnos: │ T9  T9  T8  T8  T8  L   L
Horas:  │ 9   9   8   8   8   0   0
        │ └────────────────────┬──┘
        │    5 trabajados   2 libres
        │    42 horas       semanales
        │
        │ Restricción 1: ∑T9 = 2 ✓
        │ Restricción 2: ∑T8 = 3 ✓
        │ Restricción 3: ∑(L+LC) = 2 ✓
        └──────────────────────→ TOTALES: 42h/semana
```

### 3.2 Ejemplo Completo de Mes con Ambas Restricciones

```
DATOS DE ENTRADA:
- Mes: Abril 2026 (30 días)
- Feriados Normales: {2, 15, 30}
- Empleado: Juan Pérez (Full Time)

SOLUCIÓN DEL MODELO:

Semana 1 (días 1-7):
  Día 1 (Lun): T9 (9h)
  Día 2 (Mar): T8 (8h) ← Trabajó feriado normal
  Día 3 (Mié): T8 (8h)
  Día 4 (Jue): T8 (8h)
  Día 5 (Vie): T9 (9h)
  Día 6 (Sáb): L  (0h)
  Día 7 (Dom): L  (0h)
  Subtotal: 2×9 + 3×8 + 2×0 = 42h ✓

  Restricciones cumplidas:
  ✓ ∑T9 = 2  (días 1, 5)
  ✓ ∑T8 = 3  (días 2, 3, 4)
  ✓ ∑L = 2   (días 6, 7)
  ✓ Trabajó feriado el 2: total_worked_holidays += 1

Semanas 2-4... (similar estructura)

Semana 5 (días 29-30):
  Día 29 (Jue): T9 (9h)
  Día 30 (Vie): T8 (8h) ← Trabajó feriado normal

  Subtotal mes para compensación:
  - Feriados normales trabajados: {2, 30} → count = 2
  - Total LC requerido: >= 2

Compensación en el mes (distribuida):
  Día 8 (Lun):  LC (0h) ← Compensa feriado del día 2
  Día 22 (Lun): LC (0h) ← Compensa feriado del día 30
  
VERIFICACIÓN FINAL:
  ✓ Cada semana:  42h exactamente
  ✓ Cada semana:  2 T9, 3 T8, 2 libres (L o LC)
  ✓ Todo el mes:  4 domingos trabajados + 4 libres
  ✓ Compensación: 2 feriados  normales trabajados = 2 LC en el mes
  ✓ SOLUCIÓN VÁLIDA
```

---

## 4. PSEUDOCÓDIGO UNIFICADO

```
PROCEDIMIENTO optimizar_horarios():
  
  1. CREAR MODELO PULP
     model ← new LpProblem(MINIMIZE)
  
  2. CREAR VARIABLES BINARIAS
     for cada empleado e, día d, código s:
       x[e, d, s] ← binary_variable()
  
  3. AGREGAR RESTRICCIONES HARD
  
     3.1. Una asignación por día
          ∀e, d: ∑_s x[e, d, s] = 1
     
     3.2. FULL TIME: Distribución T9 vs T8
          ∀e ∈ E_FT, ∀semana w:
             ∑_{d ∈ w} x[e, d, T9] = 2   ← EXACTAMENTE 2
             ∑_{d ∈ w} x[e, d, T8] = 3   ← EXACTAMENTE 3
             (Garantiza: 2×9 + 3×8 = 42h)
     
     3.3. FULL TIME: Compensación por feriados
          ∀e ∈ E_FT:
             ∑_{d ∈ D} x[e, d, LC] ≥ ∑_{d ∈ NORMAL_HOLS} (x[e, d, T8] + x[e, d, T9])
             (Si trabaja N feriados → necesita ≥ N LC)
     
     3.4-3.10. Otras restricciones (cobertura, domingos, etc.)
  
  4. CONFIGURAR FUNCIÓN OBJETIVO
     Minimizar: fragmentación de descansos
     (Preferencia soft de que 2 libres sean consecutivos)
  
  5. RESOLVER
     status ← model.solve(CBC_SOLVER)
  
  6. EXTRAER SOLUCIÓN
     if status == OPTIMAL:
       schedule ← parse solution
       return ÉXITO
     else:
       return INFEASIBLE
```

---

## 5. VALIDACIÓN POST-SOLUCIÓN

Algoritmo para verificar una solución:

```python
def validate_solution(schedule, summary, employees, holidays_normal, holidays_irren):
    """
    Verifica que una solución cumple con TODAS las restricciones
    """
    
    for emp_id, days_assignments in schedule.items():
        emp_type = employees[emp_id].contract_type
        
        if emp_type == "Full Time":
            
            # Validar 42h/semana
            for week in weeks:
                t9_count = sum(1 for d in week if days_assignments[d] == "T9")
                t8_count = sum(1 for d in week if days_assignments[d] == "T8")
                
                assert t9_count == 2, f"❌ {emp_id} semana {week}: T9 count = {t9_count} (expected 2)"
                assert t8_count == 3, f"❌ {emp_id} semana {week}: T8 count = {t8_count} (expected 3)"
                
                hours = t9_count * 9 + t8_count * 8
                assert hours == 42, f"❌ {emp_id} semana {week}: {hours}h (expected 42)"
                print(f"✅ {emp_id} semana {week}: 2×T9 + 3×T8 = 42h")
            
            # Validar compensación por feriados normales
            worked_holidays = sum(1 for d in holidays_normal 
                                 if days_assignments[d] in ["T8", "T9"])
            total_lc = sum(1 for d in days_range 
                          if days_assignments[d] == "LC")
            
            assert total_lc >= worked_holidays, \
                f"❌ {emp_id}: trabajó {worked_holidays} feriados pero tiene {total_lc} LC"
            print(f"✅ {emp_id}: {worked_holidays} feriados trabajados ≤ {total_lc} LC compensados")
    
    return True
```

---

## CONCLUSIÓN

Ambas restricciones funcionan en sinergia:

| Restricción | Propósito | Ecuación |
|-------------|---------|----------|
| **T9 vs T8** | Garantizar exactamente 42h/semana | ∑T9=2, ∑T8=3 |
| **Compensación LC** | Justicia por trabajar feriados especiales | ∑LC ≥ (feriados trabajados) |

Combinadas aseguran un horario:
✅ **Exacto en horas**
✅ **Justo laboralmente**  
✅ **Automático (sin ajustes manuales)**
✅ **Auditable (fácil verificar)**

