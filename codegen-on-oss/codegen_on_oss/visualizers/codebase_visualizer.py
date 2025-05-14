"""Base class for codebase visualizers."""

from abc import ABC, abstractmethod

import networkx as nx


class CodebaseVisualizer(ABC):
    """Base class for codebase visualizers.
    
    This abstract class defines the interface for all codebase visualizers.
    Subclasses must implement the visualize method to create a visualization
    of some aspect of the codebase.
    """
    
    @abstractmethod
    def visualize(self, codebase) -> nx.DiGraph:
        """Create a visualization of the codebase.
        
        Args:
            codebase: The codebase to visualize
            
        Returns:
            A directed graph representing the visualization
        """
        pass

