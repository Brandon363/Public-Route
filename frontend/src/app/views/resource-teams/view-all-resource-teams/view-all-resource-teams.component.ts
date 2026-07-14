import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { ResourceTeamService } from '../../../services/resource-team.service';
import { DistrictService } from '../../../services/district.service';
import { AuthService } from '../../../services/auth.service';
import { LoadingService } from '../../../services/loading.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ResourceTeamCreateRequest, ResourceTeamDTO, ResourceTeamUpdateRequest } from '../../../models/resource-team.interface';
import { DistrictDTO } from '../../../models/district.interface';

// CAN_MANAGE_REFERENCE_DATA — create/delete. CAN_MANAGE_QUEUE — update/deactivate.
const CAN_CREATE_DELETE_ROLES = ['administrator'];
const CAN_MANAGE_ROLES = ['supervisor', 'administrator'];

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
  selector: 'app-view-all-resource-teams',
  imports: [SharedModules],
  templateUrl: './view-all-resource-teams.component.html',
  styleUrl: './view-all-resource-teams.component.scss'
})
export class ViewAllResourceTeamsComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  teams: ResourceTeamDTO[] = [];
  loading = true;
  canCreateDelete = false;
  canManage = false;

  categoryOptions = CATEGORY_OPTIONS;
  districts: DistrictDTO[] = [];
  districtOptions: { label: string; value: number }[] = [];

  showFormDialog = false;
  editingTeam: ResourceTeamDTO | null = null;
  saving = false;
  form: ResourceTeamCreateRequest & { skillsText: string } = this.emptyForm();

  constructor(
    private teamService: ResourceTeamService,
    private districtService: DistrictService,
    private authService: AuthService,
    private loadingService: LoadingService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
  ) {}

  ngOnInit(): void {
    const role = this.authService.getCurrentUser()?.role || '';
    this.canCreateDelete = CAN_CREATE_DELETE_ROLES.includes(role);
    this.canManage = CAN_MANAGE_ROLES.includes(role) || this.canCreateDelete;
    this.loadTeams();
    this.loadDistricts();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  private emptyForm(): ResourceTeamCreateRequest & { skillsText: string } {
    return { name: '', skillsText: '', service_categories: [], capacity: 1, base_district_id: null, is_active: true };
  }

  loadTeams(): void {
    this.loading = true;
    const sub = this.teamService.listTeams().subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.teams) {
          this.teams = res.teams;
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Failed to load resource teams.' });
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

  districtLabel(id: number | null | undefined): string {
    if (id == null) return '—';
    return this.districts.find(d => d.id === id)?.name || `District #${id}`;
  }

  categoryLabel(value: string): string {
    return this.categoryOptions.find(o => o.value === value)?.label || value;
  }

  openCreateDialog(): void {
    this.editingTeam = null;
    this.form = this.emptyForm();
    this.showFormDialog = true;
  }

  openEditDialog(team: ResourceTeamDTO): void {
    this.editingTeam = team;
    this.form = {
      name: team.name,
      skillsText: (team.skills || []).join(', '),
      service_categories: team.service_categories || [],
      capacity: team.capacity,
      base_district_id: team.base_district_id ?? null,
      is_active: team.is_active,
    };
    this.showFormDialog = true;
  }

  closeFormDialog(): void {
    this.showFormDialog = false;
    this.editingTeam = null;
  }

  get isFormValid(): boolean {
    return this.form.name.trim().length > 0 && (this.form.capacity || 0) >= 1;
  }

  save(): void {
    if (!this.isFormValid || this.saving) return;
    this.saving = true;
    this.loadingService.setLoadingState(true);

    const skills = this.form.skillsText.split(',').map(s => s.trim()).filter(s => s.length > 0);
    const payload = {
      name: this.form.name,
      skills,
      service_categories: this.form.service_categories,
      capacity: this.form.capacity,
      base_district_id: this.form.base_district_id,
      is_active: this.form.is_active,
    };

    const request$ = this.editingTeam
      ? this.teamService.updateTeam(this.editingTeam.id, payload as ResourceTeamUpdateRequest)
      : this.teamService.createTeam(payload);

    const sub = request$.subscribe({
      next: (res) => {
        this.saving = false;
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: this.editingTeam ? 'Team updated.' : 'Team created.' });
          this.closeFormDialog();
          this.loadTeams();
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

  toggleActive(team: ResourceTeamDTO): void {
    this.loadingService.setLoadingState(true);
    const sub = this.teamService.updateTeam(team.id, { is_active: !team.is_active }).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: `Team ${res.team?.is_active ? 'activated' : 'deactivated'}.` });
          this.loadTeams();
        }
      },
      error: () => this.loadingService.setLoadingState(false)
    });
    this.subs.push(sub);
  }

  confirmDelete(event: Event, team: ResourceTeamDTO): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: `Delete resource team "${team.name}"? This cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', outlined: true },
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      accept: () => this.deleteTeam(team.id),
    });
  }

  deleteTeam(id: number): void {
    this.loadingService.setLoadingState(true);
    const sub = this.teamService.deleteTeam(id).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Team deleted.' });
          this.loadTeams();
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
