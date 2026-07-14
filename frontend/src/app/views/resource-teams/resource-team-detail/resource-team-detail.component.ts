import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { SharedModules } from '../../shared/shared_modules';
import { ResourceTeamService } from '../../../services/resource-team.service';
import { DistrictService } from '../../../services/district.service';
import { ResourceTeamDTO } from '../../../models/resource-team.interface';
import { DistrictDTO } from '../../../models/district.interface';

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
  selector: 'app-resource-team-detail',
  imports: [SharedModules],
  templateUrl: './resource-team-detail.component.html',
  styleUrl: './resource-team-detail.component.scss'
})
export class ResourceTeamDetailComponent implements OnInit, OnDestroy {
  private subs: Subscription[] = [];

  teamId!: number;
  team: ResourceTeamDTO | null = null;
  loading = true;
  notFound = false;

  baseDistrict: DistrictDTO | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private teamService: ResourceTeamService,
    private districtService: DistrictService,
  ) {}

  ngOnInit(): void {
    const sub = this.route.paramMap.subscribe(params => {
      const id = Number(params.get('id'));
      if (id) {
        this.teamId = id;
        this.loadTeam();
      }
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  loadTeam(): void {
    this.loading = true;
    this.notFound = false;
    this.baseDistrict = null;
    const sub = this.teamService.getTeam(this.teamId).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.success && res.team) {
          this.team = res.team;
          if (res.team.base_district_id != null) {
            this.loadDistrict(res.team.base_district_id);
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

  loadDistrict(districtId: number): void {
    const sub = this.districtService.getDistrict(districtId).subscribe({
      next: (res) => {
        if (res.success && res.district) {
          this.baseDistrict = res.district;
        }
      }
    });
    this.subs.push(sub);
  }

  goBack(): void {
    this.router.navigate(['/resource-teams']);
  }

  humanizeCategory(value: string): string {
    return CATEGORY_LABELS[value] || value;
  }
}
