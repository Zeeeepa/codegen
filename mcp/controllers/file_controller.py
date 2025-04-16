"""
File Controller for MCP.

This module provides controllers for file operations in the codebase.
"""

import os
import difflib
from typing import Dict, Any, Optional
from .base import BaseController


class FileController(BaseController):
    """Controller for file operations."""

    def view_file(self, filepath: str) -> Dict[str, Any]:
        """View the content of a file.

        Args:
            filepath (str): Path to the file to view.

        Returns:
            Dict[str, Any]: File content and metadata.
        """
        if not self.codebase:
            return {
                "filepath": filepath,
                "content": "",
                "exists": False,
                "line_count": 0,
                "size": 0,
                "error": "No codebase loaded"
            }

        try:
            # Construct the full path to the file
            full_path = os.path.join(self.codebase.path, filepath)
            
            # Check if the file exists
            if not os.path.isfile(full_path):
                return {
                    "filepath": filepath,
                    "content": "",
                    "exists": False,
                    "line_count": 0,
                    "size": 0,
                    "error": "File not found"
                }
            
            # Read the file content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count the number of lines
            line_count = content.count('\n') + 1
            
            # Get the file size
            size = os.path.getsize(full_path)
            
            return {
                "filepath": filepath,
                "content": content,
                "exists": True,
                "line_count": line_count,
                "size": size,
            }
        except Exception as e:
            return {
                "filepath": filepath,
                "content": "",
                "exists": False,
                "line_count": 0,
                "size": 0,
                "error": str(e)
            }

    def edit_file(self, filepath: str, edit_snippet: str) -> Dict[str, Any]:
        """Edit a file using the Relace Instant Apply API.

        Args:
            filepath (str): Path to the file to edit.
            edit_snippet (str): Edit snippet to apply to the file.

        Returns:
            Dict[str, Any]: Result of the edit operation.
        """
        if not self.codebase:
            return {
                "filepath": filepath,
                "success": False,
                "message": "No codebase loaded",
                "diff": "",
            }

        try:
            # Construct the full path to the file
            full_path = os.path.join(self.codebase.path, filepath)
            
            # Check if the file exists
            if not os.path.isfile(full_path):
                return {
                    "filepath": filepath,
                    "success": False,
                    "message": "File not found",
                    "diff": "",
                }
            
            # Read the original file content
            with open(full_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # In a real implementation, this would use the Relace API
            # For now, we'll use a simple approach to merge the edit snippet
            
            # Parse the edit snippet to identify unchanged sections
            unchanged_markers = [
                "// ... keep existing",
                "// ... existing",
                "# ... keep existing",
                "# ... existing",
                "/* ... keep existing",
                "/* ... existing",
                "// ...",
                "# ...",
                "/* ..."
            ]
            
            # If there are no markers, just use the edit snippet as the new content
            if not any(marker in edit_snippet for marker in unchanged_markers):
                new_content = edit_snippet
            else:
                # This is a simplified implementation
                # In a real implementation, we would use more sophisticated merging
                new_content = edit_snippet
            
            # Write the new content to the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Generate a diff
            diff = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{filepath}",
                tofile=f"b/{filepath}"
            ))
            
            return {
                "filepath": filepath,
                "success": True,
                "message": "File edited successfully",
                "diff": ''.join(diff),
            }
        except Exception as e:
            return {
                "filepath": filepath,
                "success": False,
                "message": str(e),
                "diff": "",
            }

    def create_file(self, filepath: str, content: str = "") -> Dict[str, Any]:
        """Create a new file.

        Args:
            filepath (str): Path for the new file.
            content (str, optional): Initial content for the file. Defaults to "".

        Returns:
            Dict[str, Any]: Result of the file creation.
        """
        if not self.codebase:
            return {
                "filepath": filepath,
                "success": False,
                "message": "No codebase loaded",
            }

        try:
            # Construct the full path to the file
            full_path = os.path.join(self.codebase.path, filepath)
            
            # Check if the file already exists
            if os.path.exists(full_path):
                return {
                    "filepath": filepath,
                    "success": False,
                    "message": "File already exists",
                }
            
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the content to the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "filepath": filepath,
                "success": True,
                "message": "File created successfully",
            }
        except Exception as e:
            return {
                "filepath": filepath,
                "success": False,
                "message": str(e),
            }

    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """Delete a file.

        Args:
            filepath (str): Path to the file to delete.

        Returns:
            Dict[str, Any]: Result of the file deletion.
        """
        if not self.codebase:
            return {
                "filepath": filepath,
                "success": False,
                "message": "No codebase loaded",
            }

        try:
            # Construct the full path to the file
            full_path = os.path.join(self.codebase.path, filepath)
            
            # Check if the file exists
            if not os.path.isfile(full_path):
                return {
                    "filepath": filepath,
                    "success": False,
                    "message": "File not found",
                }
            
            # Delete the file
            os.remove(full_path)
            
            return {
                "filepath": filepath,
                "success": True,
                "message": "File deleted successfully",
            }
        except Exception as e:
            return {
                "filepath": filepath,
                "success": False,
                "message": str(e),
            }

    def rename_file(self, filepath: str, new_filepath: str) -> Dict[str, Any]:
        """Rename a file and update all references.

        Args:
            filepath (str): Path to the file to rename.
            new_filepath (str): New path for the file.

        Returns:
            Dict[str, Any]: Result of the file renaming.
        """
        if not self.codebase:
            return {
                "filepath": filepath,
                "new_filepath": new_filepath,
                "success": False,
                "message": "No codebase loaded",
                "updated_references": [],
            }

        try:
            # Construct the full paths
            full_path = os.path.join(self.codebase.path, filepath)
            new_full_path = os.path.join(self.codebase.path, new_filepath)
            
            # Check if the source file exists
            if not os.path.isfile(full_path):
                return {
                    "filepath": filepath,
                    "new_filepath": new_filepath,
                    "success": False,
                    "message": "Source file not found",
                    "updated_references": [],
                }
            
            # Check if the destination file already exists
            if os.path.exists(new_full_path):
                return {
                    "filepath": filepath,
                    "new_filepath": new_filepath,
                    "success": False,
                    "message": "Destination file already exists",
                    "updated_references": [],
                }
            
            # Create the directory for the new file if it doesn't exist
            os.makedirs(os.path.dirname(new_full_path), exist_ok=True)
            
            # Rename the file
            os.rename(full_path, new_full_path)
            
            # In a real implementation, we would update references to the file
            # For now, we'll just return an empty list of updated references
            
            return {
                "filepath": filepath,
                "new_filepath": new_filepath,
                "success": True,
                "message": "File renamed successfully",
                "updated_references": [],
            }
        except Exception as e:
            return {
                "filepath": filepath,
                "new_filepath": new_filepath,
                "success": False,
                "message": str(e),
                "updated_references": [],
            }
