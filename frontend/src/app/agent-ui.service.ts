import { Injectable, signal } from '@angular/core';

const STORAGE_KEY = 'ragatool.agent.pane.v1';
const MIN_WIDTH = 320;
const MAX_WIDTH = 900;
const DEFAULT_WIDTH = 400;

interface PaneState {
  visible: boolean;
  width: number;
}

@Injectable({ providedIn: 'root' })
export class AgentUiService {
  private readonly _visible = signal(false);
  private readonly _width = signal(DEFAULT_WIDTH);

  readonly visible = this._visible.asReadonly();
  readonly width = this._width.asReadonly();

  constructor() {
    this.restore();
  }

  toggle(): void {
    this._visible.update((visible) => !visible);
    this.persist();
  }

  open(): void {
    this._visible.set(true);
    this.persist();
  }

  hide(): void {
    this._visible.set(false);
    this.persist();
  }

  setWidth(width: number): void {
    this._width.set(this.clamp(width));
  }

  persist(): void {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ visible: this._visible(), width: this._width() })
      );
    } catch {
      // Storage is best-effort; the pane still works for this session.
    }
  }

  clamp(width: number): number {
    return Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, Math.round(width)));
  }

  private restore(): void {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw) as Partial<PaneState>;
      if (typeof parsed.visible === 'boolean') {
        this._visible.set(parsed.visible);
      }
      if (typeof parsed.width === 'number' && Number.isFinite(parsed.width)) {
        this._width.set(this.clamp(parsed.width));
      }
    } catch {
      // Ignore malformed or unavailable storage.
    }
  }
}
