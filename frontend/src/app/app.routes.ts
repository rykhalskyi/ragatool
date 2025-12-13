import { Routes } from '@angular/router';
import { SelectedCollectionComponent } from './selected-collection/selected-collection.component';
import { SettingsComponent } from './settings/settings.component';

export const routes: Routes = [
    { path: 'collection/:collectionId', component: SelectedCollectionComponent },
    { path: 'settings', component: SettingsComponent }
];
