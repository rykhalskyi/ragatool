import { Component, OnInit } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { CollectionsService } from '../client/services/CollectionsService';
import { Collection } from '../client/models/Collection';
import { Router } from '@angular/router';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { AddCollectionDialogComponent } from '../add-collection-dialog/add-collection-dialog.component';

@Component({
  selector: 'app-collections-list',
  standalone: true,
  imports: [MatListModule, MatIconModule, CommonModule, MatButtonModule, MatDialogModule],
  templateUrl: './collections-list.component.html',
  styleUrl: './collections-list.component.scss'
})
export class CollectionsListComponent implements OnInit {
  collections: Collection[] = [];

  constructor(private router: Router, public dialog: MatDialog) {}

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

  openAddCollectionDialog(): void {
    const dialogRef = this.dialog.open(AddCollectionDialogComponent, {
      width: 'auto',
      height: 'auto',
      data: {}
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        // Handle the result (new collection name) here
        console.log('The dialog was closed with result:', result);
        // Call API to create collection and refresh list
        this.createCollection(result);
      }
    });
  }

  async createCollection(collectionName: string): Promise<void> {
    try {
      await CollectionsService.createNewCollectionCollectionsPost({ name: collectionName });
      this.fetchCollections(); // Refresh the list
    } catch (error) {
      console.error('Error creating collection:', error);
    }
  }
}
