import { Routes } from '@angular/router';
import { SelectedCollectionComponent } from './selected-collection/selected-collection.component';
import { SettingsComponent } from './settings/settings.component';
// No need to import CollectionDetailsComponent or ExtensionToolDetailsComponent here, as SelectedCollectionComponent will render them directly or display its own content

export const routes: Routes = [
    { path: 'collection/:collectionId', component: SelectedCollectionComponent },
    { path: 'extension-tool/:toolId', component: SelectedCollectionComponent },
    { path: 'settings', component: SettingsComponent },
    { path: '', redirectTo: 'collection', pathMatch: 'full' }
];
