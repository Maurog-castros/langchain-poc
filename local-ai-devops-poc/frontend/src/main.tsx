import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, Database, MessageSquare, Timer } from "lucide-react";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

type Panel = "chat" | "rag" | "benchmark";

function App() {
  const [panel, setPanel] = useState<Panel>("chat");
  const [health, setHealth] = useState("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => response.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("offline"));
  }, []);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity size={22} />
          <span>local-ai-devops-poc</span>
        </div>
        <button className={panel === "chat" ? "active" : ""} onClick={() => setPanel("chat")}>
          <MessageSquare size={18} /> Chat
        </button>
        <button className={panel === "rag" ? "active" : ""} onClick={() => setPanel("rag")}>
          <Database size={18} /> RAG
        </button>
        <button className={panel === "benchmark" ? "active" : ""} onClick={() => setPanel("benchmark")}>
          <Timer size={18} /> Benchmark
        </button>
      </aside>

      <section className="workspace">
        <header>
          <div>
            <h1>AI DevOps Console</h1>
            <p>Backend: {health}</p>
          </div>
          <code>{API_URL}</code>
        </header>
        {panel === "chat" && <ChatPanel />}
        {panel === "rag" && <RagPanel />}
        {panel === "benchmark" && <BenchmarkPanel />}
      </section>
    </main>
  );
}

function ChatPanel() {
  const [prompt, setPrompt] = useState("Resume riesgos de operar RAG local con modelos descargados.");
  const [response, setResponse] = useState("");

  async function submit() {
    setResponse("running...");
    const result = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: "ollama", model: "llama3.2", prompt })
    });
    setResponse(JSON.stringify(await result.json(), null, 2));
  }

  return <ToolPanel title="Chat Ollama" value={prompt} setValue={setPrompt} onRun={submit} output={response} />;
}

function RagPanel() {
  const [question, setQuestion] = useState("Que documentos mencionan AWS?");
  const [response, setResponse] = useState("");

  async function submit() {
    setResponse("running...");
    const result = await fetch(`${API_URL}/rag/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, collection: "local_documents", top_k: 4 })
    });
    setResponse(JSON.stringify(await result.json(), null, 2));
  }

  return <ToolPanel title="RAG Query" value={question} setValue={setQuestion} onRun={submit} output={response} />;
}

function BenchmarkPanel() {
  const [prompt, setPrompt] = useState("Diagnostica latencia alta en API LLM local.");
  const [response, setResponse] = useState("");

  async function submit() {
    setResponse("running...");
    const result = await fetch(`${API_URL}/benchmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompts: [prompt],
        models: [{ provider: "ollama", model: "llama3.2", prompt }]
      })
    });
    setResponse(JSON.stringify(await result.json(), null, 2));
  }

  return <ToolPanel title="Benchmark" value={prompt} setValue={setPrompt} onRun={submit} output={response} />;
}

function ToolPanel(props: {
  title: string;
  value: string;
  output: string;
  setValue: (value: string) => void;
  onRun: () => void;
}) {
  return (
    <section className="tool">
      <h2>{props.title}</h2>
      <textarea value={props.value} onChange={(event) => props.setValue(event.target.value)} />
      <button className="run" onClick={props.onRun}>Run</button>
      <pre>{props.output}</pre>
    </section>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
