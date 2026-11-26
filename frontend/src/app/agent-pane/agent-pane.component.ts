import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  OnInit,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';
import { AgentUiService } from '../agent-ui.service';
import { TestIds } from '../testing/test-ids';
import { AgentService } from './agent.service';
import { CurrentCollectionService } from './current-collection.service';

@Component({
  selector: 'app-agent-pane',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, RouterLink],
  templateUrl: './agent-pane.component.html',
  styleUrl: './agent-pane.component.scss',
})
export class AgentPaneComponent implements OnInit {
  protected readonly TestIds = TestIds;
  protected readonly agent = inject(AgentService);
  protected readonly ui = inject(AgentUiService);
  protected readonly collection = inject(CurrentCollectionService).collection;

  protected readonly draft = signal('');
  protected readonly quickPrompts = [
    'Summarize the selected collection.',
    'What are the main topics covered here?',
    'Find the most relevant passages about ',
  ];

  private readonly messagesEl = viewChild<ElementRef<HTMLElement>>('messagesEl');
  private stickToBottom = true;

  constructor() {
    effect(() => {
      this.agent.messages();
      this.agent.isSending();
      if (this.stickToBottom) {
        queueMicrotask(() => this.scrollToBottom());
      }
    });
  }

  ngOnInit(): void {
    void this.agent.loadProfiles();
  }

  protected onDraftInput(event: Event): void {
    this.draft.set((event.target as HTMLTextAreaElement).value);
  }

  protected onComposerKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void this.send();
    }
  }

  protected async send(): Promise<void> {
    const text = this.draft();
    if (!text.trim() || this.agent.isSending() || !this.agent.activeProfile()) {
      return;
    }
    this.draft.set('');
    this.stickToBottom = true;
    await this.agent.send(text);
  }

  protected async sendQuickPrompt(prompt: string): Promise<void> {
    if (!this.agent.activeProfile() || this.agent.isSending()) {
      return;
    }
    this.stickToBottom = true;
    await this.agent.send(prompt);
  }

  protected onChatSelected(event: Event): void {
    this.agent.selectChat((event.target as HTMLSelectElement).value);
  }

  protected onMessagesScroll(): void {
    const element = this.messagesEl()?.nativeElement;
    if (!element) {
      return;
    }
    this.stickToBottom =
      element.scrollHeight - element.scrollTop - element.clientHeight < 80;
  }

  protected formatArguments(value: unknown): string {
    if (typeof value === 'string') {
      return value;
    }
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  protected hide(): void {
    this.ui.hide();
  }

  private scrollToBottom(): void {
    const element = this.messagesEl()?.nativeElement;
    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }
}
