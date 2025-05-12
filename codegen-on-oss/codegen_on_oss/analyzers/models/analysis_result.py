#!/usr/bin/env python3
"""
Analysis Result Model

This module defines data models for analysis results, providing a standardized
way to represent and serialize analysis outcomes.
"""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Set, Any, Optional, Union
from datetime import datetime

from codegen_on_oss.analyzers.issues import AnalysisType, IssueCollection

@dataclass
class AnalysisSummary:
    """Summary statistics for an analysis."""
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_issues: int = 0
    analysis_time: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class CodeQualityResult:
    """Results of code quality analysis."""
    dead_code: Dict[str, Any] = field(default_factory=dict)
    complexity: Dict[str, Any] = field(default_factory=dict)
    parameter_issues: Dict[str, Any] = field(default_factory=dict)
    style_issues: Dict[str, Any] = field(default_factory=dict)
    implementation_issues: Dict[str, Any] = field(default_factory=dict)
    maintainability: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items()}

@dataclass
class DependencyResult:
    """Results of dependency analysis."""
    import_dependencies: Dict[str, Any] = field(default_factory=dict)
    circular_dependencies: Dict[str, Any] = field(default_factory=dict)
    module_coupling: Dict[str, Any] = field(default_factory=dict)
    external_dependencies: Dict[str, Any] = field(default_factory=dict)
    call_graph: Dict[str, Any] = field(default_factory=dict)
    class_hierarchy: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items()}

@dataclass
class PrAnalysisResult:
    """Results of PR analysis."""
    modified_symbols: List[Dict[str, Any]] = field(default_factory=list)
    added_symbols: List[Dict[str, Any]] = field(default_factory=list)
    removed_symbols: List[Dict[str, Any]] = field(default_factory=list)
    signature_changes: List[Dict[str, Any]] = field(default_factory=list)
    impact: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items()}

@dataclass
class SecurityResult:
    """Results of security analysis."""
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    secrets: List[Dict[str, Any]] = field(default_factory=list)
    injection_risks: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items()}

@dataclass
class PerformanceResult:
    """Results of performance analysis."""
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    memory_issues: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items()}

@dataclass
class MetadataEntry:
    """Metadata about an analysis."""
    key: str
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {"key": self.key, "value": self.value}

@dataclass
class AnalysisResult:
    """Comprehensive analysis result."""
    # Core data
    analysis_types: List[AnalysisType]
    summary: AnalysisSummary = field(default_factory=AnalysisSummary)
    issues: IssueCollection = field(default_factory=IssueCollection)
    
    # Analysis results
    code_quality: Optional[CodeQualityResult] = None
    dependencies: Optional[DependencyResult] = None
    pr_analysis: Optional[PrAnalysisResult] = None
    security: Optional[SecurityResult] = None
    performance: Optional[PerformanceResult] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    repo_name: Optional[str] = None
    repo_path: Optional[str] = None
    language: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "analysis_types": [at.value for at in self.analysis_types],
            "summary": self.summary.to_dict(),
            "issues": self.issues.to_dict(),
            "metadata": self.metadata,
        }
        
        # Add optional sections if present
        if self.repo_name:
            result["repo_name"] = self.repo_name
        
        if self.repo_path:
            result["repo_path"] = self.repo_path
        
        if self.language:
            result["language"] = self.language
        
        # Add analysis results if present
        if self.code_quality:
            result["code_quality"] = self.code_quality.to_dict()
        
        if self.dependencies:
            result["dependencies"] = self.dependencies.to_dict()
        
        if self.pr_analysis:
            result["pr_analysis"] = self.pr_analysis.to_dict()
        
        if self.security:
            result["security"] = self.security.to_dict()
        
        if self.performance:
            result["performance"] = self.performance.to_dict()
        
        return result
    
    def save_to_file(self, file_path: str, indent: int = 2):
        """
        Save analysis result to a file.
        
        Args:
            file_path: Path to save to
            indent: JSON indentation level
        """
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """
        Create analysis result from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Analysis result object
        """
        # Convert analysis types
        analysis_types = [
            AnalysisType(at) if isinstance(at, str) else at
            for at in data.get("analysis_types", [])
        ]
        
        # Create summary
        summary = AnalysisSummary(**data.get("summary", {})) if "summary" in data else AnalysisSummary()
        
        # Create issues collection
        issues = IssueCollection.from_dict(data.get("issues", {})) if "issues" in data else IssueCollection()
        
        # Create result object
        result = cls(
            analysis_types=analysis_types,
            summary=summary,
            issues=issues,
            repo_name=data.get("repo_name"),
            repo_path=data.get("repo_path"),
            language=data.get("language"),
            metadata=data.get("metadata", {})
        )
        
        # Add analysis results if present
        if "code_quality" in data:
            result.code_quality = CodeQualityResult(**data["code_quality"])
        
        if "dependencies" in data:
            result.dependencies = DependencyResult(**data["dependencies"])
        
        if "pr_analysis" in data:
            result.pr_analysis = PrAnalysisResult(**data["pr_analysis"])
        
        if "security" in data:
            result.security = SecurityResult(**data["security"])
        
        if "performance" in data:
            result.performance = PerformanceResult(**data["performance"])
        
        return result
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'AnalysisResult':
        """
        Load analysis result from file.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Analysis result object
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    def get_issue_count(self, severity: Optional[str] = None, category: Optional[str] = None) -> int:
        """
        Get count of issues matching criteria.
        
        Args:
            severity: Optional severity to filter by
            category: Optional category to filter by
            
        Returns:
            Count of matching issues
        """
        issues_dict = self.issues.to_dict()
        
        if severity and category:
            # Count issues with specific severity and category
            return sum(
                1 for issue in issues_dict.get("issues", [])
                if issue.get("severity") == severity and issue.get("category") == category
            )
        elif severity:
            # Count issues with specific severity
            return issues_dict.get("statistics", {}).get("by_severity", {}).get(severity, 0)
        elif category:
            # Count issues with specific category
            return issues_dict.get("statistics", {}).get("by_category", {}).get(category, 0)
        else:
            # Total issues
            return issues_dict.get("statistics", {}).get("total", 0)
    
    def merge(self, other: 'AnalysisResult') -> 'AnalysisResult':
        """
        Merge with another analysis result.
        
        Args:
            other: Analysis result to merge with
            
        Returns:
            New merged analysis result
        """
        # Create new result with combined analysis types
        merged = AnalysisResult(
            analysis_types=list(set(self.analysis_types + other.analysis_types)),
            repo_name=self.repo_name or other.repo_name,
            repo_path=self.repo_path or other.repo_path,
            language=self.language or other.language,
        )
        
        # Merge issues
        merged.issues.add_issues(self.issues.issues)
        merged.issues.add_issues(other.issues.issues)
        
        # Merge metadata
        merged.metadata = {**self.metadata, **other.metadata}
        
        # Merge analysis results (take non-None values)
        merged.code_quality = self.code_quality or other.code_quality
        merged.dependencies = self.dependencies or other.dependencies
        merged.pr_analysis = self.pr_analysis or other.pr_analysis
        merged.security = self.security or other.security
        merged.performance = self.performance or other.performance
        
        # Update summary
        merged.summary = AnalysisSummary(
            total_files=max(self.summary.total_files, other.summary.total_files),
            total_functions=max(self.summary.total_functions, other.summary.total_functions),
            total_classes=max(self.summary.total_classes, other.summary.total_classes),
            total_issues=len(merged.issues.issues),
            analysis_time=datetime.now().isoformat()
        )
        
        return merged