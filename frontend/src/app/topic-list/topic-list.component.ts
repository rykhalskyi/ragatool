import { Component } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-topic-list',
  standalone: true,
  imports: [MatListModule, MatIconModule, CommonModule, MatButtonModule],
  templateUrl: './topic-list.component.html',
  styleUrl: './topic-list.component.scss'
})
export class TopicListComponent {
  topics = [
    {
      name: 'Brunch this weekend?',
      description: 'I\'ll be in your neighborhood doing errands this weekend.',
      icon: 'folder'
    },
    {
      name: 'Summer BBQ',
      description: 'Wish I could come, but I\'m out of town this weekend.',
      icon: 'book'
    },
    {
      name: 'Oui Oui',
      description: 'Do you have Paris recommendations? Have you ever been?',
      icon: 'home'
    }
  ];
}
