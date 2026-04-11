# Formulación Matemática del Sistema de Generación de Horarios

## 1. Resumen Ejecutivo

El sistema resuelve el **Problema de Satisfacción de Restricciones (CSP - Constraint Satisfaction Problem)** para la asignación de turnos en retail utilizando programación lineal entera mediante la librería **PuLP**.

**Objetivo:** Asignar a cada empleado un código de glosa (T, DT, L, LC, V, LM, FI, C) para cada día del mes, respetando:
- Límites contractuales de horas
- Leyes laborales de descansos
- Requisitos de cobertura de la tienda

---

## 2. Conjuntos y Parámetros

### Conjuntos

- $E$ = Conjunto de empleados
- $D$ = Conjunto de días del mes (1 a 30/31)
- $G$ = Conjunto de glosas/códigos: $\{T, DT, L, LC, V, LM, FI, C\}$
- $S$ = Conjunto de domingos en el mes
- $W$ = Conjuntos de semanas del mes

### Parámetros

| Símbolo | Descripción | Unidad |
|---------|-------------|--------|
| $H^{\max}_{e}$ | Horas máximas del mes para empleado $e$ | horas |
| $h_d^e$ | Horas de trabajo por día para empleado $e$ | horas/día |
| $M^{\max}_{e}$ | Máximo días consecutivos trabajando | días |
| $C^{\min}_d$ | Cobertura mínima requerida el día $d$ | empleados |
| $DT^{\max}_{e}$ | Máximo domingos trabajados por empleado | domingos/mes |

---

## 3. Variables de Decisión

### Variable Principal

$$x^g_{ed} \in \{0, 1\} \quad \forall e \in E, d \in D, g \in G$$

Donde:
- $x^g_{ed} = 1$ si el empleado $e$ tiene asignada la glosa $g$ el día $d$
- $x^g_{ed} = 0$ en caso contrario

**Interpretación de glosas:**
- $x^T_{ed} = 1$: Empleado $e$ trabaja el día $d$ (jornada normal)
- $x^{DT}_{ed} = 1$: Empleado $e$ trabaja un domingo
- $x^L_{ed} = 1$: Empleado $e$ tiene libre el día $d$
- $x^{LC}_{ed} = 1$: Día libre compensado (por feriado trabajado)
- $x^V_{ed} = 1$: Empleado $e$ en vacaciones
- $x^{LM}_{ed} = 1$: Licencia médica
- $x^{FI}_{ed} = 1$: Feriado irrenunciable (día no trabajable)
- $x^C_{ed} = 1$: Local cerrado

---

## 4. Restricciones

### 4.1 Restricción 1: Asignación Única por Día

**Ecuación:**
$$\sum_{g \in G} x^g_{ed} = 1 \quad \forall e \in E, \forall d \in D$$

**Interpretación:** Cada empleado tiene exactamente una asignación cada día del mes.

**En PuLP:**
```python
for emp in employees:
    for day in range(1, days_in_month + 1):
        constraint = lpSum([x[emp][day][g] for g in shift_codes]) == 1
        model += constraint
```

---

### 4.2 Restricción 2: Límite de Horas Mensuales ⭐ PRINCIPAL

**Ecuación:**
$$\sum_{d \in D \setminus \{V, LM, FI, C\}} h_d^e \cdot (x^T_{ed} + x^{DT}_{ed}) \leq H^{\max}_{e} \quad \forall e \in E$$

Donde $D \setminus \{V, LM, FI, C\}$ significa todos los días excepto vacaciones, licencias, feriados y cierres.

**Interpretación:** La suma de horas de días trabajados (T) y domingos trabajados (DT) no puede exceder el máximo del contrato.

**Ejemplo numérico:**
- Empleado Full Time: máximo 176 horas/mes (44 hrs/semana × 4 semanas)
- Empleado Part Time: máximo 88 horas/mes (22 hrs/semana × 4 semanas)
- Si trabaja 8 hrs/día: máximo 22 días trabajados

**En PuLP:**
```python
for emp in employees:
    hours_constraint = lpSum([
        emp.hours_per_day * (x[emp.id][day]['T'] + x[emp.id][day]['DT'])
        for day in eligible_days
    ]) <= emp.max_hours_per_month
    model += hours_constraint, f"max_hours_{emp.id}"
```

---

### 4.3 Restricción 3: Máximo Días Consecutivos Trabajando ⭐ PRINCIPAL

