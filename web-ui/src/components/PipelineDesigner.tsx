/**
 * Visual Pipeline Designer Component
 * 
 * This component provides a drag-and-drop interface for designing CI/CD pipelines
 * with support for stages, dependencies, and real-time execution monitoring.
 */

import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  ReactFlowProvider,
  useReactFlow,
} from 'react-flow-renderer';
import dagre from 'dagre';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Toolbar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Grid
} from '@mui/material';
import {
  Add as AddIcon,
  Save as SaveIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  AccountTree as TreeIcon
} from '@mui/icons-material';

import { StageNode } from './nodes/StageNode';
import { AgentTaskNode } from './nodes/AgentTaskNode';
import { ConditionalNode } from './nodes/ConditionalNode';
import { PipelineExecution, StageDefinition, StageType, ExecutionStatus } from '../types/pipeline';
import { usePipelineStore } from '../stores/pipelineStore';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';

// Custom node types
const nodeTypes = {
  stageNode: StageNode,
  agentTaskNode: AgentTaskNode,
  conditionalNode: ConditionalNode,
};

// Layout configuration for dagre
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 150, height: 50 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return {
    nodes: nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      return {
        ...node,
        targetPosition: isHorizontal ? 'left' : 'top',
        sourcePosition: isHorizontal ? 'right' : 'bottom',
        position: {
          x: nodeWithPosition.x - 75,
          y: nodeWithPosition.y - 25,
        },
      };
    }),
    edges,
  };
};

interface PipelineDesignerProps {
  pipelineId?: string;
  execution?: PipelineExecution;
  readOnly?: boolean;
  onPipelineChange?: (stages: StageDefinition[], edges: Edge[]) => void;
  onExecutePipeline?: () => void;
  onStopPipeline?: () => void;
}

