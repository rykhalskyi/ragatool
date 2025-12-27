import { ChangeDetectionStrategy, Component, OnInit, Input, OnChanges, SimpleChanges, OnDestroy, signal, WritableSignal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule, MatSelectChange } from '@angular/material/select'; // Import MatSelectChange
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ImportService } from '../../client/services/ImportService';
import { Import } from '../../client/models/Import';

import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { ExtendedCollection } from '../selected-collection.component';
import { LogStreamService } from '../../log-stream.service';
import { TaskCachingService } from '../../task-caching.service';
import { Message } from '../../client/models/Message';
import { MatDialog } from '@angular/material/dialog';
import { FileImportDialog } from '../file-import-dialog/file-import-dialog';
import { Body_import_file_import__collection_id__post } from '../../client/models/Body_import_file_import__collection_id__post';
import { UrlImportDialog } from '../url-import-dialog/url-import-dialog';
import { Body_import_url_import_url__colletion_id__post } from '../../client/models/Body_import_url_import_url__colletion_id__post';
import { CollectionDetailsComponent } from '../collection-details/collection-details.component';
import { CollectionDetails, FilesService, Task } from '../../client';
import { TaskCenterService } from '../../task-center/task-center.service';
import { SettingsService } from '../../settings.service';
import { PreviewDialogComponent } from '../preview-dialog/preview-dialog.component';
import { CollectionRefreshService } from '../../collection-refresh.service';
import { DeleteConfirmationDialogComponent } from '../../delete-confirmation-dialog/delete-confirmation-dialog.component';

