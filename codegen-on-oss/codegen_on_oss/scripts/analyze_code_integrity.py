#!/usr/bin/env python3
"""
Script to analyze code integrity in a repository.

This script analyzes code integrity in a repository, including:
- Finding all functions and classes
- Identifying errors in functions and classes
- Detecting improper parameter usage
- Finding incorrect function callback points
- Comparing error counts between branches
- Analyzing code complexity and duplication
- Checking for type hint usage
- Detecting unused imports
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import yaml
from codegen import Codebase
from codegen.sdk.core.codebase import Codebase

from codegen_on_oss.analysis.code_integrity_analyzer import (
    CodeIntegrityAnalyzer,
    analyze_pr,
    compare_branches,
)
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