export const PipelineDesigner: React.FC<PipelineDesignerProps> = ({
  pipelineId,
  execution,
  readOnly = false,
  onPipelineChange,
  onExecutePipeline,
  onStopPipeline,
}) => {
  const reactFlowInstance = useReactFlow();
  const { 
    pipelines, 
    updatePipeline, 
    executePipeline, 
    stopPipeline 
  } = usePipelineStore();
  const { events, connectionStatus } = useRealtimeUpdates(pipelineId);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isAddStageDialogOpen, setIsAddStageDialogOpen] = useState(false);
  const [selectedNodeType, setSelectedNodeType] = useState<StageType>(StageType.AGENT_TASK);
  const [newStageData, setNewStageData] = useState({
    name: '',
    description: '',
    prompt: '',
    command: '',
    image: '',
  });

  // Auto-layout nodes when pipeline changes
  const onLayout = useCallback(
    (direction: string) => {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodes,
        edges,
        direction
      );

      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
    },
    [nodes, edges, setNodes, setEdges]
  );

  // Handle connection between nodes
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Add new stage
  const onAddStage = useCallback(() => {
    const newNodeId = `stage-${Date.now()}`;
    const newNode: Node = {
      id: newNodeId,
      type: 'stageNode',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        label: newStageData.name || `Stage ${nodes.length + 1}`,
        stageType: selectedNodeType,
        description: newStageData.description,
        config: {
          prompt: newStageData.prompt,
          command: newStageData.command,
          image: newStageData.image,
        },
        status: ExecutionStatus.PENDING,
        onEdit: (nodeId: string, data: any) => {
          setNodes((nds) =>
            nds.map((node) =>
              node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
            )
          );
        },
        onDelete: (nodeId: string) => {
          setNodes((nds) => nds.filter((node) => node.id !== nodeId));
          setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
        },
      },
    };

    setNodes((nds) => nds.concat(newNode));
    setIsAddStageDialogOpen(false);
    setNewStageData({ name: '', description: '', prompt: '', command: '', image: '' });
  }, [newStageData, selectedNodeType, nodes.length, setNodes, setEdges]);

  // Update nodes based on execution status
  useEffect(() => {
    if (execution) {
      setNodes((nds) =>
        nds.map((node) => {
          const taskExecution = execution.tasks[node.id];
          if (taskExecution) {
            return {
              ...node,
              data: {
                ...node.data,
                status: taskExecution.status,
                startTime: taskExecution.started_at,
                endTime: taskExecution.completed_at,
                duration: taskExecution.duration_seconds,
                error: taskExecution.error_message,
                agentRunId: taskExecution.agent_run_id,
                agentWebUrl: taskExecution.agent_web_url,
              },
            };
          }
          return node;
        })
      );
    }
  }, [execution, setNodes]);

  // Update nodes based on real-time events
  useEffect(() => {
    events.forEach((event) => {
      if (event.stage_id) {
        setNodes((nds) =>
          nds.map((node) => {
            if (node.id === event.stage_id) {
              return {
                ...node,
                data: {
                  ...node.data,
                  status: event.data.status || node.data.status,
                  lastUpdate: event.timestamp,
                },
              };
            }
            return node;
          })
        );
      }
    });
  }, [events, setNodes]);

  // Save pipeline
  const handleSavePipeline = useCallback(() => {
    if (pipelineId && onPipelineChange) {
      const stages: StageDefinition[] = nodes.map((node) => ({
        id: node.id,
        name: node.data.label,
        stage_type: node.data.stageType,
        description: node.data.description,
        depends_on: edges
          .filter((edge) => edge.target === node.id)
          .map((edge) => edge.source),
        can_run_parallel: true,
        continue_on_failure: false,
        agent_config: node.data.stageType === StageType.AGENT_TASK ? {
          prompt: node.data.config.prompt,
        } : undefined,
        shell_config: node.data.stageType === StageType.SHELL_COMMAND ? {
          command: node.data.config.command,
        } : undefined,
        docker_config: node.data.stageType === StageType.DOCKER_RUN ? {
          image: node.data.config.image,
        } : undefined,
      }));

      onPipelineChange(stages, edges);
    }
  }, [nodes, edges, pipelineId, onPipelineChange]);

  const isExecuting = execution?.status === ExecutionStatus.RUNNING;

  return (
    <Box sx={{ height: '100%', width: '100%' }}>
      <Toolbar sx={{ backgroundColor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Pipeline Designer
          {connectionStatus === 'connected' && (
            <Chip 
              label="Live" 
              color="success" 
              size="small" 
              sx={{ ml: 2 }} 
            />
          )}
        </Typography>
        
        {!readOnly && (
          <>
            <Button
              startIcon={<AddIcon />}
              onClick={() => setIsAddStageDialogOpen(true)}
              disabled={isExecuting}
            >
              Add Stage
            </Button>
            
            <IconButton onClick={() => onLayout('TB')} disabled={isExecuting}>
              <TreeIcon />
            </IconButton>
            
            <Button
              startIcon={<SaveIcon />}
              onClick={handleSavePipeline}
              disabled={isExecuting}
              sx={{ ml: 1 }}
            >
              Save
            </Button>
          </>
        )}
        
        {onExecutePipeline && (
          <Button
            startIcon={isExecuting ? <StopIcon /> : <PlayIcon />}
            onClick={isExecuting ? onStopPipeline : onExecutePipeline}
            color={isExecuting ? 'error' : 'primary'}
            variant="contained"
            sx={{ ml: 1 }}
          >
            {isExecuting ? 'Stop' : 'Execute'}
          </Button>
        )}
      </Toolbar>

      <Box sx={{ height: 'calc(100% - 64px)', position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background variant={BackgroundVariant.Dots} />
          <Controls />
          <MiniMap />
          
          {execution && (
            <Panel position="top-right">
              <Card sx={{ minWidth: 200 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Execution Status
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Status: <Chip 
                      label={execution.status} 
                      color={
                        execution.status === ExecutionStatus.SUCCESS ? 'success' :
                        execution.status === ExecutionStatus.FAILED ? 'error' :
                        execution.status === ExecutionStatus.RUNNING ? 'warning' :
                        'default'
                      }
                      size="small"
                    />
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Completed: {execution.completed_stages} / {execution.total_stages}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Duration: {execution.duration_seconds ? `${execution.duration_seconds.toFixed(1)}s` : 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Panel>
          )}
        </ReactFlow>
      </Box>

      {/* Add Stage Dialog */}
      <Dialog
        open={isAddStageDialogOpen}
        onClose={() => setIsAddStageDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add New Stage</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Stage Name"
                value={newStageData.name}
                onChange={(e) => setNewStageData({ ...newStageData, name: e.target.value })}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Stage Type</InputLabel>
                <Select
                  value={selectedNodeType}
                  onChange={(e) => setSelectedNodeType(e.target.value as StageType)}
                >
                  <MenuItem value={StageType.AGENT_TASK}>Agent Task</MenuItem>
                  <MenuItem value={StageType.SHELL_COMMAND}>Shell Command</MenuItem>
                  <MenuItem value={StageType.DOCKER_RUN}>Docker Run</MenuItem>
                  <MenuItem value={StageType.CONDITIONAL}>Conditional</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={newStageData.description}
                onChange={(e) => setNewStageData({ ...newStageData, description: e.target.value })}
              />
            </Grid>
            
            {selectedNodeType === StageType.AGENT_TASK && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Agent Prompt"
                  value={newStageData.prompt}
                  onChange={(e) => setNewStageData({ ...newStageData, prompt: e.target.value })}
                />
              </Grid>
            )}
            
            {selectedNodeType === StageType.SHELL_COMMAND && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Shell Command"
                  value={newStageData.command}
                  onChange={(e) => setNewStageData({ ...newStageData, command: e.target.value })}
                />
              </Grid>
            )}
            
            {selectedNodeType === StageType.DOCKER_RUN && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Docker Image"
                  value={newStageData.image}
                  onChange={(e) => setNewStageData({ ...newStageData, image: e.target.value })}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsAddStageDialogOpen(false)}>Cancel</Button>
          <Button onClick={onAddStage} variant="contained" disabled={!newStageData.name}>
            Add Stage
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export const PipelineDesignerWithProvider: React.FC<PipelineDesignerProps> = (props) => (
  <ReactFlowProvider>
    <PipelineDesigner {...props} />
  </ReactFlowProvider>
);