import { Component, Input, OnChanges, signal, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CollectionDetails } from '../../client/models/CollectionDetails';
import { MatListModule } from '@angular/material/list';
import { MatDialog } from '@angular/material/dialog'; // Import MatDialog
import { MatButtonModule } from '@angular/material/button';
import { InspectDialogComponent } from '../inspect-dialog/inspect-dialog.component'; // Import InspectDialogComponent

@Component({
  selector: 'app-collection-details',
  standalone: true,
  imports: [CommonModule, MatListModule, MatButtonModule],
  templateUrl: './collection-details.component.html',
  styleUrls: ['./collection-details.component.scss']
})
export class CollectionDetailsComponent implements OnChanges{
  @Input() collectionDetails: CollectionDetails | null = null;
  @Input() filesImported: boolean = false;

  protected canInspect = signal<boolean>(false);
  constructor(public dialog: MatDialog) {} // Inject MatDialog
  ngOnChanges(changes: SimpleChanges): void {
    if (this.collectionDetails?.count)
    {
      this.canInspect.set(this.collectionDetails?.count > 0);
    }
    else{
      this.canInspect.set(false);
    }
    console.log('can inspect', this.collectionDetails?.count, this.canInspect);
  }

  openInspectDialog(): void {
    if (this.collectionDetails) {
      this.dialog.open(InspectDialogComponent, {
        width: '800px', // Adjust width as needed
        data: { collectionId: this.collectionDetails.id }
      });
    }
  }
}
