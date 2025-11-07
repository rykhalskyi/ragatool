import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TopbarComponent } from "./topbar/topbar.component";
import { TopicListComponent } from './topic-list/topic-list.component';
import { SelectedTopicComponent } from './selected-topic/selected-topic.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, TopbarComponent, TopicListComponent, SelectedTopicComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'ragatouille';
}
