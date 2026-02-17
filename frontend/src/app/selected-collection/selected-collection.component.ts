import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ActivatedRoute, Router } from '@angular/router';
import { CollectionsService } from '../client/services/CollectionsService';
import { Collection } from '../client/models/Collection';
import { CollectionDetails } from '../client/models/CollectionDetails';
import { MatIconModule } from '@angular/material/icon';
import { CollectionRefreshService } from '../collection-refresh.service';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { DeleteConfirmationDialogComponent } from '../delete-confirmation-dialog/delete-confirmation-dialog.component';
import { SelectedCollectionImportComponent } from './selected-collection-import/selected-collection-import.component';
import { LogsViewComponent } from '../logs-view/logs-view';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { File, FilesService } from '../client';
import { Subscription } from 'rxjs';
import { ExtensionToolDetailsComponent } from './extension-tool-details/extension-tool-details.component'; // Import the new component


export interface ExtendedCollection extends Collection {
  saved: boolean;
}
@UntilDestroy()
@Component({
  selector: 'app-selected-collection',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatIconModule,
    MatDialogModule,
    SelectedCollectionImportComponent,
    LogsViewComponent,
    ExtensionToolDetailsComponent // Add this
  ],
  templateUrl: './selected-collection.component.html',
  styleUrl: './selected-collection.component.scss'
})

export class SelectedCollectionComponent implements OnInit, OnDestroy {
  collection: ExtendedCollection | undefined;
  collectionDetails = signal<CollectionDetails | null>(null);
  collectionFiles  = signal<File[] | null>(null);
  isEnabled: boolean = false;
  isEditingDescription = false;
  editedDescription = '';
  activeType: 'collection' | 'extension-tool' | null = null; // <-- Add this
  selectedId: string | null = null; // To hold either collectionId or toolId
  private refreshSubscription: Subscription | undefined;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private collectionRefreshService: CollectionRefreshService,
    public dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.route.paramMap.pipe(untilDestroyed(this))
      .subscribe(params => {
        const collectionId = params.get('collectionId');
        const toolId = params.get('toolId');

        if (collectionId) {
          this.activeType = 'collection';
          this.selectedId = collectionId;
          this.fetchCollection(collectionId);
          CollectionsService.readCollectionDetailsCollectionsCollectionIdDetailsGet(collectionId)
            .then(res => this.collectionDetails.set(res));
          FilesService.readFilesFilesCollectionIdGet(collectionId)
            .then(res => this.collectionFiles.set(res));
        } else if (toolId) {
          this.activeType = 'extension-tool';
          this.selectedId = toolId;
          // No specific fetch for extension tool details here; ExtensionToolDetailsComponent will handle its @Input
          this.collection = undefined; // Clear collection data if navigating to extension tool
          this.collectionDetails.set(null);
          this.collectionFiles.set(null);
        } else {
          this.activeType = null;
          this.selectedId = null;
          this.collection = undefined;
          this.collectionDetails.set(null);
          this.collectionFiles.set(null);
        }
      });

    this.refreshSubscription = this.collectionRefreshService.refreshNeeded$.subscribe(() => {
      if (this.collection && this.activeType === 'collection') {
        this.updateInfo();
      }
    });
  }

  ngOnDestroy(): void {
    if (this.refreshSubscription) {
        this.refreshSubscription.unsubscribe();
    }
  }

  async fetchCollection(collectionId: string): Promise<void> {
    try {
      const collection = await CollectionsService.readCollectionCollectionsCollectionIdGet(collectionId);

       this.collection = {
        ...collection,
        saved: collection.import_type !== 'NONE',
      };

      this.isEnabled = this.collection?.enabled || false;
    } catch (error) {
      console.error('Error fetching collection details:', error);
    }
  }

  async onToggleChange(): Promise<void> {
    if (this.collection) {
      try {
        await CollectionsService.updateExistingCollectionCollectionsCollectionIdPut(this.collection.id, {
          name: this.collection.name,
          description:  this.editedDescription,
          enabled: this.isEnabled });
        console.log('Collection enabled status updated.');
      } catch (error) {
        console.error('Error updating collection enabled status:', error);
        this.isEnabled = !this.isEnabled;
      }
      this.collectionRefreshService.triggerRefresh();
    }
  }

  async deleteCollection(): Promise<void> {
    if (!this.collection) return;

    const dialogRef = this.dialog.open(DeleteConfirmationDialogComponent, {
      data: {
        title: 'Delete Collection',
        message: `Are you sure you want to delete collection "${this.collection.name}"?`
      },
    });

    dialogRef.afterClosed().subscribe(async result => {
      if (result) {
        try {
          if (this.collection) {
            console.log(`delete .${this.collection.id}.`)
            await CollectionsService.deleteExistingCollectionCollectionsCollectionIdDelete(this.collection.id);
            console.log('Collection deleted successfully.');
            this.router.navigate(['/']);
          }
        } catch (error) {
          console.error('Error deleting collection:', error);
        }

        this.collectionRefreshService.triggerRefresh();}
    });
  }

  startEditingDescription(): void {
    this.isEditingDescription = true;
    this.editedDescription = this.collection?.description || '';
  }

  cancelEditingDescription(): void {
    this.isEditingDescription = false;
  }

  async saveDescription(): Promise<void> {
    if (this.collection) {
      try {
        await CollectionsService.updateExistingCollectionCollectionsCollectionIdPut(this.collection.id, {
          name: this.collection.name,
          description: this.editedDescription,
          enabled: this.isEnabled
        });
        if(this.collection) {
          this.collection.description = this.editedDescription;
        }
        this.isEditingDescription = false;
        this.collectionRefreshService.triggerRefresh();
      } catch (error) {
        console.error('Error updating collection description:', error);
      }
    }
  }

  async updateInfo(){
     const collectionId = this.collection!.id;
     this.fetchCollection(collectionId);
        CollectionsService.readCollectionDetailsCollectionsCollectionIdDetailsGet(collectionId)
        .then(res => this.collectionDetails.set(res));

        FilesService.readFilesFilesCollectionIdGet(collectionId)
        .then(res => this.collectionFiles.set(res));
  }
}

