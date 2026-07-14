import { Routes } from '@angular/router';
import { LoginComponent } from './views/auth/login/login.component';
import { LayoutComponent } from './components/layout/layout.component';
import { ViewAllCasesComponent } from './views/cases/view-all-cases/view-all-cases.component';
import { ReportCaseComponent } from './views/cases/report-case/report-case.component';
import { CaseDetailComponent } from './views/cases/case-detail/case-detail.component';
import { ViewAllDistrictsComponent } from './views/districts/view-all-districts/view-all-districts.component';
import { DistrictDetailComponent } from './views/districts/district-detail/district-detail.component';
import { ViewAllOrganisationUnitsComponent } from './views/organisation-units/view-all-organisation-units/view-all-organisation-units.component';
import { OrganisationUnitDetailComponent } from './views/organisation-units/organisation-unit-detail/organisation-unit-detail.component';
import { ViewAllQueuesComponent } from './views/queues/view-all-queues/view-all-queues.component';
import { QueueDetailComponent } from './views/queues/queue-detail/queue-detail.component';
import { ViewAllResourceTeamsComponent } from './views/resource-teams/view-all-resource-teams/view-all-resource-teams.component';
import { ResourceTeamDetailComponent } from './views/resource-teams/resource-team-detail/resource-team-detail.component';
import { PublicSubmitComponent } from './views/cases/public-submit/public-submit.component';


export const routes: Routes = [
    {
        path: '',
        redirectTo: 'login',
        pathMatch: 'full'
    },
    { path: 'login', component: LoginComponent },
    { path: 'submit', component: PublicSubmitComponent },
    {
        path: '', component: LayoutComponent, children: [
            { path: '', redirectTo: 'cases', pathMatch: 'full' },
            { path: 'cases', component: ViewAllCasesComponent },
            { path: 'case/:id', component: CaseDetailComponent },
            { path: 'report', component: ReportCaseComponent },
            { path: 'districts', component: ViewAllDistrictsComponent },
            { path: 'district/:id', component: DistrictDetailComponent },
            { path: 'organisation-units', component: ViewAllOrganisationUnitsComponent },
            { path: 'organisation-unit/:id', component: OrganisationUnitDetailComponent },
            { path: 'queues', component: ViewAllQueuesComponent },
            { path: 'queue/:id', component: QueueDetailComponent },
            { path: 'resource-teams', component: ViewAllResourceTeamsComponent },
            { path: 'resource-team/:id', component: ResourceTeamDetailComponent },
        ]
    }
];
