import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  BackgroundVariant,
  Panel,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Plus, Play, Save, Trash2 } from 'lucide-react';
import ChainNode from './ChainNode';
import { ChainConfig, ChainStep } from '@/types';

interface WorkflowCanvasProps {
  chain?: ChainConfig;
  onSave?: (chain: ChainConfig) => void;
  onExecute?: (chain: ChainConfig) => void;
}

const nodeTypes = {
  chainStep: ChainNode,
};

function WorkflowCanvasInner({ chain, onSave, onExecute }: WorkflowCanvasProps) {
  const initialNodes: Node[] = useMemo(() => {
    if (!chain?.steps) return [];
    
    return chain.steps.map((step, idx) => ({
      id: `step-${idx}`,
      type: 'chainStep',
      position: { x: 250, y: idx * 150 },
      data: {
        ...step,
        stepIndex: idx,
      },
    }));
  }, [chain]);

  const initialEdges: Edge[] = useMemo(() => {
    if (!chain?.steps) return [];
    
    const edges: Edge[] = [];
    for (let i = 0; i < chain.steps.length - 1; i++) {
      edges.push({
        id: `e-${i}-${i + 1}`,
        source: `step-${i}`,
        target: `step-${i + 1}`,
        animated: true,
        style: { stroke: '#a855f7' },
      });
    }
    return edges;
  }, [chain]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const { addNodes: addFlowNodes } = useReactFlow();

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleAddNode = useCallback(() => {
    const newNode: Node = {
      id: `step-${nodes.length}`,
      type: 'chainStep',
      position: {
        x: 250,
        y: nodes.length * 150,
      },
      data: {
        type: 'sequential',
        prompt: 'Enter prompt here',
        model: 'Sonnet 4.5',
        taskType: 'implementation',
        stepIndex: nodes.length,
      },
    };
    
    addFlowNodes(newNode);
    
    if (nodes.length > 0) {
      const lastNodeId = nodes[nodes.length - 1].id;
      setEdges((eds) => [
        ...eds,
        {
          id: `e-${lastNodeId}-${newNode.id}`,
          source: lastNodeId,
          target: newNode.id,
          animated: true,
          style: { stroke: '#a855f7' },
        },
      ]);
    }
  }, [nodes, addFlowNodes, setEdges]);

  const handleSave = useCallback(() => {
    if (!chain) return;
    
    const steps: ChainStep[] = nodes
      .sort((a, b) => a.position.y - b.position.y)
      .map((node) => ({
        type: (node.data.type as string) || 'sequential',
        prompt: (node.data.prompt as string) || '',
        model: (node.data.model as string) || 'Sonnet 4.5',
        taskType: node.data.taskType as string | undefined,
        waitForPrevious: true,
      } as ChainStep));

    const updatedChain: ChainConfig = {
      ...chain,
      steps,
    };

    onSave?.(updatedChain);
  }, [nodes, chain, onSave]);

  const handleExecute = useCallback(() => {
    if (!chain) return;
    
    const steps: ChainStep[] = nodes
      .sort((a, b) => a.position.y - b.position.y)
      .map((node) => ({
        type: (node.data.type as string) || 'sequential',
        prompt: (node.data.prompt as string) || '',
        model: (node.data.model as string) || 'Sonnet 4.5',
        taskType: node.data.taskType as string | undefined,
        waitForPrevious: true,
      } as ChainStep));

    const updatedChain: ChainConfig = {
      ...chain,
      steps,
    };

    onExecute?.(updatedChain);
  }, [nodes, chain, onExecute]);

  const handleDeleteSelected = useCallback(() => {
    const selectedNodes = nodes.filter((n) => n.selected);
    const selectedNodeIds = new Set(selectedNodes.map((n) => n.id));
    
    setNodes((nds) => nds.filter((n) => !n.selected));
    setEdges((eds) => eds.filter((e) => !selectedNodeIds.has(e.source) && !selectedNodeIds.has(e.target)));
  }, [nodes, setNodes, setEdges]);

  return (
    <div style={{ width: '100%', height: '600px', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#4b5563" />
        <Controls />
        <MiniMap
          nodeColor={(node) => node.selected ? '#a855f7' : '#1f2937'}
          maskColor="rgba(0, 0, 0, 0.6)"
        />
        
        <Panel position="top-right">
          <div className="flex gap-2 bg-gray-900 border border-gray-700 rounded-lg p-2 shadow-lg">
            <button
              onClick={handleAddNode}
              className="p-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors flex items-center gap-1"
              title="Add Step"
            >
              <Plus className="w-4 h-4" />
              <span className="text-xs">Add Step</span>
            </button>
            <button
              onClick={handleDeleteSelected}
              className="p-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              title="Delete Selected"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleSave}
              className="p-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center gap-1"
              title="Save Chain"
            >
              <Save className="w-4 h-4" />
              <span className="text-xs">Save</span>
            </button>
            <button
              onClick={handleExecute}
              className="p-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors flex items-center gap-1"
              title="Execute Chain"
            >
              <Play className="w-4 h-4" />
              <span className="text-xs">Execute</span>
            </button>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default function WorkflowCanvas(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
