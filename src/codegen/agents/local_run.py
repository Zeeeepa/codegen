"""Local run of the agent."""

import click

from codegen.agents.code_agent import CodeAgent
from codegen.sdk.core.codebase import Codebase

DEFAULT_PROMPT = """
Add a notion integration to the codebase. View similar integrations for linear.
Please view the existing integrations for linear.
- src/codegen/extensions/clients/linear.py
"""


@click.command()
@click.option("--prompt", help="The prompt to run the agent with.", type=str, default=DEFAULT_PROMPT)
@click.option("--model", help="The model to use.", type=str, default="claude-3-5-sonnet-latest")
@click.option("--model-provider", help="The model provider to use.", type=str, default="anthropic")
@click.option("--repo-full-name", help="The repo full name to use.", type=str, default="codegen-sh/cloud")
def main(prompt, model, model_provider, repo_full_name):
    codebase = Codebase.from_repo(repo_full_name=repo_full_name)
    agent = CodeAgent(codebase=codebase, tags=["local_test"], model_name=model, model_provider=model_provider)
    agent.run(prompt)


if __name__ == "__main__":
    main()
