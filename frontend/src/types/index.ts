export type NodeType =
  | 'start'
  | 'sequential'
  | 'parallel'
  | 'conditional'
  | 'merge'
  | 'thought'
  | 'validation'
  | 'error'
  | 'documentation';

export type WorkflowNodeData = {
  label: string;
  config: Record<string, unknown>;
};

export type WorkflowNode = {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  data: WorkflowNodeData;
};

export type WorkflowEdge = {
  id: string;
  source: string;
  target: string;
  type?: string;
};

export type Workflow = {
  id: string;
  name: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: Date;
  updatedAt: Date;
};

