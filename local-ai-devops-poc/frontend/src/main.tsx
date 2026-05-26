/**
 * main.tsx — Application shell and all panel components.
 *
 * Architecture: single-file for a PoC.  In a larger app, split into:
 *   src/components/Chat.tsx
 *   src/components/Rag.tsx
 *   src/components/Benchmark.tsx
 *   src/components/Health.tsx
 *   src/api.ts
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle,
  ChevronRight,
  Clock,
  Database,
  Download,
  FileText,
  MessageSquare,
  RefreshCw,
  Send,
  Server,
  Timer,
  Upload,
  XCircle,
  Zap,
} from "lucide-react";
import "./styles.css";

// ── API client ───────────────────────────────────────────────────────────────

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`${response.status} ${text}`);
  }
  return response.json();
}

// ── Types ────────────────────────────────────────────────────────────────────

type Panel = "health" | "chat" | "rag" | "benchmark" | "models";

interface HealthData {
  status: string;
  app: string;
  environment: string;
  integrations: Record<string, Record<string, unknown>>;
}

interface ChatResponse {
  provider: string;
  model: string;
  response: string;
  elapsed_ms: number;
}

interface RagSource {
  text: string;
  source: string;
  page?: number;
  score?: number;
}

interface RagQueryResponse {
  answer?: string;
  sources: RagSource[];
}

interface BenchmarkResult {
  provider: string;
  model: string;
  prompt: string;
  elapsed_ms: number;
  ok: boolean;
  response_preview?: string;
  error?: string;
}

interface BenchmarkReport {
  results: BenchmarkResult[];
  summary: Record<string, Record<string, unknown>>;
  report_path?: string;
  s3_uri?: string;
}

// ── Utility components ───────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "ok"
      ? "ok"
      : status === "degraded" || status === "unreachable"
      ? "warn"
      : status === "not_configured" || status === "not_installed"
      ? "muted"
      : "error";
  return <span className={`badge ${cls}`}>{status}</span>;
}

function Spinner() {
  return <span className="spinner" aria-label="carregando" />;
}

// ── App shell ─────────────────────────────────────────────────────────────────

function App() {
  const [panel, setPanel] = useState<Panel>("health");

  const navItems: Array<{ id: Panel; label: string; icon: React.ReactNode }> = [
    { id: "health",    label: "Health",    icon: <Activity size={15} /> },
    { id: "chat",      label: "Chat",      icon: <MessageSquare size={15} /> },
    { id: "rag",       label: "RAG",       icon: <Database size={15} /> },
    { id: "benchmark", label: "Benchmark", icon: <Timer size={15} /> },
    { id: "models",    label: "Models / S3", icon: <Server size={15} /> },
  ];

  return (
    <main className="shell">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="brand">
          <Zap size={16} />
          <span>local-ai-devops</span>
        </div>
        <div className="sidebar-section">Navigation</div>
        {navItems.map(({ id, label, icon }) => (
          <button
            key={id}
            id={`nav-${id}`}
            className={`nav-btn${panel === id ? " active" : ""}`}
            onClick={() => setPanel(id)}
            aria-current={panel === id ? "page" : undefined}
          >
            {icon} {label}
          </button>
        ))}
        <div className="sidebar-footer">
          <code>{API_URL}</code>
        </div>
      </aside>

      {/* ── Workspace ───────────────────────────────────────────────────── */}
      <section className="workspace">
        <div className="topbar">
          <span className="topbar-title">
            {navItems.find((n) => n.id === panel)?.label}
          </span>
          <div className="topbar-meta">
            <span className="poc-version">
              PoC v0.1.0
            </span>
          </div>
        </div>

        <div className="panel">
          {panel === "health"    && <HealthPanel />}
          {panel === "chat"      && <ChatPanel />}
          {panel === "rag"       && <RagPanel />}
          {panel === "benchmark" && <BenchmarkPanel />}
          {panel === "models"    && <ModelsPanel />}
        </div>
      </section>
    </main>
  );
}

// ── Health panel ──────────────────────────────────────────────────────────────

