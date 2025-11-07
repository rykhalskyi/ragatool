import { Component, HostListener, ElementRef, Renderer2 } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TopbarComponent } from "./topbar/topbar.component";
import { TopicListComponent } from './topic-list/topic-list.component';
import { SelectedTopicComponent } from './selected-topic/selected-topic.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [TopbarComponent, TopicListComponent, SelectedTopicComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'ragatouille';

  isDragging = false;

  constructor(private el: ElementRef, private renderer: Renderer2) {}

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