**Ecuación:**
$$\sum_{j=0}^{6} (x^T_{e,d+j} + x^{DT}_{e,d+j}) \leq M^{\max}_{e} \quad \forall e \in E, \forall d \in \{1 \ldots |D|-6\}$$

Donde $M^{\max}_{e}$ típicamente es 6 días (máximo establecido por ley).

**Interpretación:** En cualquier ventana de 7 días consecutivos, el empleado puede trabajar como máximo 6 días (mínimo 1 día libre cada 7 días).

**Ejemplo:**
- Días 1-7: máximo 6 trabajados, mínimo 1 libre
- Días 2-8: máximo 6 trabajados, mínimo 1 libre
- Etc.

**En PuLP:**
```python
for emp in employees:
    for start_day in range(1, days_in_month - 5):
        consecutive = lpSum([
            x[emp.id][start_day + offset]['T'] +
            x[emp.id][start_day + offset]['DT']
            for offset in range(7)
        ])
        model += consecutive <= 6, f"consecutive_{emp.id}_{start_day}"
```

---

### 4.4 Restricción 4: Asignaciones Fijas (No Modificables)

**Ecuación:**
$$x^g_{ed} = 1 \quad \text{si} \ g \in \{V, LM, FI, C\} \ \text{y} \ d \ \text{es pre-asignado}$$

**Interpretación:** Los días de vacaciones (V), licencias médicas (LM), feriados (FI) y cierres (C) deben ser respetados y no pueden cambiarse.

**En PuLP:**
```python
# Excepciones del empleado
for emp in employees:
    for day in emp.prior_exceptions:  # (day, type)
        model += x[emp.id][day][type] == 1

# Días especiales de tienda
for day, day_type in store_special_days.items():
    for emp in employees:
        model += x[emp.id][day][day_type] == 1
```

---

### 4.5 Restricción 5: Cobertura Mínima de Empleados

**Ecuación:**
$$\sum_{e \in E} (x^T_{ed} + x^{DT}_{ed}) \geq C^{\min}_d \quad \forall d \in D$$

Donde:
$$C^{\min}_d = \begin{cases} 
C^{\text{min}}_{\text{domingo}} & \text{si } d \in S \\
C^{\text{min}}_{\text{normal}} & \text{en otro caso}
\end{cases}$$

**Interpretación:** Cada día debe tener un mínimo de empleados trabajando (diferenciado para domingos).

**Ejemplo:**
- Días normales: mínimo 3 empleados trabajando
- Domingos: mínimo 2 empleados trabajando
- Feriados/Cierres: 0 empleados (porque nadie puede trabajar)

**En PuLP:**
```python
for day in days:
    if day in sundays:
        min_coverage = min_employees_on_sunday
    else:
        min_coverage = min_employees_per_day
    
    coverage = lpSum([
        x[emp.id][day]['T'] + x[emp.id][day]['DT']
        for emp in employees
    ])
    model += coverage >= min_coverage, f"coverage_{day}"
```

---

### 4.6 Restricción 6: Máximo Domingos Trabajados (Opcional)

**Ecuación:**
$$\sum_{d \in S} x^{DT}_{ed} \leq DT^{\max}_{e} \quad \forall e \in E$$

Donde $DT^{\max}_{e}$ es típicamente 2-4 domingos por mes según contrato.

**Interpretación:** Limita la cantidad de domingos que un empleado puede trabajar por mes (por ley laboral).

---

## 5. Función Objetivo

### Función Ficticia (CSP)

Dado que es un **Problema de Satisfacción de Restricciones**, la función objetivo es secundaria:

$$\text{Minimize} \ Z = 0$$

O alternativamente, minimizar una penalización pequeña:

$$\text{Minimize} \ Z = \sum_{e \in E} \sum_{d \in D} w \cdot x^g_{ed}$$

Donde $w$ es una constante pequeña (ej. 0.1).

**Razón:** El objetivo principal es **encontrar una solución factible que satisfaga todas las restricciones**, no optimizar costos. El solucionador PuLP buscará cualquier solución válida.

---

## 6. Formulación Compacta del Modelo

### Modelo Completo

