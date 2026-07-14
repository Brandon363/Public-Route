import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { OrganisationUnitService } from '../../../services/organisation-unit.service';
import { DistrictService } from '../../../services/district.service';
import { QueueService } from '../../../services/queue.service';
import { OrganisationUnitDTO } from '../../../models/organisation-unit.interface';
import { DistrictDTO } from '../../../models/district.interface';
import { QueueDTO } from '../../../models/queue.interface';

const CATEGORY_LABELS: Record<string, string> = {
  water_sanitation: 'Water & Sanitation',
  roads_infrastructure: 'Roads & Infrastructure',
  electricity_power: 'Electricity / Power',
  waste_management: 'Waste Management',
  health_services: 'Health Services',
  security_safety: 'Security & Safety',
  other: 'Other',
};

@Component({
  selector: 'app-organisation-unit-detail',
  imports: [SharedModules],
  templateUrl: './organisation-unit-detail.component.html',
  styleUrl: './organisation-unit-detail.component.scss'
})
export class OrganisationUnitDetailComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  unitId!: number;
  unit: OrganisationUnitDTO | null = null;
  loading = true;
  notFound = false;

  districts: DistrictDTO[] = [];
  jurisdictionDistricts: DistrictDTO[] = [];
  coversAllDistricts = false;

  queues: QueueDTO[] = [];
  loadingQueues = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private unitService: OrganisationUnitService,
    private districtService: DistrictService,
    private queueService: QueueService,
  ) {}

  ngOnInit(): void {
    const sub = this.route.paramMap.subscribe(params => {
      const id = Number(params.get('id'));
      if (id) {
        this.unitId = id;
        this.loadUnit();
      }
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  loadUnit(): void {
    this.loading = true;
    this.notFound = false;
    const sub = this.unitService.getUnit(this.unitId).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.unit) {
          this.unit = res.unit;
          this.coversAllDistricts = !this.unit.jurisdiction || this.unit.jurisdiction.length === 0;
          this.loadDistricts();
          this.loadQueues();
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

  loadDistricts(): void {
    const sub = this.districtService.listDistricts().subscribe({
      next: (res) => {
        if (res.success && res.districts) {
          this.districts = res.districts;
          this.jurisdictionDistricts = this.coversAllDistricts
            ? []
            : this.districts.filter(d => this.unit!.jurisdiction.includes(d.id));
        }
      }
    });
    this.subs.push(sub);
  }

  loadQueues(): void {
    this.loadingQueues = true;
    const sub = this.queueService.listQueues(false, this.unitId).subscribe({
      next: (res) => {
        this.loadingQueues = false;
        if (res.success && res.queues) {
          this.queues = res.queues;
        }
      },
      error: () => { this.loadingQueues = false; }
    });
    this.subs.push(sub);
  }

  goBack(): void {
    this.router.navigate(['/organisation-units']);
  }

  humanizeCategory(value: string): string {
    return CATEGORY_LABELS[value] || value;
  }
}
