"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

type Message = {
  role: "assistant" | "user";
  content: string;
};

const initialMessages: Message[] = [
  {
    role: "assistant",
    content:
      "Upload documents into a project, then ask questions here. I will answer from the project context and show sources on the right.",
  },
];

type ChatSession = {
  chat_id: string;
  project_id: string;
  title: string | null;
  created_at: string;
  updated_at?: string;
};

type ImportedDocument = {
  document_id: string;
  project_id: string;
  filename: string;
  content_type: string | null;
  uploaded_at?: string;
  status: string;
  page_count: number;
  chunk_count: number;
};

type Source = {
  id: string;
  text?: string;
  distance?: number | null;
  metadata?: {
    filename?: string;
    page?: number;
    chunk_index?: number;
    document_id?: string;
    project_id?: string;
  };
};

const PROJECT_ID = "default";
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [chat, setChat] = useState<ChatSession | null>(null);
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [documents, setDocuments] = useState<ImportedDocument[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isStartingChat, setIsStartingChat] = useState(true);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSend = Boolean(chat?.chat_id) && !isSending && !isLoadingWorkspace;
  const activeChatTitle = chat?.title || "Document chat";
  const statusText = useMemo(() => {
    if (isStartingChat) {
      return "Loading workspace...";
    }

    if (isUploading) {
      return "Indexing document...";
    }

    if (isSending) {
      return "Retrieving document context...";
    }

    if (documents.length === 0) {
      return "Upload a document to build context";
    }

    return `${documents.length} indexed document${documents.length === 1 ? "" : "s"}`;
  }, [documents.length, isSending, isStartingChat, isUploading]);

  useEffect(() => {
    let ignore = false;

    async function loadWorkspace() {
      setIsLoadingWorkspace(true);
      setIsStartingChat(true);
      setError(null);

      try {
        const [chatsResponse, documentsResponse] = await Promise.all([
          fetch(`${API_BASE}/chat?project_id=${PROJECT_ID}`),
          fetch(`${API_BASE}/file?project_id=${PROJECT_ID}`),
        ]);

        if (!chatsResponse.ok) {
          throw new Error(`Chat list failed with ${chatsResponse.status}`);
        }

        if (!documentsResponse.ok) {
          throw new Error(`Document list failed with ${documentsResponse.status}`);
        }

        const chatsResult = (await chatsResponse.json()) as { chats: ChatSession[] };
        const documentsResult = (await documentsResponse.json()) as {
          documents: ImportedDocument[];
        };

        let nextChats = chatsResult.chats || [];
        let nextChat = nextChats[0] || null;

        if (!nextChat) {
          nextChat = await createChat();
          nextChats = [nextChat];
        }

        if (!ignore) {
          setChats(nextChats);
          setChat(nextChat);
          setDocuments(documentsResult.documents || []);
        }
      } catch (setupError) {
        if (!ignore) {
          setError(getErrorMessage(setupError, "Could not load the workspace."));
        }
      } finally {
        if (!ignore) {
          setIsStartingChat(false);
          setIsLoadingWorkspace(false);
        }
      }
    }

    loadWorkspace();

    return () => {
      ignore = true;
    };
  }, []);

  async function createChat() {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_id: PROJECT_ID,
        title: "Document chat",
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat setup failed with ${response.status}`);
    }

    return (await response.json()) as ChatSession;
  }

  async function startNewChat() {
    if (isStartingChat) {
      return;
    }

    setIsStartingChat(true);
    setError(null);

    try {
      const nextChat = await createChat();
      setChats((current) => [nextChat, ...current]);
      setChat(nextChat);
      setSources([]);
      setMessages(initialMessages);
    } catch (chatError) {
      setError(getErrorMessage(chatError, "Could not create a new chat."));
    } finally {
      setIsStartingChat(false);
    }
  }

  function selectChat(nextChat: ChatSession) {
    setChat(nextChat);
    setSources([]);
    setMessages(initialMessages);
    setError(null);
  }

  async function refreshDocuments() {
    const response = await fetch(`${API_BASE}/file?project_id=${PROJECT_ID}`);

    if (!response.ok) {
      throw new Error(`Document list failed with ${response.status}`);
    }

    const result = (await response.json()) as { documents: ImportedDocument[] };
    setDocuments(result.documents || []);
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = message.trim();

    if (!trimmed || !chat || isSending) {
      return;
    }

    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setMessage("");
    setIsSending(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/chat/${chat.chat_id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: trimmed,
          top_k: 5,
        }),
      });

      if (!response.ok) {
        throw new Error(`Message failed with ${response.status}`);
      }

      const result = (await response.json()) as {
        answer: string;
        sources?: Source[];
      };

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: result.answer,
        },
      ]);
      setSources(result.sources || []);
    } catch (sendError) {
      setError(getErrorMessage(sendError, "Could not send the message."));
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "I could not reach the chat endpoint. Check that the FastAPI server is running.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  async function uploadDocument(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file || isUploading) {
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const body = new FormData();
      body.append("file", file);

      const params = new URLSearchParams({
        project_id: PROJECT_ID,
      });

      if (chat?.chat_id) {
        params.set("chat_id", chat.chat_id);
      }

      const response = await fetch(`${API_BASE}/file/import?${params.toString()}`, {
        method: "POST",
        body,
      });

      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(detail || `Upload failed with ${response.status}`);
      }

      const importedDocument = (await response.json()) as ImportedDocument;
      await refreshDocuments();
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: `${importedDocument.filename} is indexed with ${importedDocument.chunk_count} chunks.`,
        },
      ]);
    } catch (uploadError) {
      setError(getErrorMessage(uploadError, "Could not upload and index the document."));
    } finally {
      setIsUploading(false);
    }
  }

  async function deleteDocument(documentId: string) {
    if (deletingDocumentId) {
      return;
    }

    setDeletingDocumentId(documentId);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/file/${documentId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(detail || `Delete failed with ${response.status}`);
      }

      setDocuments((current) => current.filter((document) => document.document_id !== documentId));
      setSources((current) =>
        current.filter((source) => source.metadata?.document_id !== documentId),
      );
    } catch (deleteError) {
      setError(getErrorMessage(deleteError, "Could not delete the document."));
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <main className="h-screen overflow-hidden bg-[#0f1115] text-[#e7e9ee]">
      <div className="grid h-full grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_320px]">
        <aside className="hidden min-h-0 flex-col border-r border-white/10 bg-[#13161c] lg:flex">
          <div className="border-b border-white/10 px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold">Local RAG</p>
                <p className="text-xs text-[#8c93a3]">Connected workspace</p>
              </div>
              <button
                className="grid h-8 w-8 place-items-center rounded-md border border-white/10 bg-white/[0.04] text-lg leading-none hover:bg-white/[0.08]"
                type="button"
                onClick={startNewChat}
                disabled={isStartingChat}
              >
                +
              </button>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
            <div className="mb-3 flex items-center justify-between px-1">
              <p className="text-xs font-medium uppercase tracking-wide text-[#8c93a3]">
                Projects
              </p>
              <span className="text-xs text-[#7f8798]">Live</span>
            </div>

            <div className="space-y-1">
              <button className="w-full rounded-md bg-white/[0.08] px-3 py-2 text-left text-sm text-white transition">
                <span className="block truncate font-medium">Default project</span>
                <span className="text-xs text-[#7f8798]">{statusText}</span>
              </button>
            </div>

            <div className="mt-6 mb-3 flex items-center justify-between px-1">
              <p className="text-xs font-medium uppercase tracking-wide text-[#8c93a3]">
                Chats
              </p>
              <button
                className="text-xs text-[#b8becd] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                onClick={startNewChat}
                disabled={isStartingChat}
              >
                New
              </button>
            </div>

            <div className="space-y-1">
              {chats.map((item) => (
                <button
                  key={item.chat_id}
                  className={`w-full truncate rounded-md px-3 py-2 text-left text-sm transition ${
                    item.chat_id === chat?.chat_id
                      ? "bg-[#263044] text-white"
                      : "text-[#b8becd] hover:bg-white/[0.05] hover:text-white"
                  }`}
                  type="button"
                  onClick={() => selectChat(item)}
                >
                  {item.title || "Document chat"}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-white/10 p-3">
            <button className="w-full rounded-md border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-[#d6dae4] hover:bg-white/[0.08]">
              Settings
            </button>
          </div>
        </aside>

        <section className="flex min-w-0 flex-col bg-[#0f1115]">
          <header className="flex h-14 items-center justify-between border-b border-white/10 px-5">
            <div className="min-w-0">
              <h1 className="truncate text-sm font-semibold">{activeChatTitle}</h1>
              <p className="truncate text-xs text-[#8c93a3]">
                {statusText}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <label className="cursor-pointer rounded-md border border-white/10 bg-white/[0.04] px-3 py-1.5 text-sm text-[#d6dae4] hover:bg-white/[0.08]">
                {isUploading ? "Indexing" : "Upload"}
                <input
                  className="sr-only"
                  type="file"
                  onChange={uploadDocument}
                  disabled={isUploading}
                />
              </label>
            </div>
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
            <div className="mx-auto flex max-w-3xl flex-col gap-5">
              {error && (
                <div className="rounded-md border border-[#7f423f] bg-[#321d1d] px-4 py-3 text-sm text-[#ffd8d5]">
                  {error}
                </div>
              )}
              {messages.map((item, index) => (
                <article
                  key={`${item.role}-${index}`}
                  className={`flex ${item.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[78%] rounded-lg border px-4 py-3 text-sm leading-6 ${
                      item.role === "user"
                        ? "border-[#3f5f91] bg-[#22314a] text-white"
                        : "border-white/10 bg-[#171a21] text-[#dce0ea]"
                    }`}
                  >
                    {item.content}
                  </div>
                </article>
              ))}
              {isSending && (
                <article className="flex justify-start">
                  <div className="max-w-[78%] rounded-lg border border-white/10 bg-[#171a21] px-4 py-3 text-sm leading-6 text-[#aeb5c4]">
                    Thinking with the indexed context...
                  </div>
                </article>
              )}
            </div>
          </div>

          <form onSubmit={sendMessage} className="border-t border-white/10 p-4">
            <div className="mx-auto flex max-w-3xl items-end gap-3 rounded-lg border border-white/10 bg-[#171a21] p-2">
              <textarea
                className="max-h-36 min-h-12 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-6 text-white outline-none placeholder:text-[#70798c]"
                placeholder="Ask about this project..."
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                disabled={!canSend}
              />
              <button
                className="h-10 rounded-md bg-[#e7e9ee] px-4 text-sm font-medium text-[#111318] hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!canSend || !message.trim()}
              >
                {isSending ? "Sending" : "Send"}
              </button>
            </div>
          </form>
        </section>

        <aside className="hidden min-h-0 flex-col border-l border-white/10 bg-[#13161c] lg:flex">
          <div className="border-b border-white/10 px-4 py-3">
            <p className="text-sm font-semibold">Project context</p>
            <p className="text-xs text-[#8c93a3]">Documents and retrieved sources</p>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <section>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-xs font-medium uppercase tracking-wide text-[#8c93a3]">
                  Documents
                </h2>
                <span className="rounded bg-white/[0.06] px-2 py-0.5 text-xs text-[#aeb5c4]">
                  {documents.length}
                </span>
              </div>
              <div className="space-y-2">
                {documents.length === 0 && (
                  <p className="rounded-md border border-white/10 bg-white/[0.03] p-3 text-sm text-[#8c93a3]">
                    No indexed documents yet.
                  </p>
                )}
                {documents.map((document) => (
                  <div
                    key={document.document_id}
                    className="rounded-md border border-white/10 bg-white/[0.03] p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="min-w-0 truncate text-sm font-medium text-[#eef1f7]">
                        {document.filename}
                      </p>
                      <button
                        className="shrink-0 rounded border border-white/10 px-2 py-0.5 text-xs text-[#aeb5c4] hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                        type="button"
                        onClick={() => deleteDocument(document.document_id)}
                        disabled={deletingDocumentId === document.document_id}
                      >
                        {deletingDocumentId === document.document_id ? "..." : "Remove"}
                      </button>
                    </div>
                    <p className="mt-1 text-xs text-[#8c93a3]">
                      {document.chunk_count} chunks - {document.status}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            <section className="mt-7">
              <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-[#8c93a3]">
                Sources
              </h2>
              <div className="space-y-3">
                {sources.length === 0 && (
                  <p className="rounded-md border border-white/10 bg-[#171a21] p-3 text-sm text-[#8c93a3]">
                    Sources will appear after an answer uses retrieved context.
                  </p>
                )}
                {sources.map((source, index) => (
                  <div
                    key={`${source.id}-${index}`}
                    className="rounded-md border border-white/10 bg-[#171a21] p-3"
                  >
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <p className="truncate text-sm font-medium">
                        {source.metadata?.filename || source.metadata?.document_id || source.id}
                      </p>
                      <span className="shrink-0 rounded bg-[#263044] px-2 py-0.5 text-xs text-[#c8d3ee]">
                        {formatSourceBadge(source)}
                      </span>
                    </div>
                    <p className="text-xs leading-5 text-[#aeb5c4]">
                      {source.text || `Chunk ${source.metadata?.chunk_index ?? "unknown"}`}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </aside>
      </div>
    </main>
  );
}

function formatSourceBadge(source: Source) {
  if (source.metadata?.page) {
    return `p. ${source.metadata.page}`;
  }

  if (typeof source.distance === "number") {
    return source.distance.toFixed(2);
  }

  return "source";
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

async function readErrorDetail(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail;
  } catch {
    return null;
  }
}
