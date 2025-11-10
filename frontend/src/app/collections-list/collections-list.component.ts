import { Component, OnInit } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { CollectionsService } from '../client/services/CollectionsService';
import { Collection } from '../client/models/Collection';
import { Router } from '@angular/router';
import { MatDialogModule } from '@angular/material/dialog';

@Component({
  selector: 'app-collections-list',
  standalone: true,
  imports: [MatListModule, MatIconModule, CommonModule, MatButtonModule, MatDialogModule],
  templateUrl: './collections-list.component.html',
  styleUrl: './collections-list.component.scss'
})
export class CollectionsListComponent implements OnInit {
  collections: Collection[] = [];

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.fetchCollections();
  }

  async fetchCollections(): Promise<void> {
    try {
      this.collections = await CollectionsService.readCollectionsCollectionsGet();
    } catch (error) {
      console.error('Error fetching collections:', error);
    }
  }

  selectCollection(collectionId: string): void {
    this.router.navigate(['/collection', collectionId]);
  }

 
}
