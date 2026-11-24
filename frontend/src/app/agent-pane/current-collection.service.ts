import { Injectable, signal } from '@angular/core';
import { AgentCollectionContext } from './agent.models';

@Injectable({ providedIn: 'root' })
export class CurrentCollectionService {
  private readonly _collection = signal<AgentCollectionContext | null>(null);

  readonly collection = this._collection.asReadonly();

  set(collection: AgentCollectionContext | null): void {
    this._collection.set(collection);
  }

  clear(): void {
    this._collection.set(null);
  }
}
