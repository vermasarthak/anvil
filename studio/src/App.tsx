import React, { useState, useEffect } from 'react';
import { 
  Play, Cpu, Code, FileCode, History, Terminal as TerminalIcon, 
  Folder, File, ChevronRight, ChevronDown, CheckCircle, AlertCircle, 
  Shield, RefreshCw, Bot, Terminal, Users, Star, Activity, Download
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
  { id: 'google/gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'google', model: 'gemini-2.5-flash', tag: 'Cloud API', cost: 'Free Tier' },
  { id: 'ollama/qwen3-coder:14b', name: 'Qwen3 Coder 14B', provider: 'ollama', model: 'qwen3-coder:14b', tag: 'Local Ollama', cost: 'Local $0' },
  { id: 'ollama/deepseek-v4:32b', name: 'DeepSeek V4 32B', provider: 'ollama', model: 'deepseek-v4:32b', tag: 'Local Reasoning', cost: 'Local $0' },
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
  const [terminalLogs, setTerminalLogs] = useState<string[]>(['[System] Anvil Engine Environment Initialized.']);

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
      setTerminalLogs((prev) => [...prev, '[WebSocket] JSON-RPC transport established with Anvil Engine.']);
    };
    socket.onclose = () => {
      setConnected(false);
      setTerminalLogs((prev) => [...prev, '[WebSocket] Transport disconnected. Reconnecting...']);
    };
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSteps((prev) => [...prev, { ...data, timestamp: new Date().toLocaleTimeString() }]);
      
      if (data.type === 'tool_call_start') {
        setTerminalLogs((prev) => [...prev, `[Tool Subprocess] Executing tool: ${data.data.name}`]);
      } else if (data.type === 'tool_call_end') {
        setTerminalLogs((prev) => [...prev, `[Tool Subprocess] Output: ${data.data.output || 'OK'}`]);
      } else if (data.type === 'task_complete' || data.type === 'error' || data.type === 'task_limit_reached') {
        setIsExecuting(false);
        setTerminalLogs((prev) => [...prev, `[Execution Loop] Task lifecycle terminated with event: ${data.type}`]);
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
    setTerminalLogs((prev) => [...prev, `\n> Task Execution Request: ${prompt}`]);

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

  const renderStepContent = (step: Step) => {
    if (step.type === 'task_start') {
      return (
        <div className="flex items-start gap-3 p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/60 text-indigo-200 text-xs font-mono">
          <Terminal className="h-4 w-4 text-indigo-400 mt-0.5 shrink-0" />
          <div>
            <div className="font-bold text-white mb-0.5">Task Initiated</div>
            <div className="text-slate-300">"{step.data?.prompt}"</div>
          </div>
        </div>
      );
    }
    if (step.type === 'thinking') {
      return (
        <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 text-xs">
          <Bot className="h-4 w-4 text-purple-400 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <div className="font-bold text-purple-300 font-mono">Agent Reasoning</div>
            <div className="whitespace-pre-wrap font-sans text-slate-300 leading-relaxed">{step.data?.content}</div>
          </div>
        </div>
      );
    }
    if (step.type === 'tool_call_start') {
      return (
        <div className="p-3 rounded-lg bg-slate-900/80 border border-amber-900/50 text-xs font-mono">
          <div className="flex items-center gap-2 font-bold text-amber-400 mb-1">
            <Code className="h-3.5 w-3.5" /> Tool Dispatch: {step.data?.name}
          </div>
          <pre className="text-slate-300 bg-slate-950 p-2 rounded border border-slate-800/60 overflow-x-auto">
            {JSON.stringify(step.data?.arguments, null, 2)}
          </pre>
        </div>
      );
    }
    if (step.type === 'tool_call_end') {
      const isSuccess = step.data?.success;
      return (
        <div className={`p-3 rounded-lg border text-xs font-mono ${isSuccess ? 'bg-emerald-950/30 border-emerald-800/50' : 'bg-rose-950/30 border-rose-800/50'}`}>
          <div className={`flex items-center gap-2 font-bold mb-1 ${isSuccess ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isSuccess ? <CheckCircle className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}
            Execution Result: {step.data?.name}
          </div>
          <pre className="text-slate-300 bg-slate-950 p-2 rounded border border-slate-800/60 overflow-x-auto whitespace-pre-wrap">
            {step.data?.output}
          </pre>
        </div>
      );
    }
    if (step.type === 'error') {
      return (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-700/80 text-rose-200 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold text-rose-300 text-sm font-mono">
            <AlertCircle className="h-4 w-4 text-rose-400" /> Runtime Exception
          </div>
          <div className="font-mono bg-slate-950/80 p-3 rounded-lg border border-rose-900/50 whitespace-pre-wrap text-rose-300">
            {step.data?.error}
          </div>
        </div>
      );
    }

    return (
      <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/60 text-xs font-mono">
        <div className="text-slate-400 font-bold mb-1 uppercase tracking-wider text-[10px]">{step.type}</div>
        <pre className="whitespace-pre-wrap text-slate-200">{JSON.stringify(step.data, null, 2)}</pre>
      </div>
    );
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090D16] text-slate-100 font-sans antialiased">
      {/* Sidebar: Navigation & Models */}
      <div className="w-80 border-r border-slate-800/80 bg-[#0B0F19] p-4 flex flex-col justify-between shadow-2xl z-10">
        <div>
          {/* Minecraft / CurseForge Inspired Pixel-Art Anvil Logo */}
          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-800/60">
            <div className="relative p-1 rounded-xl bg-slate-900 border border-indigo-500/40 shadow-lg shadow-indigo-500/10 group overflow-hidden">
              <img src="/logo.jpg" alt="Anvil Logo" className="h-10 w-10 object-cover rounded-lg transform group-hover:scale-105 transition-transform" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-xl font-black tracking-wider text-white font-mono">ANVIL</h1>
                <span className="text-[9px] bg-indigo-500/20 text-indigo-300 font-mono px-1.5 py-0.2 rounded border border-indigo-500/30">v1.2</span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono tracking-widest uppercase">Agentic Workspace</p>
            </div>
          </div>

          {/* Active Community Stats Badge */}
          <div className="mb-5 p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] font-mono flex items-center justify-between text-slate-400">
            <div className="flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-indigo-400" />
              <span>1.4k Active Devs</span>
            </div>
            <div className="flex items-center gap-1">
              <Star className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
              <span className="text-white font-bold">2.8k</span>
            </div>
          </div>

          {/* Model Selector Cards */}
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 block font-mono">
                Model Router Configuration
              </label>
              
              <div className="space-y-2">
                {MODEL_PRESETS.map((preset) => {
                  const isSelected = selectedPreset === preset.id;
                  return (
                    <div
                      key={preset.id}
                      onClick={() => setSelectedPreset(preset.id)}
                      className={`p-3 rounded-lg border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-slate-800/90 border-indigo-500/80 shadow-sm'
                          : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-bold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                          {preset.name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                          {preset.cost}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">{preset.tag}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Optional API Key Input */}
            <div className="pt-2">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1 block flex items-center gap-1 font-mono">
                <Shield className="h-3 w-3 text-slate-400" /> API Key (Environment Fallback)
              </label>
              <input
                type="password"
                placeholder="Optional provider API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full rounded-lg bg-slate-900/80 border border-slate-800 px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-mono text-[11px]">System Status</span>
          <span className={`inline-flex items-center gap-1.5 font-medium px-2.5 py-1 rounded text-[11px] font-mono ${
            connected ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/50' : 'bg-amber-950/60 text-amber-400 border border-amber-800/50'
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            {connected ? 'CONNECTED' : 'CONNECTING'}
          </span>
        </div>
      </div>

      {/* Workspace Directory Bar */}
      <div className="w-64 border-r border-slate-800/80 bg-[#0B0F19]/60 p-3 overflow-y-auto font-mono text-xs">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-3 px-2 flex items-center gap-1.5">
          <Folder className="h-3.5 w-3.5 text-indigo-400" /> Repository Files
        </div>
        <div className="space-y-1 text-slate-300">
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
        <div className="flex items-center justify-between border-b border-slate-800/80 bg-[#0B0F19]/80 px-6 py-1 font-mono">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('stream')}
              className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all ${
                activeTab === 'stream'
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="h-4 w-4" /> Agent Event Stream
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
              <TerminalIcon className="h-4 w-4" /> Server Audit Log
            </button>
          </div>

          <div className="text-xs text-slate-500 flex items-center gap-2">
            <span>Port: 8000</span>
          </div>
        </div>

        {/* Tab Body Viewports */}
        <div className="flex-1 overflow-hidden p-6">
          {activeTab === 'stream' && (
            <div className="h-full overflow-y-auto space-y-4 pr-2">
              {steps.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center border border-slate-800 rounded-xl p-8 text-center bg-slate-900/10">
                  <Cpu className="h-8 w-8 text-slate-600 mb-3" />
                  <h3 className="text-sm font-bold text-slate-300 mb-1 font-mono">Agent Engine Idle</h3>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Specify task instruction below. Anvil will execute tool calls and generate verified code.
                  </p>
                </div>
              ) : (
                steps.map((step, idx) => (
                  <div key={idx}>
                    {renderStepContent(step)}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'diff' && (
            <div className="h-full border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
              <div className="p-3 text-xs font-mono text-slate-500 border-b border-slate-800">
                Unified Diff Inspection Output:
              </div>
              <div className="p-4 font-mono text-xs text-slate-400">
                {diffs.length === 0 ? "No active file modifications recorded." : JSON.stringify(diffs, null, 2)}
              </div>
            </div>
          )}

          {activeTab === 'terminal' && (
            <div className="h-full border border-slate-800 rounded-xl overflow-hidden bg-[#05070D] p-4 font-mono text-xs text-emerald-400 overflow-y-auto space-y-1">
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
              placeholder="Execute agentic instruction (e.g., refactor module, run pytest)..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isExecuting && handleRun()}
              disabled={isExecuting}
              className="w-full rounded-xl bg-slate-900 border border-slate-700/80 pl-5 pr-32 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/80 font-mono shadow-xl transition-all"
            />
            <button
              onClick={handleRun}
              disabled={isExecuting || !prompt.trim()}
              className={`absolute right-2 flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold text-white transition-all font-mono ${
                isExecuting || !prompt.trim()
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 active:scale-95'
              }`}
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" /> RUNNING
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-white" /> RUN
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
