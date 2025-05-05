from typing import Annotated, List, Optional

import typer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp_server.server import MCPServer
from mcp_server.tools import Tool

from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
from codegen.cli.mcp.tools.codebase_tools import (
    get_codebase_tools,
    get_codebase_tools_with_codebase,
)
from codegen.cli.mcp.tools.file_tools import get_file_tools
from codegen.cli.mcp.tools.git_tools import get_git_tools
from codegen.cli.mcp.tools.search_tools import get_search_tools
from codegen.cli.mcp.tools.web_tools import get_web_tools

app = typer.Typer()


@app.command()
def run(
    port: int = 8000,
    host: str = "0.0.0.0",
    codebase_path: Optional[str] = None,
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    api_type: Optional[str] = None,
    api_version: Optional[str] = None,
    deployment_id: Optional[str] = None,
    organization: Optional[str] = None,
):
    fastapi_app = FastAPI()
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    tools: List[Tool] = []
    tools.extend(get_file_tools())
    tools.extend(get_git_tools())
    tools.extend(get_search_tools())
    tools.extend(get_web_tools())

    if codebase_path:
        tools.extend(get_codebase_tools_with_codebase(codebase_path))
    else:
        tools.extend(get_codebase_tools())

    # Update function name to reflect graph-sitter instead of codegen.sdk
    @Tool.tool(name="ask_graph_sitter")
    def ask_graph_sitter(query: Annotated[str, "Ask a question to an exper agent for details about any aspect of the graph-sitter core set of classes and utilities"]):
        """
        Ask a question to an expert agent for details about any aspect of the graph-sitter core set of classes and utilities
        """
        return "I'll help you understand graph-sitter! What would you like to know?"

    tools.append(ask_graph_sitter)

    server = MCPServer(
        fastapi_app=fastapi_app,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        model=model,
        api_key=api_key,
        base_url=base_url,
        api_type=api_type,
        api_version=api_version,
        deployment_id=deployment_id,
        organization=organization,
    )

    import uvicorn

    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
