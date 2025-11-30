import React from 'react';
import { Folder, File, ChevronRight, ChevronDown } from 'lucide-react';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  status?: 'modified' | 'added' | 'deleted';
}

interface FileExplorerProps {
  files: FileNode[];
  onSelectFile?: (path: string) => void;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({ files, onSelectFile }) => {
  const [openDirs, setOpenDirs] = React.useState<Record<string, boolean>>({});

  const toggleDir = (path: string) => {
    setOpenDirs((prev) => ({ ...prev, [path]: !prev[path] }));
  };

  const renderTree = (nodes: FileNode[]) => {
    return (
      <div className="space-y-0.5 pl-2 font-mono text-xs">
        {nodes.map((node) => {
          if (node.type === 'directory') {
            const isOpen = !!openDirs[node.path];
            return (
              <div key={node.path}>
                <div
                  onClick={() => toggleDir(node.path)}
                  className="flex items-center gap-1.5 py-1 px-2 rounded hover:bg-slate-800 text-slate-300 cursor-pointer select-none"
                >
                  {isOpen ? <ChevronDown className="h-3.5 w-3.5 text-slate-500" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-500" />}
                  <Folder className="h-3.5 w-3.5 text-indigo-400" />
                  <span>{node.name}</span>
                </div>
                {isOpen && node.children && renderTree(node.children)}
              </div>
            );
          }

          return (
            <div
              key={node.path}
              onClick={() => onSelectFile && onSelectFile(node.path)}
              className="flex items-center gap-1.5 py-1 px-2 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 cursor-pointer select-none"
            >
              <File className="h-3.5 w-3.5 text-slate-500 ml-4" />
              <span>{node.name}</span>
              {node.status && (
                <span
                  className={`ml-auto text-[10px] uppercase px-1 rounded font-bold ${
                    node.status === 'modified'
                      ? 'text-amber-400 bg-amber-950/50'
                      : node.status === 'added'
                      ? 'text-emerald-400 bg-emerald-950/50'
                      : 'text-rose-400 bg-rose-950/50'
                  }`}
                >
                  {node.status[0]}
                </span>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex h-full flex-col bg-slate-900 border-r border-slate-800 p-3 overflow-y-auto">
      <div className="text-xs font-semibold uppercase text-slate-400 mb-2 px-2 tracking-wider">Workspace Files</div>
      {files.length === 0 ? (
        <div className="text-xs text-slate-600 px-2">No files loaded</div>
      ) : (
        renderTree(files)
      )}
    </div>
  );
};
