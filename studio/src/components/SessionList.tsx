import React from 'react';
import { History, MessageSquare, Clock } from 'lucide-react';

export interface SessionItem {
  id: string;
  title: string;
  model: string;
  created_at: number;
}

interface SessionListProps {
  sessions: SessionItem[];
  onSelectSession: (id: string) => void;
  activeSessionId?: string;
}

export const SessionList: React.FC<SessionListProps> = ({ sessions, onSelectSession, activeSessionId }) => {
  return (
    <div className="flex h-full flex-col bg-slate-900 border-r border-slate-800 p-3 overflow-y-auto">
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-400 mb-3 px-2 tracking-wider">
        <History className="h-4 w-4 text-indigo-400" />
        Session History
      </div>

      {sessions.length === 0 ? (
        <div className="text-xs text-slate-600 px-2 py-4 text-center">No previous sessions saved.</div>
      ) : (
        <div className="space-y-1 font-sans text-xs">
          {sessions.map((s) => {
            const isActive = s.id === activeSessionId;
            const dateStr = new Date(s.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            return (
              <div
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`p-2.5 rounded border transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-slate-800 border-indigo-500/50 text-white font-medium'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center justify-between text-[11px] mb-1">
                  <span className="truncate text-slate-200 font-semibold">{s.title || 'Untitled Task'}</span>
                  <span className="flex items-center gap-1 text-[10px] text-slate-500">
                    <Clock className="h-3 w-3" /> {dateStr}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between">
                  <span>{s.model}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
