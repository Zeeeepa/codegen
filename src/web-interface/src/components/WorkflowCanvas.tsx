/**
 * Visual Workflow Canvas Component
 * Drag-and-drop interface for creating and editing CICD workflows
 */

'use client';

import React, { useCallback, useRef, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { WorkflowNode, WorkflowEdge } from '@/types/codegen';
import useAppStore from '@/store/app-store';

// Custom node types
import AgentNode from './workflow-nodes/AgentNode';
import ConditionNode from './workflow-nodes/ConditionNode';
import IntegrationNode from './workflow-nodes/IntegrationNode';
import ManualNode from './workflow-nodes/ManualNode';

const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
  integration: IntegrationNode,
  manual: ManualNode,
};

interface WorkflowCanvasProps {
  workflowId?: string;
  readOnly?: boolean;
  className?: string;
}

const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({
  workflowId,
  readOnly = false,
  className = '',
}) => {
  const { workflows, updateWorkflow } = useAppStore();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

  // Get current workflow
  const currentWorkflow = workflows.current || workflows.list.find(w => w.id === workflowId);

  // Convert workflow nodes/edges to ReactFlow format
  const initialNodes: Node[] = currentWorkflow?.nodes.map(node => ({
    id: node.id,
    type: node.type,
    position: node.position,
    data: node.data,
  })) || [];

  const initialEdges: Edge[] = currentWorkflow?.edges.map(edge => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: edge.type,
    data: edge.data,
  })) || [];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Handle new connections
  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;
      setEdges((eds) => addEdge(params, eds));
    },
    [readOnly, setEdges]
  );

  // Handle drag over for dropping new nodes
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop for creating new nodes
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      if (readOnly) return;

      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');

      if (typeof type === 'undefined' || !type || !reactFlowInstance || !reactFlowBounds) {
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: {
          label: `${type.charAt(0).toUpperCase() + type.slice(1)} Node`,
          description: `New ${type} node`,
          config: {},
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [readOnly, reactFlowInstance, setNodes]
  );

  // Save workflow changes
  const saveWorkflow = useCallback(async () => {
    if (!currentWorkflow || readOnly) return;

    const updatedWorkflow = {
      ...currentWorkflow,
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type as WorkflowNode['type'],
        position: node.position,
        data: node.data,
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type as WorkflowEdge['type'],
        data: edge.data,
      })),
    };

    await updateWorkflow(updatedWorkflow);
  }, [currentWorkflow, nodes, edges, updateWorkflow, readOnly]);

  // Auto-save on changes (debounced)
  React.useEffect(() => {
    if (readOnly) return;

    const timeoutId = setTimeout(() => {
      saveWorkflow();
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [nodes, edges, saveWorkflow, readOnly]);

  return (
    <div className={`h-full w-full ${className}`} ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onDrop={onDrop}
        onDragOver={onDragOver}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="top-right"
        className="bg-gray-50"
      >
        <Controls />
        <MiniMap />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>

      {/* Workflow Info Panel */}
      {currentWorkflow && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm">
          <h3 className="font-semibold text-gray-900 mb-2">{currentWorkflow.name}</h3>
          {currentWorkflow.description && (
            <p className="text-sm text-gray-600 mb-3">{currentWorkflow.description}</p>
          )}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Nodes: {nodes.length}</span>
            <span>Edges: {edges.length}</span>
            <span className={`px-2 py-1 rounded-full ${
              currentWorkflow.status === 'active' ? 'bg-green-100 text-green-800' :
              currentWorkflow.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
              currentWorkflow.status === 'paused' ? 'bg-orange-100 text-orange-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {currentWorkflow.status}
            </span>
          </div>
        </div>
      )}

      {/* Save Status */}
      {!readOnly && (
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-2">
          <div className="flex items-center space-x-2 text-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-gray-600">Auto-saving...</span>
          </div>
        </div>
      )}
    </div>
  );
};

// Wrapper component with ReactFlowProvider
const WorkflowCanvasWrapper: React.FC<WorkflowCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <WorkflowCanvas {...props} />
    </ReactFlowProvider>
  );
};

export default WorkflowCanvasWrapper;
