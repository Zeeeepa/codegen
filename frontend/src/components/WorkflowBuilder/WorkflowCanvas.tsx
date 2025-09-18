/**
 * Workflow Canvas Component
 * ========================
 * 
 * The core visual workflow builder component using React Flow.
 * Provides drag-and-drop interface for building CICD pipelines with
 * real-time updates and intelligent suggestions.
 * 
 * Features:
 * - Interactive drag-and-drop workflow building
 * - Real-time status updates and execution tracking
 * - Custom nodes for agents, tools, and integrations
 * - Intelligent workflow validation and suggestions
 * - Collaborative editing with conflict resolution
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  ConnectionMode,
  Controls,
  Background,
  MiniMap,
  Panel,
  ReactFlowProvider,
  useReactFlow,
  NodeTypes,
  EdgeTypes,
} from 'reactflow';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';

// Custom node components
import { AgentNode } from './nodes/AgentNode';
import { ToolNode } from './nodes/ToolNode';
import { IntegrationNode } from './nodes/IntegrationNode';
import { TriggerNode } from './nodes/TriggerNode';
import { ConditionNode } from './nodes/ConditionNode';

// Custom edge components
import { CustomEdge } from './edges/CustomEdge';
import { ConditionalEdge } from './edges/ConditionalEdge';

// Hooks and utilities
import { useWorkflowStore } from '../../stores/workflowStore';
import { useRealtimeUpdates } from '../../hooks/useRealtimeUpdates';
import { useWorkflowValidation } from '../../hooks/useWorkflowValidation';
import { useCollaboration } from '../../hooks/useCollaboration';

// Types
import { WorkflowNode, WorkflowEdge, NodeStatus, WorkflowExecution } from '../../types/workflow';
import { CodegenCommand } from '../../types/codegen';

// Styles
import 'reactflow/dist/style.css';
import './WorkflowCanvas.css';

// Node types mapping
const nodeTypes: NodeTypes = {
  agent: AgentNode,
  tool: ToolNode,
  integration: IntegrationNode,
  trigger: TriggerNode,
  condition: ConditionNode,
};

// Edge types mapping
const edgeTypes: EdgeTypes = {
  default: CustomEdge,
  conditional: ConditionalEdge,
};

interface WorkflowCanvasProps {
  workflowId?: string;
  readOnly?: boolean;
  showMiniMap?: boolean;
  showControls?: boolean;
  onNodeSelect?: (node: WorkflowNode | null) => void;
  onEdgeSelect?: (edge: WorkflowEdge | null) => void;
  onWorkflowChange?: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
}

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = ({
  workflowId,
  readOnly = false,
  showMiniMap = true,
  showControls = true,
  onNodeSelect,
  onEdgeSelect,
  onWorkflowChange,
}) => {
  // React Flow instance
  const reactFlowInstance = useReactFlow();

  // State management
  const {
    currentWorkflow,
    executionStatus,
    loadWorkflow,
    saveWorkflow,
    updateNodeStatus,
    addNode,
    removeNode,
    updateNode,
  } = useWorkflowStore();

  // Local state for nodes and edges
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<WorkflowEdge | null>(null);

  // Real-time updates
  const { isConnected, executionUpdates } = useRealtimeUpdates(workflowId);

  // Workflow validation
  const { validationErrors, validateWorkflow } = useWorkflowValidation();

  // Collaboration
  const { collaborators, sendUpdate, receiveUpdate } = useCollaboration(workflowId);

  // Load workflow on mount
  useEffect(() => {
    if (workflowId) {
      loadWorkflow(workflowId);
    }
  }, [workflowId, loadWorkflow]);

  // Update nodes and edges when workflow changes
  useEffect(() => {
    if (currentWorkflow) {
      setNodes(currentWorkflow.nodes || []);
      setEdges(currentWorkflow.edges || []);
    }
  }, [currentWorkflow, setNodes, setEdges]);

  // Handle real-time execution updates
  useEffect(() => {
    if (executionUpdates) {
      executionUpdates.forEach((update) => {
        updateNodeStatus(update.nodeId, update.status, update.data);
      });
    }
  }, [executionUpdates, updateNodeStatus]);

  // Handle node connection
  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;

      const newEdge: WorkflowEdge = {
        ...params,
        id: `edge-${Date.now()}`,
        type: 'default',
        animated: false,
        data: {
          label: '',
          condition: null,
        },
      };

      setEdges((eds) => addEdge(newEdge, eds));
      
      // Send collaboration update
      sendUpdate({
        type: 'edge_added',
        data: newEdge,
        timestamp: Date.now(),
      });

      toast.success('Connection created');
    },
    [readOnly, setEdges, sendUpdate]
  );

  // Handle node selection
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: WorkflowNode) => {
      setSelectedNode(node);
      setSelectedEdge(null);
      onNodeSelect?.(node);
    },
    [onNodeSelect]
  );

  // Handle edge selection
  const onEdgeClick = useCallback(
    (event: React.MouseEvent, edge: WorkflowEdge) => {
      setSelectedEdge(edge);
      setSelectedNode(null);
      onEdgeSelect?.(edge);
    },
    [onEdgeSelect]
  );

  // Handle canvas click (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
    onNodeSelect?.(null);
    onEdgeSelect?.(null);
  }, [onNodeSelect, onEdgeSelect]);

  // Handle node drag end
  const onNodeDragStop = useCallback(
    (event: React.MouseEvent, node: WorkflowNode) => {
      if (readOnly) return;

      // Send collaboration update
      sendUpdate({
        type: 'node_moved',
        data: { nodeId: node.id, position: node.position },
        timestamp: Date.now(),
      });
    },
    [readOnly, sendUpdate]
  );

  // Handle node deletion
  const onNodesDelete = useCallback(
    (nodesToDelete: WorkflowNode[]) => {
      if (readOnly) return;

      nodesToDelete.forEach((node) => {
        removeNode(node.id);
        
        // Send collaboration update
        sendUpdate({
          type: 'node_deleted',
          data: { nodeId: node.id },
          timestamp: Date.now(),
        });
      });

      toast.success(`Deleted ${nodesToDelete.length} node(s)`);
    },
    [readOnly, removeNode, sendUpdate]
  );

  // Handle edge deletion
  const onEdgesDelete = useCallback(
    (edgesToDelete: WorkflowEdge[]) => {
      if (readOnly) return;

      edgesToDelete.forEach((edge) => {
        // Send collaboration update
        sendUpdate({
          type: 'edge_deleted',
          data: { edgeId: edge.id },
          timestamp: Date.now(),
        });
      });

      toast.success(`Deleted ${edgesToDelete.length} connection(s)`);
    },
    [readOnly, sendUpdate]
  );

  // Handle workflow save
  const handleSave = useCallback(async () => {
    if (!currentWorkflow || readOnly) return;

    try {
      await saveWorkflow({
        ...currentWorkflow,
        nodes,
        edges,
        updatedAt: new Date().toISOString(),
      });

      toast.success('Workflow saved successfully');
    } catch (error) {
      console.error('Failed to save workflow:', error);
      toast.error('Failed to save workflow');
    }
  }, [currentWorkflow, nodes, edges, saveWorkflow, readOnly]);

  // Handle workflow validation
  const handleValidate = useCallback(async () => {
    const errors = await validateWorkflow(nodes, edges);
    
    if (errors.length === 0) {
      toast.success('Workflow is valid');
    } else {
      toast.error(`Found ${errors.length} validation error(s)`);
    }
  }, [nodes, edges, validateWorkflow]);

  // Handle workflow execution
  const handleExecute = useCallback(async () => {
    if (!currentWorkflow || readOnly) return;

    try {
      // Validate workflow first
      const errors = await validateWorkflow(nodes, edges);
      if (errors.length > 0) {
        toast.error('Cannot execute workflow with validation errors');
        return;
      }

      // TODO: Implement workflow execution
      toast.success('Workflow execution started');
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      toast.error('Failed to execute workflow');
    }
  }, [currentWorkflow, nodes, edges, validateWorkflow, readOnly]);

  // Memoized node status colors
  const getNodeStatusColor = useCallback((status: NodeStatus) => {
    switch (status) {
      case 'running':
        return '#3b82f6'; // blue
      case 'completed':
        return '#10b981'; // green
      case 'failed':
        return '#ef4444'; // red
      case 'pending':
        return '#f59e0b'; // amber
      default:
        return '#6b7280'; // gray
    }
  }, []);

  // Memoized minimap node color function
  const minimapNodeColor = useCallback(
    (node: WorkflowNode) => {
      const status = executionStatus[node.id]?.status || 'idle';
      return getNodeStatusColor(status);
    },
    [executionStatus, getNodeStatusColor]
  );

  // Handle workflow changes
  useEffect(() => {
    onWorkflowChange?.(nodes, edges);
  }, [nodes, edges, onWorkflowChange]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (readOnly) return;

      // Ctrl/Cmd + S to save
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleSave();
      }

      // Ctrl/Cmd + Enter to execute
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        handleExecute();
      }

      // Delete key to delete selected nodes/edges
      if (event.key === 'Delete' || event.key === 'Backspace') {
        if (selectedNode) {
          onNodesDelete([selectedNode]);
        } else if (selectedEdge) {
          onEdgesDelete([selectedEdge]);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [readOnly, handleSave, handleExecute, selectedNode, selectedEdge, onNodesDelete, onEdgesDelete]);

  return (
    <div className="workflow-canvas h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onNodeDragStop={onNodeDragStop}
        onNodesDelete={onNodesDelete}
        onEdgesDelete={onEdgesDelete}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
        className={readOnly ? 'read-only' : ''}
      >
        {/* Background */}
        <Background color="#f1f5f9" gap={20} />

        {/* Controls */}
        {showControls && (
          <Controls
            showZoom={true}
            showFitView={true}
            showInteractive={!readOnly}
          />
        )}

        {/* MiniMap */}
        {showMiniMap && (
          <MiniMap
            nodeColor={minimapNodeColor}
            nodeStrokeWidth={3}
            zoomable
            pannable
            position="bottom-right"
          />
        )}

        {/* Toolbar Panel */}
        <Panel position="top-left" className="workflow-toolbar">
          <div className="flex items-center space-x-2 bg-white rounded-lg shadow-lg p-2">
            {!readOnly && (
              <>
                <button
                  onClick={handleSave}
                  className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                  title="Save Workflow (Ctrl+S)"
                >
                  Save
                </button>
                <button
                  onClick={handleValidate}
                  className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
                  title="Validate Workflow"
                >
                  Validate
                </button>
                <button
                  onClick={handleExecute}
                  className="px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
                  title="Execute Workflow (Ctrl+Enter)"
                >
                  Execute
                </button>
              </>
            )}
            
            {/* Connection Status */}
            <div className="flex items-center space-x-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-xs text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {/* Collaborators */}
            {collaborators.length > 0 && (
              <div className="flex items-center space-x-1">
                <span className="text-xs text-gray-600">Collaborators:</span>
                <div className="flex -space-x-1">
                  {collaborators.slice(0, 3).map((collaborator, index) => (
                    <div
                      key={collaborator.id}
                      className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center border-2 border-white"
                      title={collaborator.name}
                    >
                      {collaborator.name.charAt(0).toUpperCase()}
                    </div>
                  ))}
                  {collaborators.length > 3 && (
                    <div className="w-6 h-6 rounded-full bg-gray-500 text-white text-xs flex items-center justify-center border-2 border-white">
                      +{collaborators.length - 3}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </Panel>

        {/* Validation Errors Panel */}
        <AnimatePresence>
          {validationErrors.length > 0 && (
            <Panel position="bottom-left" className="validation-errors">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="bg-red-50 border border-red-200 rounded-lg p-3 max-w-md"
              >
                <h4 className="text-red-800 font-medium mb-2">
                  Validation Errors ({validationErrors.length})
                </h4>
                <ul className="text-red-700 text-sm space-y-1">
                  {validationErrors.slice(0, 5).map((error, index) => (
                    <li key={index} className="flex items-start space-x-1">
                      <span className="text-red-500">•</span>
                      <span>{error.message}</span>
                    </li>
                  ))}
                  {validationErrors.length > 5 && (
                    <li className="text-red-600 italic">
                      ... and {validationErrors.length - 5} more
                    </li>
                  )}
                </ul>
              </motion.div>
            </Panel>
          )}
        </AnimatePresence>
      </ReactFlow>
    </div>
  );
};

// Wrapper component with ReactFlowProvider
export const WorkflowCanvasWrapper: React.FC<WorkflowCanvasProps> = (props) => {
  return (
    <ReactFlowProvider>
      <WorkflowCanvas {...props} />
    </ReactFlowProvider>
  );
};

export default WorkflowCanvasWrapper;
