"""
GraphQL API for Codegen-on-OSS

This module defines the GraphQL schema for the API.
"""

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from datetime import datetime
from typing import Dict, List, Optional, Any

from codegen_on_oss.database.models import (
    CodebaseSnapshot as DBCodebaseSnapshot,
    AnalysisResult as DBAnalysisResult,
    CodeMetrics as DBCodeMetrics,
    SymbolAnalysis as DBSymbolAnalysis,
    DependencyGraph as DBDependencyGraph
)
from codegen_on_oss.database.manager import DatabaseManager
from codegen_on_oss.analysis.orchestrator import AnalysisOrchestrator
from codegen_on_oss.snapshot.enhanced_snapshot import EnhancedSnapshotManager


# SQLAlchemy Object Types
class CodebaseSnapshot(SQLAlchemyObjectType):
    class Meta:
        model = DBCodebaseSnapshot
        interfaces = (relay.Node,)


class AnalysisResult(SQLAlchemyObjectType):
    class Meta:
        model = DBAnalysisResult
        interfaces = (relay.Node,)


class CodeMetrics(SQLAlchemyObjectType):
    class Meta:
        model = DBCodeMetrics
        interfaces = (relay.Node,)


class SymbolAnalysis(SQLAlchemyObjectType):
    class Meta:
        model = DBSymbolAnalysis
        interfaces = (relay.Node,)


class DependencyGraph(SQLAlchemyObjectType):
    class Meta:
        model = DBDependencyGraph
        interfaces = (relay.Node,)


# Input Types
class SnapshotFilter(graphene.InputObjectType):
    id = graphene.String()
    snapshot_id = graphene.String()
    commit_sha = graphene.String()
    before_date = graphene.DateTime()
    after_date = graphene.DateTime()


class AnalysisFilter(graphene.InputObjectType):
    id = graphene.String()
    snapshot_id = graphene.String()
    analyzer_type = graphene.String()
    status = graphene.String()
    before_date = graphene.DateTime()
    after_date = graphene.DateTime()


class SymbolFilter(graphene.InputObjectType):
    id = graphene.String()
    analysis_id = graphene.String()
    symbol_type = graphene.String()
    symbol_name = graphene.String()
    file_path = graphene.String()


class MetricsFilter(graphene.InputObjectType):
    analysis_id = graphene.String()
    min_complexity = graphene.Float()
    max_complexity = graphene.Float()
    min_maintainability = graphene.Float()
    max_maintainability = graphene.Float()


# Custom Types
class AnalysisProgress(graphene.ObjectType):
    id = graphene.String()
    status = graphene.String()
    progress = graphene.Float()
    message = graphene.String()
    started_at = graphene.DateTime()
    elapsed_time = graphene.Float()


class SnapshotDiff(graphene.ObjectType):
    base_snapshot_id = graphene.String()
    compare_snapshot_id = graphene.String()
    files_added = graphene.List(graphene.String)
    files_removed = graphene.List(graphene.String)
    files_modified = graphene.List(graphene.String)
    functions_added = graphene.List(graphene.String)
    functions_removed = graphene.List(graphene.String)
    functions_modified = graphene.List(graphene.String)
    classes_added = graphene.List(graphene.String)
    classes_removed = graphene.List(graphene.String)
    classes_modified = graphene.List(graphene.String)
    file_diffs = graphene.JSONString()


# Mutations
class CreateSnapshot(graphene.Mutation):
    class Arguments:
        repo_url = graphene.String(required=True)
        commit_sha = graphene.String()
        metadata = graphene.JSONString()

    snapshot = graphene.Field(lambda: CodebaseSnapshot)

    def mutate(self, info, repo_url, commit_sha=None, metadata=None):
        db_manager = DatabaseManager()
        snapshot_manager = EnhancedSnapshotManager(db_manager=db_manager)
        
        # Create codebase from repo
        from codegen import Codebase
        codebase = Codebase.from_repo(repo_url)
        
        if commit_sha:
            codebase.checkout(commit=commit_sha)
        
        # Create snapshot
        snapshot = snapshot_manager.create_snapshot(
            codebase=codebase,
            commit_sha=commit_sha,
            metadata=metadata
        )
        
        # Get database record
        db_snapshot = db_manager.get_by_id(DBCodebaseSnapshot, snapshot.snapshot_id)
        
        return CreateSnapshot(snapshot=db_snapshot)


