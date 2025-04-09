"""
Enhanced PR Review Agent with planning and research capabilities.
"""

import os
import sys
import logging
import traceback
from logging import getLogger
from typing import Dict, List, Any, Optional, Tuple
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = getLogger("pr_review_agent")

from codegen.agents.code_agent import CodeAgent
from codegen.agents.utils import AgentConfig
from codegen.tools.planning.manager import PlanManager, ProjectPlan, Step, Requirement
from codegen.tools.research.researcher import Researcher, CodeInsight, ResearchResult
from codegen.tools.reflection.reflector import Reflector, ReflectionResult
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
