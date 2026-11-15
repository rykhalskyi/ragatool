import { Routes } from '@angular/router';
import { AccessComponent } from './access/access.component';
import { authGuard, loginGuard, setupGuard } from './auth/auth.guard';
import { LoginComponent } from './login/login.component';
import { SelectedCollectionComponent } from './selected-collection/selected-collection.component';
import { SettingsComponent } from './settings/settings.component';
import { SetupComponent } from './setup/setup.component';

export const routes: Routes = [
    { path: 'login', component: LoginComponent, canActivate: [loginGuard] },
    { path: 'setup', component: SetupComponent, canActivate: [setupGuard] },
    { path: 'access', component: AccessComponent, canActivate: [authGuard] },
    { path: 'collection/:collectionId', component: SelectedCollectionComponent, canActivate: [authGuard] },
    { path: 'collection', component: SelectedCollectionComponent, canActivate: [authGuard] },
    { path: 'extension-tool/:toolId', component: SelectedCollectionComponent, canActivate: [authGuard] },
    { path: 'settings', component: SettingsComponent, canActivate: [authGuard] },
    { path: '', redirectTo: 'collection', pathMatch: 'full' }
];
