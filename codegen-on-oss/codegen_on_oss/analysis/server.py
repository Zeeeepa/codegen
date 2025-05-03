"""
Server script for running the code analysis API.
"""

import argparse
import uvicorn
from codegen_on_oss.analysis.analysis import app


def main():
    """Run the code analysis API server."""
    parser = argparse.ArgumentParser(description="Run the code analysis API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    
    args = parser.parse_args()
    
    print(f"Starting code analysis API server on {args.host}:{args.port}")
    print("API documentation available at http://localhost:8000/docs")
    
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

