import { FC } from 'react';
import { 
  Play, 
  Link, 
  GitBranch, 
  GitMerge, 
  Repeat, 
  AlertCircle,
  CheckCircle,
  Code,
  FileText
} from 'lucide-react';

type NodeType = {
  type: string;
  label: string;
  icon: React.ReactNode;
  description: string;
  color: string;
};

const nodeTypes: NodeType[] = [
  {
    type: 'start',
    label: 'Start',
    icon: <Play size={20} />,
    description: 'Begin workflow execution',
    color: 'bg-green-100 text-green-700 border-green-300',
  },
  {
    type: 'sequential',
    label: 'Sequential',
    icon: <Link size={20} />,
    description: 'Execute step after previous completes',
    color: 'bg-blue-100 text-blue-700 border-blue-300',
  },
  {
    type: 'parallel',
    label: 'Parallel',
    icon: <GitBranch size={20} />,
    description: 'Execute multiple branches simultaneously',
    color: 'bg-purple-100 text-purple-700 border-purple-300',
  },
  {
    type: 'conditional',
    label: 'Conditional',
    icon: <Repeat size={20} />,
    description: 'Retry on failure with error analysis',
    color: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  },
  {
    type: 'merge',
    label: 'Merge',
    icon: <GitMerge size={20} />,
    description: 'Combine parallel branch results',
    color: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  },
  {
    type: 'thought',
    label: 'ToT Node',
    icon: <Code size={20} />,
    description: 'Tree-of-Thoughts reasoning node',
    color: 'bg-pink-100 text-pink-700 border-pink-300',
  },
  {
    type: 'validation',
    label: 'Validation',
    icon: <CheckCircle size={20} />,
    description: 'Validate workflow before execution',
    color: 'bg-teal-100 text-teal-700 border-teal-300',
  },
  {
    type: 'error',
    label: 'Error Handler',
    icon: <AlertCircle size={20} />,
    description: 'Handle execution errors',
    color: 'bg-red-100 text-red-700 border-red-300',
  },
  {
    type: 'documentation',
    label: 'Document',
    icon: <FileText size={20} />,
    description: 'Generate documentation',
    color: 'bg-gray-100 text-gray-700 border-gray-300',
  },
];

const NodePalette: FC = () => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Node Palette
      </h3>
      
      <div className="space-y-2">
        {nodeTypes.map((node) => (
          <div
            key={node.type}
            draggable
            onDragStart={(e) => onDragStart(e, node.type)}
            className={`
              p-3 rounded-lg border-2 cursor-move transition-all
              hover:shadow-md active:shadow-lg
              ${node.color}
            `}
          >
            <div className="flex items-center gap-2 mb-1">
              {node.icon}
              <span className="font-semibold text-sm">{node.label}</span>
            </div>
            <p className="text-xs opacity-80">
              {node.description}
            </p>
          </div>
        ))}
      </div>

      {/* Instructions */}
      <div className="mt-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800 font-semibold mb-1">
          💡 How to use:
        </p>
        <ul className="text-xs text-blue-700 space-y-1">
          <li>• Drag nodes onto canvas</li>
          <li>• Connect nodes by dragging from handles</li>
          <li>• Click nodes to configure</li>
          <li>• Double-click to edit</li>
        </ul>
      </div>
    </div>
  );
};

export default NodePalette;

