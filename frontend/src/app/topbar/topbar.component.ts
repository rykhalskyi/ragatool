import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { CollectionsService } from '../client/services/CollectionsService';
import { AddCollectionDialogComponent } from '../add-collection-dialog/add-collection-dialog.component';
import { MatDialog } from '@angular/material/dialog';
import { CollectionRefreshService } from '../collection-refresh.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [MatSlideToggleModule, MatButtonModule, MatIconModule],
  templateUrl: './topbar.component.html',
  styleUrl: './topbar.component.scss'
})
export class TopbarComponent {
  
  constructor(public dialog: MatDialog, private collectionRefreshService: CollectionRefreshService){}

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
      this.collectionRefreshService.triggerRefresh();
    } catch (error) {
      console.error('Error creating collection:', error);
    }
  }

}
