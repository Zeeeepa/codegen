import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.interfaces.editable import Editable
from codegen.visualizations.api.visualization_api import router
from codegen.visualizations.enums import ElementType, SelectedElement
from codegen.visualizations.visualization_manager import VisualizationManager


class TestVisualizationAPI(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Mock the RepoOperator
        self.mock_op = MagicMock(spec=RepoOperator)
        self.mock_op.base_dir = self.temp_dir.name
        self.mock_op.folder_exists.return_value = False
        
        # Create the visualization manager
        self.viz_manager = VisualizationManager(self.mock_op)
        
        # Create a mock codebase
        self.mock_codebase = MagicMock(spec=Codebase)
        
        # Create a mock element
        self.mock_element = MagicMock(spec=Editable)
        self.mock_element.name = "test_element"
        self.mock_element.node_id = "test_id"
        self.mock_element.viz = MagicMock()
        
        # Set up paths
        self.viz_path = os.path.join(self.temp_dir.name, "codegen-graphviz")
        self.viz_file_path = os.path.join(self.viz_path, "graph.json")
        self.selection_file_path = os.path.join(self.viz_path, "selection.json")
        
        # Create the visualization directory
        os.makedirs(self.viz_path, exist_ok=True)
        
        # Create a FastAPI app and add the router
        self.app = FastAPI()
        self.app.include_router(router)
        
        # Create a test client
        self.client = TestClient(self.app)
        
        # Add middleware to set the visualization manager and codebase in the request state
        @self.app.middleware("http")
        async def add_viz_manager(request, call_next):
            request.state.viz_manager = self.viz_manager
            request.state.codebase = self.mock_codebase
            response = await call_next(request)
            return response
    
    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()
    
    def test_get_graph_data(self):
        # Create a mock graph file
        graph_data = {"test": "data"}
        os.makedirs(os.path.dirname(self.viz_file_path), exist_ok=True)
        with open(self.viz_file_path, "w") as f:
            json.dump(graph_data, f)
        
        # Make the request
        response = self.client.get("/api/visualization/graph")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), graph_data)
    
    def test_get_selection_data(self):
        # Create a mock selection file
        selection_data = {"test_id": {"type": "symbol", "id": "test_id", "name": "test_element"}}
        os.makedirs(os.path.dirname(self.selection_file_path), exist_ok=True)
        with open(self.selection_file_path, "w") as f:
            json.dump(selection_data, f)
        
        # Make the request
        response = self.client.get("/api/visualization/selection")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), selection_data)
    
    def test_select_element(self):
        # Mock the codebase to return the mock element
        self.mock_codebase.symbols = [self.mock_element]
        
        # Mock the select_element method
        mock_selected = SelectedElement(
            type=ElementType.SYMBOL,
            id="test_id",
            name="test_element",
            methods=["method1", "method2"],
            related_elements=["related1", "related2"]
        )
        
        with patch.object(self.viz_manager, "select_element", return_value=mock_selected):
            # Make the request
            response = self.client.post(
                "/api/visualization/select",
                json={"id": "test_id"}
            )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["id"], "test_id")
            self.assertEqual(response.json()["name"], "test_element")
            self.assertEqual(response.json()["type"], "symbol")
            self.assertEqual(len(response.json()["methods"]), 2)
            self.assertEqual(len(response.json()["related_elements"]), 2)
    
    def test_deselect_element(self):
        # Make the request
        response = self.client.post(
            "/api/visualization/deselect",
            json={"id": "test_id"}
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})
    
    def test_clear_selection(self):
        # Make the request
        response = self.client.post("/api/visualization/clear-selection")
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})


if __name__ == "__main__":
    unittest.main()

