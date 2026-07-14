import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { QueueService } from '../../../services/queue.service';
import { OrganisationUnitService } from '../../../services/organisation-unit.service';
import { AuthService } from '../../../services/auth.service';
import { LoadingService } from '../../../services/loading.service';
import { ConfirmationService, MessageService } from 'primeng/api';
import { QueueCreateRequest, QueueDTO, QueueUpdateRequest } from '../../../models/queue.interface';
import { OrganisationUnitDTO } from '../../../models/organisation-unit.interface';

// CAN_MANAGE_REFERENCE_DATA — create/delete. CAN_MANAGE_QUEUE — update/deactivate.
const CAN_CREATE_DELETE_ROLES = ['administrator'];
const CAN_MANAGE_ROLES = ['supervisor', 'administrator'];

@Component({
  selector: 'app-view-all-queues',
  imports: [SharedModules],
  templateUrl: './view-all-queues.component.html',
  styleUrl: './view-all-queues.component.scss'
})
export class ViewAllQueuesComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  queues: QueueDTO[] = [];
  loading = true;
  canCreateDelete = false;
  canManage = false;

  units: OrganisationUnitDTO[] = [];
  unitOptions: { label: string; value: number }[] = [];

  showFormDialog = false;
  editingQueue: QueueDTO | null = null;
  saving = false;
  form: QueueCreateRequest = this.emptyForm();

  constructor(
    private queueService: QueueService,
    private unitService: OrganisationUnitService,
    private authService: AuthService,
    private loadingService: LoadingService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
  ) {}

  ngOnInit(): void {
    const role = this.authService.getCurrentUser()?.role || '';
    this.canCreateDelete = CAN_CREATE_DELETE_ROLES.includes(role);
    this.canManage = CAN_MANAGE_ROLES.includes(role) || this.canCreateDelete;
    this.loadQueues();
    this.loadUnits();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  private emptyForm(): QueueCreateRequest {
    return { unit_id: 0, name: '', capacity: null, is_active: true };
  }

  loadQueues(): void {
    this.loading = true;
    const sub = this.queueService.listQueues().subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.queues) {
          this.queues = res.queues;
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Failed to load queues.' });
        }
      },
      error: () => {
        this.loading = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
      }
    });
    this.subs.push(sub);
  }

  loadUnits(): void {
    const sub = this.unitService.listUnits().subscribe({
      next: (res) => {
        if (res.success && res.units) {
          this.units = res.units;
          this.unitOptions = res.units.map(u => ({ label: u.name, value: u.id }));
        }
      }
    });
    this.subs.push(sub);
  }

  unitName(unitId: number): string {
    return this.units.find(u => u.id === unitId)?.name || `Unit #${unitId}`;
  }

  openCreateDialog(): void {
    this.editingQueue = null;
    this.form = this.emptyForm();
    this.showFormDialog = true;
  }

  openEditDialog(queue: QueueDTO): void {
    this.editingQueue = queue;
    this.form = {
      unit_id: queue.unit_id,
      name: queue.name,
      capacity: queue.capacity ?? null,
      is_active: queue.is_active,
    };
    this.showFormDialog = true;
  }

  closeFormDialog(): void {
    this.showFormDialog = false;
    this.editingQueue = null;
  }

  get isFormValid(): boolean {
    return this.form.name.trim().length > 0 && (this.editingQueue != null || this.form.unit_id > 0);
  }

  save(): void {
    if (!this.isFormValid || this.saving) return;
    this.saving = true;
    this.loadingService.setLoadingState(true);

    const request$ = this.editingQueue
      ? this.queueService.updateQueue(this.editingQueue.id, {
          name: this.form.name,
          capacity: this.form.capacity,
          is_active: this.form.is_active,
        } as QueueUpdateRequest)
      : this.queueService.createQueue(this.form);

    const sub = request$.subscribe({
      next: (res) => {
        this.saving = false;
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: this.editingQueue ? 'Queue updated.' : 'Queue created.' });
          this.closeFormDialog();
          this.loadQueues();
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

  toggleActive(queue: QueueDTO): void {
    this.loadingService.setLoadingState(true);
    const sub = this.queueService.updateQueue(queue.id, { is_active: !queue.is_active }).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: `Queue ${res.queue?.is_active ? 'activated' : 'deactivated'}.` });
          this.loadQueues();
        }
      },
      error: () => this.loadingService.setLoadingState(false)
    });
    this.subs.push(sub);
  }

  confirmDelete(event: Event, queue: QueueDTO): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: `Delete queue "${queue.name}"? This cannot be undone.`,
      header: 'Confirm Delete',
      icon: 'pi pi-exclamation-triangle',
      rejectButtonProps: { label: 'Cancel', severity: 'secondary', outlined: true },
      acceptButtonProps: { label: 'Delete', severity: 'danger' },
      accept: () => this.deleteQueue(queue.id),
    });
  }

  deleteQueue(id: number): void {
    this.loadingService.setLoadingState(true);
    const sub = this.queueService.deleteQueue(id).subscribe({
      next: (res) => {
        this.loadingService.setLoadingState(false);
        if (res.success) {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Queue deleted.' });
          this.loadQueues();
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
