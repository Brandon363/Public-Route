import { Component, OnDestroy, OnInit, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { catchError, of } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { IntakeService } from '../../../services/intake.service';
import { DistrictService } from '../../../services/district.service';
import { DistrictDTO } from '../../../models/district.interface';
import { CaseDTO } from '../../../models/case.interface';
import { SubmissionCreatePayload } from '../../../models/intake.interface';

// ── Country codes ──────────────────────────────────────────────────────────────
export interface CountryCode {
  label: string;
  flag: string;
  dialCode: string;   // e.g. +263
  value: string;      // same as dialCode — used by p-select
}

export const COUNTRY_CODES: CountryCode[] = [
  { flag: '🇿🇼', label: '🇿🇼  Zimbabwe',        dialCode: '+263', value: '+263' },
  { flag: '🇿🇦', label: '🇿🇦  South Africa',    dialCode: '+27',  value: '+27'  },
  { flag: '🇿🇲', label: '🇿🇲  Zambia',           dialCode: '+260', value: '+260' },
  { flag: '🇧🇼', label: '🇧🇼  Botswana',         dialCode: '+267', value: '+267' },
  { flag: '🇲🇿', label: '🇲🇿  Mozambique',       dialCode: '+258', value: '+258' },
  { flag: '🇳🇦', label: '🇳🇦  Namibia',          dialCode: '+264', value: '+264' },
  { flag: '🇹🇿', label: '🇹🇿  Tanzania',         dialCode: '+255', value: '+255' },
  { flag: '🇰🇪', label: '🇰🇪  Kenya',            dialCode: '+254', value: '+254' },
  { flag: '🇺🇬', label: '🇺🇬  Uganda',           dialCode: '+256', value: '+256' },
  { flag: '🇷🇼', label: '🇷🇼  Rwanda',           dialCode: '+250', value: '+250' },
  { flag: '🇪🇹', label: '🇪🇹  Ethiopia',         dialCode: '+251', value: '+251' },
  { flag: '🇳🇬', label: '🇳🇬  Nigeria',          dialCode: '+234', value: '+234' },
  { flag: '🇬🇭', label: '🇬🇭  Ghana',            dialCode: '+233', value: '+233' },
  { flag: '🇬🇧', label: '🇬🇧  United Kingdom',   dialCode: '+44',  value: '+44'  },
  { flag: '🇺🇸', label: '🇺🇸  United States',    dialCode: '+1',   value: '+1'   },
  { flag: '🇮🇳', label: '🇮🇳  India',            dialCode: '+91',  value: '+91'  },
  { flag: '🇨🇳', label: '🇨🇳  China',            dialCode: '+86',  value: '+86'  },
];

const CONSENT_OPTIONS = [
  { label: 'Granted — I consent to my data being used for service improvement', value: 'granted' },
  { label: 'Not Required',                                                       value: 'not_required' },
  { label: 'Declined',                                                           value: 'declined' },
];

const STEPS = [
  { n: 1, title: 'AI Classification',  desc: 'The AI reads your description and assigns a category, subcategory, and urgency level.' },
  { n: 2, title: 'Automatic Routing',  desc: 'The case is routed to the most appropriate queue for your area.' },
  { n: 3, title: 'Officer Review',     desc: 'A dispatcher or intake officer reviews and can correct the classification if needed.' },
  { n: 4, title: 'Field Assignment',   desc: 'A field team is assigned and the case moves to In Progress.' },
];

@Component({
  selector: 'app-public-submit',
  standalone: true,
  imports: [SharedModules],
  templateUrl: './public-submit.component.html',
  styleUrl: './public-submit.component.scss',
})
export class PublicSubmitComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  // ── Form fields ──
  description   = '';
  locationText  = '';
  contactEmail  = '';
  contactPhone  = '';
  selectedCountry: CountryCode = COUNTRY_CODES[0]; // Zimbabwe default
  consentStatus: 'granted' | 'declined' | 'not_required' = 'not_required';

  // ── Reference data ──
  countryOptions = COUNTRY_CODES;
  consentOptions = CONSENT_OPTIONS;
  steps = STEPS;
  districts: DistrictDTO[] = [];
  districtOptions: { label: string; value: number }[] = [];
  loadingDistricts = false;
  selectedDistrictId: number | null = null;

  // ── State ──
  submitting   = false;
  submitted    = false;
  createdCase: CaseDTO | null = null;
  errorMessage = '';
  currentStep: 1 | 2 | 3 = 1;

  // ── Voice Assistant ──
  isRecording = false;
  voiceLoading = false;
  recordingDuration = 0;
  private durationInterval: any = null;
  private mediaRecorder: any = null;
  private audioChunks: Blob[] = [];
  voiceResponseText = '';
  voiceActive = false; // toggles between typing mode and voice assistant mode
  modeOptions = [
    { label: 'Type Form', value: false, icon: 'pi pi-pencil' },
    { label: 'Speak to AI (Beta)', value: true, icon: 'pi pi-microphone' }
  ];

  readonly MAX_DESC = 1000;

  constructor(
    private intakeService: IntakeService,
    private districtService: DistrictService,
    private router: Router,
    private ngZone: NgZone,
  ) {}

  ngOnInit(): void {
    this.loadDistricts();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
    if (this.durationInterval) {
      clearInterval(this.durationInterval);
      this.durationInterval = null;
    }
  }

  // ── Districts ────────────────────────────────────────────────────────────────
  loadDistricts(): void {
    this.loadingDistricts = true;
    const sub = this.districtService.listDistricts().pipe(
      catchError(() => of({ success: false, districts: null } as any))
    ).subscribe(res => {
      this.loadingDistricts = false;
      if (res.success && res.districts) {
        this.districts = res.districts;
        this.districtOptions = res.districts.map((d: DistrictDTO) => ({
          label: `${d.name} — ${d.province}`,
          value: d.id,
        }));
      }
    });
    this.subs.push(sub);
  }

  // ── Phone normalisation ──────────────────────────────────────────────────────
  /**
   * Standardises a raw phone input to E.164 format using the selected country's
   * dial code.
   *   "0771234567"   + +263  →  "+263771234567"
   *   "00263 77 123" + +263  →  "+26377123…"
   *   "+44 7700 900" + any   →  "+447700900…"
   *   "263771234567" + +263  →  "+263771234567"
   */
  normalizePhone(raw: string): string {
    if (!raw || !raw.trim()) return '';
    // Strip spaces, hyphens, parentheses
    let digits = raw.replace(/[\s\-\(\)\.]/g, '');
    // Already has a + prefix — strip non-digits after the +
    if (digits.startsWith('+')) {
      return '+' + digits.slice(1).replace(/\D/g, '');
    }
    // International 00 prefix
    if (digits.startsWith('00')) {
      return '+' + digits.slice(2).replace(/\D/g, '');
    }
    const dialCode = this.selectedCountry.dialCode; // e.g. "+263"
    const rawDial  = dialCode.slice(1);             // e.g. "263"
    // Strip remaining non-digits
    digits = digits.replace(/\D/g, '');
    // Leading 0 → replace with dial code
    if (digits.startsWith('0')) {
      return dialCode + digits.slice(1);
    }
    // Already starts with dial code digits → prepend +
    if (digits.startsWith(rawDial)) {
      return '+' + digits;
    }
    // Otherwise prepend full dial code
    return dialCode + digits;
  }

  get phonePreviewed(): string {
    return this.contactPhone ? this.normalizePhone(this.contactPhone) : '';
  }

  // ── Form validation ──────────────────────────────────────────────────────────
  get descriptionLength(): number { return this.description.length; }

  get isEmailValid(): boolean {
    if (!this.contactEmail.trim()) return true; // optional
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.contactEmail.trim());
  }

  get isFormValid(): boolean {
    return (
      this.description.trim().length >= 5 &&
      this.description.length <= this.MAX_DESC &&
      this.isEmailValid
    );
  }

  get isStep1Valid(): boolean {
    return this.description.trim().length >= 5 && this.description.length <= this.MAX_DESC;
  }

  // ── Step navigation ──────────────────────────────────────────────────────────
  nextStep(): void {
    if (this.currentStep === 1 && this.isStep1Valid) this.currentStep = 2;
    else if (this.currentStep === 2)                 this.currentStep = 3;
  }

  prevStep(): void {
    if (this.currentStep === 2) this.currentStep = 1;
    else if (this.currentStep === 3) this.currentStep = 2;
  }

  // ── Submit ───────────────────────────────────────────────────────────────────
  submit(): void {
    if (!this.isFormValid || this.submitting) return;

    const normalizedPhone = this.normalizePhone(this.contactPhone);

    const payload: SubmissionCreatePayload = {
      channel:             'web',
      received_at:         new Date().toISOString(),
      service_description: this.description.trim(),
      location_text:       this.locationText.trim() || null,
      consent_status:      this.consentStatus,
      district_id:         this.selectedDistrictId || null,
      contact_email:       this.contactEmail.trim() || null,
      contact_phone:       normalizedPhone || null,
    };

    this.submitting    = true;
    this.errorMessage  = '';

    const sub = this.intakeService.createSubmission(payload).subscribe({
      next: (res) => {
        this.submitting = false;
        if (res.success && res.case) {
          this.createdCase = res.case;
          this.submitted   = true;
        } else {
          this.errorMessage = res.message || 'Submission failed. Please try again.';
        }
      },
      error: () => {
        this.submitting   = false;
        this.errorMessage = 'Could not reach the server. Please try again.';
      },
    });
    this.subs.push(sub);
  }

  // ── Reset / nav ──────────────────────────────────────────────────────────────
  resetForm(): void {
    this.description        = '';
    this.locationText       = '';
    this.contactEmail       = '';
    this.contactPhone       = '';
    this.selectedCountry    = COUNTRY_CODES[0];
    this.selectedDistrictId = null;
    this.consentStatus      = 'not_required';
    this.submitted          = false;
    this.createdCase        = null;
    this.errorMessage       = '';
    this.currentStep        = 1;
  }

  goToLogin(): void {
    this.router.navigate(['/login']);
  }

  // ── Voice Assistant Methods ──────────────────────────────────────────────────
  toggleVoiceMode(): void {
    this.voiceActive = !this.voiceActive;
    this.onModeChange();
  }

  onModeChange(): void {
    this.voiceResponseText = '';
    if (!this.voiceActive) {
      this.stopRecording();
    }
  }

  async startRecording() {
    if (this.voiceLoading) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.ngZone.run(() => {
        this.audioChunks = [];
        const options = { mimeType: 'audio/webm' };
        let recorder: any;
        try {
          recorder = new MediaRecorder(stream, options);
        } catch (e) {
          recorder = new MediaRecorder(stream);
        }

        this.mediaRecorder = recorder;
        this.mediaRecorder.ondataavailable = (event: any) => {
          if (event.data && event.data.size > 0) {
            this.audioChunks.push(event.data);
          }
        };

        this.mediaRecorder.onstop = () => {
          this.ngZone.run(() => {
            stream.getTracks().forEach(track => track.stop());

            if (this.audioChunks.length > 0) {
              const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
              const audioBlob = new Blob(this.audioChunks, { type: mimeType });
              const extension = mimeType.includes('wav') ? 'wav' : (mimeType.includes('webm') ? 'webm' : 'ogg');
              const audioFile = new File([audioBlob], `voice_input.${extension}`, { type: mimeType });
              this.sendVoiceMessage(audioFile);
            }
          });
        };

        this.mediaRecorder.start();
        this.isRecording = true;
        this.recordingDuration = 0;
        if (this.durationInterval) {
          clearInterval(this.durationInterval);
        }
        this.durationInterval = setInterval(() => {
          this.ngZone.run(() => {
            this.recordingDuration++;
          });
        }, 1000);
      });
    } catch (err) {
      console.error('Error opening microphone:', err);
      this.errorMessage = 'Could not access microphone. Please check permissions.';
    }
  }

  stopRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      if (this.durationInterval) {
        clearInterval(this.durationInterval);
        this.durationInterval = null;
      }
    }
  }

  cancelRecording(): void {
    if (this.mediaRecorder) {
      this.audioChunks = [];
      this.mediaRecorder.stop();
      this.isRecording = false;
      if (this.durationInterval) {
        clearInterval(this.durationInterval);
        this.durationInterval = null;
      }
    }
  }

  sendVoiceMessage(audioFile: File): void {
    this.voiceLoading = true;
    this.errorMessage = '';
    this.voiceResponseText = 'Processing your voice message...';

    const sub = this.intakeService
      .sendVoiceMessage(audioFile, this.description, this.locationText)
      .subscribe({
        next: (res: any) => {
          this.voiceLoading = false;
          if (res.success && res.data) {
            const data = res.data;
            this.description = data.extracted_issue || this.description;
            this.locationText = data.extracted_location || this.locationText;
            this.voiceResponseText = data.response_text || '';

            // Play the response TTS audio if returned
            if (data.audio_base64) {
              try {
                const audio = new Audio('data:audio/wav;base64,' + data.audio_base64);
                audio.play();
              } catch (playErr) {
                console.error('Failed to play response audio:', playErr);
              }
            }

            // Auto-advance logic based on what was parsed
            if (data.is_complete) {
              this.currentStep = 3;
            } else if (this.description.trim().length >= 5 && this.currentStep === 1) {
              this.currentStep = 2;
            }
          } else {
            this.voiceResponseText = 'Sorry, I failed to process that. Please try again.';
            this.errorMessage = res.message || 'Voice processing failed.';
          }
        },
        error: (err) => {
          this.voiceLoading = false;
          this.voiceResponseText = 'Failed to reach the voice assistant.';
          this.errorMessage = 'Network error during voice transmission.';
        }
      });
    this.subs.push(sub);
  }

  formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
}
