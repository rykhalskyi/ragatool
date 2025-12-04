import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CollectionDetails } from '../../client/models/CollectionDetails';
import { MatListModule } from '@angular/material/list';

@Component({
  selector: 'app-collection-details',
  standalone: true,
  imports: [CommonModule, MatListModule],
  templateUrl: './collection-details.component.html',
  styleUrls: ['./collection-details.component.scss']
})
export class CollectionDetailsComponent {
  @Input() collectionDetails: CollectionDetails | null = null;
}
