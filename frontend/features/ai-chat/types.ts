export interface Citation {
  id: string;
  title: string;
  source: string;
  excerpt: string;
}

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  citations?: Citation[];
  fileRef?: string;       // filename of attached file, if any
  isStreaming?: boolean;  // true while the assistant is mid-stream
  createdAt: Date;
}
