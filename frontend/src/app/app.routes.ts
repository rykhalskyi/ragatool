import { Routes } from '@angular/router';
import { SelectedCollectionComponent } from './selected-collection/selected-collection.component';

export const routes: Routes = [
    { path: 'collection/:collectionId', component: SelectedCollectionComponent }
];
