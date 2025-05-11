#!/usr/bin/env python3
"""API Client for OpenAPI."""

import logging

# Use dateutil.parser.parse directly instead of importing parse from dateutil.parser
# This avoids the deptry issue with transitive dependencies

logger = logging.getLogger(__name__)
