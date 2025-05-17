import os
from typing import Any

from codegen.agents.client.openapi_client.api.agents_api import AgentsApi
from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.models.agent_run_response import AgentRunResponse
from codegen.agents.client.openapi_client.models.create_agent_run_input import CreateAgentRunInput
from codegen.agents.constants import CODEGEN_BASE_API_URL


class AgentTask:
    """Represents an agent run job."""

    def __init__(self, task_data: AgentRunResponse, api_client: ApiClient):
        self.id = task_data.id
        self.org_id = api_client.configuration.org_id if hasattr(api_client.configuration, "org_id") else None
        self.status = task_data.status
        self.result = task_data.result
        self.web_url = task_data.web_url
        self._api_client = api_client
        self._agents_api = AgentsApi(api_client)

    def refresh(self) -> None:
        """Refresh the job status from the API."""
        if self.id is None:
            return

        job_data = self._agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get(
            agent_run_id=int(self.id), org_id=int(self.org_id)
        )

        # Convert API response to dict for attribute access
        job_dict = {}
        if hasattr(job_data, "__dict__"):
            job_dict = job_data.__dict__
        elif isinstance(job_data, dict):
            job_dict = job_data

        self.status = job_dict.get("status")
        self.result = job_dict.get("result")


class Agent:
    """API client for interacting with Codegen AI agents."""

    def __init__(self, token: str, org_id: int | None = None, base_url: str | None = CODEGEN_BASE_API_URL):
        """Initialize a new Agent client.

        Args:
            token: API authentication token
            org_id: Optional organization ID. If not provided, default org will be used.
        """
        self.token = token
        self.org_id = org_id or int(os.environ.get("CODEGEN_ORG_ID", "1"))  # Default to org ID 1 if not specified

        # Configure API client
        config = Configuration(host=base_url)
        config.api_key["Authorization"] = token
        config.api_key_prefix["Authorization"] = "Bearer"
        config.org_id = self.org_id  # Add org_id to configuration
        self.api_client = ApiClient(configuration=config)
        self.agents_api = AgentsApi(self.api_client)

        # Current job
        self.current_job = None

    def run(self, prompt: str) -> AgentTask:
        """Run an agent with the given prompt.

        Args:
            prompt: The prompt to send to the agent.

        Returns:
            An AgentTask object representing the running job.
        """
        # Create the agent run
        create_input = CreateAgentRunInput(prompt=prompt)
        response = self.agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
            org_id=self.org_id, create_agent_run_input=create_input
        )

        # Create a task object from the response
        self.current_job = AgentTask(
            task_data=response,
            api_client=self.api_client,
        )

        return self.current_job

    def get_status(self) -> dict[str, Any] | None:
        """Get the status of the current job.

        Returns:
            dict: A dictionary containing job status information,
                  or None if no job has been run.
        """
        if self.current_job:
            self.current_job.refresh()
            return {"id": self.current_job.id, "status": self.current_job.status, "result": self.current_job.result, "web_url": self.current_job.web_url}
        return None
