import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { IntakeService } from '../../../services/intake.service';
import { DistrictService } from '../../../services/district.service';
import { AuthService } from '../../../services/auth.service';
import { LoadingService } from '../../../services/loading.service';
import { MessageService } from 'primeng/api';
import { DistrictDTO } from '../../../models/district.interface';
import { CaseDTO } from '../../../models/case.interface';
import { SubmissionCreatePayload } from '../../../models/intake.interface';
import { COUNTRY_CODES, CountryCode } from '../public-submit/public-submit.component';

const CAN_CREATE_SUBMISSIONS_ROLES = ['citizen', 'intake_officer', 'dispatcher'];

const CATEGORY_OPTIONS = [
  { label: 'Water & Sanitation',   value: 'water_sanitation' },
  { label: 'Roads & Infrastructure', value: 'roads_infrastructure' },
  { label: 'Electricity / Power',  value: 'electricity_power' },
  { label: 'Waste Management',     value: 'waste_management' },
  { label: 'Health Services',      value: 'health_services' },
  { label: 'Security & Safety',    value: 'security_safety' },
  { label: 'Other',                value: 'other' },
];

const CONSENT_OPTIONS = [
  { label: 'Granted — I consent to my data being used for service improvement', value: 'granted' },
  { label: 'Not Required',                                                       value: 'not_required' },
  { label: 'Declined',                                                           value: 'declined' },
];

@Component({
  selector: 'app-report-case',
  imports: [SharedModules],
  templateUrl: './report-case.component.html',
  styleUrl: './report-case.component.scss',
})
export class ReportCaseComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  // Permission
  canSubmit = false;
  userRole = '';

  // Form fields
  description = '';
  locationText = '';
  contactEmail = '';
  contactPhone = '';
  selectedCountry: CountryCode = COUNTRY_CODES[0];  // Zimbabwe default
  selectedDistrictId: number | null = null;
  consentStatus: 'granted' | 'declined' | 'not_required' = 'not_required';

  // Reference data
  categoryOptions = CATEGORY_OPTIONS;
  consentOptions = CONSENT_OPTIONS;
  countryOptions = COUNTRY_CODES;
  districts: DistrictDTO[] = [];
  districtOptions: { label: string; value: number }[] = [];
  loadingDistricts = false;

  // Submission state
  submitting = false;
  submitted = false;
  createdCase: CaseDTO | null = null;
  errorMessage = '';

  readonly MAX_DESC = 1000;

  constructor(
    private intakeService: IntakeService,
    private districtService: DistrictService,
    private authService: AuthService,
    private loadingService: LoadingService,
    private messageService: MessageService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    this.userRole = user?.role || '';
    this.canSubmit = CAN_CREATE_SUBMISSIONS_ROLES.includes(this.userRole);
    if (this.canSubmit) {
      this.loadDistricts();
    }
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  loadDistricts(): void {
    this.loadingDistricts = true;
    const sub = this.districtService.listDistricts().subscribe({
      next: (res) => {
        this.loadingDistricts = false;
        if (res.success && res.districts) {
          this.districts = res.districts;
          this.districtOptions = res.districts.map(d => ({
            label: `${d.name} — ${d.province}`,
            value: d.id,
          }));
        }
      },
      error: () => { this.loadingDistricts = false; }
    });
    this.subs.push(sub);
  }

  get descriptionLength(): number {
    return this.description.length;
  }

  get isEmailValid(): boolean {
    if (!this.contactEmail.trim()) return true;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.contactEmail.trim());
  }

  get isFormValid(): boolean {
    return this.description.trim().length >= 5 && this.description.length <= this.MAX_DESC && this.isEmailValid;
  }

  normalizePhone(raw: string): string {
    if (!raw || !raw.trim()) return '';
    let digits = raw.replace(/[\s\-\(\)\.]/g, '');
    if (digits.startsWith('+')) return '+' + digits.slice(1).replace(/\D/g, '');
    if (digits.startsWith('00')) return '+' + digits.slice(2).replace(/\D/g, '');
    const dialCode = this.selectedCountry.dialCode;
    const rawDial  = dialCode.slice(1);
    digits = digits.replace(/\D/g, '');
    if (digits.startsWith('0')) return dialCode + digits.slice(1);
    if (digits.startsWith(rawDial)) return '+' + digits;
    return dialCode + digits;
  }

  get phonePreviewed(): string {
    return this.contactPhone ? this.normalizePhone(this.contactPhone) : '';
  }

  submit(): void {
    if (!this.isFormValid || this.submitting) return;

    const normalizedPhone = this.normalizePhone(this.contactPhone);

    const payload: SubmissionCreatePayload = {
      channel: 'web',
      received_at: new Date().toISOString(),
      service_description: this.description.trim(),
      location_text: this.locationText.trim() || null,
      consent_status: this.consentStatus,
      district_id: this.selectedDistrictId || null,
      contact_email: this.contactEmail.trim() || null,
      contact_phone: normalizedPhone || null,
    };

    this.submitting = true;
    this.errorMessage = '';
    this.loadingService.setLoadingState(true);

    const sub = this.intakeService.createSubmission(payload).subscribe({
      next: (res) => {
        this.submitting = false;
        this.loadingService.setLoadingState(false);
        if (res.success && res.case) {
          this.createdCase = res.case;
          this.submitted = true;
          this.messageService.add({
            severity: 'success',
            summary: 'Case Created',
            detail: `Reference: ${res.case.reference_number}`,
          });
        } else {
          this.errorMessage = res.message || 'Submission failed. Please try again.';
        }
      },
      error: () => {
        this.submitting = false;
        this.loadingService.setLoadingState(false);
        this.errorMessage = 'Could not reach the server. Please try again.';
      },
    });
    this.subs.push(sub);
  }

  resetForm(): void {
    this.description = '';
    this.locationText = '';
    this.contactEmail = '';
    this.contactPhone = '';
    this.selectedCountry = COUNTRY_CODES[0];
    this.selectedDistrictId = null;
    this.consentStatus = 'not_required';
    this.submitted = false;
    this.createdCase = null;
    this.errorMessage = '';
  }

  goToCases(): void {
    this.router.navigate(['/cases']);
  }
}
