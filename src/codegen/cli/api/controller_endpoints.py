"""API endpoints for Controller Dashboard operations."""

from typing import Any, Optional

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ControllerAPI:
    """API client for Controller Dashboard operations."""

    def __init__(self):
        """Initialize Controller API client."""
        self.token = get_current_token()
        self.org_id = resolve_org_id() if self.token else None
        self.base_url = API_ENDPOINT
        self.timeout = 30

    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def list_workflows(self, filters: Optional[dict] = None) -> list[dict[str, Any]]:
        """List all workflows with optional filters."""
        try:
            params = {"org_id": self.org_id}
            if filters:
                params.update(filters)
            
            response = requests.get(
                f"{self.base_url}/workflows",
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                workflows = response.json().get("workflows", [])
                logger.info(f"Retrieved {len(workflows)} workflows")
                return workflows
            else:
                logger.error(f"Failed to list workflows: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []

    def get_workflow(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """Get detailed workflow information."""
        try:
            response = requests.get(
                f"{self.base_url}/workflows/{workflow_id}",
                headers=self._get_headers(),
                params={"org_id": self.org_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get workflow: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
            return None

    def create_workflow(self, workflow_data: dict[str, Any]) -> Optional[str]:
        """Create a new workflow."""
        try:
            workflow_data["org_id"] = self.org_id
            
            response = requests.post(
                f"{self.base_url}/workflows",
                headers=self._get_headers(),
                json=workflow_data,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                workflow_id = response.json().get("workflow_id")
                logger.info(f"Created workflow: {workflow_id}")
                return workflow_id
            else:
                logger.error(f"Failed to create workflow: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None

    def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> bool:
        """Update workflow configuration."""
        try:
            response = requests.patch(
                f"{self.base_url}/workflows/{workflow_id}",
                headers=self._get_headers(),
                json=updates,
                params={"org_id": self.org_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Updated workflow: {workflow_id}")
                return True
            else:
                logger.error(f"Failed to update workflow: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return False

    def toggle_workflow(self, workflow_id: str) -> bool:
        """Toggle workflow enabled/disabled status."""
        try:
            response = requests.post(
                f"{self.base_url}/workflows/{workflow_id}/toggle",
                headers=self._get_headers(),
                params={"org_id": self.org_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                new_status = response.json().get("enabled")
                logger.info(f"Toggled workflow {workflow_id} to {new_status}")
                return True
            else:
                logger.error(f"Failed to toggle workflow: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error toggling workflow: {e}")
            return False

    def execute_workflow(self, workflow_id: str, params: Optional[dict] = None) -> Optional[str]:
        """Execute workflow in sandbox."""
        try:
            payload = {
                "workflow_id": workflow_id,
                "org_id": self.org_id,
                "params": params or {}
            }
            
            response = requests.post(
                f"{self.base_url}/workflows/{workflow_id}/execute",
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                run_id = response.json().get("run_id")
                logger.info(f"Started workflow execution: {run_id}")
                return run_id
            else:
                logger.error(f"Failed to execute workflow: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return None

    def list_sandboxes(self, workflow_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List sandbox instances."""
        try:
            params = {"org_id": self.org_id}
            if workflow_id:
                params["workflow_id"] = workflow_id
            
            response = requests.get(
                f"{self.base_url}/sandboxes",
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                sandboxes = response.json().get("sandboxes", [])
                logger.info(f"Retrieved {len(sandboxes)} sandboxes")
                return sandboxes
            else:
                logger.error(f"Failed to list sandboxes: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing sandboxes: {e}")
            return []

    def get_sandbox_status(self, sandbox_id: str) -> Optional[dict[str, Any]]:
        """Get sandbox status and metrics."""
        try:
            response = requests.get(
                f"{self.base_url}/sandboxes/{sandbox_id}/status",
                headers=self._get_headers(),
                params={"org_id": self.org_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get sandbox status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting sandbox status: {e}")
            return None

    def terminate_sandbox(self, sandbox_id: str) -> bool:
        """Terminate sandbox execution."""
        try:
            response = requests.post(
                f"{self.base_url}/sandboxes/{sandbox_id}/terminate",
                headers=self._get_headers(),
                params={"org_id": self.org_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Terminated sandbox: {sandbox_id}")
                return True
            else:
                logger.error(f"Failed to terminate sandbox: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error terminating sandbox: {e}")
            return False

    def get_workflow_metrics(self, workflow_id: str, time_range: Optional[str] = None) -> dict[str, Any]:
        """Get workflow execution metrics."""
        try:
            params = {"org_id": self.org_id}
            if time_range:
                params["time_range"] = time_range
            
            response = requests.get(
                f"{self.base_url}/workflows/{workflow_id}/metrics",
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get workflow metrics: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {e}")
            return {}

    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects."""
        try:
            response = requests.get(
                f"{self.base_url}/projects",
                headers=self._get_headers(),
                params={"org_id": self.org_id},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                projects = response.json().get("projects", [])
                logger.info(f"Retrieved {len(projects)} projects")
                return projects
            else:
                logger.error(f"Failed to list projects: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return []

    def create_project(self, project_data: dict[str, Any]) -> Optional[str]:
        """Create a new project."""
        try:
            project_data["org_id"] = self.org_id
            
            response = requests.post(
                f"{self.base_url}/projects",
                headers=self._get_headers(),
                json=project_data,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                project_id = response.json().get("project_id")
                logger.info(f"Created project: {project_id}")
                return project_id
            else:
                logger.error(f"Failed to create project: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None

    def list_prds(self, project_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List PRDs with optional project filter."""
        try:
            params = {"org_id": self.org_id}
            if project_id:
                params["project_id"] = project_id
            
            response = requests.get(
                f"{self.base_url}/prds",
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                prds = response.json().get("prds", [])
                logger.info(f"Retrieved {len(prds)} PRDs")
                return prds
            else:
                logger.error(f"Failed to list PRDs: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error listing PRDs: {e}")
            return []

    def create_prd(self, prd_data: dict[str, Any]) -> Optional[str]:
        """Create a new PRD."""
        try:
            prd_data["org_id"] = self.org_id
            
            response = requests.post(
                f"{self.base_url}/prds",
                headers=self._get_headers(),
                json=prd_data,
                timeout=self.timeout
            )
            
            if response.status_code == 201:
                prd_id = response.json().get("prd_id")
                logger.info(f"Created PRD: {prd_id}")
                return prd_id
            else:
                logger.error(f"Failed to create PRD: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating PRD: {e}")
            return None


def get_controller_api() -> ControllerAPI:
    """Get Controller API client instance."""
    return ControllerAPI()

