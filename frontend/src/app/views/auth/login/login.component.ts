import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { MessageService } from 'primeng/api';
import { Subscription } from 'rxjs';
import { LoadingService } from '../../../services/loading.service';
import { AuthService } from '../../../services/auth.service';
import { UserLoginRequest } from '../../../models/user.interface';
import { SharedModules } from '../../shared/shared_modules';
import { Router } from '@angular/router';
import { FormControl, FormGroup, Validators } from '@angular/forms';


@Component({
  selector: 'app-login',
  imports: [SharedModules],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnDestroy, OnInit {
  loginSubscription!: Subscription;
  loadingSubscription!: Subscription;
  notificationSubscription!: Subscription;
  // email: string = '';
  loading: boolean = false;
  // password: string = '';
  loginForm!: FormGroup;

  constructor(
    private loadingService: LoadingService,
    private authService: AuthService,
    private messageService: MessageService,
    private router: Router
  ) { }


  ngOnInit(): void {
    this.loading = false;
    sessionStorage.clear();
    this.loadingSubscription = this.loadingService.isManipulatingData$.subscribe((isLoading) => {
      Promise.resolve(null).then(() => {
        this.loading = isLoading;
      });
    });

    this.loginForm = new FormGroup({
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [Validators.required])
    });
  }


  ngOnDestroy(): void {
    this.loginSubscription?.unsubscribe();
    this.notificationSubscription?.unsubscribe();
    this.loginSubscription?.unsubscribe();
  }


  onLogin() {
    // if (this.password.trim() === '' || this.email.trim() === '') {
    //   this.messageService.add({ severity: 'error', summary: 'Failed', detail: `Enter valid username and password` });
    //   return
    // }
    this.loadingService.setLoadingState(true);
    const loginRequest: UserLoginRequest = {
      email: this.loginForm.value.email,
      password: this.loginForm.value.password
    };

    this.loginSubscription = this.authService.login(loginRequest).subscribe((response) => {
      this.loadingService.setLoadingState(false);
      if (!response.success) {
        this.loadingService.setLoadingState(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Login Failed',
          detail: response.message || 'Invalid username or password.'
        });
        return;
      }

      this.messageService.add({ severity: 'success', summary: 'Logged In', detail: `Welcome back ${response.user?.first_name}` });
      this.router.navigate(['/cases']);
    }, (error) => {
      this.loadingService.setLoadingState(false);
      this.messageService.add({ severity: 'error', summary: 'Login Failed', detail: error.message });
    })
  }


  @HostListener('document:keydown.enter', ['$event'])
  handleGlobalEnter() {
    if (this.loginForm.invalid) {
      return
    }
    else {
      return this.onLogin()
    }
  }

}
