import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, signal } from '@angular/core';
import { Subject, firstValueFrom, takeUntil } from 'rxjs';
import { getApiUrl } from '../../environments/runtime-config';
import { LlmProfile } from '../settings/llm-profiles/llm-profile.models';
import { LlmProfilesService } from '../settings/llm-profiles/llm-profiles.service';
import {
  AgentChat,
  AgentChatHistoryMessage,
  AgentChatRequest,
  AgentChatResponse,
  AgentMessage,
} from './agent.models';
import { CurrentCollectionService } from './current-collection.service';

const CHATS_KEY = 'ragatool.agent.chats.v1';
const ACTIVE_CHAT_KEY = 'ragatool.agent.active-chat.v1';
const MAX_CHATS = 50;
const MAX_MESSAGES_PER_CHAT = 200;
const MAX_HISTORY_MESSAGES = 20;

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

@Injectable({ providedIn: 'root' })
export class AgentService {
  private readonly _chats = signal<AgentChat[]>([]);
  private readonly _activeChatId = signal<string | null>(null);
  private readonly _isSending = signal(false);
  private readonly _profiles = signal<LlmProfile[]>([]);

  readonly chats = this._chats.asReadonly();
  readonly activeChatId = this._activeChatId.asReadonly();
  readonly isSending = this._isSending.asReadonly();
  readonly profiles = this._profiles.asReadonly();

  readonly activeChat = computed(
    () => this._chats().find((chat) => chat.id === this._activeChatId()) ?? null
  );
  readonly messages = computed(() => this.activeChat()?.messages ?? []);
  readonly activeProfile = computed(
    () => this._profiles().find((profile) => profile.is_active) ?? null
  );

  private cancelRequest: Subject<void> | null = null;
  private cancelled = false;

  constructor(
    private readonly http: HttpClient,
    private readonly llmProfiles: LlmProfilesService,
    private readonly currentCollection: CurrentCollectionService
  ) {
    this.restoreChats();
    void this.loadProfiles();
  }