class RunAnalysis(graphene.Mutation):
    class Arguments:
        snapshot_id = graphene.String(required=True)
        analyzer_type = graphene.String(required=True)
        params = graphene.JSONString()

    analysis = graphene.Field(lambda: AnalysisResult)

    def mutate(self, info, snapshot_id, analyzer_type, params=None):
        db_manager = DatabaseManager()
        orchestrator = AnalysisOrchestrator(db_manager=db_manager)
        
        # Run analysis
        analysis_id = orchestrator.run_analysis(
            analyzer_type=analyzer_type,
            snapshot_id=snapshot_id,
            params=params
        )
        
        # Get database record
        db_analysis = db_manager.get_by_id(DBAnalysisResult, analysis_id)
        
        return RunAnalysis(analysis=db_analysis)


class CompareSnapshots(graphene.Mutation):
    class Arguments:
        base_snapshot_id = graphene.String(required=True)
        compare_snapshot_id = graphene.String(required=True)

    diff = graphene.Field(lambda: SnapshotDiff)

    def mutate(self, info, base_snapshot_id, compare_snapshot_id):
        db_manager = DatabaseManager()
        snapshot_manager = EnhancedSnapshotManager(db_manager=db_manager)
        
        # Compare snapshots
        diff = snapshot_manager.compare_snapshots(base_snapshot_id, compare_snapshot_id)
        
        return CompareSnapshots(diff=SnapshotDiff(
            base_snapshot_id=base_snapshot_id,
            compare_snapshot_id=compare_snapshot_id,
            files_added=diff.get("files_added", []),
            files_removed=diff.get("files_removed", []),
            files_modified=diff.get("files_modified", []),
            functions_added=diff.get("functions_added", []),
            functions_removed=diff.get("functions_removed", []),
            functions_modified=diff.get("functions_modified", []),
            classes_added=diff.get("classes_added", []),
            classes_removed=diff.get("classes_removed", []),
            classes_modified=diff.get("classes_modified", []),
            file_diffs=diff.get("file_diffs", {})
        ))


class CreateSnapshotBranch(graphene.Mutation):
    class Arguments:
        base_snapshot_id = graphene.String(required=True)
        branch_name = graphene.String(required=True)

    snapshot = graphene.Field(lambda: CodebaseSnapshot)

    def mutate(self, info, base_snapshot_id, branch_name):
        db_manager = DatabaseManager()
        snapshot_manager = EnhancedSnapshotManager(db_manager=db_manager)
        
        # Create branch
        branch_id = snapshot_manager.create_snapshot_branch(base_snapshot_id, branch_name)
        
        # Get database record
        db_snapshot = db_manager.get_by_id(DBCodebaseSnapshot, branch_id)
        
        return CreateSnapshotBranch(snapshot=db_snapshot)


class MergeSnapshotBranches(graphene.Mutation):
    class Arguments:
        branch1_id = graphene.String(required=True)
        branch2_id = graphene.String(required=True)
        merge_name = graphene.String(required=True)

    snapshot = graphene.Field(lambda: CodebaseSnapshot)

    def mutate(self, info, branch1_id, branch2_id, merge_name):
        db_manager = DatabaseManager()
        snapshot_manager = EnhancedSnapshotManager(db_manager=db_manager)
        
        # Merge branches
        merged_id = snapshot_manager.merge_snapshot_branches(branch1_id, branch2_id, merge_name)
        
        # Get database record
        db_snapshot = db_manager.get_by_id(DBCodebaseSnapshot, merged_id)
        
        return MergeSnapshotBranches(snapshot=db_snapshot)


class Mutation(graphene.ObjectType):
    create_snapshot = CreateSnapshot.Field()
    run_analysis = RunAnalysis.Field()
    compare_snapshots = CompareSnapshots.Field()
    create_snapshot_branch = CreateSnapshotBranch.Field()
    merge_snapshot_branches = MergeSnapshotBranches.Field()


