import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSlideToggleChange, MatSlideToggleModule } from '@angular/material/slide-toggle';
import { CollectionsService } from '../client/services/CollectionsService';
import { AddCollectionDialogComponent } from '../add-collection-dialog/add-collection-dialog.component';
import { MatDialog } from '@angular/material/dialog';
import { CollectionRefreshService } from '../collection-refresh.service';
import { McpService } from '../client';
import { TaskCachingService } from '../task-caching.service';
import { Router } from '@angular/router';
import { Overlay, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal } from '@angular/cdk/portal';
import { TaskCenterComponent } from '../task-center/task-center.component';
import { MatBadgeModule } from '@angular/material/badge';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [MatSlideToggleModule, MatButtonModule, MatIconModule, MatBadgeModule],
  templateUrl: './topbar.component.html',
  styleUrl: './topbar.component.scss'
})
export class TopbarComponent implements OnInit {
  @ViewChild('taskCenterButton', { read: ElementRef }) taskCenterButton: ElementRef | undefined;
  public taskCount = 0;
  private overlayRef: OverlayRef | null = null;

    constructor(public dialog: MatDialog, 
    private collectionRefreshService: CollectionRefreshService,
    private taskCashedService: TaskCachingService,
    private router: Router,
    private overlay: Overlay){}
  
  ngOnInit(): void {
    this.taskCashedService.tasks$.subscribe(tasks => {
      this.taskCount = tasks.length;
    });
  }

 openAddCollectionDialog(): void {
    const dialogRef = this.dialog.open(AddCollectionDialogComponent, {
      width: 'auto',
      height: 'auto',
      data: {}
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
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

  protected async onToggleChange(event: MatSlideToggleChange) {
    console.log('toggle', event.checked);
    await McpService.setMcpEnabledMcpMcpEnabledPut({enabled : event.checked});

  }

  protected settings_click() {
      this.router.navigate(['/settings']);
  }

  public openTaskCenter() { 
   if (this.taskCount == 0) return; 

    if (this.overlayRef) {
      this.overlayRef.dispose();
      this.overlayRef = null;
      return;
    }

    if (!this.taskCenterButton) {
      return;
    }

    const positionStrategy = this.overlay.position()
      .flexibleConnectedTo(this.taskCenterButton.nativeElement)
      .withPositions([{
        originX: 'end',
        originY: 'bottom',
        overlayX: 'end',
        overlayY: 'top',
      }]);

    this.overlayRef = this.overlay.create({
      positionStrategy,
      hasBackdrop: true,
      backdropClass: 'cdk-overlay-transparent-backdrop'
    });

    this.overlayRef.backdropClick().subscribe(() => {
      if(this.overlayRef) {
        this.overlayRef.dispose();
        this.overlayRef = null;
      }
    });

    const componentPortal = new ComponentPortal(TaskCenterComponent);
    this.overlayRef.attach(componentPortal);
  }
}
