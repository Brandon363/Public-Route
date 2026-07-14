import { Component, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SharedModules } from './views/shared/shared_modules';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, SharedModules],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'ServiceFlow AI';

  darkMode = signal<boolean>(false);
  themeIcon = signal<string>('pi pi-moon');

  ngOnInit(): void {
    this.handDarkMode();
  }

  handDarkMode() {
    const storedMode = localStorage.getItem('darkMode');

    if (storedMode === null) {
      this.darkMode.set(false);
      localStorage.setItem('darkMode', 'false');
    } else {
      this.darkMode.set(storedMode === 'true');
    }

    const element = document.querySelector('html');

    if (this.darkMode()) {
      element?.classList.add('dark-theme');
      this.themeIcon.set('pi pi-sun');
    } else {
      element?.classList.remove('dark-theme');
      this.themeIcon.set('pi pi-moon');
    }
  }
}