# Queries
class Query(graphene.ObjectType):
    node = relay.Node.Field()
    
    # Snapshot queries
    snapshot = graphene.Field(
        CodebaseSnapshot,
        id=graphene.String(),
        snapshot_id=graphene.String()
    )
    snapshots = graphene.List(
        CodebaseSnapshot,
        filter=graphene.Argument(SnapshotFilter)
    )
    
    # Analysis queries
    analysis = graphene.Field(
        AnalysisResult,
        id=graphene.String()
    )
    analyses = graphene.List(
        AnalysisResult,
        filter=graphene.Argument(AnalysisFilter)
    )
    
    # Symbol queries
    symbol = graphene.Field(
        SymbolAnalysis,
        id=graphene.String()
    )
    symbols = graphene.List(
        SymbolAnalysis,
        filter=graphene.Argument(SymbolFilter)
    )
    
    # Metrics queries
    metrics = graphene.Field(
        CodeMetrics,
        analysis_id=graphene.String()
    )
    
    def resolve_snapshot(self, info, id=None, snapshot_id=None):
        db_manager = DatabaseManager()
        
        if id:
            return db_manager.get_by_id(DBCodebaseSnapshot, id)
        elif snapshot_id:
            snapshots = db_manager.get_all(DBCodebaseSnapshot, snapshot_id=snapshot_id)
            return snapshots[0] if snapshots else None
        return None
    
    def resolve_snapshots(self, info, filter=None):
        db_manager = DatabaseManager()
        query_args = {}
        
        if filter:
            if filter.id:
                query_args["id"] = filter.id
            if filter.snapshot_id:
                query_args["snapshot_id"] = filter.snapshot_id
            if filter.commit_sha:
                query_args["commit_sha"] = filter.commit_sha
        
        snapshots = db_manager.get_all(DBCodebaseSnapshot, **query_args)
        
        # Apply date filters if provided
        if filter and (filter.before_date or filter.after_date):
            filtered_snapshots = []
            for snapshot in snapshots:
                if filter.before_date and snapshot.timestamp > filter.before_date:
                    continue
                if filter.after_date and snapshot.timestamp < filter.after_date:
                    continue
                filtered_snapshots.append(snapshot)
            return filtered_snapshots
        
        return snapshots
    
    def resolve_analysis(self, info, id):
        db_manager = DatabaseManager()
        return db_manager.get_by_id(DBAnalysisResult, id)
    
    def resolve_analyses(self, info, filter=None):
        db_manager = DatabaseManager()
        query_args = {}
        
        if filter:
            if filter.id:
                query_args["id"] = filter.id
            if filter.snapshot_id:
                query_args["snapshot_id"] = filter.snapshot_id
            if filter.analyzer_type:
                query_args["analyzer_type"] = filter.analyzer_type
            if filter.status:
                query_args["status"] = filter.status
        
        analyses = db_manager.get_all(DBAnalysisResult, **query_args)
        
        # Apply date filters if provided
        if filter and (filter.before_date or filter.after_date):
            filtered_analyses = []
            for analysis in analyses:
                if filter.before_date and analysis.created_at > filter.before_date:
                    continue
                if filter.after_date and analysis.created_at < filter.after_date:
                    continue
                filtered_analyses.append(analysis)
            return filtered_analyses
        
        return analyses
    
    def resolve_symbol(self, info, id):
        db_manager = DatabaseManager()
        return db_manager.get_by_id(DBSymbolAnalysis, id)
    
    def resolve_symbols(self, info, filter=None):
        db_manager = DatabaseManager()
        query_args = {}
        
        if filter:
            if filter.id:
                query_args["id"] = filter.id
            if filter.analysis_id:
                query_args["analysis_id"] = filter.analysis_id
            if filter.symbol_type:
                query_args["symbol_type"] = filter.symbol_type
            if filter.symbol_name:
                query_args["symbol_name"] = filter.symbol_name
            if filter.file_path:
                query_args["file_path"] = filter.file_path
        
        return db_manager.get_all(DBSymbolAnalysis, **query_args)
    
    def resolve_metrics(self, info, analysis_id):
        db_manager = DatabaseManager()
        metrics = db_manager.get_all(DBCodeMetrics, analysis_id=analysis_id)
        return metrics[0] if metrics else None


# Subscriptions
class Subscription(graphene.ObjectType):
    analysis_progress = graphene.Field(
        AnalysisProgress,
        id=graphene.String()
    )
    snapshot_created = graphene.Field(CodebaseSnapshot)
    
    async def resolve_analysis_progress(self, info, id):
        db_manager = DatabaseManager()
        orchestrator = AnalysisOrchestrator(db_manager=db_manager)
        
        # Get analysis status
        status = orchestrator.scheduler.get_analysis_status(id)
        
        # Convert to subscription format
        progress = AnalysisProgress(
            id=id,
            status=status.get("status", "unknown"),
            progress=0.0,  # Not implemented yet
            message="",    # Not implemented yet
            started_at=datetime.fromisoformat(status.get("created_at", datetime.now().isoformat())),
            elapsed_time=status.get("elapsed_time", 0.0)
        )
        
        return progress
    
    async def resolve_snapshot_created(self, info):
        # This would be implemented with an async generator in a real application
        # For now, just return None
        return None


# Create Schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)

