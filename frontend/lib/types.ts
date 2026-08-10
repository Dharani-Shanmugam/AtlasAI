export interface SourceRef {
  number: number;
  text: string;
  filename: string;
  doc_id: string;
  chunk_index: number;
}

export interface DocumentItem {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  status: "pending" | "ready" | "failed";
  error?: string | null;
  chunk_count: number;
  created_at: string;
}

export interface TopicItem {
  id: string;
  doc_id: string;
  name: string;
  summary: string;
  keywords: string[];
  chunk_indices: number[];
  created_at: string;
}

export interface BatchResult {
  total: number;
  succeeded: number;
  failed: number;
  documents: DocumentItem[];
}

export interface SessionItem {
  id: string;
  title: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceRef[];
  created_at: string;
}

export type ChatEvent =
  | { type: "meta"; session_id: string; citations: SourceRef[] }
  | { type: "token"; content: string }
  | { type: "error"; message: string }
  | { type: "done"; message_id: string };
