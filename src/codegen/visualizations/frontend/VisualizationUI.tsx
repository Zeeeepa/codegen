import React, { useState, useEffect } from 'react';
import SelectionRow from './SelectionRow';
import './SelectionRow.css';

interface GraphNode {
  id: string;
  name: string;
  type: string;
  [key: string]: any;
}

interface GraphEdge {
  source: string;
  target: string;
  [key: string]: any;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface Method {
  name: string;
  id: string;
}

interface RelatedElement {
  name: string;
  id: string;
  type: string;
}

interface SelectedElement {
  id: string;
  name: string;
  type: string;
  methods: Method[];
  related_elements: RelatedElement[];
}

/**
 * VisualizationUI component that displays the graph visualization and selection row
 */
const VisualizationUI: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch graph data and selection data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch graph data
        const graphResponse = await fetch('/api/visualization/graph');
        if (!graphResponse.ok) {
          throw new Error('Failed to fetch graph data');
        }
        const graphJson = await graphResponse.json();
        setGraphData(graphJson);
        
        // Fetch selection data if available
        try {
          const selectionResponse = await fetch('/api/visualization/selection');
          if (selectionResponse.ok) {
            const selectionJson = await selectionResponse.json();
            // If there's a selected element, use the first one
            const selectedIds = Object.keys(selectionJson);
            if (selectedIds.length > 0) {
              setSelectedElement(selectionJson[selectedIds[0]]);
            }
          }
        } catch (selectionError) {
          // Selection data is optional, so we don't throw an error
          console.warn('Failed to fetch selection data:', selectionError);
        }
        
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        setLoading(false);
      }
    };
    
    fetchData();
    
    // Set up polling to refresh data
    const intervalId = setInterval(fetchData, 5000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  // Handle node selection in the graph
  const handleNodeSelect = async (nodeId: string) => {
    try {
      // Find the node in the graph data
      const node = graphData?.nodes.find(n => n.id === nodeId);
      if (!node) return;
      
      // Send selection to the backend
      const response = await fetch('/api/visualization/select', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: nodeId }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to select element');
      }
      
      // Get the updated selection data
      const selectionData = await response.json();
      setSelectedElement(selectionData);
    } catch (err) {
      console.error('Error selecting node:', err);
    }
  };

  // Handle method selection
  const handleMethodSelect = (method: Method) => {
    // Find the method in the graph and select it
    handleNodeSelect(method.id);
  };

  // Handle related element selection
  const handleRelatedElementSelect = (element: RelatedElement) => {
    // Find the related element in the graph and select it
    handleNodeSelect(element.id);
  };

  if (loading) {
    return <div className="visualization-loading">Loading visualization...</div>;
  }

  if (error) {
    return <div className="visualization-error">Error: {error}</div>;
  }

  return (
    <div className="visualization-container">
      <div className="visualization-graph">
        {/* This is a placeholder for the actual graph visualization component */}
        <div className="graph-placeholder">
          Graph Visualization Goes Here
          <p>This component would integrate with your existing graph visualization library</p>
        </div>
      </div>
      
      <SelectionRow
        selectedElement={selectedElement}
        onMethodSelect={handleMethodSelect}
        onRelatedElementSelect={handleRelatedElementSelect}
      />
    </div>
  );
};

export default VisualizationUI;