@Component({
  selector: 'app-selected-collection-import',
  standalone: true,
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    ReactiveFormsModule,
    MatProgressBarModule,
    CollectionDetailsComponent,
    MatIconModule
  ],
  templateUrl: './selected-collection-import.component.html',
  styleUrl: './selected-collection-import.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})

@UntilDestroy()
export class SelectedCollectionImportComponent implements OnInit, OnChanges{


  @Input() collection: ExtendedCollection | undefined;
  @Input() collectionDetails: WritableSignal<CollectionDetails | null> = signal(null);
  @Input() filesImported: boolean = false;

  importForm!: FormGroup;
  importTypes: Import[] = [];
  showProgressBar = signal(false);
  task = signal<Task | undefined>(undefined);
  infoString = signal<string>("");
  twoStepImport = signal<boolean>(false);
  
  constructor(
    private fb: FormBuilder,
    private logStreamService: LogStreamService,
    private taskCachingService: TaskCachingService,
    private dialog: MatDialog,
    private readonly taskCenterService: TaskCenterService,
    private readonly settingsService: SettingsService,
    private readonly collectionRefreshService: CollectionRefreshService,
  ) {}

  async ngOnInit(): Promise<void> {

    this.importForm = this.fb.group({
      importType: ['', Validators.required]
    });

    await this.getImportTypes();

    this.logStreamService.logs$
      .pipe(untilDestroyed(this))
      .subscribe((log: Message) => {
        if (log.collectionId === this.collection?.id) {
          this.infoString.set(log.message);
        }
      });

    this.taskCachingService
      .tasks$
      .pipe(untilDestroyed(this))
      .subscribe(tasks => {
        const task = tasks.find(i => i.collectionId === this.collection?.id);
        this.showProgressBar.set(task ? true : false);
        this.task.set(task);
        this.collectionRefreshService.triggerRefresh();
      });

     if (this.collection?.saved && this.collection?.import_type)
     {
        const collectionImport: Import = {
          name : this.collection?.import_type,
          model: this.collection?.model!, 
          settings:  JSON.parse(this.collection!.settings!)
        }
        this.importForm.get('importType')?.setValue(collectionImport);
     }

     this.settingsService.settings$
     .pipe(untilDestroyed(this))
     .subscribe(settings => {
      const twoStepImort = settings.find(i=>i.name == "TwoStepImport");
      this.twoStepImport.set(twoStepImort?.value === "true");
    });

     const twoStepImort = this.settingsService.settings.find(i=>i.name == "TwoStepImport");
     this.twoStepImport.set(twoStepImort?.value === "true");
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['collection'] && this.collection && this.importForm) {
      const collectionId = this.collection.id;

      if (this.collectionIsSaved()) {
        this.importForm?.get('importType')?.disable({ emitEvent: false });
      } else {
        this.importForm.get('importType')?.enable({ emitEvent: false });
      }
     
      if (this.collectionIsSaved()) {
        const importType = this.importTypes.find(i => i.name === this.collection!.import_type);
        const initialState = {
          importType: importType,
          settings: this.collection!.settings
        };

        this.importForm.patchValue(initialState, { emitEvent: false });
      } else {

        this.importForm.reset({
          importType: '',
          settings: {}
        }, { emitEvent: false });

      }

      const task = this.taskCachingService.getTaskByCollectionId(this.collection.id);
      this.showProgressBar.set(task ? true : false);

      const info = this.logStreamService.getInfo(collectionId);
      if (info)
        this.infoString.set(info);

      this.importForm.markAsPristine();
      this.importForm.markAsUntouched();
      this.importForm.updateValueAndValidity({ emitEvent: false });
  
    }
  }


  async getImportTypes(): Promise<void> {
    try {
      const data = await ImportService.getImportsImportGet();
      this.importTypes = data;
    } 
    catch (e)
    {
        console.error('Error fetching import types:', e);
    }
    
  }

  onImportTypeChange(event: MatSelectChange): void {
    const selectedImportType: Import = event.value;
    this.importForm.get('importType')?.setValue(selectedImportType);
  }

  openSelectedImportDialog(): void {
    const selectedImportType: Import | null = this.importForm.get('importType')?.value ?? null;
    if (!selectedImportType) {
      return;
    }

    const commonData = this.getDialogData(selectedImportType);

    if (selectedImportType.name === 'FILE') {
      this.dialog.open(FileImportDialog, { data: { ...commonData, twoStepImport: this.twoStepImport() } })
        .afterClosed()
        .subscribe(result => { if (result) this.handleFileImport(result, selectedImportType); });
      return;
    }

    if (selectedImportType.name === 'URL') {
      this.dialog.open(UrlImportDialog, { data: commonData })
        .afterClosed()
        .subscribe(result => { if (result) this.handleUrlImport(result, selectedImportType); });
      return;
    }

    console.log('Other import types are not yet implemented.');
  }

  private getDialogData(selectedImportType: Import) {
    return {
      collectionName: this.collection?.name,
      collectionId: this.collection?.id,
      model: this.collectionIsSaved() ? this.collection!.model! : selectedImportType.model,
      settings: this.collectionIsSaved() ? JSON.parse(this.collection!.settings!) : selectedImportType.settings,
      saved: this.collection?.saved
    };
  }

  private buildFileFormData(selectedImportType: Import, result: any): Body_import_file_import__collection_id__post {
    return {
      file: result.selectedFile,
      import_params: JSON.stringify({
        name: selectedImportType.name,
        model: result.model,
        settings: {
          chunk_size: result.chunkSize,
          chunk_overlap: result.chunkOverlap,
          no_chunks: false
        }
      })
    };
  }

  private async handleFileImport(result: any, selectedImportType: Import) {
    const formData = this.buildFileFormData(selectedImportType, result);
    try {
      if (this.twoStepImport()) {
        await ImportService.importFileStep1ImportStep1CollectionIdPost(result.collectionId, formData);
      } else {
        await ImportService.importFileImportCollectionIdPost(result.collectionId, formData);
      }
      console.log('File imported successfully');
    } catch (error) {
      console.error('Error importing file:', error);
    }
  }

  private buildUrlFormData(selectedImportType: Import, result: any): Body_import_url_import_url__colletion_id__post {
    return {
      import_params: JSON.stringify({
        name: selectedImportType.name,
        model: result.model,
        settings: {
          chunk_size: result.chunkSize,
          chunk_overlap: result.chunkOverlap,
          no_chunks: result.no_chunks ?? result.noChunks
        }
      })
    };
  }

  private async handleUrlImport(result: any, selectedImportType: Import) {
    const formData = this.buildUrlFormData(selectedImportType, result);
    try {
      await ImportService.importUrlImportUrlColletionIdPost(result.collectionId, result.url, formData);
      console.log('Url imported successfully');
    } catch (error) {
      console.error('Error importing Url:', error);
    }
  }

openPreviewDialog() {
    const selectedImportType: Import | null = this.importForm.get('importType')?.value ?? null;
    if (!selectedImportType) {
      return;
    }

   const commonData = this.getDialogData(selectedImportType);

  this.dialog.open(PreviewDialogComponent, { data: { ...commonData, twoStepImport: this.twoStepImport() } })
        .afterClosed()
        .subscribe(result => { 
          if (result) this.handle2ndStepFileImport(result, selectedImportType,);
         });
      return;
}
  async handle2ndStepFileImport(result: any, selectedImportType: Import) {
     const formData = this.buildUrlFormData(selectedImportType, result);
     console.log("form_data",formData);
    try {
      await ImportService.importFileStep2ImportStep2CollectionIdPost(result.collectionId, formData);
      console.log('Url imported successfully');
    } catch (error) {
      console.error('Error importing Url:', error);
    }
  }

  compareImportTypes(o1: Import, o2: Import): boolean {
    return o1 && o2 ? o1.name === o2.name : o1 === o2;
  }

  trackByImportType(index: number, item: Import): string {
    return item.name;
  }

  private collectionIsSaved(): boolean {
    return (this.collection?.saved) ?? false;
  }

  async cancelTask(arg0: any) {
      await this.taskCenterService.cancelTask(this.task()!.id);
  } 

  async onDeleteFiles() {
    if (!this.collection) return;

    const dialogRef = this.dialog.open(DeleteConfirmationDialogComponent, {
      data: {
        title: 'Delete Files',
        message: `Are you sure you want to delete all files from collection "${this.collection.name}"?`
      },
    });

    dialogRef.afterClosed().subscribe(async result => {
      if (result) {
        try {
          await FilesService.deleteFilesFilesCollectionIdDelete(this.collection!.id);
          this.collectionRefreshService.triggerRefresh();
        } catch (error) {
          console.error('Error deleting files:', error);
        }
      }
    });
  }
}

