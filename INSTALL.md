# Guía de Instalación y Ejecución Rápida

## 🚀 Inicio Rápido (5 minutos)

### Opción 1: Prueba Local Instantánea (Sin Frontend)

```bash
cd backend
pip install -r requirements.txt
python test_local.py
```

Esto genera un Excel de prueba sin necesidad de un servidor web. ✓ Funciona en 30 segundos.

**Output esperado:**
```
══════════════════════════════════════════════════════════════════
PRUEBA LOCAL DE GENERADOR DE HORARIOS
══════════════════════════════════════════════════════════════════

[TEST] Tienda: Sucursal Centro
[TEST] Empleados: 4
[TEST] Mes: 4/2026
[TEST] Días especiales: 2

EMPLEADOS:
  - Juan Pérez            (Full Time  ) - 176 hrs/mes
  - María García          (Full Time  ) - 176 hrs/mes
  - Carlos López          (Part Time  ) - 88 hrs/mes
  - Ana Martínez          (Full Time  ) - 176 hrs/mes

[OPTIMIZER] Inicializando optimizador...
[OPTIMIZER] Ejecutando optimización...
[SUCCESS] Optimización completada exitosamente!

RESUMEN DE ASIGNACIONES:
─────────────────────────────────────────────────────────────────

Juan Pérez:
  T: 20 días
  DT:  2 días
  L:  6 días
  ...

[Excel guardado en: ./generated_schedules/horario_ejemplo.xlsx]

══════════════════════════════════════════════════════════════════
PRUEBA COMPLETADA EXITOSAMENTE
══════════════════════════════════════════════════════════════════
```

---

### Opción 2: Servidor Backend + Frontend Angular

#### Paso 1: Instalar Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Output esperado:**
```
╔═══════════════════════════════════════════════════════════════╗
║     SISTEMA DE GENERACIÓN DE HORARIOS - BACKEND INICIADO      ║
║                      Puerto: 5000                             ║
║                 URL: http://localhost:5000                    ║
╚═══════════════════════════════════════════════════════════════╝

 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

#### Paso 2: Instalar y Ejecutar Frontend (en otra terminal)
```bash
cd frontend
npm install
ng serve
```

**Output esperado:**
```
✔ Compiled successfully.

✔ Compiled successfully.
WARNING in buildOptimizer: Cannot understand the signature of declare classDescriptor in node_modules/@angular/core/core.d.ts, the library may need to be updated
⠙ Building...
✔ Application bundle generation complete.

Application bundle generation complete. [123.456 seconds]

Application live at: http://localhost:4200/
```

Accede a: **http://localhost:4200**

---

## 📋 Estructura de Directorios Completa

```
Sistema de horarios/
│
├── README.md                          # Este archivo
├── INSTALL.md                         # Guía de instalación
│
├── backend/
│   ├── main.py                        # Servidor Flask (API REST)
│   ├── models.py                      # Modelos Pydantic para validación
│   ├── scheduler.py                   # Motor de optimización PuLP
│   ├── excel_generator.py             # Generador de Excel con estilos
│   ├── test_local.py                  # Script de prueba sin API
│   ├── test_data.json                 # Datos de ejemplo JSON
│   ├── requirements.txt               # Dependencias Python
│   └── generated_schedules/           # Carpeta de salida (se crea automáticamente)
│       └── horario_ejemplo.xlsx       # Ejemplo de salida
│
├── frontend/
│   ├── package.json                   # Dependencias Angular
│   ├── angular.json                   # Configuración Angular
│   ├── tsconfig.json                  # Configuración TypeScript
│   ├── src/
│   │   ├── main.ts                    # Punto de entrada
│   │   ├── index.html                 # HTML principal
│   │   └── app/
│   │       ├── app.module.ts          # Módulo principal
│   │       ├── app.component.ts       # Lógica del componente
│   │       ├── app.component.html     # Template HTML
│   │       ├── app.component.css      # Estilos
│   │       └── services/
│   │           └── scheduler.service.ts  # Servicio de conexión a API
│   └── node_modules/                  # Dependencias instaladas
│
└── docs/
    ├── API_REFERENCE.md               # Documentación completa de endpoints
    ├── FORMULATION.md                 # Formulación matemática detallada
    └── INSTALL.md                     # Este archivo

