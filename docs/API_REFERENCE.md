# Documentación de API

## Base URL
```
http://localhost:5000
```

---

## Endpoints

### 1. **POST** `/api/schedule/generate`

#### Descripción
Genera un horario completo basado en los parámetros enviados.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
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
      "min_employees_per_day": 3,
      "min_employees_on_sunday": 2,
      "special_days": [
        {
          "day": 1,
          "type": "FI",
          "description": "Feriado Irrenunciable - Día del Trabajo"
        },
        {
          "day": 10,
          "type": "C",
          "description": "Local Cerrado - Mantenimiento"
        }
      ]
    },
    "employees": [
      {
        "employee_id": "EMP001",
        "name": "Juan Pérez",
        "contract_type": "Full Time",
        "max_hours_per_month": 176,
        "hours_per_day": 8,
        "max_consecutive_work_days": 6,
        "min_rest_days_per_week": 1,
        "prior_exceptions": [
          {
            "day": 5,
            "type": "V",
            "description": "Vacaciones"
          }
        ]
      },
      {
        "employee_id": "EMP002",
        "name": "María García",
        "contract_type": "Full Time",
        "max_hours_per_month": 176,
        "hours_per_day": 8,
        "max_consecutive_work_days": 6,
        "min_rest_days_per_week": 1,
        "prior_exceptions": []
      }
    ]
  }
}
```

#### Response

**Status: 200 OK**
```json
{
  "success": true,
  "message": "Horarios generados exitosamente",
  "schedule": {
    "EMP001": {
      "1": "FI",
      "2": "T",
      "3": "T",
      "4": "T",
      "5": "V",
      "6": "L",
      "7": "DT",
      "8": "T",
      ...
    },
    "EMP002": {
      "1": "FI",
      "2": "T",
      ...
    }
  },
  "summary": {
    "EMP001": {
      "T": 18,
      "DT": 2,
      "L": 6,
      "LC": 0,
      "V": 1,
      "LM": 0,
      "FI": 1,
      "C": 1
    },
    "EMP002": {
      "T": 20,
      "DT": 2,
      "L": 6,
      "LC": 0,
      "V": 0,
      "LM": 0,
      "FI": 1,
      "C": 1
    }
  },
  "file_name": "horario_Sucursal_Centro_20260410_120000.xlsx",
  "file_path": "./generated_schedules/horario_Sucursal_Centro_20260410_120000.xlsx",
  "errors": []
}
```

**Status: 400 Bad Request**
```json
{
  "success": false,
  "message": "Error en validación de datos",
  "errors": [
    "Field validation error details..."
  ]
}
```

**Status: 422 Unprocessable Entity**
```json
{
  "success": false,
  "message": "No se pudo encontrar una solución válida para los parámetros especificados",
  "errors": [
    "El modelo PuLP no encontró solución factible"
  ]
}
```

**Status: 500 Internal Server Error**
```json
{
  "success": false,
  "message": "Error interno del servidor",
  "errors": [
    "Exception details..."
  ]
}
```

---

### 2. **GET** `/api/schedule/list`

#### Descripción
Lista todos los archivos de horarios generados previamente.

#### Response

**Status: 200 OK**
```json
{
  "success": true,
  "files": [
    {
      "filename": "horario_Sucursal_Centro_20260410_120000.xlsx",
      "size": 25600,
      "created": "2026-04-10T12:00:00"
    },
    {
      "filename": "horario_Sucursal_Centro_20260410_115000.xlsx",
      "size": 24512,
      "created": "2026-04-10T11:50:00"
    }
  ]
}
```

---

### 3. **GET** `/api/schedule/download/<filename>`

#### Descripción
Descarga un archivo de horario en formato Excel.

#### URL Parameters
- `filename` (string): Nombre del archivo a descargar

#### Response

**Status: 200 OK**
- Retorna el archivo Excel en formato Blob

**Status: 404 Not Found**
```json
{
  "success": false,
  "message": "Archivo no encontrado",
  "errors": [
    "El archivo especificado no existe"
  ]
}
```

#### Ejemplo de uso
```bash
curl -O http://localhost:5000/api/schedule/download/horario_Sucursal_Centro_20260410_120000.xlsx
```

---

### 4. **GET** `/health`

#### Descripción
Verifica el estado del servidor.

#### Response

**Status: 200 OK**
```json
{
  "status": "ok",
  "service": "Schedule Optimizer Backend",
  "timestamp": "2026-04-10T12:00:00"
}
```

---

## Modelos de Datos

### MonthConfig
```json
{
  "year": 2026,
  "month": 4,
  "days_in_month": 30,
  "starting_day_of_week": "Wednesday"
}
```

**Campos:**
- `year` (integer): Año (2020-2100)
- `month` (integer): Mes (1-12)
- `days_in_month` (integer): Cantidad de días del mes (28-31)
- `starting_day_of_week` (string): Día de inicio ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

---

### StoreConfig
```json
{
  "store_name": "Sucursal Centro",
  "min_employees_per_day": 3,
  "min_employees_on_sunday": 2,
  "special_days": [...]
}
```

**Campos:**
- `store_name` (string): Nombre de la sucursal
- `min_employees_per_day` (integer): Mínimo empleados por día ≥ 1
- `min_employees_on_sunday` (integer): Mínimo empleados el domingo ≥ 1
- `special_days` (array): Lista de días especiales

---

### SpecialDay
```json
{
  "day": 1,
  "type": "FI",
  "description": "Feriado Irrenunciable - Día del Trabajo"
}
```

**Campos:**
- `day` (integer): Número de día (1-31)
- `type` (string): Tipo ["FI" = Feriado Irrenunciable, "C" = Local Cerrado]
- `description` (string): Descripción del evento

---

### Employee
```json
{
  "employee_id": "EMP001",
  "name": "Juan Pérez",
  "contract_type": "Full Time",
  "max_hours_per_month": 176,
  "hours_per_day": 8,
  "max_consecutive_work_days": 6,
  "min_rest_days_per_week": 1,
  "prior_exceptions": []
}
```

**Campos:**
- `employee_id` (string): ID único del empleado
- `name` (string): Nombre completo
- `contract_type` (string): Tipo de contrato ["Full Time", "Part Time"]
- `max_hours_per_month` (integer): Máximo de horas mensuales
- `hours_per_day` (integer): Horas que trabaja cada día (1-12)
- `max_consecutive_work_days` (integer): Máximo días consecutivos trabajando (1-7)
- `min_rest_days_per_week` (integer): Mínimo descansos por semana ≥ 1
- `prior_exceptions` (array): Vacaciones o licencias previas

---

### PriorException
```json
{
  "day": 5,
  "type": "V",
  "description": "Vacaciones"
}
```

**Campos:**
- `day` (integer): Número de día (1-31)
- `type` (string): Tipo ["V" = Vacaciones, "LM" = Licencia Médica]
- `description` (string): Descripción

---

## Códigos de Glosas (Shift Codes)

| Código | Nombre | Descripción |
|--------|--------|-------------|
| **T** | Día Trabajado | Jornada normal de trabajo |
| **DT** | Domingo Trabajado | Trabajo en domingo (remuneración adicional) |
| **L** | Libre por Horario | Descanso obligatorio según ciclo laboral |
| **LC** | Libre Compensado | Día libre a cambio de feriado trabajado |
| **V** | Vacaciones | Período de vacaciones |
| **LM** | Licencia Médica | Licencia por enfermedad |
| **FI** | Feriado Irrenunciable | Feriado legal (debe estar libre) |
| **C** | Local Cerrado | Tienda cerrada por decisión empresarial |

---

## Manejo de Errores

### Códigos de Error

| Status | Error | Descripción |
|--------|-------|-------------|
| 400 | Bad Request | Datos inválidos o incompletos |
| 404 | Not Found | Recurso no encontrado (archivo no existe) |
| 422 | Unprocessable Entity | No hay solución factible para los parámetros |
| 500 | Internal Server Error | Error no controlado en el servidor |

### Estructura de Respuesta de Error
```json
{
  "success": false,
  "message": "Descripción general del error",
  "errors": [
    "Detalle de error 1",
    "Detalle de error 2"
  ]
}
```

---

## Ejemplos de uso con cURL

### Generar horarios
```bash
curl -X POST http://localhost:5000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### Listar horarios
```bash
curl http://localhost:5000/api/schedule/list
```

### Descargar horario
```bash
curl http://localhost:5000/api/schedule/download/horario_Sucursal_Centro_20260410_120000.xlsx \
  -o horario.xlsx
```

### Verificar salud del servidor
```bash
curl http://localhost:5000/health
```

