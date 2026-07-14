import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { QueueService } from '../../../services/queue.service';
import { OrganisationUnitService } from '../../../services/organisation-unit.service';
import { CaseService } from '../../../services/case.service';
import { AuthService } from '../../../services/auth.service';
import { QueueDTO } from '../../../models/queue.interface';
import { OrganisationUnitDTO } from '../../../models/organisation-unit.interface';
import { CaseDTO } from '../../../models/case.interface';

// Mirrors the backend's CAN_VIEW_CASES group (Utils/permissions.py) —
// checked client-side purely to avoid firing a request we already know
// will 403 (e.g. field_team/auditor can see the Queues nav but not /cases).
const CAN_VIEW_CASES_ROLES = ['intake_officer', 'dispatcher', 'supervisor', 'analyst', 'manager', 'administrator'];

const STATUS_SEVERITY: Record<string, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
  RECEIVED: 'info', VALIDATING: 'info', CLASSIFIED: 'info',
  ROUTED: 'warn', ASSIGNED: 'warn', IN_PROGRESS: 'warn',
  RESOLVED: 'success', CLOSED: 'success', REJECTED: 'danger',
  MANUAL_REVIEW: 'secondary', NEEDS_INFORMATION: 'secondary',
  ON_HOLD: 'secondary', ESCALATED: 'secondary', REOPENED: 'secondary',
};

const URGENCY_SEVERITY: Record<string, 'success' | 'info' | 'warn' | 'danger'> = {
  low: 'success', medium: 'info', high: 'warn', critical: 'danger',
};

@Component({
  selector: 'app-queue-detail',
  imports: [SharedModules],
  templateUrl: './queue-detail.component.html',
  styleUrl: './queue-detail.component.scss'
})
export class QueueDetailComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  queueId!: number;
  queue: QueueDTO | null = null;
  loading = true;
  notFound = false;

  unit: OrganisationUnitDTO | null = null;

  cases: CaseDTO[] = [];
  loadingCases = false;
  canViewCases = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private queueService: QueueService,
    private unitService: OrganisationUnitService,
    private caseService: CaseService,
    private authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.canViewCases = CAN_VIEW_CASES_ROLES.includes(this.authService.getCurrentUser()?.role || '');

    const sub = this.route.paramMap.subscribe(params => {
      const id = Number(params.get('id'));
      if (id) {
        this.queueId = id;
        this.loadQueue();
      }
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  loadQueue(): void {
    this.loading = true;
    this.notFound = false;
    const sub = this.queueService.getQueue(this.queueId).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.queue) {
          this.queue = res.queue;
          this.loadUnit(res.queue.unit_id);
          if (this.canViewCases) {
            this.loadCases();
          }
        } else {
          this.notFound = true;
        }
      },
      error: () => {
        this.loading = false;
        this.notFound = true;
      }
    });
    this.subs.push(sub);
  }

  loadUnit(unitId: number): void {
    const sub = this.unitService.getUnit(unitId).subscribe({
      next: (res) => {
        if (res.success && res.unit) {
          this.unit = res.unit;
        }
      }
    });
    this.subs.push(sub);
  }

  loadCases(): void {
    this.loadingCases = true;
    const sub = this.caseService.getAllCases({ queue_id: this.queueId }).subscribe({
      next: (res) => {
        this.loadingCases = false;
        if (res.success) {
          this.cases = res.cases || [];
        }
      },
      error: () => { this.loadingCases = false; }
    });
    this.subs.push(sub);
  }

  goBack(): void {
    this.router.navigate(['/queues']);
  }

  getStatusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
    return STATUS_SEVERITY[status] || 'secondary';
  }

  getUrgencySeverity(urgency: string): 'success' | 'info' | 'warn' | 'danger' {
    return URGENCY_SEVERITY[urgency?.toLowerCase()] || 'info';
  }

  humanize(value: string | null | undefined): string {
    if (!value) return 'Unknown';
    return value.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  }
}
