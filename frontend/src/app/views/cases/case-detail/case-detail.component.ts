import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { CaseService } from '../../../services/case.service';
import { QueueService } from '../../../services/queue.service';
import { OrganisationUnitService } from '../../../services/organisation-unit.service';
import { DistrictService } from '../../../services/district.service';
import { AuditEventService } from '../../../services/audit-event.service';
import { LoadingService } from '../../../services/loading.service';
import { AuthService } from '../../../services/auth.service';
import { MessageService } from 'primeng/api';
import { CaseDTO, ClassificationCorrectionPayload, RouteCasePayload, StatusUpdatePayload } from '../../../models/case.interface';
import { AuditEventDTO } from '../../../models/audit-event.interface';
import { QueueDTO } from '../../../models/queue.interface';
import { OrganisationUnitDTO } from '../../../models/organisation-unit.interface';

// Backend permission groups — mirrored from Utils/permissions.py
const CAN_CORRECT_CLASSIFICATION_ROLES = ['intake_officer', 'dispatcher', 'administrator'];
const CAN_ROUTE_CASES_ROLES            = ['dispatcher', 'supervisor', 'administrator'];
const CAN_UPDATE_STATUS_ROLES          = ['dispatcher', 'supervisor', 'administrator'];
// Note: there's no CAN_VIEW_AUDIT role gate here anymore — the case roadmap
// (loadAuditTrail) is loaded for every role, and the backend itself decides
// what to send back (full / redacted / empty). See audit_event_controller.py.

// Case state machine — mirrored exactly from Service/case_service.py's
// ALLOWED_TRANSITIONS, so the "New Status" dropdown can disable moves the
// backend would reject rather than letting the officer discover that on submit.
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  RECEIVED: ['VALIDATING', 'REJECTED'],
  VALIDATING: ['CLASSIFIED', 'NEEDS_INFORMATION', 'REJECTED'],
  CLASSIFIED: ['ROUTED', 'MANUAL_REVIEW'],
  ROUTED: ['ASSIGNED', 'ESCALATED'],
  ASSIGNED: ['IN_PROGRESS', 'ESCALATED'],
  IN_PROGRESS: ['RESOLVED', 'ON_HOLD', 'ESCALATED'],
  RESOLVED: ['CLOSED', 'REOPENED'],
  CLOSED: ['REOPENED'],
  REJECTED: ['MANUAL_REVIEW'],
  MANUAL_REVIEW: ['CLASSIFIED', 'ROUTED', 'REJECTED'],
  NEEDS_INFORMATION: ['VALIDATING', 'REJECTED'],
  ON_HOLD: ['IN_PROGRESS', 'ESCALATED', 'CLOSED'],
  ESCALATED: ['ASSIGNED', 'IN_PROGRESS', 'RESOLVED'],
  REOPENED: ['VALIDATING', 'ASSIGNED', 'IN_PROGRESS'],
};

const FINAL_STATUSES = ['RESOLVED', 'CLOSED', 'REJECTED'];

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

const CATEGORY_OPTIONS = [
  { label: 'Water & Sanitation',     value: 'water_sanitation' },
  { label: 'Roads & Infrastructure', value: 'roads_infrastructure' },
  { label: 'Electricity / Power',    value: 'electricity_power' },
  { label: 'Waste Management',       value: 'waste_management' },
  { label: 'Health Services',        value: 'health_services' },
  { label: 'Security & Safety',      value: 'security_safety' },
  { label: 'Other',                  value: 'other' },
];

const URGENCY_OPTIONS = [
  { label: 'Low',      value: 'low' },
  { label: 'Medium',   value: 'medium' },
  { label: 'High',     value: 'high' },
  { label: 'Critical', value: 'critical' },
];

@Component({
  selector: 'app-case-detail',
  imports: [SharedModules],
  templateUrl: './case-detail.component.html',
  styleUrl: './case-detail.component.scss'
})
export class CaseDetailComponent implements OnInit, OnDestroy {
  private routeSubscription!: Subscription;
  private caseSubscription!: Subscription;
  private auditSubscription!: Subscription;
  private queueSubscription!: Subscription;
  private actionSubscription!: Subscription;

  caseId: string = '';
  caseItem: CaseDTO | null = null;
  loading = true;
  notFound = false;

