"""
MCP Editing Tools
This module defines controllers for editing tools in the MCP server.
These tools provide functionality for semantic editing, pattern replacement, and relace editing.
"""
from typing import Dict, List, Optional, Any, Union, Pattern
import re
import os
import tempfile
import difflib
from pathlib import Path
from .models import Codebase, File, Symbol, Function, Class, Import, SemanticEditTool, ReplacementEditTool

class SemanticEditController:
    """Controller for semantic editing operations."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    
    def create_semantic_edit_tool(self, file: File) -> SemanticEditTool:
        """Create a semantic edit tool for a file.
        
        Args:
            file: The file to create a semantic edit tool for
            
        Returns:
            A SemanticEditTool instance for the file
        """
        return SemanticEditTool(file=file)
    
    def semantic_edit(self, filepath: str, edit_description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply a semantic edit to a file.
        
        Args:
            filepath: Path to the file to edit
            edit_description: Natural language description of the edit to make
            context: Optional additional context for the edit
            
        Returns:
            Dictionary with edit results
        """
        # Get the file
        file = None
        for f in self.codebase.files:
            if f.path == filepath:
                file = f
                break
        
        if not file:
            raise ValueError(f"File not found: {filepath}")
        
        # Create a semantic edit tool
        tool = self.create_semantic_edit_tool(file)
        
        # Get the file content
        file_path = os.path.join(self.codebase.path, filepath)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return {
                "success": False,
                "file": filepath,
                "edit_description": edit_description,
                "context": context,
                "error": f"Failed to read file: {str(e)}"
            }
        
        # In a real implementation, this would use an AI model to generate the edit
        # For now, we'll implement a simple edit based on the description
        
        # Create a modified version based on simple rules
        modified_content = original_content
        
        # Apply some basic transformations based on the edit description
        if "add comment" in edit_description.lower():
            # Add a comment at the top of the file
            comment = f"# {edit_description}\n"
            modified_content = comment + original_content
        
        elif "remove comments" in edit_description.lower():
            # Remove comments (simple implementation)
            lines = original_content.split('\n')
            modified_lines = []
            for line in lines:
                if not line.strip().startswith('#'):
                    modified_lines.append(line)
            modified_content = '\n'.join(modified_lines)
        
        elif "rename function" in edit_description.lower():
            # Extract old and new function names from the description
            words = edit_description.split()
            old_name = None
            new_name = None
            
            for i, word in enumerate(words):
                if word == "from" and i + 1 < len(words):
                    old_name = words[i + 1]
                elif word == "to" and i + 1 < len(words):
                    new_name = words[i + 1]
            
            if old_name and new_name:
                # Simple replacement (in a real implementation, this would be more sophisticated)
                modified_content = re.sub(
                    rf"def\s+{re.escape(old_name)}\s*\(", 
                    f"def {new_name}(", 
                    original_content
                )
        
        # Write the modified content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
        except Exception as e:
            return {
                "success": False,
                "file": filepath,
                "edit_description": edit_description,
                "context": context,
                "error": f"Failed to write file: {str(e)}"
            }
        
        # Generate a diff
        diff = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            modified_content.splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}"
        ))
        
        return {
            "success": True,
            "file": filepath,
            "edit_description": edit_description,
            "context": context,
            "diff": ''.join(diff)
        }

class PatternReplacementController:
    """Controller for pattern replacement operations."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    
    def apply_pattern(self, pattern: str, replacement: str, files: List[File]) -> Dict[str, Any]:
        """Apply a pattern replacement to files.
        
        Args:
            pattern: Regular expression pattern to match
            replacement: Replacement string
            files: List of files to apply the replacement to
            
        Returns:
            Dictionary with replacement results
        """
        # Create a replacement edit tool
        tool = ReplacementEditTool(pattern=pattern, replacement=replacement, files=files)
        
        # Compile the regex pattern
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return {
                "success": False,
                "pattern": pattern,
                "replacement": replacement,
                "files": [f.path for f in files],
                "error": f"Invalid regex pattern: {str(e)}"
            }
        
        # Track the number of matches replaced
        total_matches = 0
        modified_files = []
        
        # Apply the replacement to each file
        for file in files:
            file_path = os.path.join(self.codebase.path, file.path)
            
            try:
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Apply the replacement
                new_content, count = regex.subn(replacement, content)
                
                # If there were matches, write the modified content back to the file
                if count > 0:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    total_matches += count
                    modified_files.append(file.path)
            
            except Exception as e:
                return {
                    "success": False,
                    "pattern": pattern,
                    "replacement": replacement,
                    "files": [f.path for f in files],
                    "error": f"Error processing file {file.path}: {str(e)}"
                }
        
        return {
            "success": True,
            "pattern": pattern,
            "replacement": replacement,
            "files": [f.path for f in files],
            "matches_replaced": total_matches,
            "modified_files": modified_files
        }
    
    def global_replacement_edit(self, pattern: str, replacement: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Apply a global pattern replacement to the codebase.
        
        Args:
            pattern: Regular expression pattern to match
            replacement: Replacement string
            file_pattern: Optional pattern to filter files by path
            
        Returns:
            Dictionary with replacement results
        """
        # Filter files by pattern if provided
        files = self.codebase.files
        if file_pattern:
            try:
                regex = re.compile(file_pattern)
                files = [f for f in files if regex.search(f.path)]
            except re.error as e:
                raise ValueError(f"Invalid file pattern regex: {str(e)}")
        
        # Apply the replacement
        return self.apply_pattern(pattern, replacement, files)

