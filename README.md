# SISTEMA DE GENERACIÓN DE HORARIOS DE TRABAJO

Sistema web completo para la generación automática de mallas de turnos para el sector retail, resolviendo el problema como un **Constraint Satisfaction Problem (CSP)** usando PuLP.

## 📋 Requisitos del Proyecto

### Stack Tecnológico
- **Frontend**: Angular 16+
- **Backend**: Python 3.9+
- **Motor Matemático**: PuLP (optimización lineal)
- **Generación de Archivos**: XlsxWriter (Excel)

---

## 🚀 Instalación y Ejecución

### Backend (Python)

#### 1. Instalar dependencias
```bash
cd backend
pip install -r requirements.txt
```

#### 2. Ejecutar servidor
```bash
python main.py
```

El servidor estará disponible en: **http://localhost:5000**

#### 3. Pruebas locales (sin API)
```bash
python test_local.py
```

Esto genera un Excel de prueba sin necesidad de levantar el servidor.

---

### Frontend (Angular)

#### 1. Instalar dependencias
```bash
cd frontend
npm install
```

#### 2. Ejecutar servidor de desarrollo
```bash
ng serve
```

La aplicación estará disponible en: **http://localhost:4200**

---

## 📊 Estructura del Proyecto

```
Sistema de horarios/
├── backend/
│   ├── models.py              # Modelos Pydantic para validación
│   ├── scheduler.py           # Motor PuLP + restricciones
│   ├── excel_generator.py     # Generador de Excel con estilos
│   ├── main.py                # API Flask
│   ├── test_local.py          # Script de prueba
│   ├── test_data.json         # Datos de ejemplo
│   └── requirements.txt       # Dependencias Python
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── month-config/       # Configuración del mes
│   │   │   │   ├── employee-data/      # Ingreso de empleados
│   │   │   │   ├── special-days/       # Días especiales
│   │   │   │   └── schedule-result/    # Visualización de resultados
│   │   │   ├── services/
│   │   │   │   └── scheduler.service.ts
│   │   │   └── app.component.ts
│   │   └── main.ts
│   └── package.json
│
└── docs/
    ├── API_REFERENCE.md       # Documentación de endpoints
    └── FORMULATION.md         # Formulación matemática detallada
```

---

## 🔌 Endpoints de la API

### 1. **POST** `/api/schedule/generate`
Genera los horarios basado en los parámetros enviados.

**Request Body:**
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
        {"day": 1, "type": "FI", "description": "Feriado"}
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
        "prior_exceptions": []
      }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Horarios generados exitosamente",
  "schedule": {
    "EMP001": {
      "1": "FI",
      "2": "T",
      "3": "T",
      ...
    }
  },
  "summary": {
    "EMP001": {
      "T": 20,
      "DT": 2,
      "L": 8,
      ...
    }
  },
  "file_name": "horario_Sucursal_Centro_20260410_120000.xlsx",
  "file_path": "./generated_schedules/horario_..."
}
```

### 2. **GET** `/api/schedule/list`
Lista todos los archivos generados.

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "filename": "horario_Sucursal_Centro_20260410_120000.xlsx",
      "size": 25600,
      "created": "2026-04-10T12:00:00"
    }
  ]
}
```

### 3. **GET** `/api/schedule/download/<filename>`
Descarga un archivo de horario generado.

### 4. **GET** `/health`
Verifica el estado del servidor.

---

## 📐 Restricciones Implementadas

### Restricción 1: Límite de Horas Mensuales
```
∑_d (h_d × x_T[e][d] + h_d × x_DT[e][d]) ≤ H_max[e]
```

Asegura que la suma de horas trabajadas no exceda el contrato del empleado.

### Restricción 2: Máximo Días Consecutivos
```
∑_{j=0}^{6} (x_T[e][d+j] + x_DT[e][d+j]) ≤ 6, ∀d
```

Máximo 6 días trabajados consecutivos, al menos 1 día libre cada 7 días.

### Restricción 3: Asignación Única por Día
```
∑_code x[e][d][code] = 1, ∀e,d
```

Cada empleado tiene exactamente una asignación cada día.

### Restricción 4: Excepciones Fijas
```
x[e][d][code] = 1 si code ∈ {V, LM, FI, C}
```

Pre-asignaciones no modificables (vacaciones, licencias, feriados).

### Restricción 5: Cobertura Mínima
```
∑_e (x_T[e][d] + x_DT[e][d]) ≥ C_min[d]
```

Mínimos empleados trabajando cada día.

---

## 🎨 Códigos de Glosas y Colores

| Código | Descripción | Color | Hexadecimal |
|--------|-------------|-------|-------------|
| **T** | Día Trabajado | Azul Claro | #ADD8E6 |
| **DT** | Domingo Trabajado | Azul Intenso | #00BFFF |
| **L** | Libre por Horario | Verde Claro | #90EE90 |
| **LC** | Libre Compensado | Amarillo Pálido | #FFFFE0 |
| **V** | Vacaciones | Rosa | #FFB6C1 |
| **LM** | Licencia Médica | Naranja | #FFA07A |
| **FI** | Feriado Irrenunciable | Rojo | #FF0000 |
| **C** | Local Cerrado | Gris | #808080 |

---

## 📝 Ejemplo de Generación

### Input (JSON)
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
        {"day": 1, "type": "FI", "description": "Día del Trabajo"},
        {"day": 10, "type": "C", "description": "Mantenimiento"}
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
          {"day": 5, "type": "V", "description": "Vacaciones"}
        ]
      }
    ]
  }
}
```

### Output (Excel)
Se genera un archivo `.xlsx` con:

1. **Matriz de Horarios**: Filas = empleados, Columnas = días del mes
2. **Tabla de Resumen**: Conteos de cada glosa por empleado
3. **Leyenda de Colores**: Referencia visual

---

## 🛠️ Troubleshooting

### Error: "No se puede encontrar una solución válida"
- Reducir `min_employees_per_day`
- Aumentar `max_hours_per_month` de algunos empleados
- Revisar que haya suficientes empleados disponibles

### Error: Módulos Python no encontrados
```bash
pip install -r requirements.txt
```

### Puerto 5000 ya en uso
```bash
# Cambiar puerto en main.py línea: app.run(..., port=5001, ...)
```

---

## 📧 Contacto
Sistema desarrollado para optimización de turnos retail.

