"""
Modelos de datos con Pydantic para validación de entrada del Frontend
VERSIÓN 2.0: Nuevas restricciones de negocio con FT/PT, feriados compensados, y optimización de continuidad
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum
from datetime import datetime


class ContractType(str, Enum):
    """Tipos de contrato"""
    FULL_TIME = "Full Time"
    PART_TIME = "Part Time"


class ShiftCode(str, Enum):
    """Códigos de asignación de turnos (Glosas) - Versión 2.0
    
    TURNOS TRABAJADOS:
    - T8: Turno de 8 horas (Full Time)
    - T9: Turno de 9 horas (Full Time)
    - T10: Turno de 10 horas (Part Time, Sábado/Domingo)
    - DT: Domingo Trabajado (Full Time)
    
    DÍAS LIBRES:
    - L: Libre por horario (parte del ciclo 2 libres/semana)
    - LC: Libre Compensado (por trabajar feriado normal)
    
    EXCEPCIONES FIJAS:
    - V: Vacaciones
    - LM: Licencia Médica
    - FI: Feriado Irrenunciable (no consume días libres)
    - C: Local Cerrado
    """
    T8 = "T8"         # Turno 8h (FT)
    T9 = "T9"         # Turno 9h (FT)
    T10 = "T10"       # Turno 10h (PT)
    DT = "DT"         # Domingo Trabajado (FT)
    L = "L"           # Libre normal
    LC = "LC"         # Libre Compensado (por feriado trabajado)
    V = "V"           # Vacaciones
    LM = "LM"         # Licencia Médica
    FI = "FI"         # Feriado Irrenunciable
    C = "C"           # Local Cerrado


class DayOfWeek(str, Enum):
    """Días de la semana"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class HolidayType(str, Enum):
    """Tipos de feriados"""
    NORMAL = "Normal"              # Worked = LC compensado
    IRRENUNCIABLE = "Irrenunciable" # Asignado como FI (no consume descansos)


class Holiday(BaseModel):
    """Feriado del mes"""
    day: int = Field(..., ge=1, le=31, description="Número del día (1-31)")
    type: HolidayType = Field(..., description="Normal o Irrenunciable")
    description: str = Field(default="", description="Nombre del feriado")


class SpecialDay(BaseModel):
    """Representación genérica de un día especial (feriado o cierre)"""
    day: int = Field(..., ge=1, le=31, description="Número del día (1-31)")
    type: str = Field(..., description="Holiday=Feriado, Closed=Cerrado")
    holiday_type: Optional[HolidayType] = Field(default=None, description="Si type=Holiday, especificar Normal/Irrenunciable")
    description: str = Field(default="", description="Descripción del evento")


class PriorException(BaseModel):
    """Pre-asignaciones de días especiales para cada empleado"""
    day: int = Field(..., ge=1, le=31, description="Número del día")
    type: str = Field(..., description="V=Vacaciones, LM=Licencia Médica")
    description: str = Field(default="", description="Descripción")

    @validator('type')
    def validate_type(cls, v):
        if v not in ['V', 'LM']:
            raise ValueError("type debe ser 'V' o 'LM'")
        return v


class MonthConfig(BaseModel):
    """Configuración del mes a programar"""
    year: int = Field(..., description="Año (ej. 2026)")
    month: int = Field(..., ge=1, le=12, description="Mes (1-12)")
    days_in_month: int = Field(..., ge=28, le=31, description="Cantidad de días del mes")
    starting_day_of_week: DayOfWeek = Field(..., description="Día de la semana en que inicia el mes")


class StoreConfig(BaseModel):
    """Configuración de la tienda"""
    store_name: str = Field(default="Sucursal Retail", description="Nombre de la sucursal")
    min_employees_per_day: int = Field(default=2, ge=1, description="Mínimo empleados por día")
    min_employees_on_sunday: int = Field(default=1, ge=1, description="Mínimo empleados el domingo")
    holidays: List[Holiday] = Field(default_factory=list, description="Feriados del mes")
    closed_days: List[int] = Field(default_factory=list, description="Días que cierra (1-31)")


class Employee(BaseModel):
    """Datos de cada trabajador - Versión 2.0
    
    FULL TIME:
    - Exactamente 42h/semana (2 días de 9h + 3 días de 8h)
    - 5 días trabajados + 2 libres por semana
    - Mín 2 domingos trabajados y 2 libres al mes
    - Los 2 libres semanales deben ser continuos (preferencia soft)
    
    PART TIME:
    - Exactamente 20h/semana (2 días de 10h, solo Sábado/Domingo)
    - Disponibilidad limitada a Sábado y Domingo
    """
    employee_id: str = Field(..., description="ID único del empleado")
    name: str = Field(..., description="Nombre completo")
    contract_type: ContractType = Field(..., description="Full Time o Part Time")
    prior_exceptions: List[PriorException] = Field(default_factory=list, description="Vacaciones/Licencias previas")

    @validator('contract_type')
    def allowed_contracts(cls, v):
        # Future: expandir a otros tipos si es necesario
        return v


class SchedulingRequest(BaseModel):
    """Solicitud completa de generación de horarios - Versión 2.0"""
    scheduling_request: 'SchedulingRequestData' = Field(..., description="Datos completos de la solicitud")


class SchedulingRequestData(BaseModel):
    """Datos internos de la solicitud de horarios"""
    month_config: MonthConfig = Field(..., description="Configuración del mes")
    store_config: StoreConfig = Field(..., description="Configuración de la tienda")
    employees: List[Employee] = Field(..., min_items=1, description="Lista de empleados")

    @validator('employees')
    def validate_employees(cls, v):
        ids = [e.employee_id for e in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Los IDs de empleados deben ser únicos")
        return v


# Actualizar forward references
SchedulingRequest.update_forward_refs()


class ScheduleResult(BaseModel):
    """Resultado de la programación"""
    success: bool
    message: str
    schedule: Optional[dict] = None  # {employee_id: {day: code}}
    summary: Optional[dict] = None  # {employee_id: {code: count}}
    file_path: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


# Color mapping para cada glosa - Versión 2.0
SHIFT_CODE_COLORS = {
    "T": "#C8E6C9",    # Verde pastel (Turno de trabajo)
    "DT": "#90CAF9",   # Azul pastel (Domingo Trabajado)
    "L": "#FFE0B2",    # Naranja pastel (Libre normal)
    "LC": "#FFF9C4",   # Amarillo pastel (Libre Compensado)
    "V": "#F8BBD0",    # Rosa pastel (Vacaciones)
    "LM": "#FFCCBC",   # Naranja pastel oscuro (Licencia Médica)
    "FI": "#EF9A9A",   # Rojo pastel (Feriado Irrenunciable)
    "C": "#F5F5F5"     # Gris pastel (Cerrado)
}

# Horas asociadas a cada glosa
SHIFT_CODE_HOURS = {
    "T": 8,     # Turno genérico (8-10 horas dependiendo del tipo)
    "DT": 8,    # Domingo Trabajado
    "L": 0,     # Libre
    "LC": 0,    # Libre Compensado
    "V": 0,     # Vacaciones
    "LM": 0,    # Licencia Médica
    "FI": 0,    # Feriado Irrenunciable
    "C": 0      # Cerrado
}
