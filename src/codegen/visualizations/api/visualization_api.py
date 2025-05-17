import json
import os
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.enums import SelectedElement
from codegen.visualizations.visualization_manager import VisualizationManager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


class SelectElementRequest(BaseModel):
    id: str


class SelectElementResponse(BaseModel):
    id: str
    name: str
    type: str
    methods: List[Dict[str, str]]
    related_elements: List[Dict[str, str]]


@router.get("/graph")
async def get_graph_data(request: Request):
    """Get the graph visualization data."""
    try:
        # Get the visualization manager from the request state
        viz_manager = request.state.viz_manager
        
        # Check if the graph file exists
        if not os.path.exists(viz_manager.viz_file_path):
            raise HTTPException(status_code=404, detail="Graph data not found")
        
        # Read the graph data from the file
        with open(viz_manager.viz_file_path, "r") as f:
            graph_data = json.load(f)
        
        return graph_data
    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/selection")
async def get_selection_data(request: Request):
    """Get the selection data."""
    try:
        # Get the visualization manager from the request state
        viz_manager = request.state.viz_manager
        
        # Check if the selection file exists
        if not os.path.exists(viz_manager.selection_file_path):
            return {}
        
        # Read the selection data from the file
        with open(viz_manager.selection_file_path, "r") as f:
            selection_data = json.load(f)
        
        return selection_data
    except Exception as e:
        logger.error(f"Error getting selection data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select")
async def select_element(request: Request, select_request: SelectElementRequest):
    """Select an element in the visualization."""
    try:
        # Get the visualization manager from the request state
        viz_manager = request.state.viz_manager
        
        # Get the codebase from the request state
        codebase = request.state.codebase
        
        # Find the element in the codebase
        element = None
        element_id = select_request.id
        
        # Try to find the element in different collections
        for collection_name in ["symbols", "files", "functions", "classes"]:
            if hasattr(codebase, collection_name):
                collection = getattr(codebase, collection_name)
                for item in collection:
                    if hasattr(item, "node_id") and item.node_id == element_id:
                        element = item
                        break
                    elif hasattr(item, "span") and str(item.span) == element_id:
                        element = item
                        break
            
            if element:
                break
        
        if not element:
            raise HTTPException(status_code=404, detail=f"Element with ID {element_id} not found")
        
        # Select the element
        selected = viz_manager.select_element(element)
        
        # Convert the selected element to a response
        response = SelectElementResponse(
            id=selected.id,
            name=selected.name,
            type=selected.type,
            methods=[{"name": method, "id": f"{selected.id}_{method}"} for method in (selected.methods or [])],
            related_elements=[
                {"name": related, "id": f"related_{i}", "type": "unknown"}
                for i, related in enumerate(selected.related_elements or [])
            ],
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting element: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deselect")
async def deselect_element(request: Request, select_request: SelectElementRequest):
    """Deselect an element in the visualization."""
    try:
        # Get the visualization manager from the request state
        viz_manager = request.state.viz_manager
        
        # Deselect the element
        viz_manager.deselect_element(select_request.id)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deselecting element: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-selection")
async def clear_selection(request: Request):
    """Clear all selected elements."""
    try:
        # Get the visualization manager from the request state
        viz_manager = request.state.viz_manager
        
        # Clear the selection
        viz_manager.clear_selection()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error clearing selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

