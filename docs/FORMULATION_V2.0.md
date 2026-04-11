# FORMULACIÓN MATEMÁTICA V2.0 - Sistema de Horarios Retail
**Sistema de Generación de Horarios con Restricciones Avanzadas de Negocio**

---

## 1. ESTRUCTURA DE DATOS JSON (Frontend → Backend)

### Ejemplo Completo del Payload Angular → Python

```json
{
  "scheduling_request": {
    "month_config": {
      "year": 2026,
      "month": 4,
      "days_in_month": 30,
      "starting_day_of_week": "Wednesday"
    },
    "store_config": {
      "store_name": "Sucursal Centro",
      "min_employees_per_day": 2,
      "min_employees_on_sunday": 1,
      "holidays": [
        {
          "day": 2,
          "type": "Normal",
          "description": "Jueves Santo"
        },
        {
          "day": 25,
          "type": "Irrenunciable",
          "description": "Día del Trabajador"
        }
      ],
      "closed_days": [12]
    },
    "employees": [
      {
        "employee_id": "EMP001",
        "name": "Juan Pérez",
        "contract_type": "Full Time",
        "prior_exceptions": [
          {
            "day": 15,
            "type": "V",
            "description": "Vacaciones"
          }
        ]
      },
      {
        "employee_id": "EMP002",
        "name": "María García",
        "contract_type": "Full Time",
        "prior_exceptions": []
      },
      {
        "employee_id": "EMP003",
        "name": "Carlos López",
        "contract_type": "Part Time",
        "prior_exceptions": []
      },
      {
        "employee_id": "EMP004",
        "name": "Ana Martínez",
        "contract_type": "Part Time",
        "prior_exceptions": []
      }
    ]
  }
}
```

---

## 2. CONJUNTOS, ÍNDICES Y PARÁMETROS

### 2.1 Conjuntos
- **E** = Conjunto de empleados
- **D** = Conjunto de días del mes (1 a 30/31)
- **S** = {T8, T9, T10, DT, L, LC, V, LM, FI, C} = Códigos de turno
- **W** = Conjuntos de semanas del mes (aproximadamente 4-5 semanas)

### 2.2 Clasificación de Empleados
- **E_FT** ⊆ E = Empleados Full Time
- **E_PT** ⊆ E = Empleados Part Time

### 2.3 Parámetros Fijos
- **h_T8** = 8 horas/día
- **h_T9** = 9 horas/día
- **h_T10** = 10 horas/día
- **h_42** = 42 horas/semana (Full Time)
- **h_20** = 20 horas/semana (Part Time)
- **d_work_FT** = 5 días trabajados/semana (Full Time)
- **d_rest_FT** = 2 días libres/semana (Full Time)
- **d_work_PT** = 2 días trabajados/semana (Part Time - solo Sábado/Domingo)

### 2.4 Identificadores de Días Especiales
- **SUNDAYS** = {d ∈ D : día_de_semana(d) = Sunday}
- **SATURDAYS** = {d ∈ D : día_de_semana(d) = Saturday}
- **HOLIDAYS_NORMAL** = {d : tipo_feriado(d) = Normal}
- **HOLIDAYS_IRREN** = {d : tipo_feriado(d) = Irrenunciable}
- **WEEKDAYS** = {d ∈ D : lunes a viernes}

---

## 3. VARIABLES DE DECISIÓN

### 3.1 Variable Principal (Binaria)
```
x[e, d, s] ∈ {0, 1}   para toda e ∈ E, d ∈ D, s ∈ S

Significado:
  x[e, d, s] = 1  ⟺  empleado e está asignado código s en día d
  x[e, d, s] = 0  ⟹  empleado e NO está asignado código s en día d
```

### 3.2 Variables Auxiliares (Tracking)
```
worked[e, d] ∈ {0, 1}  = 1 si empleado e trabajó en día d (cualquier T*)
  worked[e, d] = min(x[e,d,T8] + x[e,d,T9] + x[e,d,T10] + x[e,d,DT], 1)

free[e, d] ∈ {0, 1}  = 1 si empleado e descansa en día d (L o LC)
  free[e, d] = x[e,d,L] + x[e,d,LC]

consecutive_free[e, d] ∈ {0, 1}  = 1 si d y d+1 son consecutivos libres
  (para penalizar no-continuidad)
```

