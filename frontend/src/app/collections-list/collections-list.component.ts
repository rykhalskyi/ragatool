import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { CollectionsService } from '../client/services/CollectionsService';
import { Collection } from '../client/models/Collection';
import { Router } from '@angular/router';
import { MatDialogModule } from '@angular/material/dialog';
import { CollectionRefreshService } from '../collection-refresh.service';
import { Subscription } from 'rxjs';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { MatTooltipModule } from '@angular/material/tooltip'; // Import MatTooltipModule
import { ExtensionsStateService } from '../extensions-state.service'; // Import ExtensionsStateService
import { ExtensionTool } from '../client/models/ExtensionTool'; // Import ExtensionTool
import { ExtensionsRefreshService } from '../extensions-refresh.service';
// Removed: BrowserAnimationsModule import as it might cause BrowserModule conflicts

@UntilDestroy()
@Component({
  selector: 'app-collections-list',
  standalone: true,
  imports: [
    MatListModule,
    MatIconModule,
    CommonModule,
    MatButtonModule,
    MatDialogModule,
    MatTooltipModule, // Add MatTooltipModule here
    // Removed: BrowserAnimationsModule
  ],
  templateUrl: './collections-list.component.html',
  styleUrl: './collections-list.component.scss'
})
export class CollectionsListComponent implements OnInit, OnDestroy {
  collections: Collection[] = [];
  connectedExtensions: ExtensionTool[] = []; // <-- Add this
  private refreshSubscription: Subscription;

  constructor(private router: Router,
    private collectionRefreshService: CollectionRefreshService,
    private extensionsStateService: ExtensionsStateService,
    private extensionUpdateService: ExtensionsRefreshService // <-- Add this
  ) {
    this.refreshSubscription = this.collectionRefreshService.refreshNeeded$
    .pipe(untilDestroyed(this))
    .subscribe(() => {
      console.log('refresh triggered');
      this.fetchCollections();
    });
  }

  ngOnInit(): void {
    this.fetchCollections();
    this.extensionsStateService.connectedExtensions$
      .pipe(untilDestroyed(this))
      .subscribe((tools) => {
        this.connectedExtensions = tools;
      });
  }

  ngOnDestroy(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
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

  selectExtensionTool(toolId: string): void {
    this.router.navigate(['/extension-tool', toolId]); // This will be adjusted once routing is set up
  }
}
