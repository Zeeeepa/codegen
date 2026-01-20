"""
CI/CD template generator.

Generates configuration files for various CI/CD platforms.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import structlog
from jinja2 import Environment, PackageLoader, select_autoescape

logger = structlog.get_logger(__name__)


class CIProvider(StrEnum):
    """Supported CI/CD providers."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_PIPELINES = "azure_pipelines"
    CIRCLECI = "circleci"


class CITemplateGenerator:
    """Generates CI/CD configuration files from templates."""

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        self._templates_dir = Path(templates_dir) if templates_dir else None
        self._log = logger.bind(component="ci_generator")

        if self._templates_dir and self._templates_dir.exists():
            self._env = Environment(
                loader=PackageLoader("autoqa", "templates"),
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self._env = None

    def generate(
        self,
        provider: CIProvider,
        test_paths: list[str],
        python_version: str = "3.12",
        node_count: int = 1,
        parallel: bool = False,
        environment: str = "production",
        notify_on_failure: bool = True,
        artifacts_retention_days: int = 30,
        timeout_minutes: int = 60,
        custom_variables: dict[str, str] | None = None,
    ) -> str:
        """
        Generate CI/CD configuration for specified provider.

        Args:
            provider: CI/CD provider to generate for
            test_paths: Paths to test specification files
            python_version: Python version to use
            node_count: Number of parallel nodes
            parallel: Enable parallel execution
            environment: Target environment
            notify_on_failure: Send notifications on failure
            artifacts_retention_days: Days to retain artifacts
            timeout_minutes: Job timeout in minutes
            custom_variables: Additional environment variables

        Returns:
            Generated configuration as string
        """
        context = {
            "test_paths": test_paths,
            "python_version": python_version,
            "node_count": node_count,
            "parallel": parallel,
            "environment": environment,
            "notify_on_failure": notify_on_failure,
            "artifacts_retention_days": artifacts_retention_days,
            "timeout_minutes": timeout_minutes,
            "custom_variables": custom_variables or {},
        }

        match provider:
            case CIProvider.GITHUB_ACTIONS:
                return self._generate_github_actions(context)
            case CIProvider.GITLAB_CI:
                return self._generate_gitlab_ci(context)
            case CIProvider.JENKINS:
                return self._generate_jenkins(context)
            case CIProvider.AZURE_PIPELINES:
                return self._generate_azure_pipelines(context)
            case CIProvider.CIRCLECI:
                return self._generate_circleci(context)
            case _:
                raise ValueError(f"Unknown CI provider: {provider}")

    def _generate_github_actions(self, context: dict[str, Any]) -> str:
        """Generate GitHub Actions workflow."""
        test_paths_str = " ".join(context["test_paths"])
        parallel_str = "--parallel" if context["parallel"] else ""
        node_matrix = list(range(context["node_count"])) if context["node_count"] > 1 else []

        env_vars = "\n".join(
            f"          {k}: {v}" for k, v in context["custom_variables"].items()
        )

        matrix_section = ""
        if node_matrix:
            matrix_section = f"""
    strategy:
      matrix:
        node: {node_matrix}
      fail-fast: false"""

        return f'''name: AutoQA Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: '{context["environment"]}'
        type: choice
        options:
          - production
          - staging
          - development

env:
  PYTHON_VERSION: '{context["python_version"]}'
  AUTOQA_ENVIRONMENT: ${{{{ github.event.inputs.environment || '{context["environment"]}' }}}}

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: {context["timeout_minutes"]}{matrix_section}

    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ env.PYTHON_VERSION }}}}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install autoqa-ai-testing

      - name: Run tests
        env:
          OWL_API_KEY: ${{{{ secrets.OWL_API_KEY }}}}
          REDIS_URL: redis://localhost:6379/0
{env_vars}
        run: |
          autoqa run {test_paths_str} {parallel_str} \\
            --environment ${{{{ env.AUTOQA_ENVIRONMENT }}}} \\
            --output-format junit \\
            --output-file results.xml \\
            --artifacts-dir ./artifacts

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results${{{{ matrix.node && format('-{{0}}', matrix.node) || '' }}}}
          path: |
            results.xml
            ./artifacts/
          retention-days: {context["artifacts_retention_days"]}

      - name: Publish test results
        if: always()
        uses: mikepenz/action-junit-report@v4
        with:
          report_paths: 'results.xml'
          fail_on_failure: true

      - name: Notify on failure
        if: failure() && {str(context["notify_on_failure"]).lower()}
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          fields: repo,message,commit,author,workflow
        env:
          SLACK_WEBHOOK_URL: ${{{{ secrets.SLACK_WEBHOOK_URL }}}}
'''

    def _generate_gitlab_ci(self, context: dict[str, Any]) -> str:
        """Generate GitLab CI configuration."""
        test_paths_str = " ".join(context["test_paths"])
        parallel_str = "--parallel" if context["parallel"] else ""

        env_vars = "\n".join(
            f"    {k}: {v}" for k, v in context["custom_variables"].items()
        )

        parallel_section = ""
        if context["node_count"] > 1:
            parallel_section = f"""
  parallel: {context["node_count"]}"""

        return f'''stages:
  - test
  - report

variables:
  PYTHON_VERSION: "{context["python_version"]}"
  AUTOQA_ENVIRONMENT: "{context["environment"]}"
{env_vars}

.test_template:
  image: python:${{PYTHON_VERSION}}
  services:
    - redis:7
  before_script:
    - pip install --upgrade pip
    - pip install autoqa-ai-testing
  cache:
    key: ${{CI_COMMIT_REF_SLUG}}
    paths:
      - .cache/pip
  artifacts:
    when: always
    paths:
      - results.xml
      - artifacts/
    reports:
      junit: results.xml
    expire_in: {context["artifacts_retention_days"]} days

test:
  extends: .test_template
  stage: test
  timeout: {context["timeout_minutes"]} minutes{parallel_section}
  script:
    - autoqa run {test_paths_str} {parallel_str}
        --environment $AUTOQA_ENVIRONMENT
        --output-format junit
        --output-file results.xml
        --artifacts-dir ./artifacts
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

report:
  stage: report
  image: python:3.12-slim
  needs: ["test"]
  script:
    - pip install autoqa-ai-testing
    - autoqa report --input results.xml --format html --output report.html
  artifacts:
    paths:
      - report.html
    expire_in: {context["artifacts_retention_days"]} days
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
'''

    def _generate_jenkins(self, context: dict[str, Any]) -> str:
        """Generate Jenkinsfile."""
        test_paths_str = " ".join(context["test_paths"])
        parallel_str = "--parallel" if context["parallel"] else ""

        env_vars = "\n".join(
            f"        {k} = '{v}'" for k, v in context["custom_variables"].items()
        )

        parallel_stages = ""
        if context["node_count"] > 1:
            stages = []
            for i in range(context["node_count"]):
                stages.append(f'''                "Node {i}": {{
                    agent any
                    steps {{
                        runTests("{i}")
                    }}
                }}''')
            parallel_stages = f'''
            parallel {{
{chr(10).join(stages)}
            }}'''

        return f'''pipeline {{
    agent any

    environment {{
        PYTHON_VERSION = '{context["python_version"]}'
        AUTOQA_ENVIRONMENT = '{context["environment"]}'
        OWL_API_KEY = credentials('owl-api-key')
{env_vars}
    }}

    options {{
        timeout(time: {context["timeout_minutes"]}, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '30'))
        disableConcurrentBuilds()
    }}

    stages {{
        stage('Setup') {{
            steps {{
                sh 'python -m pip install --upgrade pip && pip install autoqa-ai-testing'
            }}
        }}

        stage('Test') {{
            steps {{
                sh 'autoqa run {test_paths_str} {parallel_str} --environment $AUTOQA_ENVIRONMENT --output-format junit --output-file results.xml --artifacts-dir ./artifacts'
            }}
        }}
    }}

    post {{
        always {{
            junit 'results.xml'
            archiveArtifacts artifacts: 'artifacts/**/*', allowEmptyArchive: true
        }}
        failure {{
            script {{
                if ({str(context["notify_on_failure"]).lower()}) {{
                    slackSend(
                        channel: '#test-failures',
                        color: 'danger',
                        message: "Test failed: ${{env.JOB_NAME}} #${{env.BUILD_NUMBER}}"
                    )
                }}
            }}
        }}
    }}
}}
'''

    def _generate_azure_pipelines(self, context: dict[str, Any]) -> str:
        """Generate Azure Pipelines configuration."""
        test_paths_str = " ".join(context["test_paths"])
        parallel_str = "--parallel" if context["parallel"] else ""

        env_vars = "\n".join(
            f"    {k}: {v}" for k, v in context["custom_variables"].items()
        )

        parallel_section = ""
        if context["node_count"] > 1:
            parallel_section = f"""
  strategy:
    parallel: {context["node_count"]}"""

        return f'''trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

variables:
  pythonVersion: '{context["python_version"]}'
  autoqaEnvironment: '{context["environment"]}'
{env_vars}

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Test
    displayName: 'Run AutoQA Tests'
    jobs:
      - job: RunTests
        displayName: 'Execute Tests'
        timeoutInMinutes: {context["timeout_minutes"]}{parallel_section}
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'
              addToPath: true

          - script: |
              python -m pip install --upgrade pip
              pip install autoqa-ai-testing
            displayName: 'Install dependencies'

          - script: |
              autoqa run {test_paths_str} {parallel_str} \\
                --environment $(autoqaEnvironment) \\
                --output-format junit \\
                --output-file $(Build.ArtifactStagingDirectory)/results.xml \\
                --artifacts-dir $(Build.ArtifactStagingDirectory)/artifacts
            displayName: 'Run tests'
            env:
              OWL_API_KEY: $(OWL_API_KEY)

          - task: PublishTestResults@2
            condition: always()
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: '$(Build.ArtifactStagingDirectory)/results.xml'
              failTaskOnFailedTests: true

          - task: PublishBuildArtifacts@1
            condition: always()
            inputs:
              PathtoPublish: '$(Build.ArtifactStagingDirectory)/artifacts'
              ArtifactName: 'test-artifacts'
              publishLocation: 'Container'
'''

    def _generate_circleci(self, context: dict[str, Any]) -> str:
        """Generate CircleCI configuration."""
        test_paths_str = " ".join(context["test_paths"])
        parallel_str = "--parallel" if context["parallel"] else ""

        env_vars = "\n".join(
            f"      {k}: {v}" for k, v in context["custom_variables"].items()
        )

        parallelism = f"parallelism: {context['node_count']}" if context["node_count"] > 1 else ""

        return f'''version: 2.1

orbs:
  python: circleci/python@2.1

executors:
  autoqa-executor:
    docker:
      - image: cimg/python:{context["python_version"]}
      - image: cimg/redis:7.0
    resource_class: medium

jobs:
  test:
    executor: autoqa-executor
    {parallelism}
    environment:
      AUTOQA_ENVIRONMENT: {context["environment"]}
{env_vars}
    steps:
      - checkout

      - python/install-packages:
          pkg-manager: pip
          packages: autoqa-ai-testing

      - run:
          name: Run AutoQA Tests
          command: |
            autoqa run {test_paths_str} {parallel_str} \\
              --environment $AUTOQA_ENVIRONMENT \\
              --output-format junit \\
              --output-file results.xml \\
              --artifacts-dir ./artifacts
          no_output_timeout: {context["timeout_minutes"]}m

      - store_test_results:
          path: results.xml

      - store_artifacts:
          path: artifacts
          destination: test-artifacts

workflows:
  version: 2
  test:
    jobs:
      - test:
          filters:
            branches:
              only:
                - main
                - develop
'''

    def save(
        self,
        provider: CIProvider,
        output_path: str | Path,
        **kwargs: Any,
    ) -> Path:
        """
        Generate and save CI configuration to file.

        Args:
            provider: CI/CD provider
            output_path: Output file path
            **kwargs: Arguments passed to generate()

        Returns:
            Path to saved file
        """
        content = self.generate(provider, **kwargs)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

        self._log.info("CI configuration saved", provider=provider, path=str(path))
        return path