---

## 4. RESTRICCIONES HARD (OBLIGATORIAS)

### 4.1 Una Asignación por Empleado por Día
```
∑_{s ∈ S} x[e, d, s] = 1   ∀e ∈ E, ∀d ∈ D

Significado: Cada empleado debe tener exactamente 1 código asignado cada día
```

### 4.2 Restricciones EXCLUSIVAS para Full Time

#### 4.2.1 Exactamente 5 Días Trabajados por Semana
```
∑_{d ∈ W_i} worked[e, d] = 5   ∀e ∈ E_FT, ∀i ∈ W

Donde W_i es la semana i del mes
```

#### 4.2.2 Exactamente 2 Días Libres por Semana
```
∑_{d ∈ W_i} free[e, d] = 2   ∀e ∈ E_FT, ∀i ∈ W
```

#### 4.2.3 Distribución de Turnos: 2 de 9h + 3 de 8h por Semana
```
∑_{d ∈ W_i} x[e, d, T9] = 2     ∀e ∈ E_FT, ∀i ∈ W
∑_{d ∈ W_i} x[e, d, T8] = 3     ∀e ∈ E_FT, ∀i ∈ W

Resultado: 2×9 + 3×8 = 18 + 24 = 42 horas/semana ✓
```

#### 4.2.4 Exactamente 2 Domingos TRABAJADOS al Mes
```
∑_{d ∈ SUNDAYS} (x[e, d, T8] + x[e, d, T9] + x[e, d, DT]) = 2   ∀e ∈ E_FT
```

#### 4.2.5 Exactamente 2 Domingos LIBRES al Mes
```
∑_{d ∈ SUNDAYS} (x[e, d, L] + x[e, d, LC]) = 2   ∀e ∈ E_FT
```

#### 4.2.6 Máximo 6 Días Consecutivos Trabajados
```
En cualquier ventana de 7 días, máximo 6 pueden ser trabajados

∑_{d ∈ [t, t+6]} worked[e, d] ≤ 6   ∀e ∈ E_FT, ∀t ∈ D
```

### 4.3 Restricciones EXCLUSIVAS para Part Time

#### 4.3.1 Disponibilidad Limitada: Solo Sábados y Domingos
```
x[e, d, T10] + x[e, d, DT] ≤ 0   ∀e ∈ E_PT, ∀d ∈ WEEKDAYS

(Si no es sábado/domingo, no puede trabajar)
```

#### 4.3.2 Exactamente 2 Días Trabajados por Semana (10h cada uno)
```
∑_{d ∈ W_i} (x[e, d, T10] + x[e, d, DT]) = 2   ∀e ∈ E_PT, ∀i ∈ W
```

#### 4.3.3 Exactamente 20 Horas por Semana
```
∑_{d ∈ W_i} (10 × (x[e, d, T10] + x[e, d, DT])) = 20   ∀e ∈ E_PT, ∀i ∈ W
```

### 4.4 Restricciones de Días Especiales

#### 4.4.1 Feriados Irrenunciables (FI)
```
En días HOLIDAYS_IRREN, TODOS los empleados sin excepciones previas = FI

x[e, d, FI] = 1   ∀e ∈ E, ∀d ∈ HOLIDAYS_IRREN si e ∉ excepciones

**IMPORTANTE**: FI no consume los 2 días libres semanales (se cuenta aparte)
```

#### 4.4.2 Compensación de Feriados Normales Trabajados
```
Para cada e ∈ E_FT y cada d ∈ HOLIDAYS_NORMAL:

  Si x[e, d, T8] = 1 ó x[e, d, T9] = 1 (trabajó el feriado):
    Entonces: ∑_{d' ∈ D} x[e, d', LC] ≥ 1 en same_month
    
  Si x[e, d, FI] = 1 (asignado FI):
    Entonces: no consume descansos semanales

Matemáticamente (usando variable auxiliar worked_holiday[e,d]):
  worked_holiday[e, d] = x[e, d, T8] + x[e, d, T9]   ∀d ∈ HOLIDAYS_NORMAL

  ∑_{d' ∈ D} x[e, d', LC] ≥ ∑_{d ∈ HOLIDAYS_NORMAL} worked_holiday[e, d]
    ∀e ∈ E_FT
```

