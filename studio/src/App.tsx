import React, { useState, useEffect } from 'react';
import { Play, Cpu, CheckCircle, AlertCircle, Settings, Code, Terminal } from 'lucide-react';

interface Step {
  type: string;
  data: any;
}

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [steps, setSteps] = useState<Step[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('google');
  const [model, setModel] = useState('gemini-2.5-flash');

  useEffect(() => {
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSteps((prev) => [...prev, data]);
    };
    setWs(socket);
    return () => socket.close();
  }, []);

  const handleRun = () => {
    if (ws && prompt.trim()) {
      setSteps([]);
      ws.send(JSON.stringify({ prompt }));
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100">
      {/* Sidebar / Config */}
      <div className="w-80 border-r border-slate-800 bg-slate-900 p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Cpu className="h-6 w-6 text-indigo-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">Sol Studio</h1>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold uppercase text-slate-400">Model Tier / Provider</label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="mt-1 w-full rounded-md bg-slate-800 border border-slate-700 p-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="ollama">Local Model (Ollama) — Free $0</option>
                <option value="google">Google Gemini (Free Tier) — Free $0</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase text-slate-400">Model</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 w-full rounded-md bg-slate-800 border border-slate-700 p-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800 pt-4">
          <span>Engine Status</span>
          <span className={`inline-flex items-center gap-1 font-medium ${connected ? 'text-emerald-400' : 'text-amber-500'}`}>
            <span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-amber-500'}`}></span>
            {connected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* Main Execution Studio */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Workspace Panels */}
        <div className="flex-1 flex divide-x divide-slate-800 overflow-hidden">
          {/* Agent Stream Panel */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3">
            <h2 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
              <Code className="h-4 w-4" /> Autonomous Execution Stream
            </h2>

            {steps.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-lg text-slate-500">
                <p>No active execution task.</p>
                <p className="text-xs text-slate-600 mt-1">Enter a task instruction below to start Sol.</p>
              </div>
            ) : (
              steps.map((step, idx) => (
                <div key={idx} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-xs font-mono">
                  <div className="text-slate-400 font-semibold mb-1 uppercase tracking-wider text-[10px]">{step.type}</div>
                  <pre className="whitespace-pre-wrap text-slate-200">{JSON.stringify(step.data, null, 2)}</pre>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40">
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask Sol to write code, refactor a module, or create a feature..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRun()}
              className="flex-1 rounded-md bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={handleRun}
              className="flex items-center gap-1.5 rounded-md bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
            >
              <Play className="h-4 w-4 fill-white" /> Execute
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
