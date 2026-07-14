import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { DistrictService } from '../../../services/district.service';
import { OrganisationUnitService } from '../../../services/organisation-unit.service';
import { ResourceTeamService } from '../../../services/resource-team.service';
import { QueueService } from '../../../services/queue.service';
import { DistrictDTO } from '../../../models/district.interface';
import { OrganisationUnitDTO } from '../../../models/organisation-unit.interface';
import { ResourceTeamDTO } from '../../../models/resource-team.interface';
import { QueueDTO } from '../../../models/queue.interface';

const SETTLEMENT_LABELS: Record<string, string> = {
  urban: 'Urban',
  peri_urban: 'Peri-Urban',
  rural: 'Rural',
};

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
  selector: 'app-district-detail',
  imports: [SharedModules],
  templateUrl: './district-detail.component.html',
  styleUrl: './district-detail.component.scss'
})
export class DistrictDetailComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  districtId!: number;
  district: DistrictDTO | null = null;
  loading = true;
  notFound = false;

  units: OrganisationUnitDTO[] = [];
  teams: ResourceTeamDTO[] = [];
  queuesByUnit: Record<number, QueueDTO[]> = {};
  loadingRelated = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private districtService: DistrictService,
    private unitService: OrganisationUnitService,
    private teamService: ResourceTeamService,
    private queueService: QueueService,
  ) {}

  ngOnInit(): void {
    const sub = this.route.paramMap.subscribe(params => {
      const id = Number(params.get('id'));
      if (id) {
        this.districtId = id;
        this.loadDistrict();
      }
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  loadDistrict(): void {
    this.loading = true;
    this.notFound = false;
    const sub = this.districtService.getDistrict(this.districtId).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.district) {
          this.district = res.district;
          this.loadRelated();
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

  loadRelated(): void {
    this.loadingRelated = true;

    const unitsSub = this.unitService.listUnits().subscribe({
      next: (res) => {
        if (res.success && res.units) {
          // A unit with an empty jurisdiction covers every district (see
          // Service/routing_service.py) — otherwise it must list this
          // district's ID explicitly.
          this.units = res.units.filter(u =>
            !u.jurisdiction || u.jurisdiction.length === 0 || u.jurisdiction.includes(this.districtId)
          );
          this.loadQueuesForUnits();
        }
      }
    });
    this.subs.push(unitsSub);

    const teamsSub = this.teamService.listTeams(false, this.districtId).subscribe({
      next: (res) => {
        this.loadingRelated = false;
        if (res.success && res.teams) {
          this.teams = res.teams;
        }
      },
      error: () => { this.loadingRelated = false; }
    });
    this.subs.push(teamsSub);
  }

  loadQueuesForUnits(): void {
    const sub = this.queueService.listQueues().subscribe({
      next: (res) => {
        if (res.success && res.queues) {
          this.queuesByUnit = {};
          for (const unit of this.units) {
            this.queuesByUnit[unit.id] = res.queues.filter(q => q.unit_id === unit.id);
          }
        }
      }
    });
    this.subs.push(sub);
  }

  goBack(): void {
    this.router.navigate(['/districts']);
  }

  humanizeSettlement(value: string): string {
    return SETTLEMENT_LABELS[value] || value;
  }

  humanizeCategory(value: string): string {
    return CATEGORY_LABELS[value] || value;
  }
}
