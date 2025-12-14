import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import { Settings, AlertCircle, CheckCircle, Clock, Loader } from 'lucide-react';

type ChainNodeData = {
  type: string;
  prompt: string;
  model: string;
  taskType?: string;
  stepIndex: number;
  status?: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
  error?: string;
};

function ChainNode({ data, selected }: NodeProps<Node<ChainNodeData>>) {
  const [showDetails, setShowDetails] = useState(false);

  const statusColors = {
    pending: { bg: '#fef3c7', text: '#92400e', icon: Clock },
    running: { bg: '#d1fae5', text: '#065f46', icon: Loader },
    completed: { bg: '#d1fae5', text: '#065f46', icon: CheckCircle },
    failed: { bg: '#fee2e2', text: '#991b1b', icon: AlertCircle },
  };

  const typeColors = {
    initial: '#3b82f6',
    sequential: '#8b5cf6',
    conditional: '#f59e0b',
    parallel: '#10b981',
  };

  const status = data.status || 'pending';
  const StatusIcon = statusColors[status]?.icon || Clock;
  const nodeColor = typeColors[data.type as keyof typeof typeColors] || '#8b5cf6';

  return (
    <div
      style={{
        padding: '16px',
        borderRadius: '8px',
        border: `2px solid ${selected ? '#a855f7' : '#374151'}`,
        background: '#1f2937',
        minWidth: '250px',
        maxWidth: '350px',
        boxShadow: selected ? '0 8px 16px rgba(168, 85, 247, 0.3)' : '0 4px 6px rgba(0,0,0,0.3)',
        transition: 'all 0.2s',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: nodeColor, width: 10, height: 10 }}
        isConnectable={true}
      />

      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: nodeColor,
              }}
            />
            <span className="text-sm font-semibold text-gray-100">
              Step {data.stepIndex + 1}
            </span>
            <span
              className="text-xs px-2 py-0.5 rounded"
              style={{
                background: typeColors[data.type as keyof typeof typeColors] + '20',
                color: nodeColor,
              }}
            >
              {data.type}
            </span>
          </div>
          
          <div className="flex items-center gap-1">
            {data.status && (
              <div
                className="flex items-center gap-1 px-2 py-0.5 rounded text-xs"
                style={{
                  background: statusColors[status].bg + '20',
                  color: statusColors[status].text,
                }}
              >
                <StatusIcon className="w-3 h-3" />
                <span>{status}</span>
              </div>
            )}
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <Settings className="w-3 h-3 text-gray-400" />
            </button>
          </div>
        </div>

        <div className="text-xs text-gray-300 mb-1">
          {data.taskType && (
            <span className="text-purple-400 font-medium">
              {data.taskType}
            </span>
          )}
        </div>

        <div className="text-sm text-gray-300 mb-2">
          <div className="font-medium text-gray-200 mb-1">Model:</div>
          <div className="text-xs bg-gray-800 px-2 py-1 rounded">{data.model}</div>
        </div>

        <div className="text-xs text-gray-400">
          <div className="font-medium text-gray-200 mb-1">Prompt:</div>
          <div
            className="bg-gray-800 p-2 rounded max-h-20 overflow-y-auto"
            style={{ wordBreak: 'break-word' }}
          >
            {data.prompt || 'No prompt set'}
          </div>
        </div>
      </div>

      {showDetails && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          {data.result && (
            <details className="mb-2">
              <summary className="text-xs text-green-400 cursor-pointer hover:text-green-300">
                View Result
              </summary>
              <div className="mt-2 text-xs text-gray-400 bg-gray-900 p-2 rounded max-h-32 overflow-y-auto">
                {data.result}
              </div>
            </details>
          )}
          
          {data.error && (
            <details className="mb-2">
              <summary className="text-xs text-red-400 cursor-pointer hover:text-red-300">
                View Error
              </summary>
              <div className="mt-2 text-xs text-red-300 bg-gray-900 p-2 rounded max-h-32 overflow-y-auto">
                {data.error}
              </div>
            </details>
          )}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: nodeColor, width: 10, height: 10 }}
        isConnectable={true}
      />
    </div>
  );
}

export default memo(ChainNode);
