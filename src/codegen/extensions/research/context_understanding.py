"""
Context Understanding module for agentgen.

This module provides tools for understanding and analyzing context in research
and code analysis tasks.
"""

from typing import Dict, List, Optional, Any, Union
import json
from dataclasses import dataclass, field


@dataclass
class ContextItem:
    """
    A single item of context, such as a code snippet, document, or search result.
    """
    content: str
    source: str
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextCollection:
    """
    A collection of context items with methods for analysis and manipulation.
    """
    items: List[ContextItem] = field(default_factory=list)
    
    def add_item(self, item: ContextItem) -> None:
        """
        Add a context item to the collection.
        
        Args:
            item: The context item to add
        """
        self.items.append(item)
    
    def get_by_source(self, source: str) -> List[ContextItem]:
        """
        Get all context items from a specific source.
        
        Args:
            source: The source to filter by
            
        Returns:
            List of context items from the specified source
        """
        return [item for item in self.items if item.source == source]
    
    def get_most_relevant(self, n: int = 5) -> List[ContextItem]:
        """
        Get the most relevant context items.
        
        Args:
            n: Number of items to return
            
        Returns:
            List of the n most relevant context items
        """
        sorted_items = sorted(self.items, key=lambda x: x.relevance_score, reverse=True)
        return sorted_items[:n]
    
    def to_text(self) -> str:
        """
        Convert the context collection to a text representation.
        
        Returns:
            Text representation of the context collection
        """
        result = []
        for i, item in enumerate(self.items, 1):
            result.append(f"[{i}] {item.source} (relevance: {item.relevance_score:.2f})")
            result.append(item.content)
            result.append("")
        
        return "\n".join(result)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context collection to a dictionary.
        
        Returns:
            Dictionary representation of the context collection
        """
        return {
            "items": [
                {
                    "content": item.content,
                    "source": item.source,
                    "relevance_score": item.relevance_score,
                    "metadata": item.metadata
                }
                for item in self.items
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextCollection":
        """
        Create a context collection from a dictionary.
        
        Args:
            data: Dictionary representation of a context collection
            
        Returns:
            New context collection
        """
        collection = cls()
        for item_data in data.get("items", []):
            item = ContextItem(
                content=item_data["content"],
                source=item_data["source"],
                relevance_score=item_data.get("relevance_score", 1.0),
                metadata=item_data.get("metadata", {})
            )
            collection.add_item(item)
        return collection


class ContextAnalyzer:
    """
    Analyzer for context collections.
    
    This class provides methods for analyzing and extracting insights from
    context collections.
    """
    
    def __init__(self, collection: ContextCollection):
        """
        Initialize a ContextAnalyzer.
        
        Args:
            collection: The context collection to analyze
        """
        self.collection = collection
    
    def get_summary(self, max_length: int = 500) -> str:
        """
        Generate a summary of the context collection.
        
        Args:
            max_length: Maximum length of the summary
            
        Returns:
            Summary of the context collection
        """
        # In a real implementation, this would use an LLM to generate a summary
        # For now, we'll just return a simple summary
        items = self.collection.get_most_relevant(3)
        sources = ", ".join(set(item.source for item in items))
        
        summary = f"Context collection with {len(self.collection.items)} items from {sources}."
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."
        
        return summary
    
    def extract_key_concepts(self, n: int = 5) -> List[str]:
        """
        Extract key concepts from the context collection.
        
        Args:
            n: Number of key concepts to extract
            
        Returns:
            List of key concepts
        """
        # In a real implementation, this would use an LLM or NLP techniques
        # For now, we'll just return a placeholder
        return ["concept1", "concept2", "concept3", "concept4", "concept5"][:n]
    
    def find_contradictions(self) -> List[Dict[str, Any]]:
        """
        Find contradictions in the context collection.
        
        Returns:
            List of contradictions, each as a dictionary with 'items' and 'reason' keys
        """
        # In a real implementation, this would use an LLM to identify contradictions
        # For now, we'll just return an empty list
        return []
    
    def get_context_for_query(self, query: str, n: int = 3) -> ContextCollection:
        """
        Get the most relevant context items for a specific query.
        
        Args:
            query: The query to find relevant context for
            n: Number of items to return
            
        Returns:
            New context collection with the most relevant items
        """
        # In a real implementation, this would use semantic search or an LLM
        # For now, we'll just return the most relevant items
        items = self.collection.get_most_relevant(n)
        result = ContextCollection()
        for item in items:
            result.add_item(item)
        return result


class ContextManager:
    """
    Manager for context collections.
    
    This class provides methods for creating, loading, and saving context
    collections.
    """
    
    @staticmethod
    def create_empty() -> ContextCollection:
        """
        Create an empty context collection.
        
        Returns:
            New empty context collection
        """
        return ContextCollection()
    
    @staticmethod
    def create_from_text(text: str, source: str, relevance_score: float = 1.0) -> ContextCollection:
        """
        Create a context collection from a text.
        
        Args:
            text: The text to create a context item from
            source: The source of the text
            relevance_score: The relevance score of the text
            
        Returns:
            New context collection with a single item
        """
        collection = ContextCollection()
        item = ContextItem(content=text, source=source, relevance_score=relevance_score)
        collection.add_item(item)
        return collection
    
    @staticmethod
    def create_from_texts(texts: List[str], sources: List[str], relevance_scores: Optional[List[float]] = None) -> ContextCollection:
        """
        Create a context collection from multiple texts.
        
        Args:
            texts: List of texts to create context items from
            sources: List of sources for the texts
            relevance_scores: Optional list of relevance scores for the texts
            
        Returns:
            New context collection with multiple items
        """
        if relevance_scores is None:
            relevance_scores = [1.0] * len(texts)
        
        if len(texts) != len(sources) or len(texts) != len(relevance_scores):
            raise ValueError("texts, sources, and relevance_scores must have the same length")
        
        collection = ContextCollection()
        for text, source, score in zip(texts, sources, relevance_scores):
            item = ContextItem(content=text, source=source, relevance_score=score)
            collection.add_item(item)
        
        return collection
    
    @staticmethod
    def save_to_json(collection: ContextCollection, filepath: str) -> None:
        """
        Save a context collection to a JSON file.
        
        Args:
            collection: The context collection to save
            filepath: The path to save the JSON file to
        """
        with open(filepath, "w") as f:
            json.dump(collection.to_dict(), f, indent=2)
    
    @staticmethod
    def load_from_json(filepath: str) -> ContextCollection:
        """
        Load a context collection from a JSON file.
        
        Args:
            filepath: The path to load the JSON file from
            
        Returns:
            Loaded context collection
        """
        with open(filepath, "r") as f:
            data = json.load(f)
        return ContextCollection.from_dict(data)