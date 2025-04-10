"""This is the harness for running an AI agent on the SWE Bench dataset."""

#!/usr/bin/env python
import json
import pprint
import random
import subprocess
import sys
from pathlib import Path

import lox

from codegen import Codebase
from codegen.agents.code.code_agent import CodeAgent
from codegen.configs.models.codebase import CodebaseConfig
from codegen.extensions.swebench.utils import (
    SweBenchExample,
    get_swe_bench_examples,
    load_predictions,
)
