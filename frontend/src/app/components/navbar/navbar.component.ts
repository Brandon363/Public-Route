import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router, RouterOutlet } from "@angular/router";
import { SharedModules } from '../../views/shared/shared_modules';
import { MenuItem } from 'primeng/api';
import { Subscription } from 'rxjs';
import { LoadingService } from '../../services/loading.service';
import { AuthService } from '../../services/auth.service';
import { AppComponent } from '../../app.component';

const CAN_CREATE_SUBMISSIONS_ROLES = ['citizen', 'intake_officer', 'dispatcher'];
const CITIZEN_ROLE = 'citizen';

@Component({
  selector: 'app-navbar',
  imports: [RouterOutlet, SharedModules],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})
export class NavbarComponent implements OnInit, OnDestroy {
  items: MenuItem[] = [];

  accountMenuItems: MenuItem[] = [
    {
      label: 'Logout',
      icon: 'pi pi-fw pi-sign-out',
      command: () => this.onLogout()
    }
  ];

  isManipulatingData: boolean = false;
  loadingSubscription!: Subscription;
  themeIcon: string = 'pi pi-moon';
  username: string = "-";
  avatarText: string = "-";
  showMobileMenu: boolean = false;
  showReportNav: boolean = false;

  currentLoadingMessage: string = '';
  private messageInterval: any;
  private messageIndex: number = 0;
  private loadingMessages: string[] = [
    "Processing your request...",
    "Talking to the server...",
    "Almost there..."
  ];

  constructor(
    private router: Router,
    private loadingService: LoadingService,
    private authService: AuthService,
    private app: AppComponent
  ) { }

  ngOnInit() {
    const user = this.authService.getCurrentUser();
    const firstName = user.first_name ?? "-";
    const lastName = user.last_name ?? "-";
    this.username = firstName;
    this.avatarText = `${firstName.charAt(0).toUpperCase()}${lastName ? lastName.charAt(0).toUpperCase() : ''}`;
    this.showReportNav = CAN_CREATE_SUBMISSIONS_ROLES.includes(user.role || '');
    const showReferenceData = user.role !== CITIZEN_ROLE;

    this.items = [
      { label: 'Cases', icon: 'pi pi-fw pi-briefcase', routerLink: '/cases' },
      ...(this.showReportNav ? [
        { separator: true },
        { label: 'Report a Case', icon: 'pi pi-fw pi-plus-circle', routerLink: '/report' },
      ] : []),
      ...(showReferenceData ? [
        { separator: true },
        { label: 'Districts', icon: 'pi pi-fw pi-map-marker', routerLink: '/districts' },
        { label: 'Organisation Units', icon: 'pi pi-fw pi-building', routerLink: '/organisation-units' },
        { label: 'Queues', icon: 'pi pi-fw pi-list', routerLink: '/queues' },
        { label: 'Resource Teams', icon: 'pi pi-fw pi-users', routerLink: '/resource-teams' },
      ] : []),
    ];

    this.loadingSubscription = this.loadingService.isManipulatingData$.subscribe((isLoading) => {
      Promise.resolve(null).then(() => {
        this.isManipulatingData = isLoading;
        if (isLoading) {
          this.startMessageRotation();
        } else {
          this.stopMessageRotation();
        }
      });
    });
  }

  private startMessageRotation() {
    this.clearLoadingInterval();
    this.messageIndex = Math.floor(Math.random() * this.loadingMessages.length);
    this.currentLoadingMessage = this.loadingMessages[this.messageIndex];

    this.messageInterval = setInterval(() => {
      this.messageIndex = (this.messageIndex + 1) % this.loadingMessages.length;
      this.currentLoadingMessage = this.loadingMessages[this.messageIndex];
    }, 3500);
  }

  private stopMessageRotation() {
    this.clearLoadingInterval();
  }

  private clearLoadingInterval() {
    if (this.messageInterval) {
      clearInterval(this.messageInterval);
      this.messageInterval = null;
    }
  }

  onLogout() {
    this.loadingService.setLoadingState(true);
    this.authService.logout().subscribe(() => {
      this.loadingService.setLoadingState(false);
    });
  }

  ngOnDestroy(): void {
    this.loadingSubscription?.unsubscribe();
  }

  toggleDarkMode() {
    this.app.darkMode.set(!this.app.darkMode());
    localStorage.setItem('darkMode', String(this.app.darkMode()));

    const element = document.querySelector('html');

    if (this.app.darkMode()) {
      element?.classList.add('dark-theme');
      this.themeIcon = 'pi pi-sun';
    } else {
      element?.classList.remove('dark-theme');
      this.themeIcon = 'pi pi-moon';
    }
  }

  isActiveMenu(path: string): boolean {
    return this.router.url.startsWith(path);
  }
}
