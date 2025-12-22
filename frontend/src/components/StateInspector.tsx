/**
 * State Inspector Component
 * 
 * Time-travel debugging UI for agent chain execution state
 * Features:
 * - Real-time state tree visualization
 * - Context snapshot browser
 * - Execution history timeline
 * - State diff viewer
 */

import React, { useState, useEffect } from 'react';
import {
  Clock, Database, GitBranch, Search, Filter, Download,
  ChevronRight, ChevronDown, PlayCircle, PauseCircle, SkipBack
} from 'lucide-react';
import { useAppStore } from '@/store';

interface StateSnapshot {
  timestamp: number;
  executionId: string;
  stepIndex: number;
  state: Record<string, any>;
  context: Record<string, any>;
  metadata: Record<string, any>;
}

export const StateInspector: React.FC = () => {
  const [snapshots, setSnapshots] = useState<StateSnapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<StateSnapshot | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());
  const [isLive, setIsLive] = useState(true);

  const {
    executions,
    workflows
  } = useAppStore();

  // Load snapshots from execution history
  useEffect(() => {
    if (isLive) {
      loadLatestSnapshots();
      const interval = setInterval(loadLatestSnapshots, 2000);
      return () => clearInterval(interval);
    }
  }, [isLive, executions]);

  const loadLatestSnapshots = () => {
    // Convert executions to snapshots
    const newSnapshots: StateSnapshot[] = [];
    
    Object.values(executions).forEach((execution: any) => {
      if (execution.steps) {
        execution.steps.forEach((step: any, index: number) => {
          newSnapshots.push({
            timestamp: step.startedAt || Date.now(),
            executionId: execution.id,
            stepIndex: index,
            state: step.state || {},
            context: step.context || {},
            metadata: {
              status: step.status,
              agentType: step.agentType,
              duration: step.duration
            }
          });
        });
      }
    });

    setSnapshots(newSnapshots.sort((a, b) => b.timestamp - a.timestamp));
    
    // Auto-select latest if none selected
    if (!selectedSnapshot && newSnapshots.length > 0) {
      setSelectedSnapshot(newSnapshots[0]);
    }
  };

  const toggleKey = (key: string) => {
    const newExpanded = new Set(expandedKeys);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedKeys(newExpanded);
  };

  const renderValue = (value: any, path: string): React.ReactNode => {
    if (value === null) return <span className="text-gray-400">null</span>;
    if (value === undefined) return <span className="text-gray-400">undefined</span>;
    
    const type = typeof value;
    
    if (type === 'string') {
      return <span className="text-green-600">"{value}"</span>;
    }
    
    if (type === 'number') {
      return <span className="text-blue-600">{value}</span>;
    }
    
    if (type === 'boolean') {
      return <span className="text-purple-600">{value.toString()}</span>;
    }
    
    if (Array.isArray(value)) {
      const isExpanded = expandedKeys.has(path);
      return (
        <div>
          <button
            onClick={() => toggleKey(path)}
            className="flex items-center gap-1 text-gray-700 hover:text-blue-600"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <span className="text-gray-500">[{value.length}]</span>
          </button>
          {isExpanded && (
            <div className="ml-6 mt-1 space-y-1">
              {value.map((item, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="text-gray-400">{index}:</span>
                  {renderValue(item, `${path}.${index}`)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
    
    if (type === 'object') {
      const isExpanded = expandedKeys.has(path);
      const keys = Object.keys(value);
      
      return (
        <div>
          <button
            onClick={() => toggleKey(path)}
            className="flex items-center gap-1 text-gray-700 hover:text-blue-600"
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <span className="text-gray-500">{`{${keys.length}}`}</span>
          </button>
          {isExpanded && (
            <div className="ml-6 mt-1 space-y-1">
              {keys.map((key) => (
                <div key={key} className="flex items-start gap-2">
                  <span className="text-gray-700 font-medium">{key}:</span>
                  {renderValue(value[key], `${path}.${key}`)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
    
    return <span className="text-gray-600">{String(value)}</span>;
  };

  const filteredSnapshots = snapshots.filter(snapshot => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      snapshot.executionId.toLowerCase().includes(query) ||
      snapshot.metadata.agentType?.toLowerCase().includes(query) ||
      JSON.stringify(snapshot.state).toLowerCase().includes(query)
    );
  });

  const exportSnapshot = () => {
    if (!selectedSnapshot) return;
    
    const blob = new Blob(
      [JSON.stringify(selectedSnapshot, null, 2)],
      { type: 'application/json' }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `snapshot-${selectedSnapshot.executionId}-${selectedSnapshot.stepIndex}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="text-blue-600" size={24} />
            <div>
              <h2 className="text-xl font-bold text-gray-900">State Inspector</h2>
              <p className="text-sm text-gray-600">Time-travel debugging & context viewer</p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsLive(!isLive)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg font-medium ${
                isLive
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {isLive ? <PlayCircle size={18} /> : <PauseCircle size={18} />}
              {isLive ? 'Live' : 'Paused'}
            </button>
            
            {selectedSnapshot && (
              <button
                onClick={exportSnapshot}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Download size={18} />
                Export
              </button>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="mt-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={20} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search snapshots by execution ID, agent type, or state..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Timeline (Left) */}
        <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Timeline ({filteredSnapshots.length})
            </h3>
            
            <div className="space-y-2">
              {filteredSnapshots.map((snapshot, index) => (
                <button
                  key={`${snapshot.executionId}-${snapshot.stepIndex}`}
                  onClick={() => setSelectedSnapshot(snapshot)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedSnapshot === snapshot
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-gray-500">
                      {new Date(snapshot.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      snapshot.metadata.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : snapshot.metadata.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {snapshot.metadata.status}
                    </span>
                  </div>
                  
                  <div className="flex items-center gap-2 mb-1">
                    <GitBranch size={14} className="text-gray-400" />
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {snapshot.metadata.agentType || `Step ${snapshot.stepIndex}`}
                    </span>
                  </div>
                  
                  <div className="text-xs text-gray-500 truncate">
                    {snapshot.executionId}
                  </div>
                </button>
              ))}
              
              {filteredSnapshots.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Database size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No snapshots found</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* State Viewer (Right) */}
        <div className="flex-1 overflow-y-auto">
          {selectedSnapshot ? (
            <div className="p-6 space-y-6">
              {/* Metadata */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Metadata</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Execution ID:</span>
                    <p className="font-mono text-gray-900">{selectedSnapshot.executionId}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Step Index:</span>
                    <p className="font-mono text-gray-900">{selectedSnapshot.stepIndex}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Timestamp:</span>
                    <p className="font-mono text-gray-900">
                      {new Date(selectedSnapshot.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-600">Status:</span>
                    <p className="font-medium text-gray-900">{selectedSnapshot.metadata.status}</p>
                  </div>
                </div>
              </div>

              {/* State Tree */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">State</h3>
                <div className="font-mono text-sm">
                  {renderValue(selectedSnapshot.state, 'state')}
                </div>
              </div>

              {/* Context */}
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Context</h3>
                <div className="font-mono text-sm">
                  {renderValue(selectedSnapshot.context, 'context')}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <Clock size={48} className="mx-auto mb-4 opacity-50" />
                <p className="text-lg">Select a snapshot to inspect</p>
                <p className="text-sm mt-2">Choose from the timeline on the left</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Add default export for lazy loading
export default StateInspector;
