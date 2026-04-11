"""
Generador de archivos Excel con estilos y formatos
Usa XlsxWriter para crear documentos profesionales
"""
import xlsxwriter
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from models import SHIFT_CODE_COLORS


class ExcelScheduleGenerator:
    """
    Genera reportes Excel con:
    1. Matriz de horarios (empleados vs días)
    2. Tabla resumen de glosas
    3. Estilos y colores personalizados
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.workbook = None
        self.worksheet = None
        self.shift_colors = SHIFT_CODE_COLORS
        
        # Diccionario para reutilizar formatos
        self.formats = {}

    def _create_formats(self):
        """Crear formatos reutilizables"""
        self.formats['header'] = self.workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'border_color': '#000000',
            'font_size': 11
        })

        self.formats['subheader'] = self.workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9E1F2',
            'border': 1,
            'border_color': '#000000',
            'font_size': 10
        })

        self.formats['employee_name'] = self.workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#E7E6E6',
            'border': 1,
            'border_color': '#000000',
            'font_size': 9
        })

        self.formats['shift_cell'] = {}
        for code, color in self.shift_colors.items():
            self.formats['shift_cell'][code] = self.workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': color,
                'border': 1,
                'border_color': '#000000',
                'bold': True,
                'font_size': 10,
                'font_color': '#000000'
            })

        self.formats['summary_header'] = self.workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#70AD47',
            'font_color': 'white',
            'border': 1,
            'border_color': '#000000',
            'font_size': 10
        })

        self.formats['summary_cell'] = self.workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'font_size': 9
        })

        self.formats['summary_name'] = self.workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'font_size': 9
        })

        self.formats['title'] = self.workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#4472C4',
            'font_color': 'white'
        })

        self.formats['total_cell'] = self.workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
            'bold': True,
            'bg_color': '#FFC7CE',
            'font_size': 9
        })

    def generate(self,
                 schedule: Dict,
                 summary: Dict,
                 calendar: List[Tuple[int, str]],
                 employees_data: List[Dict],
                 store_name: str = "Retail Store",
                 month_name: str = "Abril",
                 year: int = 2026,
                 month_config=None):
        """
        Genera el archivo Excel completo

        Args:
            schedule: {emp_id: {day: code}}
            summary: {emp_id: {code: count}}
            calendar: [(day, day_name), ...] - puede ser None
            employees_data: lista de empleados
            store_name: nombre de la tienda
            month_name: nombre del mes
            year: año
            month_config: config del mes (para días totales)
        """
        # Crear workbook
        self.workbook = xlsxwriter.Workbook(self.file_path)
        self.worksheet = self.workbook.add_worksheet('Horarios')
        
        self._create_formats()
        
        # Si calendar es vacío, crear uno basado en schedule
        if not calendar or len(calendar) == 0:
            days_in_month = max(max(schedule[emp].keys()) for emp in schedule) if schedule else 30
            days_of_week = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']
            calendar = [(day, days_of_week[(day - 1) % 7]) for day in range(1, days_in_month + 1)]
        
        # Configurar ancho de columnas
        self.worksheet.set_column('A:A', 22)  # Nombres empleados
        for col in range(len(calendar)):
            self.worksheet.set_column(col + 1, col + 1, 6)  # Columnas de días
        
        # Escribir título principal con sucursal y mes
        title = f"{store_name} - {month_name} {year}"
        last_col_letter = chr(65 + len(calendar))  # A=65, B=66, etc.
        range_str = f'A1:{last_col_letter}1'
        
        title_format = self.workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'bg_color': '#5B9BD5',
            'font_color': 'white',
            'border': 1
        })
        
        self.worksheet.merge_range(range_str, title, title_format)
        self.worksheet.set_row(0, 25)
        
        # Escribir encabezado de días (fila 2)
        self.worksheet.write(1, 0, 'Empleado', self.formats['header'])
        self.worksheet.set_row(1, 20)
        
        # Día (número)
        for col, (day, day_name) in enumerate(calendar):
            self.worksheet.write(1, col + 1, str(day), self.formats['subheader'])
        
        # Día de la semana (fila 3)
        self.worksheet.set_row(2, 20)
        self.worksheet.write(2, 0, '', self.formats['header'])
        for col, (day, day_name) in enumerate(calendar):
            fmt = self.workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D9E1F2',
                'border': 1,
                'font_size': 8,
                'italic': True,
                'bold': True
            })
            self.worksheet.write(2, col + 1, day_name[:3].upper(), fmt)
        
        # Escribir datos de horarios (empezando en fila 4)
        emp_list = list(schedule.keys()) if schedule else []
        for row, emp_id in enumerate(emp_list):
            # Encontrar nombre del empleado
            emp_name = next((e.get('name', emp_id) for e in employees_data if e.get('employee_id') == emp_id), emp_id)
            
            # Escribir nombre
            self.worksheet.write(row + 3, 0, emp_name, self.formats['employee_name'])
            
            # Escribir turnos
            for col, (day, _) in enumerate(calendar):
                code = schedule[emp_id].get(day, 'C')  # Default 'C' (cerrado)
                if code in self.formats['shift_cell']:
                    self.worksheet.write(row + 3, col + 1, code, self.formats['shift_cell'][code])
                else:
                    # Si el código no existe, usar formato genérico
                    fmt = self.workbook.add_format({
                        'align': 'center',
                        'valign': 'vcenter',
                        'border': 1,
                        'bg_color': '#FFFFFF'
                    })
                    self.worksheet.write(row + 3, col + 1, code, fmt)
        
        # Espaciador
        summary_start_row = len(emp_list) + 5
        
        # Escribir tabla de resumen (glosas)
        self._generate_summary_table(summary, employees_data, emp_list, summary_start_row)
        
        self._add_legend(summary_start_row + len(emp_list) + 3)
        
        self.workbook.close()
        print(f"[EXCEL] Archivo generado exitosamente: {self.file_path}")

    def _generate_summary_table(self, summary: Dict, employees_data: List[Dict], 
                               emp_list: List[str], start_row: int):
        """
        Genera tabla de resumen con conteos de glosas
        """
        # Códigos a contar (en el orden que aparecen en la imagen)
        codes = ['T', 'DT', 'L', 'LC', 'V', 'LM', 'FI', 'C']
        
        self.worksheet.write(start_row, 0, 'Empleado', self.formats['summary_header'])
        for col, code in enumerate(codes):
            self.worksheet.write(start_row, col + 1, code, self.formats['summary_header'])
        self.worksheet.write(start_row, len(codes) + 1, 'TOTAL', self.formats['summary_header'])
        
        # Datos de resumen
        for row, emp_id in enumerate(emp_list):
            emp_name = next((e.get('name', emp_id) for e in employees_data if e.get('employee_id') == emp_id), emp_id)
            self.worksheet.write(start_row + row + 1, 0, emp_name, self.formats['summary_name'])
            
            total_worked = 0
            for col, code in enumerate(codes):
                # Buscar el código en el resumen - puede venir como T, DT, L, etc.
                count = summary[emp_id].get(code, 0) if emp_id in summary else 0
                self.worksheet.write(start_row + row + 1, col + 1, count, self.formats['summary_cell'])
                
                # Sumar solo trabajos (T, DT)
                if code in ['T', 'DT']:
                    total_worked += count
            
            # Total trabajados
            self.worksheet.write(start_row + row + 1, len(codes) + 1, total_worked, self.formats['total_cell'])

    def _add_legend(self, start_row: int):
        """
        Agrega leyenda de glosas y colores
        """
        legend_data = [
            ('T8', 'Turno 8 horas (Full Time)'),
            ('T9', 'Turno 9 horas (Full Time)'),
            ('T10', 'Turno 10 horas (Part Time)'),
            ('DT', 'Domingo Trabajado'),
            ('L', 'Libre por Horario'),
            ('LC', 'Libre Compensado'),
            ('V', 'Vacaciones'),
            ('LM', 'Licencia Médica'),
            ('FI', 'Feriado Irrenunciable'),
            ('C', 'Local Cerrado'),
        ]
        
        legend_header = self.workbook.add_format({
            'bold': True,
            'font_size': 11,
            'underline': True
        })
        
        self.worksheet.write(start_row, 0, 'LEYENDA DE GLOSAS:', legend_header)
        
        for idx, (code, description) in enumerate(legend_data):
            if code in self.formats['shift_cell']:
                self.worksheet.write(start_row + idx + 1, 0, code, self.formats['shift_cell'][code])
            else:
                fmt = self.workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'bg_color': '#FFFFFF'
                })
                self.worksheet.write(start_row + idx + 1, 0, code, fmt)
            self.worksheet.write(start_row + idx + 1, 1, description, self.formats['summary_cell'])
