import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  try {
    const initialized = await auth.checkStatus();
    if (!initialized) {
      return router.parseUrl('/setup');
    }
  } catch {
    return router.parseUrl('/login');
  }

  try {
    await auth.me();
    return true;
  } catch {
    return router.parseUrl('/login');
  }
};

export const setupGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  try {
    const initialized = await auth.checkStatus();
    if (initialized) {
      return router.parseUrl('/login');
    }
  } catch {
    return true;
  }

  return true;
};

export const loginGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  try {
    const initialized = await auth.checkStatus();
    if (!initialized) {
      return router.parseUrl('/setup');
    }
  } catch {
    return true;
  }

  try {
    await auth.me();
    return router.parseUrl('/');
  } catch {
    return true;
  }
};