#### 4.4.3 Cierre de Tienda (C)
```
En días de CLOSED_DAYS, todos los empleados:
  x[e, d, C] = 1   ∀e ∈ E, ∀d ∈ CLOSED_DAYS
```

#### 4.4.4 Excepciones Previas (Vacaciones / Licencias)
```
Si empleado e tiene excepción en día d (V o LM):
  x[e, d, V] = 1 ó x[e, d, LM] = 1   (según tipo de excepción)
  
  Estas excepciones pueden consumir o no descansos según política
```

### 4.5 Cobertura Mínima de Empleados

#### 4.5.1 Mínimo por Día Regular
```
∑_{e ∈ E} worked[e, d] ≥ min_employees_per_day   ∀d ∈ D - CLOSED_DAYS
```

#### 4.5.2 Mínimo en Domingos
```
∑_{e ∈ E} worked[e, d] ≥ min_employees_on_sunday   ∀d ∈ SUNDAYS
```

---

## 5. FUNCIÓN OBJETIVO (SOFT CONSTRAINTS - Minimización)

```
Minimizar:
  Z = w1 × (Fragmentación de Libres) + w2 × (Desbalance de Horas) + w3 × (Variables auxiliares)

Donde:

  Término 1: Fragmentación de Días Libres (Continuidad)
    w1 × ∑_{e ∈ E_FT} ∑_{w ∈ W} (penalty si los 2 libres no son consecutivos)
    
    Por semana w, si free[e,d] = free[e,d+1] = 1:
      consecutive_free[e,d] contribuye positivamente
    Si están separados:
      penalty se suma a objetivo
    
    Término expandido:
    w1 × ∑_{e∈E_FT} ∑_{w∈W} ∑_{d∈W} |∑_{d'∈W} free[e,d'] × consecutive_free[e,d]| 
    
    O más simplemente:
    w1 × ∑_{e∈E_FT} ∑_{w∈W} (2 - ∑_{d∈W-1} (free[e,d] × free[e,d+1]))
    
    Si los dos libres son consecutivos → contribución 0
    Si están separados → contribución > 0

  Término 2: Desbalance de Horas en Domingos (Optional)
    (Minimizar diferencias entre empleados en total domingos trabajados)

  Término 3: Índices de variables auxiliares (≈0 en soluciones válidas)
```

### 5.1 Interpretación de Pesos
```
w1 = 100  (Muy alto: prioriza continuidad de descansos)
w2 = 50   (Medio: desbalance de cobertura)
w3 = 1    (Bajo: suavizante general)
```

---

## 6. IMPLEMENTACIÓN EN PULP - PSEUDO-CÓDIGO

