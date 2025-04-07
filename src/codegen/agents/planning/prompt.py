"""
Prompt templates for planning in codegen.

This module provides prompt templates for planning agents.
"""

PLAN_CREATION_PROMPT = """
You are a planning assistant. Create a concise, actionable plan with clear steps.
Focus on key milestones rather than detailed sub-steps.
Optimize for clarity and efficiency.

Create a reasonable plan with clear steps to accomplish the task: {task}
"""

PLAN_EXECUTION_PROMPT = """
CURRENT PLAN STATUS:
{plan_status}

YOUR CURRENT TASK:
You are now working on step {step_index}: "{step_text}"

Please execute this step using the appropriate tools. When you're done, provide a summary of what you accomplished.
"""

PLAN_SUMMARY_PROMPT = """
The plan has been completed. Here is the final plan status:

{plan_text}

Please provide a summary of what was accomplished and any final thoughts.
"""
