import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { DistrictService } from '../../../services/district.service';
import { AuthService } from '../../../services/auth.service';
import { LoadingService } from '../../../services/loading.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { DistrictCreateRequest, DistrictDTO, DistrictUpdateRequest } from '../../../models/district.interface';

const CAN_MANAGE_REFERENCE_DATA_ROLES = ['administrator'];

const SETTLEMENT_TYPE_OPTIONS = [
  { label: 'Urban', value: 'urban' },
  { label: 'Peri-Urban', value: 'peri_urban' },
  { label: 'Rural', value: 'rural' },
];

@Component({
  selector: 'app-view-all-districts',
  imports: [SharedModules],
  templateUrl: './view-all-districts.component.html',
  styleUrl: './view-all-districts.component.scss'
})
export class ViewAllDistrictsComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  districts: DistrictDTO[] = [];
  loading = true;
  canManage = false;

  settlementTypeOptions = SETTLEMENT_TYPE_OPTIONS;

  // Create/edit dialog
  showFormDialog = false;
  editingDistrict: DistrictDTO | null = null;
  saving = false;
  form: DistrictCreateRequest = this.emptyForm();

  constructor(
    private districtService: DistrictService,
    private authService: AuthService,
    private loadingService: LoadingService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
  ) {}

  ngOnInit(): void {
    const role = this.authService.getCurrentUser()?.role || '';
    this.canManage = CAN_MANAGE_REFERENCE_DATA_ROLES.includes(role);
    this.loadDistricts();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  private emptyForm(): DistrictCreateRequest {
    return { name: '', province: '', settlement_type: 'urban', latitude: null, longitude: null };
  }

  loadDistricts(): void {
    this.loading = true;
    const sub = this.districtService.listDistricts().subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.districts) {
          this.districts = res.districts;
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Failed to load districts.' });
        }
      },
      error: () => {
        this.loading = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
      }
    });
    this.subs.push(sub);
  }

  openCreateDialog(): void {
    this.editingDistrict = null;
    this.form = this.emptyForm();
    this.showFormDialog = true;
  }

  openEditDialog(district: DistrictDTO): void {
    this.editingDistrict = district;
    this.form = {
      name: district.name,
      province: district.province,
      settlement_type: district.settlement_type,
      latitude: district.latitude ?? null,
      longitude: district.longitude ?? null,
    };
    this.showFormDialog = true;
  }

  closeFormDialog(): void {
    this.showFormDialog = false;
    this.editingDistrict = null;
  }

  get isFormValid(): boolean {
    return this.form.name.trim().length > 0 && this.form.province.trim().length > 0;
  }

  save(): void {
    if (!this.isFormValid || this.saving) return;
    this.saving = true;
    this.loadingService.setLoadingState(true);

    const payload = { ...this.form };
    const request$ = this.editingDistrict
      ? this.districtService.updateDistrict(this.editingDistrict.id, payload as DistrictUpdateRequest)
      : this.districtService.createDistrict(payload);

    const sub = request$.subscribe({
      next: (res) => {
        this.saving = false;
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: this.editingDistrict ? 'District updated.' : 'District created.' });
          this.closeFormDialog();
          this.loadDistricts();
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

  confirmDelete(event: Event, district: DistrictDTO): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: `Delete district "${district.name}"? This cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', outlined: true },
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      accept: () => this.deleteDistrict(district.id),
    });
  }

  deleteDistrict(id: number): void {
    this.loadingService.setLoadingState(true);
    const sub = this.districtService.deleteDistrict(id).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'District deleted.' });
          this.loadDistricts();
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

  humanizeSettlement(value: string): string {
    return this.settlementTypeOptions.find(o => o.value === value)?.label || value;
  }
}
