"""
GraphQL Schema for Codegen OSS

This module defines the GraphQL schema for the codegen-oss system,
providing a flexible API for frontend integration.
"""

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.models import (
    Repository as RepositoryModel,
    Snapshot as SnapshotModel,
    CodeEntity as CodeEntityModel,
    FileEntity as FileEntityModel,
    FunctionEntity as FunctionEntityModel,
    ClassEntity as ClassEntityModel,
    Analysis as AnalysisModel,
    AnalysisMetrics as AnalysisMetricsModel,
    EventLog as EventLogModel,
)


# Node definitions
class Repository(SQLAlchemyObjectType):
    class Meta:
        model = RepositoryModel
        interfaces = (relay.Node,)


class Snapshot(SQLAlchemyObjectType):
    class Meta:
        model = SnapshotModel
        interfaces = (relay.Node,)


class CodeEntity(SQLAlchemyObjectType):
    class Meta:
        model = CodeEntityModel
        interfaces = (relay.Node,)


class FileEntity(SQLAlchemyObjectType):
    class Meta:
        model = FileEntityModel
        interfaces = (relay.Node,)


class FunctionEntity(SQLAlchemyObjectType):
    class Meta:
        model = FunctionEntityModel
        interfaces = (relay.Node,)


class ClassEntity(SQLAlchemyObjectType):
    class Meta:
        model = ClassEntityModel
        interfaces = (relay.Node,)


class Analysis(SQLAlchemyObjectType):
    class Meta:
        model = AnalysisModel
        interfaces = (relay.Node,)


class AnalysisMetrics(SQLAlchemyObjectType):
    class Meta:
        model = AnalysisMetricsModel
        interfaces = (relay.Node,)


class EventLog(SQLAlchemyObjectType):
    class Meta:
        model = EventLogModel
        interfaces = (relay.Node,)


# Input types for mutations
class RepositoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    url = graphene.String(required=True)
    description = graphene.String()
    default_branch = graphene.String()


class SnapshotInput(graphene.InputObjectType):
    repository_id = graphene.ID(required=True)
    commit_sha = graphene.String()
    branch = graphene.String()
    parent_snapshot_id = graphene.ID()
    is_incremental = graphene.Boolean()


class AnalysisInput(graphene.InputObjectType):
    repository_id = graphene.ID(required=True)
    snapshot_id = graphene.ID()
    analysis_type = graphene.String(required=True)


# Custom types for complex data
class SnapshotComparison(graphene.ObjectType):
    snapshot1_id = graphene.ID()
    snapshot2_id = graphene.ID()
    added_files = graphene.List(graphene.String)
    removed_files = graphene.List(graphene.String)
    modified_files = graphene.List(graphene.String)
    added_functions = graphene.List(graphene.String)
    removed_functions = graphene.List(graphene.String)
    modified_functions = graphene.List(graphene.String)
    added_classes = graphene.List(graphene.String)
    removed_classes = graphene.List(graphene.String)
    modified_classes = graphene.List(graphene.String)
    summary = graphene.String()


class VisualizationData(graphene.ObjectType):
    format = graphene.String()
    data = graphene.JSONString()


# Mutations
class CreateRepository(graphene.Mutation):
    class Arguments:
        input = RepositoryInput(required=True)

    repository = graphene.Field(lambda: Repository)

    def mutate(self, info, input):
        repository = RepositoryModel(
            name=input.name,
            url=input.url,
            description=input.description,
            default_branch=input.default_branch or "main",
        )
        db_session = info.context.get("session")
        db_session.add(repository)
        db_session.commit()
        return CreateRepository(repository=repository)


class CreateSnapshot(graphene.Mutation):
    class Arguments:
        input = SnapshotInput(required=True)

    snapshot = graphene.Field(lambda: Snapshot)

    def mutate(self, info, input):
        snapshot = SnapshotModel(
            repository_id=input.repository_id,
            commit_sha=input.commit_sha,
            branch=input.branch,
            parent_snapshot_id=input.parent_snapshot_id,
            is_incremental=input.is_incremental or False,
        )
        db_session = info.context.get("session")
        db_session.add(snapshot)
        db_session.commit()
        return CreateSnapshot(snapshot=snapshot)


class RequestAnalysis(graphene.Mutation):
    class Arguments:
        input = AnalysisInput(required=True)

    analysis = graphene.Field(lambda: Analysis)

    def mutate(self, info, input):
        analysis = AnalysisModel(
            repository_id=input.repository_id,
            snapshot_id=input.snapshot_id,
            analysis_type=input.analysis_type,
            status="pending",
        )
        db_session = info.context.get("session")
        db_session.add(analysis)
        db_session.commit()

        # In a real implementation, we would publish an event to trigger the analysis
        # event_bus.publish(EventType.ANALYSIS_REQUESTED, {...})

        return RequestAnalysis(analysis=analysis)


class Mutation(graphene.ObjectType):
    create_repository = CreateRepository.Field()
    create_snapshot = CreateSnapshot.Field()
    request_analysis = RequestAnalysis.Field()


