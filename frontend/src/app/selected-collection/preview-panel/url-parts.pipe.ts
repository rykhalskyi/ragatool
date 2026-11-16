import { Pipe, PipeTransform } from '@angular/core';

export interface UrlParts {
  origin: string;
  tail: string;
  isUrl: boolean;
}

@Pipe({
  name: 'urlParts',
  standalone: true,
})
export class UrlPartsPipe implements PipeTransform {
  transform(value: string | null | undefined): UrlParts {
    const source = (value ?? '').trim();
    if (!source) {
      return { origin: '', tail: '', isUrl: false };
    }

    try {
      const url = new URL(source);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        return { origin: '', tail: source, isUrl: false };
      }

      const tail = `${url.pathname}${url.search}${url.hash}`;
      return {
        origin: `${url.protocol}//${url.host}`,
        tail: tail && tail !== '/' ? tail : '/',
        isUrl: true,
      };
    } catch {
      return { origin: '', tail: source, isUrl: false };
    }
  }
}
