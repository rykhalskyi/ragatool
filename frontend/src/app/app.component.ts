import { Component, HostListener, ElementRef, Renderer2, signal } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { TopbarComponent } from "./topbar/topbar.component";
import { CollectionsListComponent } from './collections-list/collections-list.component';
import { OpenAPI } from './client';
import { getApiUrl } from '../environments/runtime-config';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [TopbarComponent, CollectionsListComponent, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {

  title = 'ragatool';

  isDragging = false;
  readonly isAuthPage = signal(false);

  constructor(
    private el: ElementRef,
    private renderer: Renderer2,
    private router: Router
  ) {
    OpenAPI.BASE = getApiUrl(); // Runtime/deploy-time API URL
    OpenAPI.WITH_CREDENTIALS = true;

    this.updateLayout(this.router.url);
    this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe((event) => this.updateLayout((event as NavigationEnd).urlAfterRedirects));
  }

  private updateLayout(url: string): void {
    this.isAuthPage.set(url.startsWith('/login') || url.startsWith('/setup'));
  }

  startDragging(event: MouseEvent) {
    this.isDragging = true;
    event.preventDefault();
  }

  @HostListener('document:mousemove', ['$event'])
  onDrag(event: MouseEvent) {
    if (this.isDragging) {
      const container = this.el.nativeElement.querySelector('.main-container');
      if (container) {
        const containerRect = container.getBoundingClientRect();
        const newWidth = event.clientX - containerRect.left;
        const newWidthPercent = (newWidth / containerRect.width) * 100;
        (this.el.nativeElement as HTMLElement).style.setProperty('--topic-list-width', `${newWidthPercent}%`);
      }
    }
  }

  @HostListener('document:mouseup')
  stopDragging() {
    this.isDragging = false;
  }
}