# Queries
class Query(graphene.ObjectType):
    node = relay.Node.Field()

    # Repository queries
    repository = graphene.Field(
        Repository,
        id=graphene.ID(required=True),
    )
    repositories = graphene.List(
        Repository,
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )
    repository_by_url = graphene.Field(
        Repository,
        url=graphene.String(required=True),
    )

    # Snapshot queries
    snapshot = graphene.Field(
        Snapshot,
        id=graphene.ID(required=True),
    )
    snapshots = graphene.List(
        Snapshot,
        repository_id=graphene.ID(),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )
    snapshot_by_commit = graphene.Field(
        Snapshot,
        repository_id=graphene.ID(required=True),
        commit_sha=graphene.String(required=True),
    )

    # Analysis queries
    analysis = graphene.Field(
        Analysis,
        id=graphene.ID(required=True),
    )
    analyses = graphene.List(
        Analysis,
        repository_id=graphene.ID(),
        snapshot_id=graphene.ID(),
        analysis_type=graphene.String(),
        status=graphene.String(),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )

    # Entity queries
    code_entity = graphene.Field(
        CodeEntity,
        id=graphene.ID(required=True),
    )
    code_entities = graphene.List(
        CodeEntity,
        snapshot_id=graphene.ID(),
        entity_type=graphene.String(),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0),
    )

    # Complex queries
    compare_snapshots = graphene.Field(
        SnapshotComparison,
        snapshot_id_1=graphene.ID(required=True),
        snapshot_id_2=graphene.ID(required=True),
        detail_level=graphene.String(default_value="summary"),
    )

    visualization_data = graphene.Field(
        VisualizationData,
        snapshot_id=graphene.ID(required=True),
        format=graphene.String(default_value="json"),
    )

    # Repository resolvers
    def resolve_repository(self, info, id):
        query = Repository.get_query(info)
        return query.get(id)

    def resolve_repositories(self, info, limit, offset):
        query = Repository.get_query(info)
        return query.limit(limit).offset(offset).all()

    def resolve_repository_by_url(self, info, url):
        query = Repository.get_query(info)
        return query.filter(RepositoryModel.url == url).first()

    # Snapshot resolvers
    def resolve_snapshot(self, info, id):
        query = Snapshot.get_query(info)
        return query.get(id)

    def resolve_snapshots(self, info, repository_id=None, limit=10, offset=0):
        query = Snapshot.get_query(info)
        if repository_id:
            query = query.filter(SnapshotModel.repository_id == repository_id)
        return query.limit(limit).offset(offset).all()

    def resolve_snapshot_by_commit(self, info, repository_id, commit_sha):
        query = Snapshot.get_query(info)
        return query.filter(
            SnapshotModel.repository_id == repository_id,
            SnapshotModel.commit_sha == commit_sha,
        ).first()

    # Analysis resolvers
    def resolve_analysis(self, info, id):
        query = Analysis.get_query(info)
        return query.get(id)

    def resolve_analyses(
        self,
        info,
        repository_id=None,
        snapshot_id=None,
        analysis_type=None,
        status=None,
        limit=10,
        offset=0,
    ):
        query = Analysis.get_query(info)
        if repository_id:
            query = query.filter(AnalysisModel.repository_id == repository_id)
        if snapshot_id:
            query = query.filter(AnalysisModel.snapshot_id == snapshot_id)
        if analysis_type:
            query = query.filter(AnalysisModel.analysis_type == analysis_type)
        if status:
            query = query.filter(AnalysisModel.status == status)
        return query.limit(limit).offset(offset).all()

    # Entity resolvers
    def resolve_code_entity(self, info, id):
        query = CodeEntity.get_query(info)
        return query.get(id)

    def resolve_code_entities(
        self, info, snapshot_id=None, entity_type=None, limit=10, offset=0
    ):
        query = CodeEntity.get_query(info)
        if snapshot_id:
            # This would need a join with the association table
            pass
        if entity_type:
            query = query.filter(CodeEntityModel.entity_type == entity_type)
        return query.limit(limit).offset(offset).all()

    # Complex resolvers
    def resolve_compare_snapshots(
        self, info, snapshot_id_1, snapshot_id_2, detail_level
    ):
        # In a real implementation, this would use the database service
        # to compare snapshots
        return SnapshotComparison(
            snapshot1_id=snapshot_id_1,
            snapshot2_id=snapshot_id_2,
            added_files=[],
            removed_files=[],
            modified_files=[],
            added_functions=[],
            removed_functions=[],
            modified_functions=[],
            added_classes=[],
            removed_classes=[],
            modified_classes=[],
            summary="Snapshot comparison",
        )

    def resolve_visualization_data(self, info, snapshot_id, format):
        # In a real implementation, this would use the snapshot manager
        # to export visualization data
        return VisualizationData(
            format=format,
            data="{}",
        )


schema = graphene.Schema(query=Query, mutation=Mutation)
