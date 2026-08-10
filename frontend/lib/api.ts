import type {
  BatchResult,
  ChatEvent,
  DocumentItem,
  Message,
  SessionItem,
  TopicItem,
} from "@/lib/types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(input, init);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail) && body.detail[0]?.msg)
        detail = body.detail[0].msg;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Record<string, unknown>>(`${API_URL}/health`),

  documents: {
    list: () =>
      request<{ documents: DocumentItem[]; total: number }>(`${API_URL}/api/documents`),
    upload: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<DocumentItem>(`${API_URL}/api/documents/upload`, {
        method: "POST",
        body: form,
      });
    },
    batchUpload: (files: File[]) => {
      const form = new FormData();
      for (const f of files) form.append("files", f);
      return request<BatchResult>(`${API_URL}/api/documents/batch-upload`, {
        method: "POST",
        body: form,
      });
    },
    ingestUrl: (url: string) =>
      request<DocumentItem>(`${API_URL}/api/documents/ingest-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      }),
    remove: (id: string) =>
      fetch(`${API_URL}/api/documents/${id}`, { method: "DELETE" }),
  },

  topics: {
    list: (docId?: string) => {
      const q = docId ? `?doc_id=${docId}` : "";
      return request<{ topics: TopicItem[]; total: number }>(
        `${API_URL}/api/topics${q}`
      );
    },
    extract: (docId: string) =>
      request<{ topics: TopicItem[]; total: number }>(
        `${API_URL}/api/topics/extract/${docId}`,
        { method: "POST" }
      ),
    remove: (id: string) =>
      fetch(`${API_URL}/api/topics/${id}`, { method: "DELETE" }),
  },

  sessions: {
    list: () => request<SessionItem[]>(`${API_URL}/api/sessions`),
    messages: (id: string) =>
      request<Message[]>(`${API_URL}/api/sessions/${id}/messages`),
    remove: (id: string) =>
      fetch(`${API_URL}/api/sessions/${id}`, { method: "DELETE" }),
  },
};

/** POST /api/chat and feed decoded SSE events to `onEvent`. */
export async function streamChat(
  question: string,
  sessionId: string | null,
  onEvent: (event: ChatEvent) => void
): Promise<void> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  if (!res.ok || !res.body) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data: ")) continue;
      try {
        onEvent(JSON.parse(line.slice(6)) as ChatEvent);
      } catch {
        /* skip malformed frame */
      }
    }
  }
}