class RelaceEditController:
    """Controller for relace editing operations."""
    
    def __init__(self, codebase: Codebase):
        """Initialize with a codebase reference."""
        self.codebase = codebase
    
    def relace_edit(self, filepath: str, edit_snippet: str) -> Dict[str, Any]:
        """Apply a relace edit to a file.
        
        Args:
            filepath: Path to the file to edit
            edit_snippet: Edit snippet describing the changes to make
            
        Returns:
            Dictionary with edit results
        """
        # Get the file
        file = None
        for f in self.codebase.files:
            if f.path == filepath:
                file = f
                break
        
        if not file:
            raise ValueError(f"File not found: {filepath}")
        
        # Get the file content
        file_path = os.path.join(self.codebase.path, filepath)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return {
                "success": False,
                "file": filepath,
                "edit_snippet_length": len(edit_snippet),
                "error": f"Failed to read file: {str(e)}"
            }
        
        # In a real implementation, this would use the Relace API to merge the edit snippet
        # For now, we'll implement a simple merge algorithm
        
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
        
        # Split the edit snippet into lines
        snippet_lines = edit_snippet.split('\n')
        
        # Identify sections in the original content
        original_lines = original_content.split('\n')
        
        # Create a new content by merging
        new_lines = []
        i = 0
        
        while i < len(snippet_lines):
            line = snippet_lines[i]
            
            # Check if this is a marker for unchanged content
            is_marker = False
            for marker in unchanged_markers:
                if marker in line:
                    is_marker = True
                    
                    # Try to find matching content in the original file
                    # This is a simplified approach - in a real implementation,
                    # we would use more sophisticated matching
                    
                    # Look for content before and after this marker
                    before_context = []
                    after_context = []
                    
                    # Get context before the marker
                    j = i - 1
                    while j >= 0 and j >= i - 5:
                        if not any(m in snippet_lines[j] for m in unchanged_markers):
                            before_context.insert(0, snippet_lines[j])
                        j -= 1
                    
                    # Get context after the marker
                    j = i + 1
                    while j < len(snippet_lines) and j <= i + 5:
                        if not any(m in snippet_lines[j] for m in unchanged_markers):
                            after_context.append(snippet_lines[j])
                        j += 1
                    
                    # Try to find a match in the original content
                    if before_context and after_context:
                        # Look for the before context
                        before_matches = []
                        for k in range(len(original_lines)):
                            if k + len(before_context) <= len(original_lines):
                                if all(original_lines[k + l].strip() == before_context[l].strip() for l in range(len(before_context))):
                                    before_matches.append(k + len(before_context))
                        
                        # Look for the after context
                        after_matches = []
                        for k in range(len(original_lines)):
                            if k + len(after_context) <= len(original_lines):
                                if all(original_lines[k + l].strip() == after_context[l].strip() for l in range(len(after_context))):
                                    after_matches.append(k)
                        
                        # Find pairs of matches that make sense
                        for before_end in before_matches:
                            for after_start in after_matches:
                                if before_end <= after_start:
                                    # We found a potential match
                                    # Include the content between these points
                                    new_lines.extend(original_lines[before_end:after_start])
                                    break
                            else:
                                continue
                            break
                    
                    break
            
            if not is_marker:
                # This is a line to include directly
                new_lines.append(line)
            
            i += 1
        
        # If we didn't find any markers, just use the edit snippet directly
        if not any(any(marker in line for marker in unchanged_markers) for line in snippet_lines):
            new_lines = snippet_lines
        
        # Write the new content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        except Exception as e:
            return {
                "success": False,
                "file": filepath,
                "edit_snippet_length": len(edit_snippet),
                "error": f"Failed to write file: {str(e)}"
            }
        
        # Generate a diff
        diff = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            '\n'.join(new_lines).splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}"
        ))
        
        return {
            "success": True,
            "file": filepath,
            "edit_snippet_length": len(edit_snippet),
            "diff": ''.join(diff)
        }
