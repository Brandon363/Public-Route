import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { OrganisationUnitService } from '../../../services/organisation-unit.service';
import { DistrictService } from '../../../services/district.service';
import { AuthService } from '../../../services/auth.service';
import { LoadingService } from '../../../services/loading.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { OrganisationUnitCreateRequest, OrganisationUnitDTO, OrganisationUnitUpdateRequest } from '../../../models/organisation-unit.interface';
import { DistrictDTO } from '../../../models/district.interface';

const CAN_MANAGE_REFERENCE_DATA_ROLES = ['administrator'];

const CATEGORY_OPTIONS = [
  { label: 'Water & Sanitation',     value: 'water_sanitation' },
  { label: 'Roads & Infrastructure', value: 'roads_infrastructure' },
  { label: 'Electricity / Power',    value: 'electricity_power' },
  { label: 'Waste Management',       value: 'waste_management' },
  { label: 'Health Services',        value: 'health_services' },
  { label: 'Security & Safety',      value: 'security_safety' },
  { label: 'Other',                  value: 'other' },
];

@Component({
  selector: 'app-view-all-organisation-units',
  imports: [SharedModules],
  templateUrl: './view-all-organisation-units.component.html',
  styleUrl: './view-all-organisation-units.component.scss'
})
export class ViewAllOrganisationUnitsComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  units: OrganisationUnitDTO[] = [];
  loading = true;
  canManage = false;

  categoryOptions = CATEGORY_OPTIONS;
  districts: DistrictDTO[] = [];
  districtOptions: { label: string; value: number }[] = [];

  showFormDialog = false;
  editingUnit: OrganisationUnitDTO | null = null;
  saving = false;
  form: OrganisationUnitCreateRequest & { jurisdiction: number[] } = this.emptyForm();

  constructor(
    private unitService: OrganisationUnitService,
    private districtService: DistrictService,
    private authService: AuthService,
    private loadingService: LoadingService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
  ) {}

  ngOnInit(): void {
    const role = this.authService.getCurrentUser()?.role || '';
    this.canManage = CAN_MANAGE_REFERENCE_DATA_ROLES.includes(role);
    this.loadUnits();
    this.loadDistricts();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  private emptyForm(): OrganisationUnitCreateRequest & { jurisdiction: number[] } {
    return { name: '', jurisdiction: [], service_categories: [], is_active: true };
  }

  loadUnits(): void {
    this.loading = true;
    const sub = this.unitService.listUnits().subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.units) {
          this.units = res.units;
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Failed to load organisation units.' });
        }
      },
      error: () => {
        this.loading = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
      }
    });
    this.subs.push(sub);
  }

  loadDistricts(): void {
    const sub = this.districtService.listDistricts().subscribe({
      next: (res) => {
        if (res.success && res.districts) {
          this.districts = res.districts;
          this.districtOptions = res.districts.map(d => ({ label: `${d.name} — ${d.province}`, value: d.id }));
        }
      }
    });
    this.subs.push(sub);
  }

  jurisdictionLabel(unit: OrganisationUnitDTO): string {
    if (!unit.jurisdiction || unit.jurisdiction.length === 0) return 'All districts';
    const names = unit.jurisdiction.map(id => this.districts.find(d => d.id === id)?.name || `#${id}`);
    return names.join(', ');
  }

  categoryLabel(value: string): string {
    return this.categoryOptions.find(o => o.value === value)?.label || value;
  }

  openCreateDialog(): void {
    this.editingUnit = null;
    this.form = this.emptyForm();
    this.showFormDialog = true;
  }

  openEditDialog(unit: OrganisationUnitDTO): void {
    this.editingUnit = unit;
    this.form = {
      name: unit.name,
      jurisdiction: (unit.jurisdiction || []) as number[],
      service_categories: unit.service_categories || [],
      is_active: unit.is_active,
    };
    this.showFormDialog = true;
  }

  closeFormDialog(): void {
    this.showFormDialog = false;
    this.editingUnit = null;
  }

  get isFormValid(): boolean {
    return this.form.name.trim().length > 0;
  }

  save(): void {
    if (!this.isFormValid || this.saving) return;
    this.saving = true;
    this.loadingService.setLoadingState(true);

    const payload = { ...this.form };
    const request$ = this.editingUnit
      ? this.unitService.updateUnit(this.editingUnit.id, payload as OrganisationUnitUpdateRequest)
      : this.unitService.createUnit(payload);

    const sub = request$.subscribe({
      next: (res) => {
        this.saving = false;
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: this.editingUnit ? 'Unit updated.' : 'Unit created.' });
          this.closeFormDialog();
          this.loadUnits();
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Save failed.' });
        }
      },
      error: () => {
        this.saving = false;
        this.loadingService.setLoadingState(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
      }
    });
    this.subs.push(sub);
  }

  toggleActive(unit: OrganisationUnitDTO): void {
    this.loadingService.setLoadingState(true);
    const sub = this.unitService.updateUnit(unit.id, { is_active: !unit.is_active }).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: `Unit ${res.unit?.is_active ? 'activated' : 'deactivated'}.` });
          this.loadUnits();
        }
      },
      error: () => this.loadingService.setLoadingState(false)
    });
    this.subs.push(sub);
  }

  confirmDelete(event: Event, unit: OrganisationUnitDTO): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: `Delete organisation unit "${unit.name}"? This cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', outlined: true },
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      accept: () => this.deleteUnit(unit.id),
    });
  }

  deleteUnit(id: number): void {
    this.loadingService.setLoadingState(true);
    const sub = this.unitService.deleteUnit(id).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Unit deleted.' });
          this.loadUnits();
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Delete failed.' });
        }
      },
      error: () => {
        this.loadingService.setLoadingState(false);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
      }
    });
    this.subs.push(sub);
  }
}
