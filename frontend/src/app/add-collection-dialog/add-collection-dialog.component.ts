import { Component, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-add-collection-dialog',
  standalone: true,
  imports: [FormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './add-collection-dialog.component.html',
  styleUrl: './add-collection-dialog.component.scss'
})
export class AddCollectionDialogComponent {
  collectionName: string = '';

  constructor(
    public dialogRef: MatDialogRef<AddCollectionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  onCancelClick(): void {
    this.dialogRef.close();
  }

  onOkClick(): void {
    this.dialogRef.close(this.collectionName);
  }
}
