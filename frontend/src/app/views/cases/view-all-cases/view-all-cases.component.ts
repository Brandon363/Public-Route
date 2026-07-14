import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { CaseService } from '../../../services/case.service';
import { DistrictService } from '../../../services/district.service';
import { LoadingService } from '../../../services/loading.service';
import { AuthService } from '../../../services/auth.service';
import { MessageService } from 'primeng/api';
import { CaseDTO } from '../../../models/case.interface';

// Mirrors the backend's CAN_VIEW_ANALYTICS group (Utils/permissions.py) —
// checked client-side purely to avoid firing a request that we already
// know will 403, not as a substitute for the backend's own enforcement.
const CAN_VIEW_ANALYTICS_ROLES = ['analyst', 'manager', 'supervisor', 'administrator'];
const CITIZEN_ROLE = 'citizen';

const STATUS_ICONS: Record<string, string> = {
  RECEIVED: 'pi pi-inbox',
  VALIDATING: 'pi pi-spinner',
  CLASSIFIED: 'pi pi-tag',
  ROUTED: 'pi pi-directions',
  ASSIGNED: 'pi pi-user',
  IN_PROGRESS: 'pi pi-cog',
  RESOLVED: 'pi pi-check-circle',
  CLOSED: 'pi pi-lock',
  REJECTED: 'pi pi-times-circle',
  MANUAL_REVIEW: 'pi pi-eye',
  NEEDS_INFORMATION: 'pi pi-question-circle',
  ON_HOLD: 'pi pi-pause-circle',
  ESCALATED: 'pi pi-exclamation-triangle',
  REOPENED: 'pi pi-refresh',
};

const STATUS_SEVERITY: Record<string, 'success' | 'info' | 'warn' | 'danger' | 'secondary'> = {
  RECEIVED: 'info',
  VALIDATING: 'info',
  CLASSIFIED: 'info',
  ROUTED: 'warn',
  ASSIGNED: 'warn',
  IN_PROGRESS: 'warn',
  RESOLVED: 'success',
  CLOSED: 'success',
  REJECTED: 'danger',
  MANUAL_REVIEW: 'secondary',
  NEEDS_INFORMATION: 'secondary',
  ON_HOLD: 'secondary',
  ESCALATED: 'secondary',
  REOPENED: 'secondary',
};

const URGENCY_SEVERITY: Record<string, 'success' | 'info' | 'warn' | 'danger'> = {
  low: 'success',
  medium: 'info',
  high: 'warn',
  critical: 'danger',
};

// A case in one of these states is no longer "on the clock" — SLA countdown
// text is suppressed once resolved/closed/rejected.
const FINAL_STATUSES = ['RESOLVED', 'CLOSED', 'REJECTED'];

const STATUS_OPTIONS = Object.keys(STATUS_ICONS);

const CATEGORY_OPTIONS = [
  'water_sanitation',
  'roads_infrastructure',
  'electricity_power',
  'waste_management',
  'health_services',
  'security_safety',
  'other',
];

@Component({
  selector: 'app-view-all-cases',
  imports: [SharedModules],
  templateUrl: './view-all-cases.component.html',
  styleUrl: './view-all-cases.component.scss'
})
export class ViewAllCasesComponent implements OnInit, OnDestroy {
  casesSubscription!: Subscription;
  summarySubscription!: Subscription;

  allCases: CaseDTO[] = [];
  cards: any[] = [];
  loading = true;

  statusOptions = STATUS_OPTIONS;
  categoryOptions = CATEGORY_OPTIONS;

  // Filter toolbar
  statusFilter: string | null = null;
  categoryFilter: string | null = null;
  searchQuery: string = '';

  // district_id -> "Name — Province" lookup, populated once so the table
  // can show a readable district instead of the raw numeric FK.
  districtNames: Record<number, string> = {};

  private currentUserRole = '';

  constructor(
    private caseService: CaseService,
    private districtService: DistrictService,
    private loadingService: LoadingService,
    private authService: AuthService,
    private messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.currentUserRole = this.authService.getCurrentUser()?.role || '';
    this.loadCases();
    this.loadDistrictNames();
    if (CAN_VIEW_ANALYTICS_ROLES.includes(this.currentUserRole)) {
      this.loadSummary();
    }
  }

