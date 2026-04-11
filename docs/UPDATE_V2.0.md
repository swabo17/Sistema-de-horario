# GUÍA DE ACTUALIZACIÓN V2.0

## Cambios Principales

### 1. Backend (Python)

✅ **Archivos Actualizados:**
- `models.py` → Nuevos tipos de feriados, códigos T8/T9/T10, estructura Holiday
- `scheduler_v2.py` → Completo (nuevo archivo con todas las restricciones V2.0)
- `main.py` → Actualizado para usar scheduler_v2
- Color mappings → Agregados T8, T9, T10

**Pasos para activar:**

1. Reemplaza import en main.py (✅ ya hecho):
   ```python
   from scheduler_v2 import ScheduleOptimizer
   ```

2. Ejecuta backend:
   ```bash
   cd backend
   python main.py
   ```

### 2. Frontend (Angular)

**Cambio en JSON enviado - Ejemplo:**

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
        "prior_exceptions": []
      }
    ]
  }
}
```

**Actualizaciones en app.component.ts:**

1. Cambiar estructura de "special_days" a "holidays" y "closed_days":
   ```typescript
   // ANTES (V1.0)
   special_days: []
   
   // DESPUÉS (V2.0)
   holidays: []
   closed_days: []
   ```

2. Agregar tipo a feriados:
   ```typescript
   addHoliday() {
     const holiday = {
       day: this.holidayForm.get('day')?.value,
       type: this.holidayForm.get('type')?.value, // "Normal" o "Irrenunciable"
       description: this.holidayForm.get('description')?.value
     };
     this.store_config.holidays.push(holiday);
   }
   ```

3. Tabla en HTML debe mostrar tipo de feriado:
   ```html
   <table>
     <tr>
       <td>Día</td>
       <td>Tipo</td>
       <td>Descripción</td>
       <td>Acción</td>
     </tr>
     <tr *ngFor="let h of store_config.holidays; let i = index">
       <td>{{ h.day }}</td>
       <td>{{ h.type }}</td>
       <td>{{ h.description }}</td>
       <td><button (click)="removeHoliday(i)">Eliminar</button></td>
     </tr>
   </table>
   ```

### 3. Nuevos Códigos de Turno

| Código | Horas | Significado | Color |
|--------|-------|-------------|-------|
| **T8** | 8h | Turno 8h (Full Time) | Azul Cielo |
| **T9** | 9h | Turno 9h (Full Time) | Azul Intenso |
| **T10** | 10h | Turno 10h (Part Time) | Azul Marino |
| **DT** | 8h | Domingo Trabajado (FT) | Azul Muy Oscuro |
| **L** | 0h | Libre Normal | Verde |
| **LC** | 0h | Libre Compensado (feriado) | Amarillo |
| **V** | 0h | Vacaciones | Rosa |
| **LM** | 0h | Licencia Médica | Naranja |
| **FI** | 0h | Feriado Irrenunciable | Rojo-Naranja |
| **C** | 0h | Cerrado | Gris |

### 4. Nueva Lógica de Negocio

#### Full Time (FT)
- ✅ Exactamente **42 horas/semana** (2×9h + 3×8h)
- ✅ **5 días trabajados + 2 libres** por semana
- ✅ Mínimo **2 domingos trabajados** y **2 libres** al mes
- ✅ **Máximo 6 días consecutivos** trabajando
- ✅ Descansos deben ser **continuos** (preferencia soft)

#### Part Time (PT)
- ✅ **Solo sábados y domingos** (de lunes a viernes = 0 horas)
- ✅ Exactamente **20 horas/semana** (2 días × 10h)
- ✅ Exactamente **2 días trabajados** por semana

#### Feriados
- **Normal**: Si se trabaja → genera **LC automático** en el mes
- **Irrenunciable**: Asignado **FI** (no consume descansos semanales)

### 5. Ejemplo de Resultado Esperado

**Juan Pérez (Full Time):**
```
Semana 1:
  L1: T9 (9h) | L2: T9 (9h) | L3: T8 (8h) | L4: T8 (8h) | L5: T8 (8h) | L6: L | L7: L
            ↑                                                        ↑____↑
          Subtotal: 42h                        2 libres consecutivos ✓

Mes:
  - 2 domingos trabajados ✓
  - 2 domingos libres ✓
  - Si trabajó 2 Abril (Jueves Santo Normal): agregó 1 LC en el mes ✓
```

**María García (Part Time):**
```
Semana 1:
  L1-V5: (No disponible)
  L6: T10 (10h) | L7: T10 (10h)
         ↑              ↑
      Subtotal: 20h, solo fines de semana ✓

Todo el mes: Solo trabaja sábados y domingos ✓
```

---

## Instrucciones de Prueba

### Backend

```bash
cd backend
python main.py
# Deberías ver:
# ╔═══════════════════════════════════════════════════╗
# ║ SISTEMA DE GENERACIÓN DE HORARIOS - BACKEND      ║
# ║  Puerto: 5000                                    ║
# ╚═══════════════════════════════════════════════════╝
```

### Frontend + Backend Simultáneamente

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm start
# Abre http://localhost:4200
```

### Prueba de Solicitud JSON

Usa Postman o curl:

```bash
curl -X POST http://localhost:5000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d @test_payload_v2.json
```

Donde `test_payload_v2.json` contiene el ejemplo de la sección "2. Frontend".

---

## Validaciones

### Casos de Prueba para Verificar V2.0

**Caso 1: Full Time con Feriado Normal Trabajado**
- Configurar feriado "Normal" en día 2
- Asignar Full Time a trabajar ese día
- ✅ Debe generar LC automático en el mes

**Caso 2: Full Time - 42h/semana**
- Generar horario exitoso
- Contar horas FT por semana: 2×9 + 3×8 = 42
- ✅ Cada semana debe sumar exactamente 42

**Caso 3: Part Time - Solo Fines de Semana**
- Crear Part Time
- Generar horario
- ✅ Lunes-viernes deben ser todos "L" o "LC"
- ✅ Solo trabaja sábado/domingo (T10)

**Caso 4: Domingos Abiertos**
- Full Time debe tener 2 domingos trabajados + 2 libres
- ✅ Verificar en resultado exactamente 4 domingos asignados

**Caso 5: Continuidad de Descansos**
- Generar múltiples veces el mismo escenario
- ✅ Los 2 libres semanales deberían ser consecutivos idealmente

---

## Documentación

📄 Nueva formulación matemática en: `/docs/FORMULATION_V2.0.md`
- Definición completa de variables, restricciones y función objetivo
- Pseudo-código PuLP
- Ejemplos de soluciones esperadas

