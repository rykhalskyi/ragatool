import { Component, HostListener, ElementRef, Renderer2 } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TopbarComponent } from "./topbar/topbar.component";
import { CollectionsListComponent } from './collections-list/collections-list.component';
import { OpenAPI } from './client';
import { environment } from '../environments/environment'; // Import the environment

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

  constructor(private el: ElementRef, private renderer: Renderer2) {
    OpenAPI.BASE = environment.apiUrl; // Use the API URL from the environment
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
