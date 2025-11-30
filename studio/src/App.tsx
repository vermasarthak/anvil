import React, { useState, useEffect } from 'react';
import { Play, Cpu, Code, Layers, FileCode } from 'lucide-react';
import { DiffViewer, DiffFile } from './components/DiffViewer';
import { FileExplorer, FileNode } from './components/FileExplorer';

interface Step {
  type: string;
  data: any;
}

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [steps, setSteps] = useState<Step[]>([]);
  const [diffs, setDiffs] = useState<DiffFile[]>([]);
  const [activeTab, setActiveTab] = useState<'stream' | 'diff'>('stream');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('google');
  const [model, setModel] = useState('gemini-2.5-flash');

  const workspaceFiles: FileNode[] = [
    {
      name: 'sol',
      path: 'sol',
      type: 'directory',
      children: [
        { name: 'server.py', path: 'sol/server.py', type: 'file', status: 'modified' },
        { name: 'cli.py', path: 'sol/cli.py', type: 'file' },
        {
          name: 'agent',
          path: 'sol/agent',
          type: 'directory',
          children: [
            { name: 'loop.py', path: 'sol/agent/loop.py', type: 'file' },
            { name: 'verifier.py', path: 'sol/agent/verifier.py', type: 'file', status: 'added' },
          ],
        },
      ],
    },
    { name: 'README.md', path: 'README.md', type: 'file' },
  ];

  useEffect(() => {
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSteps((prev) => [...prev, data]);
      
      if (data.type === 'tool_call_end' && data.data?.name === 'edit_file') {
        setDiffs((prev) => [
          ...prev,
          {
            path: 'sol/server.py',
            status: 'modified',
            oldContent: '# Previous server code snippet',
            newContent: data.data.output || '# Updated code snippet',
          },
        ]);
      }
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
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar / Model Selector */}
      <div className="w-72 border-r border-slate-800 bg-slate-900 p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Cpu className="h-6 w-6 text-indigo-400" />
            <h1 className="text-lg font-bold tracking-tight text-white">Sol Studio</h1>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-[11px] font-semibold uppercase text-slate-400">Model Tier / Provider</label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="mt-1 w-full rounded bg-slate-800 border border-slate-700 p-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="ollama">Local Model (Ollama) — Free $0</option>
                <option value="google">Google Gemini (Free Tier) — Free $0</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold uppercase text-slate-400">Model Name</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 w-full rounded bg-slate-800 border border-slate-700 p-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800 pt-4">
          <span>Status</span>
          <span className={`inline-flex items-center gap-1 font-medium ${connected ? 'text-emerald-400' : 'text-amber-500'}`}>
            <span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-amber-500'}`} />
            {connected ? 'Connected' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* File Explorer Tree Panel */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/50">
        <FileExplorer files={workspaceFiles} />
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Workspace Tab Header */}
        <div className="flex items-center border-b border-slate-800 bg-slate-900/80 px-4">
          <button
            onClick={() => setActiveTab('stream')}
            className={`flex items-center gap-1.5 px-4 py-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'stream'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code className="h-4 w-4" /> Agent Execution Stream
          </button>
          <button
            onClick={() => setActiveTab('diff')}
            className={`flex items-center gap-1.5 px-4 py-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === 'diff'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode className="h-4 w-4" /> Real-time Diffs ({diffs.length})
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'stream' ? (
            <div className="h-full p-4 overflow-y-auto space-y-3">
              {steps.length === 0 ? (
                <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-lg text-slate-500">
                  <p className="text-sm">No active execution task.</p>
                  <p className="text-xs text-slate-600 mt-1">Enter a task prompt below to launch Sol.</p>
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
          ) : (
            <DiffViewer files={diffs} />
          )}
        </div>

        {/* Prompt Input Bar */}
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
