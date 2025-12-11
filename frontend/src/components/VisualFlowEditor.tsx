import { FC, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  BackgroundVariant,
  Node,
  Edge,
} from '@xyflow/react';
import NodePalette from './NodePalette';

const initialNodes: Node[] = [
  {
    id: 'start-1',
    type: 'start',
    position: { x: 250, y: 50 },
    data: { label: 'Start' },
  },
];

const initialEdges: Edge[] = [];

const VisualFlowEditor: FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = {
        x: event.clientX - 250,
        y: event.clientY - 100,
      };

      const newNode: Node = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: { 
          label: type.charAt(0).toUpperCase() + type.slice(1),
          config: {}
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes]
  );

  return (
    <div className="w-full h-full flex">
      {/* Left Sidebar - Node Palette */}
      <div className="w-64 bg-white border-r border-gray-200 p-4 overflow-y-auto">
        <NodePalette />
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          fitView
          className="bg-gray-50"
        >
          <Controls position="top-right" />
          <MiniMap 
            position="bottom-right"
            nodeStrokeWidth={3}
            zoomable
            pannable
          />
          <Background 
            variant={BackgroundVariant.Dots} 
            gap={12} 
            size={1}
            color="#cbd5e1"
          />
        </ReactFlow>

        {/* Status Bar */}
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg px-4 py-2 text-sm">
          <span className="text-gray-600">Nodes: <strong>{nodes.length}</strong></span>
          <span className="mx-3 text-gray-300">|</span>
          <span className="text-gray-600">Edges: <strong>{edges.length}</strong></span>
        </div>
      </div>

      {/* Right Sidebar - Properties Panel (placeholder) */}
      <div className="w-80 bg-white border-l border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Node Properties
        </h3>
        <p className="text-sm text-gray-500">
          Select a node to configure its properties
        </p>
      </div>
    </div>
  );
};

export default VisualFlowEditor;

