import logging
import sys

logger = logging.getLogger(__name__)

# Import resource compatibility module
from codegen.sdk.utils.resource_compat import RLIMIT_STACK, RLIM_INFINITY, setrlimit

def set_recursion_limit():
    sys.setrecursionlimit(10**9)
    if sys.platform == "linux":
        logger.info(f"Setting stack limit to {RLIM_INFINITY}")
        setrlimit(RLIMIT_STACK, (RLIM_INFINITY, RLIM_INFINITY))