$$\begin{align}
\text{Minimize} & \quad Z = 0 \\
\text{s.a.} & \\
& \sum_{g \in G} x^g_{ed} = 1, \quad \forall e \in E, \forall d \in D \\
& \sum_{d} h_d^e (x^T_{ed} + x^{DT}_{ed}) \leq H^{\max}_e, \quad \forall e \in E \\
& \sum_{j=0}^{6} (x^T_{e,d+j} + x^{DT}_{e,d+j}) \leq 6, \quad \forall e \in E, \forall d \\
& x^g_{ed} = 1, \quad \text{si } (e,d,g) \text{ es pre-asignado} \\
& \sum_{e} (x^T_{ed} + x^{DT}_{ed}) \geq C^{\min}_d, \quad \forall d \\
& x^g_{ed} \in \{0, 1\}, \quad \forall e, d, g
\end{align}$$

---

## 7. Tamaño del Problema

### Dimensionamiento

Para un mes típico:
- **Empleados:** 5-10
- **Días:** 28-31
- **Glosas:** 8
- **Variables binarias:** $E \times D \times G = 10 \times 30 \times 8 = 2,400$ variables
- **Restricciones:** Orden de $E \times D + E + D = 300$ - $500$ restricciones

**Complejidad:** Tiempo de resolución típico < 5 segundos

---

## 8. Algoritmo de Resolución

### Pasos en PuLP

1. **Creación del modelo:** `LpProblem("ScheduleOptimization", LpMinimize)`
2. **Definición de variables:** Variables binarias para cada $(e, d, g)$
3. **Adición de restricciones:** En el orden definido arriba
4. **Definición de objetivo:** Minimizar 0 (ficticio)
5. **Resolución:** Usar solver CBC (default) o CPLEX/Gurobi
6. **Extracción:** Leer valores de `var.varValue`

### Solver Utilizado

- **Solver por defecto:** PULP_CBC_CMD (open source)
- **Tiempo típico:** < 5 segundos
- **Garantía:** Solución óptima si existe

---

## 9. Validación y Verificación

### Post-Procesamiento

Después de resolver, verificar:

```python
for emp in employees:
    total_hours = sum(
        emp.hours_per_day * (schedule[emp][day] in ['T', 'DT'])
        for day in days
    )
    assert total_hours <= emp.max_hours, f"Violación de horas para {emp}"
    
    for start_day in range(1, len(days) - 5):
        consecutive_worked = sum(
            1 for offset in range(7)
            if schedule[emp][start_day + offset] in ['T', 'DT']
        )
        assert consecutive_worked <= 6, f"Violación de consecutivos para {emp}"
```

---

## 10. Ejemplos Numéricos

### Ejemplo 1: Cálculo de restricción de horas

**Empleado:** María García
- Contrato: Full Time (176 hrs/mes)
- Horas por día: 8 hrs
- Máximo días trabajables: 176 / 8 = 22 días

**Solución:**
- 20 días con "T" (160 horas)
- 2 días con "DT" (16 horas)
- 6 días con "L" (0 horas)
- 1 día con "V" (0 horas)
- 1 día con "FI" (0 horas)
- **Total:** 160 + 16 = 176 horas ✓

---

### Ejemplo 2: Cálculo de restricción de consecutivos

**Ventana:** Días 1-7 de abril

| Día | 1  | 2 | 3 | 4 | 5 | 6 | 7 |
|-----|----|----|----|----|----|----|---|
| Glosa | FI | T  | T  | T  | L  | T  | T |
| Trabaja | ❌ | ✓ | ✓ | ✓ | ❌ | ✓ | ✓ |

**Consecutivos:** 3 + 2 = 5 días trabajados (máximo permitido: 6) ✓

---

## 11. Casos de Infactibilidad

El modelo puede ser **infactible** si:

1. **No hay suficientes empleados:** 
   - Si $|E| \times \text{avg\_horas}_{e} < \sum_{d} C^{\min}_d \times h_d$
   - Solución: Agregar empleados o reducir cobertura mínima

2. **Restricciones contradictorias:**
   - Máximo horas muy bajo + cobertura muy alta
   - Solución: Relajar una restricción

3. **Excepciones conflictivas:**
   - Empleado con todas las vacaciones pero debe cubrir cierto día
   - Solución: Resolver conflicto en pre-entrada

---

## 12. Referencias Bibliográficas

- Gendreau, M., & Potvin, J. Y. (2010). *Handbook of metaheuristics*.
- Ehrgott, M., et al. (2009). *Handbook of multicriteria optimization*.
- Curtis-Kashta, B., & Artigues, C. (2013). *Lecture notes on scheduling*.

