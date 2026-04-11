import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SchedulerService } from './services/scheduler.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  activeTab: string = 'config';
  schedulingForm!: FormGroup;
  employees: any[] = [];
  holidays: any[] = [];
  closedDays: any[] = [];
  generateLoading: boolean = false;
  generatedSchedule: any = null;
  errorMessage: string = '';
  successMessage: string = '';

  constructor(
    private fb: FormBuilder,
    private schedulerService: SchedulerService
  ) {
    this.initializeForm();
  }

  ngOnInit(): void {
    this.initializeForm();
  }

  initializeForm(): void {
    this.schedulingForm = this.fb.group({
      year: [2026, [Validators.required, Validators.min(2020), Validators.max(2100)]],
      month: [4, [Validators.required, Validators.min(1), Validators.max(12)]],
      days_in_month: [30, [Validators.required, Validators.min(28), Validators.max(31)]],
      starting_day: ['Wednesday', Validators.required],
      store_name: ['Sucursal Centro', Validators.required],
      min_employees_per_day: [3, [Validators.required, Validators.min(1)]],
      min_employees_on_sunday: [2, [Validators.required, Validators.min(1)]]
    });

    this.employees = [
      {
        employee_id: 'EMP001',
        name: 'Juan Pérez',
        contract_type: 'Full Time',
        prior_exceptions: []
      }
    ];

    this.holidays = [];
    this.closedDays = [];
  }

  addEmployee(): void {
    const newEmp = {
      employee_id: `EMP${String(this.employees.length + 1).padStart(3, '0')}`,
      name: '',
      contract_type: 'Full Time',
      prior_exceptions: []
    };
    this.employees.push(newEmp);
  }

  removeEmployee(index: number): void {
    this.employees.splice(index, 1);
  }

  addHoliday(): void {
    this.holidays.push({
      day: 1,
      type: 'Normal',
      description: ''
    });
  }

  removeHoliday(index: number): void {
    this.holidays.splice(index, 1);
  }

  addClosedDay(): void {
    this.closedDays.push({
      day: 1
    });
  }

  removeClosedDay(index: number): void {
    this.closedDays.splice(index, 1);
  }

  generateSchedule(): void {
    if (!this.schedulingForm.valid) {
      this.errorMessage = 'Por favor, complete todos los campos requeridos';
      return;
    }

    if (this.employees.length === 0) {
      this.errorMessage = 'Debe agregar al menos un empleado';
      return;
    }

    this.generateLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const formValue = this.schedulingForm.value;
    const requestData = {
      month_config: {
        year: formValue.year,
        month: formValue.month,
        days_in_month: formValue.days_in_month,
        starting_day_of_week: formValue.starting_day
      },
      store_config: {
        store_name: formValue.store_name,
        min_employees_per_day: formValue.min_employees_per_day,
        min_employees_on_sunday: formValue.min_employees_on_sunday,
        holidays: this.holidays,
        closed_days: this.closedDays.map(cd => cd.day)
      },
      employees: this.employees
    };

    this.schedulerService.generateSchedule(requestData).subscribe({
      next: (response: any) => {
        if (response.success) {
          this.generatedSchedule = response;
          this.successMessage = 'Horarios generados exitosamente';
          this.activeTab = 'results';
          this.downloadExcel();
        } else {
          this.errorMessage = response.message || 'Error al generar horarios';
        }
        this.generateLoading = false;
      },
      error: (error: any) => {
        this.errorMessage = error.message || 'Error en la conexión con el servidor';
        this.generateLoading = false;
      }
    });
  }

  downloadExcel(): void {
    if (this.generatedSchedule && this.generatedSchedule.file_name) {
      this.schedulerService.downloadSchedule(this.generatedSchedule.file_name).subscribe({
        next: (blob: Blob) => {
          const url = window.URL.createObjectURL(blob);
          const anchor = document.createElement('a');
          anchor.href = url;
          anchor.download = this.generatedSchedule.file_name;
          anchor.click();
          window.URL.revokeObjectURL(url);
          this.successMessage = 'Archivo descargado exitosamente';
        },
        error: (error: any) => {
          this.errorMessage = 'Error al descargar el archivo: ' + error.message;
        }
      });
    }
  }

  switchTab(tab: string): void {
    this.activeTab = tab;
  }
}