function HealthPanel() {
  const [data, setData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api<HealthData>("/health");
      setData(result);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <>
      <div className="card">
        <div className="card-header">
          <span className="card-title">System Status</span>
          <button id="btn-health-refresh" className="btn btn-ghost" onClick={refresh} disabled={loading}>
            {loading ? <Spinner /> : <RefreshCw size={12} />}
            Refresh
          </button>
        </div>
        <div className="card-body">
          {error && <div className="output has-data">{error}</div>}
          {data && (
            <div className="row row-lg-gap">
              <div className="field">
                <label>Status</label>
                <StatusBadge status={data.status} />
              </div>
              <div className="field">
                <label>App</label>
                <code>{data.app}</code>
              </div>
              <div className="field">
                <label>Environment</label>
                <code>{data.environment}</code>
              </div>
            </div>
          )}
        </div>
      </div>

      {data?.integrations && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Integrations</span>
          </div>
          <div className="card-body">
            <div className="integrations-grid">
              {Object.entries(data.integrations).map(([name, info]) => {
                const models = info.models as string[] | undefined;
                const bucket = info.bucket as string | undefined;
                const errMsg = info.error as string | undefined;
                return (
                <div key={name} className="integration-item">
                  <div className="integration-name">{name}</div>
                  <StatusBadge status={String(info.status ?? "unknown")} />
                  {models && Array.isArray(models) && (
                    <div className="integration-detail">
                      {models.join(", ") || "(no models)"}
                    </div>
                  )}
                  {bucket && (
                    <div className="integration-detail">{bucket}</div>
                  )}
                  {errMsg && (
                    <div className="integration-detail text-error">
                      {errMsg}
                    </div>
                  )}
                </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Chat panel ────────────────────────────────────────────────────────────────

const PROVIDERS = ["ollama", "local_api", "openai_compatible", "s3_artifact"];

function ChatPanel() {
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3.2");
  const [prompt, setPrompt] = useState("Resume los riesgos de operar RAG local con modelos descargados.");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [temperature, setTemperature] = useState("0.2");
  const [maxTokens, setMaxTokens] = useState("512");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify({
          provider,
          model,
          prompt,
          system_prompt: systemPrompt || undefined,
          temperature: parseFloat(temperature),
          max_tokens: parseInt(maxTokens, 10),
        }),
      });
      setResult(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Chat Request</span>
        </div>
        <div className="card-body flex-col-gap-md">
          <div className="row">
            <div className="field grow">
              <label htmlFor="chat-provider">Provider</label>
              <select id="chat-provider" name="chat-provider" value={provider} onChange={(e) => setProvider(e.target.value)} title="Provider">
                {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="field grow">
              <label htmlFor="chat-model">Model</label>
              <input id="chat-model" name="chat-model" type="text" value={model} onChange={(e) => setModel(e.target.value)} title="Model" placeholder="e.g. llama3.2" />
            </div>
            <div className="field input-w-xs">
              <label htmlFor="chat-temp">Temp</label>
              <input id="chat-temp" name="chat-temp" type="number" min="0" max="2" step="0.1" value={temperature} onChange={(e) => setTemperature(e.target.value)} title="Temperature" placeholder="0.2" />
            </div>
            <div className="field input-w-xs">
              <label htmlFor="chat-maxtokens">Max tokens</label>
              <input id="chat-maxtokens" name="chat-maxtokens" type="number" min="1" max="8192" value={maxTokens} onChange={(e) => setMaxTokens(e.target.value)} title="Max tokens" placeholder="512" />
            </div>
          </div>
          <div className="field">
            <label htmlFor="chat-system">System prompt (opcional)</label>
            <textarea id="chat-system" name="chat-system" rows={2} value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} placeholder="Eres un asistente DevOps conciso..." title="System prompt" />
          </div>
          <div className="field">
            <label htmlFor="chat-prompt">Prompt</label>
            <textarea id="chat-prompt" name="chat-prompt" rows={4} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Escribe tu prompt aquí..." title="Prompt" />
          </div>
          <div className="flex-end">
            <button id="btn-chat-run" className="btn btn-primary" onClick={submit} disabled={loading}>
              {loading ? <Spinner /> : <Send size={12} />}
              Run
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card">
          <div className="card-header">
            <span className="card-title text-error">
              <XCircle size={12} className="inline-icon-mr" />
              Error
            </span>
          </div>
          <div className="card-body">
            <div className="output has-data">{error}</div>
          </div>
        </div>
      )}

      {result && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Response</span>
            <div className="row row-sm-gap">
              <span className="badge info">{result.provider}</span>
              <span className="badge muted">{result.model}</span>
              <span className="badge ok">
                <Clock size={9} /> {result.elapsed_ms.toFixed(0)} ms
              </span>
            </div>
          </div>
          <div className="card-body">
            <div className="output has-data">{result.response}</div>
          </div>
        </div>
      )}
    </>
  );
}

// ── RAG panel ─────────────────────────────────────────────────────────────────

function RagPanel() {
  const [ingestPath, setIngestPath] = useState("data/documents");
  const [collection, setCollection] = useState("local_documents");
  const [question, setQuestion] = useState("¿Qué documentos mencionan AWS?");
  const [topK, setTopK] = useState("4");
  const [queryResult, setQueryResult] = useState<RagQueryResponse | null>(null);
  const [ingestResult, setIngestResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ingest() {
    setLoading(true);
    setError(null);
    try {
      const data = await api<{ collection: string; chunks: number }>("/rag/ingest", {
        method: "POST",
        body: JSON.stringify({ path: ingestPath, collection }),
      });
      setIngestResult(`✓ Ingestados ${data.chunks} chunks en colección "${data.collection}"`);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function query() {
    setLoading(true);
    setError(null);
    setQueryResult(null);
    try {
      const data = await api<RagQueryResponse>("/rag/query", {
        method: "POST",
        body: JSON.stringify({ question, collection, top_k: parseInt(topK, 10) }),
      });
      setQueryResult(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="card">
        <div className="card-header"><span className="card-title">Ingest Documents</span></div>
        <div className="card-body flex-col-gap-md">
          <div className="row">
            <div className="field grow">
              <label htmlFor="rag-ingest-path">Path (relativo a DOCUMENTS_PATH)</label>
              <input id="rag-ingest-path" name="rag-ingest-path" type="text" value={ingestPath} onChange={(e) => setIngestPath(e.target.value)} title="Path" placeholder="e.g. data/documents" />
            </div>
            <div className="field grow">
              <label htmlFor="rag-collection-ingest">Collection</label>
              <input id="rag-collection-ingest" name="rag-collection-ingest" type="text" value={collection} onChange={(e) => setCollection(e.target.value)} title="Collection" placeholder="e.g. local_documents" />
            </div>
          </div>
          {ingestResult && <div className="output has-data">{ingestResult}</div>}
          <div className="flex-end">
            <button id="btn-rag-ingest" className="btn btn-ghost" onClick={ingest} disabled={loading}>
              {loading ? <Spinner /> : <Upload size={12} />} Ingest
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Query</span></div>
        <div className="card-body flex-col-gap-md">
          <div className="row">
            <div className="field grow">
              <label htmlFor="rag-question">Question</label>
              <textarea id="rag-question" name="rag-question" rows={2} value={question} onChange={(e) => setQuestion(e.target.value)} title="Question" placeholder="Escribe tu pregunta..." />
            </div>
          </div>
          <div className="row">
            <div className="field grow">
              <label htmlFor="rag-collection-query">Collection</label>
              <input id="rag-collection-query" name="rag-collection-query" type="text" value={collection} onChange={(e) => setCollection(e.target.value)} title="Collection" placeholder="e.g. local_documents" />
            </div>
            <div className="field input-w-xxs">
              <label htmlFor="rag-topk">Top K</label>
              <input id="rag-topk" name="rag-topk" type="number" min="1" max="20" value={topK} onChange={(e) => setTopK(e.target.value)} title="Top K" placeholder="4" />
            </div>
          </div>
          {error && <div className="output has-data">{error}</div>}
          <div className="flex-end">
            <button id="btn-rag-query" className="btn btn-primary" onClick={query} disabled={loading}>
              {loading ? <Spinner /> : <ChevronRight size={12} />} Query
            </button>
          </div>
        </div>
      </div>

      {queryResult && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Sources</span>
            <span className="badge muted">{queryResult.sources.length} chunks</span>
          </div>
          <div className="card-body flex-col-gap-md">
            {queryResult.sources.map((src, idx) => (
              <div key={idx} className="source-item">
                <div className="row source-header">
                  <span className="source-meta">
                    [{idx + 1}] {src.source}{src.page ? ` p.${src.page}` : ""}
                  </span>
                  {src.score !== undefined && (
                    <span className="badge muted">score {src.score.toFixed(3)}</span>
                  )}
                </div>
                <div className="output has-data output-limited">{src.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ── Benchmark panel ───────────────────────────────────────────────────────────

function BenchmarkPanel() {
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3.2");
  const [prompts, setPrompts] = useState("Diagnostica latencia alta en API LLM local.\nExplica cómo funciona RAG en producción.");
  const [saveReport, setSaveReport] = useState(false);
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    setReport(null);
    const promptList = prompts.split("\n").map((p) => p.trim()).filter(Boolean);
    try {
      const data = await api<BenchmarkReport>(
        `/benchmark?save_report=${saveReport}`,
        {
          method: "POST",
          body: JSON.stringify({
            prompts: promptList,
            models: [{ provider, model, prompt: promptList[0] }],
          }),
        }
      );
      setReport(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="card">
        <div className="card-header"><span className="card-title">Benchmark Configuration</span></div>
        <div className="card-body flex-col-gap-md">
          <div className="row">
            <div className="field grow">
              <label htmlFor="bench-provider">Provider</label>
              <select id="bench-provider" name="bench-provider" value={provider} onChange={(e) => setProvider(e.target.value)} title="Provider">
                {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="field grow">
              <label htmlFor="bench-model">Model</label>
              <input id="bench-model" name="bench-model" type="text" value={model} onChange={(e) => setModel(e.target.value)} title="Model" placeholder="e.g. llama3.2" />
            </div>
            <div className="field align-self-end">
              <label htmlFor="bench-save">
                <input id="bench-save" name="bench-save" type="checkbox" checked={saveReport} onChange={(e) => setSaveReport(e.target.checked)} className="checkbox-mr" />
                Save report
              </label>
            </div>
          </div>
          <div className="field">
            <label htmlFor="bench-prompts">Prompts (1 por línea)</label>
            <textarea id="bench-prompts" name="bench-prompts" rows={4} value={prompts} onChange={(e) => setPrompts(e.target.value)} title="Prompts" placeholder="Explica cómo funciona..." />
          </div>
          {error && <div className="output has-data">{error}</div>}
          <div className="flex-end">
            <button id="btn-bench-run" className="btn btn-primary" onClick={run} disabled={loading}>
              {loading ? <Spinner /> : <Zap size={12} />} Run Benchmark
            </button>
          </div>
        </div>
      </div>

      {report && (
        <>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Summary</span>
              {report.s3_uri && <span className="badge ok">uploaded S3</span>}
            </div>
            <div className="card-body">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Avg ms</th>
                    <th>Min ms</th>
                    <th>Max ms</th>
                    <th>Success rate</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(report.summary).map(([key, stats]) => (
                    <tr key={key}>
                      <td className="primary">{key}</td>
                      <td className="ms">{typeof stats.avg_ms === "number" ? stats.avg_ms.toFixed(0) : "—"}</td>
                      <td className="ms">{typeof stats.min_ms === "number" ? stats.min_ms.toFixed(0) : "—"}</td>
                      <td className="ms">{typeof stats.max_ms === "number" ? stats.max_ms.toFixed(0) : "—"}</td>
                      <td>
                        <span className={`badge ${Number(stats.success_rate) >= 0.9 ? "ok" : Number(stats.success_rate) >= 0.5 ? "warn" : "error"}`}>
                          {(Number(stats.success_rate) * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Results</span>
              <span className="badge muted">{report.results.length} runs</span>
            </div>
            <div className="card-body card-body-p-0">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Prompt</th>
                    <th>ms</th>
                    <th>Status</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {report.results.map((r, idx) => (
                    <tr key={idx}>
                      <td className="primary">{r.model}</td>
                      <td className="muted table-cell-ellipsis-sm">{r.prompt}</td>
                      <td className="ms">{r.ok ? r.elapsed_ms.toFixed(0) : "—"}</td>
                      <td>{r.ok ? <span className="badge ok">ok</span> : <span className="badge error">fail</span>}</td>
                      <td className="muted table-cell-ellipsis-md">
                        {r.ok ? r.response_preview : r.error}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}

// ── Models / S3 panel ─────────────────────────────────────────────────────────

function ModelsPanel() {
  const [s3Prefix, setS3Prefix] = useState("");
  const [s3List, setS3List] = useState<Array<Record<string, unknown>> | null>(null);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);

  async function listS3() {
    setListLoading(true);
    setListError(null);
    try {
      const qs = s3Prefix ? `?prefix=${encodeURIComponent(s3Prefix)}` : "";
      const data = await api<{ objects: Array<Record<string, unknown>>; count: number; prefix: string }>(
        `/models/s3/list${qs}`
      );
      setS3List(data.objects);
    } catch (err) {
      setListError(String(err));
    } finally {
      setListLoading(false);
    }
  }

  return (
    <>
      <div className="card">
        <div className="card-header"><span className="card-title">S3 Artifact Browser</span></div>
        <div className="card-body flex-col-gap-md">
          <div className="row">
            <div className="field grow">
              <label htmlFor="s3-prefix">Sub-prefix (opcional: models, datasets, reports)</label>
              <input id="s3-prefix" name="s3-prefix" type="text" value={s3Prefix} onChange={(e) => setS3Prefix(e.target.value)} placeholder="models" title="Sub-prefix" />
            </div>
            <div className="align-self-end">
              <button id="btn-s3-list" className="btn btn-ghost" onClick={listS3} disabled={listLoading}>
                {listLoading ? <Spinner /> : <RefreshCw size={12} />} List
              </button>
            </div>
          </div>
          {listError && <div className="output has-data">{listError}</div>}
          {s3List && (
            <table className="results-table">
              <thead>
                <tr><th>Key</th><th>Size</th><th>Modified</th></tr>
              </thead>
              <tbody>
                {s3List.length === 0 && (
                  <tr><td colSpan={3} className="text-muted-c">No objects found</td></tr>
                )}
                {s3List.map((obj, idx) => (
                  <tr key={idx}>
                    <td className="primary font-mono-xs">{String(obj.key)}</td>
                    <td className="muted">{typeof obj.size_bytes === "number" ? `${(obj.size_bytes / 1024).toFixed(1)} KB` : "—"}</td>
                    <td className="muted text-xs">{String(obj.last_modified ?? "").slice(0, 16)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Quick Reference</span></div>
        <div className="card-body flex-col-gap-sm">
          <div className="ref-content">
            <div><strong className="text-primary-color">Upload artifact:</strong><br />
              <code>POST /models/s3/upload</code> — sube un archivo local a S3.
            </div>
            <div className="mt-8"><strong className="text-primary-color">Download artifact:</strong><br />
              <code>POST /models/s3/download</code> — descarga un objeto S3 localmente.
            </div>
            <div className="mt-8"><strong className="text-primary-color">CLI equivalente:</strong><br />
              <code>python scripts/upload_model_to_s3.py &lt;path&gt; --kind model</code>
            </div>
            <div className="mt-8"><strong className="text-primary-color">Swagger UI:</strong><br />
              <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer" className="text-accent">{API_URL}/docs</a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ── Mount ─────────────────────────────────────────────────────────────────────

createRoot(document.getElementById("root")!).render(<App />);
