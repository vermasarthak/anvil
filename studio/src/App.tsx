import React, { useState, useEffect } from 'react';
import { 
  Play, Cpu, Code, FileCode, History, Terminal as TerminalIcon, 
  Folder, File, ChevronRight, ChevronDown, CheckCircle, AlertCircle, 
  Sparkles, Zap, Shield, HelpCircle, CornerDownLeft, RefreshCw, X
} from 'lucide-react';

interface Step {
  type: string;
  data: any;
  timestamp?: string;
}

interface DiffFile {
  path: string;
  status: 'modified' | 'added' | 'deleted';
  oldContent: string;
  newContent: string;
}

interface SessionItem {
  id: string;
  title: string;
  model: string;
  created_at: number;
}

const MODEL_PRESETS = [
  { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash (Free Tier)', provider: 'google', model: 'gemini-2.5-flash', tag: '⚡ Recommended Cloud', cost: 'Free $0' },
  { id: 'ollama/qwen3-coder:14b', name: 'Qwen3 Coder 14B (Local)', provider: 'ollama', model: 'qwen3-coder:14b', tag: '🔒 100% Local', cost: 'Free $0' },
  { id: 'ollama/deepseek-v4:32b', name: 'DeepSeek V4 32B (Local)', provider: 'ollama', model: 'deepseek-v4:32b', tag: '🧠 Local Reasoning', cost: 'Free $0' },
];

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [steps, setSteps] = useState<Step[]>([]);
  const [diffs, setDiffs] = useState<DiffFile[]>([]);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'stream' | 'diff' | 'terminal' | 'history'>('stream');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(MODEL_PRESETS[0].id);
  const [apiKey, setApiKey] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>(['[System] Anvil Studio Environment Ready.']);

  const workspaceFiles = [
    {
      name: 'anvil',
      path: 'anvil',
      type: 'directory' as const,
      children: [
        { name: 'server.py', path: 'anvil/server.py', type: 'file' as const, status: 'modified' as const },
        { name: 'cli.py', path: 'anvil/cli.py', type: 'file' as const },
        {
          name: 'agent',
          path: 'anvil/agent',
          type: 'directory' as const,
          children: [
            { name: 'loop.py', path: 'anvil/agent/loop.py', type: 'file' as const },
            { name: 'verifier.py', path: 'anvil/agent/verifier.py', type: 'file' as const, status: 'added' as const },
          ],
        },
      ],
    },
    { name: 'README.md', path: 'README.md', type: 'file' as const },
    { name: 'pyproject.toml', path: 'pyproject.toml', type: 'file' as const },
  ];

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/sessions');
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch (e) {
      // Ignore
    }
  };

  useEffect(() => {
    fetchSessions();
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    socket.onopen = () => {
      setConnected(true);
      setTerminalLogs((prev) => [...prev, '[WebSocket] Connected to Anvil Engine backend.']);
    };
    socket.onclose = () => {
      setConnected(false);
      setTerminalLogs((prev) => [...prev, '[WebSocket] Disconnected from server. Retrying...']);
    };
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSteps((prev) => [...prev, { ...data, timestamp: new Date().toLocaleTimeString() }]);
      
      if (data.type === 'tool_call_start') {
        setTerminalLogs((prev) => [...prev, `[Tool Call] Executing: ${data.data.name}`]);
      } else if (data.type === 'tool_call_end') {
        setTerminalLogs((prev) => [...prev, `[Tool Result] ${data.data.output || 'Success'}`]);
      } else if (data.type === 'task_complete') {
        setIsExecuting(false);
        setTerminalLogs((prev) => [...prev, '[Task Complete] Agent finished task execution.']);
      }
      
      fetchSessions();
    };
    setWs(socket);
    return () => socket.close();
  }, []);

  const handleRun = async () => {
    if (!prompt.trim()) return;
    
    setIsExecuting(true);
    setSteps([]);
    setTerminalLogs((prev) => [...prev, `\n> User Task: ${prompt}`]);

    const activeModelConfig = MODEL_PRESETS.find((m) => m.id === selectedPreset) || MODEL_PRESETS[0];

    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: activeModelConfig.provider,
          model: activeModelConfig.model,
          api_key: apiKey,
        }),
      });
    } catch (e) {
      // Ignore
    }

    if (ws) {
      ws.send(JSON.stringify({ prompt }));
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090D16] text-slate-100 font-sans antialiased">
      {/* Sidebar: Navigation & Models */}
      <div className="w-80 border-r border-slate-800/80 bg-[#0B0F19] p-4 flex flex-col justify-between shadow-2xl z-10">
        <div>
          {/* Logo Branding */}
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800/60">
            <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-wider text-white">ANVIL</h1>
              <p className="text-[10px] text-indigo-400 font-mono tracking-widest uppercase">Autonomous Studio</p>
            </div>
          </div>

          {/* Model Selector Cards */}
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 block flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-amber-400" /> Active Model Engine
              </label>
              
              <div className="space-y-2">
                {MODEL_PRESETS.map((preset) => {
                  const isSelected = selectedPreset === preset.id;
                  return (
                    <div
                      key={preset.id}
                      onClick={() => setSelectedPreset(preset.id)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500/80 shadow-md shadow-indigo-950/50'
                          : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                          {preset.name}
                        </span>
                        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded-md border border-emerald-800/50">
                          {preset.cost}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">{preset.tag}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Optional API Key Input */}
            <div className="pt-2">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 block flex items-center gap-1">
                <Shield className="h-3 w-3 text-slate-400" /> API Key (Optional)
              </label>
              <input
                type="password"
                placeholder="Bring your own key or leave blank for free"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full rounded-lg bg-slate-900/80 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-mono text-[11px]">Backend Status</span>
          <span className={`inline-flex items-center gap-1.5 font-medium px-2 py-1 rounded-full text-[11px] ${
            connected ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/50' : 'bg-amber-950/60 text-amber-400 border border-amber-800/50'
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            {connected ? 'Engine Ready' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* Workspace Directory Bar */}
      <div className="w-64 border-r border-slate-800/80 bg-[#0B0F19]/60 p-3 overflow-y-auto">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-3 px-2 flex items-center gap-1.5">
          <Folder className="h-3.5 w-3.5 text-indigo-400" /> Workspace Files
        </div>
        <div className="space-y-1 font-mono text-xs text-slate-300">
          {workspaceFiles.map((f, i) => (
            <div key={i} className="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-slate-800/60 cursor-pointer">
              <File className="h-3.5 w-3.5 text-slate-500" />
              <span>{f.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Execution Studio */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#090D16]">
        {/* Top Header Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-slate-800/80 bg-[#0B0F19]/80 px-6 py-1">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('stream')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all ${
                activeTab === 'stream'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="h-4 w-4" /> Agent Execution Stream
            </button>
            <button
              onClick={() => setActiveTab('diff')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all ${
                activeTab === 'diff'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileCode className="h-4 w-4" /> Unified Diffs ({diffs.length})
            </button>
            <button
              onClick={() => setActiveTab('terminal')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all ${
                activeTab === 'terminal'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <TerminalIcon className="h-4 w-4" /> Terminal Output
            </button>
          </div>

          <div className="text-xs font-mono text-slate-500 flex items-center gap-2">
            <span>Local Engine Port: 8000</span>
          </div>
        </div>

        {/* Tab Body Viewports */}
        <div className="flex-1 overflow-hidden p-6">
          {activeTab === 'stream' && (
            <div className="h-full overflow-y-auto space-y-4 pr-2">
              {steps.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center border-2 border-dashed border-slate-800/80 rounded-2xl p-8 text-center bg-slate-900/20">
                  <div className="p-4 rounded-full bg-indigo-950/50 border border-indigo-800/50 mb-4 text-indigo-400">
                    <Sparkles className="h-8 w-8" />
                  </div>
                  <h3 className="text-base font-bold text-white mb-1">Anvil Studio is Idle</h3>
                  <p className="text-xs text-slate-400 max-w-sm">
                    Enter any programming task instruction below. Anvil will analyze the workspace, construct a plan, edit files, and self-verify test suites.
                  </p>
                </div>
              ) : (
                steps.map((step, idx) => (
                  <div key={idx} className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-4 shadow-lg backdrop-blur-sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800/50 font-mono">
                        {step.type}
                      </span>
                      {step.timestamp && <span className="text-[10px] font-mono text-slate-500">{step.timestamp}</span>}
                    </div>
                    <pre className="whitespace-pre-wrap text-xs font-mono text-slate-200 bg-slate-950/80 p-3 rounded-lg border border-slate-800/50 overflow-x-auto">
                      {JSON.stringify(step.data, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'diff' && (
            <div className="h-full border border-slate-800/80 rounded-2xl overflow-hidden bg-slate-950">
              <div className="p-4 text-xs font-mono text-slate-500 border-b border-slate-800">
                Active unified git diffs generated during task execution:
              </div>
              <div className="p-4 font-mono text-xs text-slate-400">
                {diffs.length === 0 ? "No active file modifications recorded yet." : JSON.stringify(diffs, null, 2)}
              </div>
            </div>
          )}

          {activeTab === 'terminal' && (
            <div className="h-full border border-slate-800/80 rounded-2xl overflow-hidden bg-[#05070D] p-4 font-mono text-xs text-emerald-400 overflow-y-auto space-y-1">
              {terminalLogs.map((log, i) => (
                <div key={i} className="leading-relaxed">{log}</div>
              ))}
            </div>
          )}
        </div>

        {/* Bottom Floating Task Input Bar */}
        <div className="p-6 border-t border-slate-800/80 bg-[#0B0F19]/90 backdrop-blur-md">
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Ask Anvil to build a feature, refactor code, or run test suites..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isExecuting && handleRun()}
              disabled={isExecuting}
              className="w-full rounded-2xl bg-slate-900 border border-slate-700/80 pl-5 pr-32 py-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/80 shadow-2xl transition-all"
            />
            <button
              onClick={handleRun}
              disabled={isExecuting || !prompt.trim()}
              className={`absolute right-2 flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-bold text-white shadow-lg transition-all ${
                isExecuting || !prompt.trim()
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 active:scale-95 shadow-indigo-500/25'
              }`}
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" /> Executing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" /> Execute
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