  newChat(): void {
    const now = Date.now();
    const chat: AgentChat = {
      id: newId(),
      title: 'New chat',
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
    this._chats.update((chats) => [...chats, chat].slice(-MAX_CHATS));
    this._activeChatId.set(chat.id);
    this.persistChats();
  }

  selectChat(id: string): void {
    if (!this._chats().some((chat) => chat.id === id)) {
      return;
    }
    this._activeChatId.set(id);
    this.persistChats();
  }

  deleteChat(id: string): void {
    const remaining = this._chats().filter((chat) => chat.id !== id);
    this._chats.set(remaining);
    if (this._activeChatId() === id) {
      this._activeChatId.set(remaining.length ? remaining[remaining.length - 1].id : null);
    }
    if (remaining.length === 0) {
      this.newChat();
      return;
    }
    this.persistChats();
  }

  async loadProfiles(): Promise<void> {
    try {
      this._profiles.set(await this.llmProfiles.listProfiles());
    } catch {
      this._profiles.set([]);
    }
  }

  async send(text: string): Promise<void> {
    const content = text.trim();
    if (!content || this._isSending()) {
      return;
    }

    let chat = this.activeChat();
    if (!chat) {
      this.newChat();
      chat = this.activeChat();
    }
    if (!chat) {
      return;
    }

    const chatId = chat.id;
    const history: AgentChatHistoryMessage[] = chat.messages
      .filter((message) => message.role === 'user' || message.role === 'assistant')
      .slice(-MAX_HISTORY_MESSAGES)
      .map((message) => ({
        role: message.role as 'user' | 'assistant',
        content: message.content,
      }));

    this.appendMessage(chatId, {
      id: newId(),
      role: 'user',
      content,
      createdAt: Date.now(),
    });

    const request: AgentChatRequest = {
      message: content,
      history,
      collection_name: this.currentCollection.collection()?.name ?? null,
    };

    const cancel = new Subject<void>();
    this.cancelRequest = cancel;
    this.cancelled = false;
    this._isSending.set(true);

    try {
      const response = await firstValueFrom(
        this.http
          .post<AgentChatResponse>(`${getApiUrl()}/agent/chat`, request)
          .pipe(takeUntil(cancel))
      );
      this.appendMessage(chatId, {
        id: newId(),
        role: 'assistant',
        content: response.message?.trim() || 'The agent returned an empty response.',
        createdAt: Date.now(),
        toolCalls: response.tool_calls ?? [],
        warnings: response.warnings ?? [],
      });
    } catch (error) {
      if (this.cancelled) {
        this.appendMessage(chatId, {
          id: newId(),
          role: 'warning',
          content: 'Request cancelled.',
          createdAt: Date.now(),
        });
      } else {
        this.appendMessage(chatId, {
          id: newId(),
          role: 'error',
          content: this.errorMessage(error),
          createdAt: Date.now(),
        });
      }
    } finally {
      if (this.cancelRequest === cancel) {
        this.cancelRequest = null;
      }
      this._isSending.set(false);
    }
  }

  cancel(): void {
    if (!this.cancelRequest) {
      return;
    }
    this.cancelled = true;
    this.cancelRequest.next();
    this.cancelRequest.complete();
    this.cancelRequest = null;
  }

  private appendMessage(chatId: string, message: AgentMessage): void {
    this._chats.update((chats) =>
      chats.map((chat) => {
        if (chat.id !== chatId) {
          return chat;
        }
        const messages = [...chat.messages, message].slice(-MAX_MESSAGES_PER_CHAT);
        const title =
          chat.title === 'New chat' && message.role === 'user'
            ? this.titleFrom(message.content)
            : chat.title;
        return {
          ...chat,
          title,
          updatedAt: Date.now(),
          messages,
        };
      })
    );
    this.persistChats();
  }

  private titleFrom(text: string): string {
    const collapsed = text.replace(/\s+/g, ' ').trim();
    return collapsed.length <= 60 ? collapsed : `${collapsed.slice(0, 57)}...`;
  }

  private errorMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const detail = error.error?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
      if (error.status === 0) {
        return 'Could not reach Ragatool. Check that the backend is running.';
      }
      return `The agent request failed (HTTP ${error.status}).`;
    }
    return 'The agent request failed unexpectedly.';
  }

  private restoreChats(): void {
    try {
      const raw = localStorage.getItem(CHATS_KEY);
      const parsed = raw ? (JSON.parse(raw) as AgentChat[]) : [];
      if (Array.isArray(parsed) && parsed.length > 0) {
        const chats = parsed
          .filter((chat) => chat && typeof chat.id === 'string')
          .slice(-MAX_CHATS)
          .map((chat) => ({
            ...chat,
            messages: Array.isArray(chat.messages)
              ? chat.messages.slice(-MAX_MESSAGES_PER_CHAT)
              : [],
          }));
        this._chats.set(chats);
        const active = localStorage.getItem(ACTIVE_CHAT_KEY);
        const activeExists = chats.some((chat) => chat.id === active);
        this._activeChatId.set(activeExists ? active : chats[chats.length - 1].id);
        return;
      }
    } catch {
      // Fall through to a fresh chat.
    }
    this.newChat();
  }

  private persistChats(): void {
    const sanitized = this._chats()
      .slice(-MAX_CHATS)
      .map((chat) => ({
        ...chat,
        messages: chat.messages.slice(-MAX_MESSAGES_PER_CHAT),
      }));

    try {
      localStorage.setItem(CHATS_KEY, JSON.stringify(sanitized));
      if (this._activeChatId()) {
        localStorage.setItem(ACTIVE_CHAT_KEY, this._activeChatId() as string);
      }
    } catch {
      // Ignore quota/availability errors; history remains in memory.
    }
  }
}