  auditEvents: AuditEventDTO[] = [];
  auditLoading = false;

  queues: QueueDTO[] = [];
  queueOptions: { label: string; value: number }[] = [];
  loadingQueues = false;

  units: OrganisationUnitDTO[] = [];

  actionLoading = false;

  // ── Modal visibility ───────────────────────────────────────────────────────
  showClassifyDialog = false;
  showRouteDialog = false;
  showStatusDialog = false;

  categoryOptions = CATEGORY_OPTIONS;
  urgencyOptions = URGENCY_OPTIONS;
  // Every status is always listed, so illegal moves are visible-but-disabled
  // rather than hidden — the officer can see the constraint, not just hit a
  // wall on submit. Recomputed whenever caseItem changes (resetActionForms).
  statusOptions: { label: string; value: string; disabled: boolean }[] = [];

  actionClassification: ClassificationCorrectionPayload & { subcategory?: string } = {
    category: '',
    urgency: 'medium',
    subcategory: '',
  };
  actionRouteQueueId: number | null = null;
  actionStatusUpdate: StatusUpdatePayload = { status: '', reason: '' };

  districtName: string | null = null;

  private currentUserRole = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private caseService: CaseService,
    private queueService: QueueService,
    private unitService: OrganisationUnitService,
    private districtService: DistrictService,
    private auditEventService: AuditEventService,
    private loadingService: LoadingService,
    private authService: AuthService,
    private messageService: MessageService
  ) { }

  ngOnInit(): void {
    this.currentUserRole = this.authService.getCurrentUser()?.role || '';
    // Queues/units are loaded unconditionally — needed to resolve the case's
    // organisation unit for display, not just for the routing dropdown.
    this.loadQueues();
    this.loadUnits();

    this.routeSubscription = this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.caseId = id;
        this.loadCase();
      }
    });
  }

  loadDistrictName(districtId: number): void {
    this.districtService.listDistricts().subscribe({
      next: (res) => {
        const match = res.districts?.find(d => d.id === districtId);
        this.districtName = match ? `${match.name} — ${match.province}` : `District #${districtId}`;
      },
      error: () => { this.districtName = `District #${districtId}`; }
    });
  }

  ngOnDestroy(): void {
    this.routeSubscription?.unsubscribe();
    this.caseSubscription?.unsubscribe();
    this.auditSubscription?.unsubscribe();
    this.queueSubscription?.unsubscribe();
    this.actionSubscription?.unsubscribe();
  }

  // ── Data loading ───────────────────────────────────────────────────────────

  loadCase(): void {
    this.loading = true;
    this.notFound = false;
    this.caseSubscription = this.caseService.getCaseById(this.caseId).subscribe({
      next: (response) => {
        this.loading = false;
        if (response.success && response.case) {
          this.caseItem = response.case;
          this.districtName = null;
          if (response.case.district_id != null) {
            this.loadDistrictName(response.case.district_id);
          }
          this.resetActionForms(response.case);
          this.loadAuditTrail();
        } else {
          this.notFound = true;
        }
      },
      error: () => {
        this.loading = false;
        this.notFound = true;
      }
    });
  }

  loadAuditTrail(): void {
    if (!this.caseItem) {
      return;
    }
    // Loaded for every role now — the backend itself decides what comes
    // back: full detail for auditor/administrator, a redacted (no actor)
    // progress trail for the citizen who owns this case, or an empty list
    // for anyone else. No role gate needed here; see
    // Controller/audit_event_controller.py.
    this.auditLoading = true;
    this.auditSubscription = this.auditEventService.listForObject('case', this.caseItem.id).subscribe({
      next: (response) => {
        this.auditLoading = false;
        this.auditEvents = response.events || [];
      },
      error: () => {
        this.auditLoading = false;
        this.auditEvents = [];
      }
    });
  }

  loadQueues(): void {
    this.loadingQueues = true;
    // All queues (not just active) so a case already routed to a since-
    // deactivated queue can still be resolved for display; the routing
    // dropdown itself is filtered to active queues below.
    this.queueSubscription = this.queueService.listQueues().subscribe({
      next: (res) => {
        this.loadingQueues = false;
        if (res.success && res.queues) {
          this.queues = res.queues;
          this.queueOptions = res.queues
            .filter(q => q.is_active)
            .map(q => ({ label: `#${q.id} — ${q.name}`, value: q.id }));
        }
      },
      error: () => { this.loadingQueues = false; }
    });
  }

  loadUnits(): void {
    this.unitService.listUnits().subscribe({
      next: (res) => {
        if (res.success && res.units) {
          this.units = res.units;
        }
      }
    });
  }

  private resetActionForms(caseItem: CaseDTO): void {
    this.actionClassification = {
      category: caseItem.category,
      urgency: (caseItem.urgency?.toLowerCase() as any) || 'medium',
      subcategory: caseItem.subcategory || '',
    };
    this.actionRouteQueueId = null;
    this.actionStatusUpdate = { status: '', reason: '' };
    this.recomputeStatusOptions(caseItem.status);
  }

  private recomputeStatusOptions(currentStatus: string): void {
    const allowedNext = ALLOWED_TRANSITIONS[currentStatus] || [];
    this.statusOptions = Object.keys(ALLOWED_TRANSITIONS).map(status => ({
      label: this.humanize(status),
      value: status,
      disabled: !allowedNext.includes(status),
    }));
  }

  // ── Role guards ────────────────────────────────────────────────────────────

  canCorrectClassification(): boolean {
    return CAN_CORRECT_CLASSIFICATION_ROLES.includes(this.currentUserRole);
  }

  canRouteCase(): boolean {
    return CAN_ROUTE_CASES_ROLES.includes(this.currentUserRole);
  }

  canUpdateStatus(): boolean {
    return CAN_UPDATE_STATUS_ROLES.includes(this.currentUserRole);
  }

  hasOfficerActions(): boolean {
    return this.canCorrectClassification() || this.canRouteCase() || this.canUpdateStatus();
  }

  // ── Dialog open/close ──────────────────────────────────────────────────────

  openClassifyDialog(): void  { this.showClassifyDialog = true; }
  closeClassifyDialog(): void { this.showClassifyDialog = false; }

  openRouteDialog(): void  { this.showRouteDialog = true; }
  closeRouteDialog(): void { this.showRouteDialog = false; }

  openStatusDialog(): void  { this.showStatusDialog = true; }
  closeStatusDialog(): void { this.showStatusDialog = false; }

  // ── Officer actions ────────────────────────────────────────────────────────

  submitClassificationCorrection(): void {
    if (!this.caseItem || !this.actionClassification.category) return;

    const payload: ClassificationCorrectionPayload = {
      category: this.actionClassification.category,
      urgency: this.actionClassification.urgency,
      subcategory: this.actionClassification.subcategory || null,
    };

    this.actionLoading = true;
    this.actionSubscription = this.caseService
      .correctClassification(this.caseItem.id, payload)
      .subscribe({
        next: (res) => {
          this.actionLoading = false;
          if (res.success && res.case) {
            this.caseItem = res.case;
            this.closeClassifyDialog();
            this.messageService.add({ severity: 'success', summary: 'Classification Updated', detail: `Case ${res.case.reference_number} re-classified.` });
            this.loadAuditTrail();
          } else {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Classification correction failed.' });
          }
        },
        error: () => {
          this.actionLoading = false;
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
        }
      });
  }

  submitRouteCase(): void {
    if (!this.caseItem) return;

    const payload: RouteCasePayload = { queue_id: this.actionRouteQueueId || null };

    this.actionLoading = true;
    this.actionSubscription = this.caseService
      .routeCase(this.caseItem.id, payload)
      .subscribe({
        next: (res) => {
          this.actionLoading = false;
          if (res.success && res.case) {
            this.caseItem = res.case;
            this.closeRouteDialog();
            this.messageService.add({ severity: 'success', summary: 'Case Routed', detail: `Case ${res.case.reference_number} routed successfully.` });
            this.loadAuditTrail();
          } else {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Routing failed.' });
          }
        },
        error: () => {
          this.actionLoading = false;
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
        }
      });
  }

  submitStatusUpdate(): void {
    if (!this.caseItem || !this.actionStatusUpdate.status || this.actionStatusUpdate.reason.length < 3) return;

    this.actionLoading = true;
    this.actionSubscription = this.caseService
      .updateCaseStatus(this.caseItem.id, this.actionStatusUpdate)
      .subscribe({
        next: (res) => {
          this.actionLoading = false;
          if (res.success && res.case) {
            this.caseItem = res.case;
            this.closeStatusDialog();
            this.messageService.add({ severity: 'success', summary: 'Status Updated', detail: `Case ${res.case.reference_number} is now ${this.humanize(res.case.status)}.` });
            this.actionStatusUpdate = { status: '', reason: '' };
            this.recomputeStatusOptions(res.case.status);
            this.loadAuditTrail();
          } else {
            this.messageService.add({ severity: 'error', summary: 'Error', detail: res.message || 'Status update failed.' });
          }
        },
        error: () => {
          this.actionLoading = false;
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Could not reach the server.' });
        }
      });
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  goBack(): void {
    this.router.navigate(['/cases']);
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  /** The organisation unit responsible for the case's queue — shown instead
   * of the (often long) queue name, which doesn't fit well in a summary tile. */
  organisationUnitName(queueId: number | null | undefined): string {
    if (queueId == null) return 'Not yet routed';
    const queue = this.queues.find(q => q.id === queueId);
    if (!queue) return `Queue #${queueId}`;
    const unit = this.units.find(u => u.id === queue.unit_id);
    return unit ? unit.name : `Unit #${queue.unit_id}`;
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

  /** "case.status_changed" -> "Case Status Changed" */
  humanizeAction(action: string): string {
    return this.humanize(action.replace(/\./g, '_'));
  }

  /**
   * Who/what performed a roadmap event — a real name for a human actor
   * (resolved server-side), an "AI/automation" label for a system step
   * (actor_channel set, no actor_user_id), or null when the viewer's role
   * doesn't get actor detail at all (backend redacts it for citizens).
   */
  describeActor(event: AuditEventDTO): string | null {
    if (event.actor_name) {
      return event.actor_name;
    }
    if (event.actor_channel) {
      // humanize() title-cases word-by-word, which turns "ai_classifier"
      // into "Ai Classifier" — fix the acronym up after the fact rather
      // than special-casing it in the generic humanize().
      return this.humanize(event.actor_channel).replace(/\bAi\b/g, 'AI');
    }
    return null;
  }

  isAutomatedActor(event: AuditEventDTO): boolean {
    return !event.actor_name && !!event.actor_channel;
  }

  /** What actually changed, in one line — from event.detail (shape varies by action). */
  describeEventChange(event: AuditEventDTO): string {
    const d = event.detail;
    if (!d) return '';

    if (event.action === 'case.status_changed' && d['from'] && d['to']) {
      return `${this.humanize(d['from'])} → ${this.humanize(d['to'])}`;
    }
    if ((event.action === 'case.classified' || event.action === 'case.classification_corrected') && d['category']) {
      const parts = [this.humanize(d['category'])];
      if (d['subcategory']) parts.push(this.humanize(d['subcategory']));
      if (d['urgency']) parts.push(`${this.humanize(d['urgency'])} urgency`);
      return parts.join(' · ');
    }
    if (event.action === 'case.created' && d['reference_number']) {
      return d['reference_number'];
    }
    return '';
  }

  /** Secondary detail line — currently just the transition reason, if any. */
  describeEventReason(event: AuditEventDTO): string {
    return event.detail?.['reason'] || '';
  }

  // ── SLA countdown ──────────────────────────────────────────────────────────
  // A case that has reached a final state is no longer "on the clock", so the
  // countdown/overdue styling is suppressed once RESOLVED/CLOSED/REJECTED.

  private isCaseFinal(status: string): boolean {
    return FINAL_STATUSES.includes(status);
  }

  private slaDaysRemaining(): number | null {
    if (!this.caseItem?.sla_deadline || this.isCaseFinal(this.caseItem.status)) return null;
    const diffMs = new Date(this.caseItem.sla_deadline).getTime() - Date.now();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  }

  isSlaOverdue(): boolean {
    const days = this.slaDaysRemaining();
    return days != null && days < 0;
  }

  isSlaUrgent(): boolean {
    const days = this.slaDaysRemaining();
    return days != null && days < 3;
  }

  slaDaysText(): string {
    const days = this.slaDaysRemaining();
    if (days == null) return '';
    if (days < 0) return `Overdue by ${Math.abs(days)} day${Math.abs(days) === 1 ? '' : 's'}`;
    if (days === 0) return 'Due today';
    return `${days} day${days === 1 ? '' : 's'} left`;
  }
}