```

---

## 🔧 Requisitos Previos

### Para Backend
```bash
# Python 3.9 o superior
python --version

# pip (gestor de paquetes)
pip --version
```

### Para Frontend
```bash
# Node.js 16+
node --version

# npm 8+
npm --version
```

---

## ⚙️ Instalación Detallada

### Backend

#### 1. Navegar a la carpeta
```bash
cd "c:\Users\javie\OneDrive\Escritorio\Sistema de horarios\backend"
```

#### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate    # En Windows
# source venv/bin/activate   # En Linux/Mac
```

#### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

**Dependencias a instalar:**
- `flask==2.3.3` - Framework web
- `flask-cors==4.0.0` - CORS para comunicación con frontend
- `pydantic==2.4.2` - Validación de datos
- `pulp==2.7.0` - Motor de optimización
- `openpyxl==3.1.2` - Lectura/escritura de Excel
- `xlsxwriter==3.1.8` - Generación avanzada de Excel
- `python-dateutil==2.8.2` - Manejo de fechas

#### 4. Ejecutar servidor
```bash
python main.py
```

El servidor estará disponible en: **http://localhost:5000**

---

### Frontend

#### 1. Navegar a la carpeta
```bash
cd "c:\Users\javie\OneDrive\Escritorio\Sistema de horarios\frontend"
```

#### 2. Instalar dependencias
```bash
npm install
```

Esto puede tardar 2-3 minutos.

#### 3. Ejecutar servidor de desarrollo
```bash
ng serve
```

O alternativamente:
```bash
npm start
```

La aplicación estará disponible en: **http://localhost:4200**

---

## 📝 Uso de la Interfaz Web

### 1. Configurar el Mes
- Seleccionar año, mes y días
- Indicar día de inicio (ej: Miércoles)

### 2. Configurar Tienda
- Nombre de la sucursal
- Mínimos empleados por día
- Mínimos empleados el domingo

### 3. Agregar Empleados
- Hacer clic en "+ Agregar Empleado"
- Llenar: Nombre, Contrato (Full Time/Part Time), Horas/mes
- Agregar vacaciones/licencias si aplica

### 4. Agregar Días Especiales
- Hacer clic en "+ Agregar Día Especial"
- Seleccionar: Día, Tipo (FI=Feriado, C=Cierre), Descripción

### 5. Generar Horarios
- Hacer clic en "🚀 Generar Horarios"
- Esperar 3-5 segundos
- Ver resultados en la pestaña "📊 Resultados"
- Descargar Excel con los horarios

---

## 🧪 Testing

### Prueba 1: Local (Sin API)
```bash
cd backend
python test_local.py
```

Verifica que PuLP funciona correctamente y genera un Excel de prueba.

### Prueba 2: API REST
```bash
# Terminal 1: Iniciar servidor
cd backend
python main.py

# Terminal 2: Hacer request
curl -X POST http://localhost:5000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Error: "El puerto 5000 ya está en uso"
```bash
# Opción 1: Cambiar puerto en main.py (línea final)
# app.run(port=5001, ...)

# Opción 2: Matar proceso que usa el puerto
# En Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Error: "Cannot find module '@angular/core'"
```bash
npm install
```

### Error: "No se encontró solución factible"
Significa que las restricciones son contradictorias. Intenta:
- Reducir `min_employees_per_day`
- Aumentar `max_hours_per_month`
- Agregar más empleados
- Revisar excepciones conflictivas

---

## 📊 Output Esperado

### Archivo Excel
El sistema genera un archivo `.xlsx` con:

1. **Matriz de Horarios** - Filas: empleados, Columnas: días del mes
   - Cada celda contiene un código (T, DT, L, etc.)
   - Colores diferenciados según el código

2. **Tabla de Resumen** - Conteo de cada glosa por empleado
   - Totales horizontales

3. **Leyenda** - Explicación de cada código y su color

---

## 💾 Ubicación de Archivos Generados

Los archivos Excel se guardan en:
```
backend/generated_schedules/horario_*.xlsx
```

Pueden ser descargados desde el frontend o accedidos directamente.

---

## 📞 Contacto y Soporte

Para problemas o sugerencias, revisar la documentación en:
- `docs/API_REFERENCE.md` - Endpoints disponibles
- `docs/FORMULATION.md` - Detalles matemáticos

