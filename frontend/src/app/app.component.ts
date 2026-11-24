import { Component, HostListener, ElementRef, Renderer2, effect, signal } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { TopbarComponent } from "./topbar/topbar.component";
import { CollectionsListComponent } from './collections-list/collections-list.component';
import { AgentPaneComponent } from './agent-pane/agent-pane.component';
import { AgentUiService } from './agent-ui.service';
import { TestIds } from './testing/test-ids';
import { OpenAPI } from './client';
import { getApiUrl } from '../environments/runtime-config';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [TopbarComponent, CollectionsListComponent, AgentPaneComponent, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {

  title = 'ragatool';
  protected readonly TestIds = TestIds;

  isDragging = false;
  isResizingAgent = false;
  readonly isAuthPage = signal(false);

  constructor(
    private el: ElementRef,
    private renderer: Renderer2,
    private router: Router,
    public readonly agentUi: AgentUiService
  ) {
    effect(() => {
      (this.el.nativeElement as HTMLElement).style.setProperty(
        '--agent-pane-width',
        `${this.agentUi.width()}px`
      );
    });
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

  startAgentResizing(event: MouseEvent) {
    this.isResizingAgent = true;
    event.preventDefault();
  }

  @HostListener('document:mousemove', ['$event'])
  onDrag(event: MouseEvent) {
    const container = this.el.nativeElement.querySelector('.main-container');
    if (!container) {
      return;
    }
    const containerRect = container.getBoundingClientRect();

    if (this.isDragging) {
      const newWidth = event.clientX - containerRect.left;
      const newWidthPercent = (newWidth / containerRect.width) * 100;
      (this.el.nativeElement as HTMLElement).style.setProperty('--topic-list-width', `${newWidthPercent}%`);
    }

    if (this.isResizingAgent) {
      const maxWidth = Math.min(900, containerRect.width * 0.6, containerRect.width - 360);
      const requested = containerRect.right - event.clientX;
      this.agentUi.setWidth(Math.min(maxWidth, Math.max(320, requested)));
    }
  }

  @HostListener('document:mouseup')
  stopDragging() {
    if (this.isResizingAgent) {
      this.agentUi.persist();
    }
    this.isDragging = false;
    this.isResizingAgent = false;
  }
}
