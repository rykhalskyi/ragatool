import { HttpInterceptorFn } from '@angular/common/http';
import { getApiUrl } from '../../environments/runtime-config';

export const credentialsInterceptor: HttpInterceptorFn = (request, next) => {
  const apiUrl = getApiUrl();
  const isApiRequest =
    apiUrl.startsWith('/')
      ? request.url.startsWith(apiUrl)
      : request.url.startsWith(apiUrl) || request.url.startsWith('/api');

  return next(
    isApiRequest ? request.clone({ withCredentials: true }) : request
  );
};
