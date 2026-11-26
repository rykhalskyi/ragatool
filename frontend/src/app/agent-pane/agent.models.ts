export interface AgentToolCall {
  id: string;
  name: string;
  arguments: unknown;
  status: 'success' | 'error' | string;
  result_preview: string;
}

export interface AgentChatResponse {
  message: string;
  model: string;
  tool_calls: AgentToolCall[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  warnings: string[];
}

export interface AgentChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AgentChatRequest {
  message: string;
  history: AgentChatHistoryMessage[];
  collection_name: string | null;
}

export type AgentMessageRole = 'user' | 'assistant' | 'warning' | 'error';

export interface AgentMessage {
  id: string;
  role: AgentMessageRole;
  content: string;
  createdAt: number;
  toolCalls?: AgentToolCall[];
  warnings?: string[];
}

export interface AgentChat {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: AgentMessage[];
}

export interface AgentCollectionContext {
  id: string;
  name: string;
}
