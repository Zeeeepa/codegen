#!/usr/bin/env python3
"""
Minimal test to understand workflows-py usage patterns.
"""

import asyncio
import logging
from workflows import Context, Workflow, step
from workflows.events import StartEvent, StopEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWorkflow(Workflow):
    @step
    async def start_step(self, ctx: Context, ev: StartEvent) -> StopEvent:
        logger.info("Starting simple workflow")
        name = getattr(ev, 'name', 'World')
        return StopEvent(result=f"Hello, {name}!")

async def main():
    workflow = SimpleWorkflow()
    
    # Test 1: Using kwargs
    logger.info("Test 1: Using kwargs")
    try:
        handler = workflow.run(name="Test")
        result = await handler
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Test 2: Using start_event
    logger.info("Test 2: Using start_event")
    try:
        start_event = StartEvent(name="Direct")
        handler = workflow.run(start_event=start_event)
        result = await handler
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
