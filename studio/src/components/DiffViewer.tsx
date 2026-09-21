import React, { useState } from 'react';

export interface DiffFile {
  path: string;
  status: 'modified' | 'added' | 'deleted';
  oldContent: string;
  newContent: string;
}

interface DiffViewerProps {
  files: DiffFile[];
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ files }) => {
  const [selectedPath, setSelectedPath] = useState<string>(files[0]?.path || '');
  const activeFile = files.find((f) => f.path === selectedPath) || files[0];

  if (!files.length) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-slate-500">
        <p className="text-sm">No active file diffs generated yet.</p>
        <p className="text-xs text-slate-600 mt-1">Edits performed by Anvil will appear here in real time.</p>
      </div>
    );
  }

  const renderUnifiedLines = (oldText: string, newText: string) => {
    const oldLines = oldText ? oldText.split('\n') : [];
    const newLines = newText ? newText.split('\n') : [];
    
    return (
      <div className="font-mono text-xs leading-relaxed">
        {oldLines.map((line, idx) => (
          <div key={`old-${idx}`} className="bg-rose-950/40 text-rose-300 px-3 py-0.5 border-l-2 border-rose-500 flex">
            <span className="w-10 select-none text-slate-600">{idx + 1}</span>
            <span className="select-none text-rose-500 mr-2">-</span>
            <span>{line}</span>
          </div>
        ))}
        {newLines.map((line, idx) => (
          <div key={`new-${idx}`} className="bg-emerald-950/40 text-emerald-300 px-3 py-0.5 border-l-2 border-emerald-500 flex">
            <span className="w-10 select-none text-slate-600">{idx + 1}</span>
            <span className="select-none text-emerald-500 mr-2">+</span>
            <span>{line}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex h-full flex-col bg-slate-950 border-l border-slate-800">
      <div className="flex items-center gap-2 border-b border-slate-800 bg-slate-900/50 px-4 py-2 overflow-x-auto">
        {files.map((file) => (
          <button
            key={file.path}
            onClick={() => setSelectedPath(file.path)}
            className={`flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-mono transition-colors ${
              selectedPath === file.path
                ? 'bg-slate-800 text-white font-medium'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                file.status === 'added'
                  ? 'bg-emerald-400'
                  : file.status === 'deleted'
                  ? 'bg-rose-400'
                  : 'bg-amber-400'
              }`}
            />
            {file.path}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {activeFile && (
          <div className="rounded border border-slate-800 bg-slate-900/30 overflow-hidden">
            <div className="bg-slate-900 px-3 py-1.5 text-xs font-mono text-slate-400 border-b border-slate-800 flex justify-between">
              <span>{activeFile.path}</span>
              <span className="uppercase text-[10px] tracking-wider">{activeFile.status}</span>
            </div>
            {renderUnifiedLines(activeFile.oldContent, activeFile.newContent)}
          </div>
        )}
      </div>
    </div>
  );
};