```python
from pulp import *

# Crear modelo
model = LpProblem("Schedule_V2", LpMinimize)

# 1. Variables de Decisión
x = LpVariable.dicts("assignment", 
                     [(e, d, s) for e in E for d in D for s in S],
                     cat='Binary')

# 2. HARD CONSTRAINT: Una asignación por día
for e in E:
    for d in D:
        model += lpSum([x[(e, d, s)] for s in S]) == 1

# 3. FULL TIME: Exactamente 5 días trabajados por semana
for e in E_FT:
    for week in weeks:
        work_days = [d for d in week if d not in CLOSED_DAYS]
        model += lpSum([x[(e, d, 'T8')] + x[(e, d, 'T9')] + x[(e, d, 'DT')] 
                       for d in work_days]) == 5

# 4. FULL TIME: Distribución 2×T9 + 3×T8 por semana
for e in E_FT:
    for week in weeks:
        model += lpSum([x[(e, d, 'T9')] for d in week]) == 2
        model += lpSum([x[(e, d, 'T8')] for d in week]) == 3

# 5. FULL TIME: Mínimo 2 domingos trabajados al mes
for e in E_FT:
    model += lpSum([x[(e, d, 'T8')] + x[(e, d, 'T9')] + x[(e, d, 'DT')] 
                   for d in SUNDAYS]) == 2

# 6. FULL TIME: 2 domingos libres
for e in E_FT:
    model += lpSum([x[(e, d, 'L')] + x[(e, d, 'LC')] 
                   for d in SUNDAYS]) == 2

# 7. PART TIME: Solo sábado/domingo
for e in E_PT:
    for d in WEEKDAYS:
        model += x[(e, d, 'T10')] == 0

# 8. PART TIME: Exactamente 2 días trabajados por semana (sábado/domingo)
for e in E_PT:
    for week in weeks:
        saturday_sunday = [d for d in week if d in SATURDAYS or d in SUNDAYS]
        model += lpSum([x[(e, d, 'T10')] + x[(e, d, 'DT')] 
                       for d in saturday_sunday]) == 2

# 9. FERIADO IRRENUNCIABLE: Todos asignados a FI
for d in HOLIDAYS_IRREN:
    for e in E:
        if not has_prior_exception(e, d):
            model += x[(e, d, 'FI')] == 1

# 10. COMPENSACIÓN: Si trabaja feriado normal → LC obligatorio ese mes
for e in E_FT:
    worked_holidays = lpSum([x[(e, d, 'T8')] + x[(e, d, 'T9')] 
                            for d in HOLIDAYS_NORMAL])
    total_lc = lpSum([x[(e, d, 'LC')] for d in D])
    model += total_lc >= worked_holidays

# 11. COBERTURA MÍNIMA
for d in D:
    if d not in CLOSED_DAYS:
        model += lpSum([x[(e, d, 'T8')] + x[(e, d, 'T9')] + x[(e, d, 'T10')] + x[(e, d, 'DT')] 
                       for e in E]) >= min_employees_per_day

# 12. COBERTURA DOMINGOS
for d in SUNDAYS:
    model += lpSum([x[(e, d, 'T8')] + x[(e, d, 'T9')] + x[(e, d, 'T10')] + x[(e, d, 'DT')] 
                   for e in E]) >= min_employees_on_sunday

# 13. FUNCIÓN OBJETIVO: Maximizar continuidad de descansos (penalizar fragmentación)
penalty = 0
for e in E_FT:
    for week in weeks:
        week_days = sorted(week)
        consecutive_count = 0
        for i in range(len(week_days) - 1):
            d1, d2 = week_days[i], week_days[i+1]
            if d2 == d1 + 1:  # días consecutivos
                is_both_free = (x[(e, d1, 'L')] + x[(e, d1, 'LC')] + 
                               x[(e, d2, 'L')] + x[(e, d2, 'LC')]) >= 1.99
                consecutive_count += is_both_free
        # Si ambos libres son consecutivos, penalty = 0
        # Si no, penalty = número de pares separados
        penalty += (2 - consecutive_count)

model += 100 * penalty  # Alto peso para continuidad

# Resolver
model.solve(PULP_CBC_CMD(msg=0))
```

---

## 7. EJEMPLO DE SOLUCIÓN ESPERADA

### Para Juan Pérez (Full Time, sin excepciones):

```
Semana 1 (días 1-7):
  L1: T9 (9h)
  L2: T9 (9h)
  L3: T8 (8h)
  L4: T8 (8h)
  L5: T8 (8h)
  S6: L
  D7:  L       ← 2 libres consecutivos (bueno) + 2 domingos libres registrados esta semana
  Subtotal: 2×9 + 3×8 = 42h ✓

Semana 2 (días 8-14):
  ...similar distribución...
  D14: DT       ← Primo domingo trabajado del mes

Semana 3-4: Similar

Final del mes:
  - Máximo 6 consecutivos trabajados: ✓
  - 2 domingos trabajados: ✓
  - 2 domingos libres: ✓
  - Si trabajó feriado normal (día 2): mín 1 LC en el mes ✓
```

---

## 8. CAMBIOS vs V1.0

| Aspecto | V1.0 | V2.0 |
|---------|------|------|
| **Turnos** | T, DT | T8, T9, T10, DT |
| **Horas FT** | Variable | Exactamente 42h/semana |
| **Estructura FT** | Flexible | Rígido: 2×9h + 3×8h |
| **Descansos FT** | 1+ por semana | Exactamente 2 por semana |
| **Domingos FT** | Sin restricción | 2 trabajados + 2 libres |
| **Part Time** | No diferenciado | Solo Sábado/Domingo, 20h/semana |
| **Feriados Normales** | No considerados | Genera LC automático |
| **Feriados Irrenunciables** | Pre-asignados | No consumen descansos |
| **Función Objetivo** | Minimizar variables | Maximizar continuidad + balance |

