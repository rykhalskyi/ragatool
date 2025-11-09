import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ActivatedRoute, Router } from '@angular/router';
import { CollectionsService } from '../client/services/CollectionsService';
import { Collection } from '../client/models/Collection';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-selected-collection',
  standalone: true,
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatSlideToggleModule, MatIconModule],
  templateUrl: './selected-collection.component.html',
  styleUrl: './selected-collection.component.scss'
})

export class SelectedCollectionComponent implements OnInit {
  collection: Collection | undefined;
  isEnabled: boolean = false;

  constructor(private route: ActivatedRoute, private router: Router) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const collectionId = params.get('collectionId');
      if (collectionId) {
        this.fetchCollectionDetails(collectionId);
      }
    });
  }

  async fetchCollectionDetails(collectionId: string): Promise<void> {
    try {
      this.collection = await CollectionsService.readCollectionCollectionsCollectionIdGet(collectionId);
      // Assuming 'enabled' is a property of the Collection model
      // If not, you might need to add it to the Collection model or handle it differently
      this.isEnabled = this.collection?.enabled || false;
    } catch (error) {
      console.error('Error fetching collection details:', error);
    }
  }

  async onToggleChange(): Promise<void> {
    if (this.collection) {
      try {
        // Assuming 'enabled' is a property of the CollectionCreate model
        await CollectionsService.updateExistingCollectionCollectionsCollectionIdPut(this.collection.id, { name: this.collection.name, enabled: this.isEnabled });
        console.log('Collection enabled status updated.');
      } catch (error) {
        console.error('Error updating collection enabled status:', error);
        // Revert toggle state if update fails
        this.isEnabled = !this.isEnabled;
      }
    }
  }

  async deleteCollection(): Promise<void> {
    if (this.collection && confirm(`Are you sure you want to delete collection "${this.collection.name}"?`)) {
      try {
        await CollectionsService.deleteExistingCollectionCollectionsCollectionIdDelete(this.collection.id);
        console.log('Collection deleted successfully.');
        this.router.navigate(['/']); // Navigate back to the collections list
      } catch (error) {
        console.error('Error deleting collection:', error);
      }
    }
  }
}
