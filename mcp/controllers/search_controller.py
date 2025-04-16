"""
Search Controller for MCP.

This module provides controllers for search operations in the codebase.
"""

import os
import re
import subprocess
from typing import Dict, List, Optional, Any, Union
from .base import BaseController


class SearchController(BaseController):
    """Controller for search operations."""

    def ripgrep_search(
        self,
        query: str,
        file_extensions: Optional[List[str]] = None,
        files_per_page: int = 10,
        page: int = 1,
        use_regex: bool = False,
    ) -> Dict[str, Any]:
        """Search the codebase using ripgrep or regex pattern matching.

        Args:
            query (str): The search query to find in the codebase.
            file_extensions (Optional[List[str]], optional): Optional list of file extensions to search.
            files_per_page (int, optional): Number of files to return per page. Defaults to 10.
            page (int, optional): Page number to return (1-based). Defaults to 1.
            use_regex (bool, optional): Whether to treat query as a regex pattern. Defaults to False.

        Returns:
            Dict[str, Any]: Search results.
        """
        if not self.codebase:
            return {
                "query": query,
                "file_extensions": file_extensions,
                "files_per_page": files_per_page,
                "page": page,
                "use_regex": use_regex,
                "results": [],
                "total_results": 0,
                "total_pages": 0,
                "error": "No codebase loaded"
            }

        try:
            # Build the ripgrep command
            cmd = ["rg", "--json"]
            
            # Add file extensions if provided
            if file_extensions:
                for ext in file_extensions:
                    cmd.extend(["-g", f"*{ext}"])
            
            # Add regex flag if needed
            if not use_regex:
                cmd.append("-F")  # Fixed strings (not regex)
            
            # Add the query and path
            cmd.append(query)
            cmd.append(self.codebase.path)
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse the results
            results = []
            if result.returncode not in [0, 1]:  # 0 = matches found, 1 = no matches
                return {
                    "query": query,
                    "file_extensions": file_extensions,
                    "files_per_page": files_per_page,
                    "page": page,
                    "use_regex": use_regex,
                    "results": [],
                    "total_results": 0,
                    "total_pages": 0,
                    "error": result.stderr
                }
            
            # Process the JSON output
            import json
            lines = result.stdout.strip().split('\n')
            
            # Group results by file
            file_results = {}
            for line in lines:
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # Process match data
                    if data.get("type") == "match":
                        file_path = data.get("data", {}).get("path", {}).get("text", "")
                        if not file_path:
                            continue
                            
                        # Get relative path to the codebase
                        rel_path = os.path.relpath(file_path, self.codebase.path)
                        
                        # Initialize file entry if not exists
                        if rel_path not in file_results:
                            file_results[rel_path] = {
                                "path": rel_path,
                                "matches": []
                            }
                            
                        # Add match data
                        match_data = data.get("data", {})
                        line_number = match_data.get("line_number", 0)
                        line_text = match_data.get("lines", {}).get("text", "")
                        
                        file_results[rel_path]["matches"].append({
                            "line": line_number,
                            "text": line_text.strip(),
                        })
                except json.JSONDecodeError:
                    continue
            
            # Convert to list and sort by path
            results_list = list(file_results.values())
            results_list.sort(key=lambda x: x["path"])
            
            # Calculate pagination
            total_results = len(results_list)
            total_pages = (total_results + files_per_page - 1) // files_per_page
            
            # Apply pagination
            start_idx = (page - 1) * files_per_page
            end_idx = start_idx + files_per_page
            paginated_results = results_list[start_idx:end_idx]
            
            return {
                "query": query,
                "file_extensions": file_extensions,
                "files_per_page": files_per_page,
                "page": page,
                "use_regex": use_regex,
                "results": paginated_results,
                "total_results": total_results,
                "total_pages": total_pages,
            }
        except Exception as e:
            # Fallback to regex search if ripgrep fails or is not available
            if "No such file or directory" in str(e) and "rg" in str(e):
                return self._regex_search(query, file_extensions, files_per_page, page, use_regex)
            
            return {
                "query": query,
                "file_extensions": file_extensions,
                "files_per_page": files_per_page,
                "page": page,
                "use_regex": use_regex,
                "results": [],
                "total_results": 0,
                "total_pages": 0,
                "error": str(e)
            }
    
    def _regex_search(
        self,
        query: str,
        file_extensions: Optional[List[str]] = None,
        files_per_page: int = 10,
        page: int = 1,
        use_regex: bool = False,
    ) -> Dict[str, Any]:
        """Fallback search using Python's regex module."""
        try:
            # Compile the regex pattern
            if not use_regex:
                # Escape special characters for literal search
                pattern = re.escape(query)
            else:
                pattern = query
                
            regex = re.compile(pattern)
            
            # Get all files in the codebase
            file_results = {}
            
            for root, _, files in os.walk(self.codebase.path):
                for file in files:
                    # Skip files that don't match the extensions
                    if file_extensions:
                        if not any(file.endswith(ext) for ext in file_extensions):
                            continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.codebase.path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        matches = []
                        for i, line in enumerate(lines):
                            if regex.search(line):
                                matches.append({
                                    "line": i + 1,
                                    "text": line.strip(),
                                })
                        
                        if matches:
                            file_results[rel_path] = {
                                "path": rel_path,
                                "matches": matches
                            }
                    except Exception:
                        # Skip files that can't be read
                        continue
            
            # Convert to list and sort by path
            results_list = list(file_results.values())
            results_list.sort(key=lambda x: x["path"])
            
            # Calculate pagination
            total_results = len(results_list)
            total_pages = (total_results + files_per_page - 1) // files_per_page
            
            # Apply pagination
            start_idx = (page - 1) * files_per_page
            end_idx = start_idx + files_per_page
            paginated_results = results_list[start_idx:end_idx]
            
            return {
                "query": query,
                "file_extensions": file_extensions,
                "files_per_page": files_per_page,
                "page": page,
                "use_regex": use_regex,
                "results": paginated_results,
                "total_results": total_results,
                "total_pages": total_pages,
            }
        except Exception as e:
            return {
                "query": query,
                "file_extensions": file_extensions,
                "files_per_page": files_per_page,
                "page": page,
                "use_regex": use_regex,
                "results": [],
                "total_results": 0,
                "total_pages": 0,
                "error": f"Regex search failed: {str(e)}"
            }

    def search_files_by_name(
        self,
        pattern: str,
        directory: Optional[str] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """Find files by name pattern.

        Args:
            pattern (str): Pattern to search for in file names.
            directory (Optional[str], optional): Directory to search in. Defaults to None (root).
            recursive (bool, optional): Whether to search recursively. Defaults to True.

        Returns:
            Dict[str, Any]: Search results.
        """
        if not self.codebase:
            return {
                "pattern": pattern,
                "directory": directory,
                "recursive": recursive,
                "results": [],
                "total_results": 0,
                "error": "No codebase loaded"
            }

        try:
            # Determine the search directory
            search_dir = self.codebase.path
            if directory:
                search_dir = os.path.join(search_dir, directory)
                
            # Compile the regex pattern
            try:
                regex = re.compile(pattern)
            except re.error:
                # If the pattern is not a valid regex, treat it as a literal string
                regex = re.compile(re.escape(pattern))
            
            # Find matching files
            results = []
            
            if recursive:
                # Walk the directory tree
                for root, _, files in os.walk(search_dir):
                    for file in files:
                        if regex.search(file):
                            # Get the path relative to the codebase
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, self.codebase.path)
                            
                            results.append({
                                "path": rel_path,
                                "name": file,
                                "directory": os.path.dirname(rel_path),
                            })
            else:
                # Only search the specified directory
                for file in os.listdir(search_dir):
                    if os.path.isfile(os.path.join(search_dir, file)) and regex.search(file):
                        # Get the path relative to the codebase
                        full_path = os.path.join(search_dir, file)
                        rel_path = os.path.relpath(full_path, self.codebase.path)
                        
                        results.append({
                            "path": rel_path,
                            "name": file,
                            "directory": os.path.dirname(rel_path),
                        })
            
            # Sort results by path
            results.sort(key=lambda x: x["path"])
            
            return {
                "pattern": pattern,
                "directory": directory,
                "recursive": recursive,
                "results": results,
                "total_results": len(results),
            }
        except Exception as e:
            return {
                "pattern": pattern,
                "directory": directory,
                "recursive": recursive,
                "results": [],
                "total_results": 0,
                "error": str(e)
            }

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Search for code semantically using embeddings.

        Args:
            query (str): Semantic query to search for.
            limit (int, optional): Maximum number of results to return. Defaults to 10.
            threshold (float, optional): Similarity threshold. Defaults to 0.7.

        Returns:
            Dict[str, Any]: Search results.
        """
        if not self.codebase:
            return {
                "query": query,
                "limit": limit,
                "threshold": threshold,
                "results": [],
                "total_results": 0,
                "error": "No codebase loaded"
            }

        try:
            # In a real implementation, this would use embeddings to perform semantic search
            # For now, we'll implement a simple keyword-based search as a placeholder
            
            # Extract keywords from the query
            keywords = query.lower().split()
            
            # Search for files containing these keywords
            results = []
            
            for root, _, files in os.walk(self.codebase.path):
                for file in files:
                    # Skip non-text files
                    if file.endswith(('.jpg', '.png', '.gif', '.pdf', '.zip', '.exe')):
                        continue
                        
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.codebase.path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            
                        # Calculate a simple similarity score based on keyword frequency
                        score = 0
                        for keyword in keywords:
                            score += content.count(keyword) / len(content)
                            
                        # Normalize the score
                        score = score / len(keywords) if keywords else 0
                        
                        # Add to results if above threshold
                        if score >= threshold:
                            # Extract a snippet containing the first match
                            snippet = ""
                            for keyword in keywords:
                                idx = content.find(keyword)
                                if idx >= 0:
                                    start = max(0, idx - 50)
                                    end = min(len(content), idx + 50)
                                    snippet = content[start:end]
                                    break
                            
                            results.append({
                                "path": rel_path,
                                "score": score,
                                "snippet": snippet,
                            })
                    except Exception:
                        # Skip files that can't be read
                        continue
            
            # Sort by score (descending)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Apply limit
            results = results[:limit]
            
            return {
                "query": query,
                "limit": limit,
                "threshold": threshold,
                "results": results,
                "total_results": len(results),
            }
        except Exception as e:
            return {
                "query": query,
                "limit": limit,
                "threshold": threshold,
                "results": [],
                "total_results": 0,
                "error": str(e)
            }