  loadDistrictNames(): void {
    this.districtService.listDistricts().subscribe({
      next: (res) => {
        if (res.success && res.districts) {
          this.districtNames = Object.fromEntries(
            res.districts.map(d => [d.id, `${d.name} — ${d.province}`])
          );
        }
      },
      error: () => { /* Non-fatal: falls back to the raw district ID. */ }
    });
  }

  getDistrictName(districtId: number | null | undefined): string {
    if (districtId == null) return '—';
    return this.districtNames[districtId] || `District #${districtId}`;
  }

  ngOnDestroy(): void {
    this.casesSubscription?.unsubscribe();
    this.summarySubscription?.unsubscribe();
  }

  // ── Data loading ───────────────────────────────────────────────────────────

  loadCases(): void {
    this.loadingService.setLoadingState(true);
    this.loading = true;

    const filters = {
      status: this.statusFilter || undefined,
      category: this.categoryFilter || undefined
    };

    // Citizens use /cases/mine (scoped to their own submissions).
    // Staff roles use /cases/ (the full platform view).
    const request$ = this.isCitizen()
      ? this.caseService.getMyCases(filters)
      : this.caseService.getAllCases(filters);

    this.casesSubscription = request$.subscribe({
      next: (response) => {
        this.loadingService.setLoadingState(false);
        this.loading = false;
        if (response.success) {
          this.allCases = response.cases || [];
        } else {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: response.message || 'Failed to retrieve cases.' });
        }
      },
      error: () => {
        this.loadingService.setLoadingState(false);
        this.loading = false;
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to connect to backend.' });
      }
    });
  }

  loadSummary(): void {
    this.summarySubscription = this.caseService.getCaseSummary('status').subscribe({
      next: (response) => {
        if (response.success) {
          const counts = response.counts || [];
          const total = counts.reduce((sum, row) => sum + row.count, 0);
          this.cards = [
            { title: 'Total Cases', value: total.toString(), description: 'Across every status', icon: 'pi pi-briefcase' },
            ...counts.map(row => ({
              title: this.humanize(row.key),
              value: row.count.toString(),
              description: `Cases currently ${this.humanize(row.key).toLowerCase()}`,
              icon: STATUS_ICONS[row.key] || 'pi pi-circle'
            }))
          ];
        }
      },
      error: () => {
        // Non-fatal: the table still renders without the summary cards.
      }
    });
  }

  // ── Filter toolbar ─────────────────────────────────────────────────────────

  onFilterChange(): void {
    this.loadCases();
  }

  clearFilters(): void {
    this.statusFilter = null;
    this.categoryFilter = null;
    this.searchQuery = '';
    this.loadCases();
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  isCitizen(): boolean {
    return this.currentUserRole === CITIZEN_ROLE;
  }

  getStatusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' {
    return STATUS_SEVERITY[status] || 'secondary';
  }

  getUrgencySeverity(urgency: string): 'success' | 'info' | 'warn' | 'danger' {
    return URGENCY_SEVERITY[urgency?.toLowerCase()] || 'info';
  }

  humanize(value: string | null | undefined): string {
    if (!value) {
      return 'Unknown';
    }
    return value
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  // ── SLA countdown ──────────────────────────────────────────────────────────

  private slaDaysRemaining(caseItem: CaseDTO): number | null {
    if (!caseItem.sla_deadline || FINAL_STATUSES.includes(caseItem.status)) return null;
    const diffMs = new Date(caseItem.sla_deadline).getTime() - Date.now();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }

  isSlaUrgent(caseItem: CaseDTO): boolean {
    const days = this.slaDaysRemaining(caseItem);
    return days != null && days < 3;
  }

  slaDaysText(caseItem: CaseDTO): string {
    const days = this.slaDaysRemaining(caseItem);
    if (days == null) return '';
    if (days < 0) return `Overdue by ${Math.abs(days)} day${Math.abs(days) === 1 ? '' : 's'}`;
    if (days === 0) return 'Due today';
    return `${days} day${days === 1 ? '' : 's'} left`;
  }
}
