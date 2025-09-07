"""
File and file system-related tools for Serena integration.

Migrated from Serena with updated imports and simplified dependencies.
Includes: ReadFileTool, CreateTextFileTool, ListDirTool, FindFileTool, 
ReplaceRegexTool, SearchForPatternTool
"""

import json
import os
import re
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List

from codegen.sdk.extensions.serena.base.tools_base import (
    Tool, 
    ToolMarkerCanEdit, 
    ToolMarkerOptional,
    SUCCESS_RESULT
)
from codegen.sdk.extensions.serena.utils.text_utils import search_files
from codegen.sdk.extensions.serena.utils.file_system import scan_directory
from codegen.sdk.extensions.serena.utils.project_adapter import ProjectAdapter


class ReadFileTool(Tool):
    """
    Reads a file within the project directory.
    """

    def __init__(self, project_root: str = None, **kwargs):
        super().__init__(project_root, **kwargs)
        self.project_adapter = ProjectAdapter(project_root)

    def apply(self, relative_path: str, start_line: int = 0, end_line: int | None = None, max_answer_chars: int = -1) -> str:
        """
        Reads the given file or a chunk of it. Generally, symbolic operations
        like find_symbol or find_referencing_symbols should be preferred if you know which symbols you are looking for.

        :param relative_path: the relative path to the file to read
        :param start_line: the 0-based index of the first line to be retrieved.
        :param end_line: the 0-based index of the last line to be retrieved (inclusive). If None, read until the end of the file.
        :param max_answer_chars: if the file (chunk) is longer than this number of characters,
            no content will be returned. Don't adjust unless there is really no other way to get the content
            required for the task.
        :return: the full text of the file at the given relative path
        """
        try:
            file_path = Path(self.project_root) / relative_path
            if not file_path.exists():
                return f"Error: File not found: {relative_path}"
            
            if not file_path.is_file():
                return f"Error: Path is not a file: {relative_path}"
            
            # Check if file is within project root
            if not file_path.resolve().is_relative_to(Path(self.project_root).resolve()):
                return f"Error: File is outside project directory: {relative_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result_lines = content.splitlines()
            if end_line is None:
                result_lines = result_lines[start_line:]
            else:
                result_lines = result_lines[start_line : end_line + 1]
            result = "\n".join(result_lines)

            return self._limit_length(result, max_answer_chars)
            
        except Exception as e:
            return f"Error reading file {relative_path}: {str(e)}"

    def _limit_length(self, content: str, max_chars: int) -> str:
        """Limit content length if specified."""
        if max_chars > 0 and len(content) > max_chars:
            return f"Error: Content too long ({len(content)} chars, max {max_chars})"
        return content


class CreateTextFileTool(Tool, ToolMarkerCanEdit):
    """
    Creates/overwrites a file in the project directory.
    """

    def __init__(self, project_root: str = None, **kwargs):
        super().__init__(project_root, **kwargs)
        self.project_adapter = ProjectAdapter(project_root)

    def apply(self, relative_path: str, content: str) -> str:
        """
        Write a new file or overwrite an existing file.

        :param relative_path: the relative path to the file to create
        :param content: the (utf-8-encoded) content to write to the file
        :return: a message indicating success or failure
        """
        try:
            abs_path = (Path(self.project_root) / relative_path).resolve()
            will_overwrite_existing = abs_path.exists()

            # Check if path is within project root
            if not abs_path.is_relative_to(Path(self.project_root).resolve()):
                return f"Error: Cannot create file outside of the project directory: {relative_path}"

            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(content, encoding="utf-8")
            
            answer = f"File created: {relative_path}."
            if will_overwrite_existing:
                answer += " Overwrote existing file."
            return json.dumps(answer)
            
        except Exception as e:
            return f"Error creating file {relative_path}: {str(e)}"


class ListDirTool(Tool):
    """
    Lists files and directories in the given directory (optionally with recursion).
    """

    def __init__(self, project_root: str = None, **kwargs):
        super().__init__(project_root, **kwargs)
        self.project_adapter = ProjectAdapter(project_root)

    def apply(self, relative_path: str, recursive: bool, max_answer_chars: int = -1) -> str:
        """
        Lists all non-gitignored files and directories in the given directory (optionally with recursion).

        :param relative_path: the relative path to the directory to list; pass "." to scan the project root
        :param recursive: whether to scan subdirectories recursively
        :param max_answer_chars: if the output is longer than this number of characters,
            no content will be returned. -1 means the default value from the config will be used.
            Don't adjust unless there is really no other way to get the content required for the task.
        :return: a JSON object with the names of directories and files within the given directory
        """
        try:
            target_path = Path(self.project_root) / relative_path
            if not target_path.exists():
                error_info = {
                    "error": f"Directory not found: {relative_path}",
                    "project_root": self.project_root,
                    "hint": "Check if the path is correct relative to the project root",
                }
                return json.dumps(error_info)

            if not target_path.is_dir():
                return json.dumps({"error": f"Path is not a directory: {relative_path}"})

            dirs, files = scan_directory(
                str(target_path),
                relative_to=self.project_root,
                recursive=recursive,
                is_ignored_dir=self._is_ignored_path,
                is_ignored_file=self._is_ignored_path,
            )

            result = json.dumps({"dirs": dirs, "files": files})
            return self._limit_length(result, max_answer_chars)
            
        except Exception as e:
            return json.dumps({"error": f"Error listing directory {relative_path}: {str(e)}"})

    def _is_ignored_path(self, path: str) -> bool:
        """Simple ignore logic for common patterns."""
        path_obj = Path(path)
        ignore_patterns = [
            '.git', '__pycache__', '.pytest_cache', 'node_modules', 
            '.venv', 'venv', '.env', 'dist', 'build', '.DS_Store'
        ]
        return any(pattern in path_obj.parts for pattern in ignore_patterns)

    def _limit_length(self, content: str, max_chars: int) -> str:
        """Limit content length if specified."""
        if max_chars > 0 and len(content) > max_chars:
            return json.dumps({"error": f"Content too long ({len(content)} chars, max {max_chars})"})
        return content


class FindFileTool(Tool):
    """
    Finds files in the given relative paths
    """

    def __init__(self, project_root: str = None, **kwargs):
        super().__init__(project_root, **kwargs)
        self.project_adapter = ProjectAdapter(project_root)

    def apply(self, file_mask: str, relative_path: str) -> str:
        """
        Finds non-gitignored files matching the given file mask within the given relative path

        :param file_mask: the filename or file mask (using the wildcards * or ?) to search for
        :param relative_path: the relative path to the directory to search in; pass "." to scan the project root
        :return: a JSON object with the list of matching files
        """
        try:
            target_path = Path(self.project_root) / relative_path
            if not target_path.exists():
                return json.dumps({"error": f"Directory not found: {relative_path}"})

            dir_to_scan = str(target_path)

            # find the files by ignoring everything that doesn't match
            def is_ignored_file(abs_path: str) -> bool:
                if self._is_ignored_path(abs_path):
                    return True
                filename = os.path.basename(abs_path)
                return not fnmatch(filename, file_mask)

            dirs, files = scan_directory(
                path=dir_to_scan,
                recursive=True,
                is_ignored_dir=self._is_ignored_path,
                is_ignored_file=is_ignored_file,
                relative_to=self.project_root,
            )

            result = json.dumps({"files": files})
            return result
            
        except Exception as e:
            return json.dumps({"error": f"Error finding files with mask {file_mask}: {str(e)}"})

    def _is_ignored_path(self, path: str) -> bool:
        """Simple ignore logic for common patterns."""
        path_obj = Path(path)
        ignore_patterns = [
            '.git', '__pycache__', '.pytest_cache', 'node_modules', 
            '.venv', 'venv', '.env', 'dist', 'build', '.DS_Store'
        ]
        return any(pattern in path_obj.parts for pattern in ignore_patterns)


class ReplaceRegexTool(Tool, ToolMarkerCanEdit):
    """
    Replaces content in a file by using regular expressions.
    """

    def __init__(self, project_root: str = None, **kwargs):
        super().__init__(project_root, **kwargs)
        self.project_adapter = ProjectAdapter(project_root)

    def apply(
        self,
        relative_path: str,
        regex: str,
        repl: str,
        allow_multiple_occurrences: bool = False,
    ) -> str:
        r"""
        Replaces one or more occurrences of the given regular expression.
        This is the preferred way to replace content in a file whenever the symbol-level
        tools are not appropriate.
        Even large sections of code can be replaced by providing a concise regular expression of
        the form "beginning.*?end-of-text-to-be-replaced".
        Always try to use wildcards to avoid specifying the exact content of the code to be replaced,
        especially if it spans several lines.

        IMPORTANT: REMEMBER TO USE WILDCARDS WHEN APPROPRIATE! I WILL BE VERY UNHAPPY IF YOU WRITE LONG REGEXES WITHOUT USING WILDCARDS INSTEAD!

        :param relative_path: the relative path to the file
        :param regex: a Python-style regular expression, matches of which will be replaced.
            Dot matches all characters, multi-line matching is enabled.
        :param repl: the string to replace the matched content with, which may contain
            backreferences like \1, \2, etc.
            Make sure to escape special characters appropriately, e.g., use `\\n` for a literal `\n`.
        :param allow_multiple_occurrences: if True, the regex may match multiple occurrences in the file
            and all of them will be replaced.
            If this is set to False and the regex matches multiple occurrences, an error will be returned
            (and you may retry with a revised, more specific regex).
        """
        try:
            file_path = Path(self.project_root) / relative_path
            if not file_path.exists():
                return f"Error: File not found: {relative_path}"
            
            # Check if file is within project root
            if not file_path.resolve().is_relative_to(Path(self.project_root).resolve()):
                return f"Error: File is outside project directory: {relative_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            updated_content, n = re.subn(regex, repl, original_content, flags=re.DOTALL | re.MULTILINE)
            
            if n == 0:
                return f"Error: No matches found for regex '{regex}' in file '{relative_path}'."
            
            if not allow_multiple_occurrences and n > 1:
                return (
                    f"Error: Regex '{regex}' matches {n} occurrences in file '{relative_path}'. "
                    "Please revise the regex to be more specific or enable allow_multiple_occurrences if this is expected."
                )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return SUCCESS_RESULT
            
        except Exception as e:
            return f"Error replacing content in {relative_path}: {str(e)}"


class SearchForPatternTool(Tool):
    """
    Performs a search for a pattern in the project.
    """

    def __init__(self, project_root: str = None, **kwargs):
        super().__init__(project_root, **kwargs)
        self.project_adapter = ProjectAdapter(project_root)

    def apply(
        self,
        substring_pattern: str,
        context_lines_before: int = 0,
        context_lines_after: int = 0,
        paths_include_glob: str = "",
        paths_exclude_glob: str = "",
        relative_path: str = "",
        restrict_search_to_code_files: bool = False,
        max_answer_chars: int = -1,
    ) -> str:
        """
        Offers a flexible search for arbitrary patterns in the codebase, including the
        possibility to search in non-code files.
        Generally, symbolic operations like find_symbol or find_referencing_symbols
        should be preferred if you know which symbols you are looking for.

        Pattern Matching Logic:
            For each match, the returned result will contain the full lines where the
            substring pattern is found, as well as optionally some lines before and after it. The pattern will be compiled with
            DOTALL, meaning that the dot will match all characters including newlines.
            This also means that it never makes sense to have .* at the beginning or end of the pattern,
            but it may make sense to have it in the middle for complex patterns.
            If a pattern matches multiple lines, all those lines will be part of the match.
            Be careful to not use greedy quantifiers unnecessarily, it is usually better to use non-greedy quantifiers like .*? to avoid
            matching too much content.

        File Selection Logic:
            The files in which the search is performed can be restricted very flexibly.
            Using `restrict_search_to_code_files` is useful if you are only interested in code symbols (i.e., those
            symbols that can be manipulated with symbolic tools like find_symbol).
            You can also restrict the search to a specific file or directory,
            and provide glob patterns to include or exclude certain files on top of that.
            The globs are matched against relative file paths from the project root (not to the `relative_path` parameter that
            is used to further restrict the search).
            Smartly combining the various restrictions allows you to perform very targeted searches.

        :param substring_pattern: Regular expression for a substring pattern to search for
        :param context_lines_before: Number of lines of context to include before each match
        :param context_lines_after: Number of lines of context to include after each match
        :param paths_include_glob: optional glob pattern specifying files to include in the search.
            Matches against relative file paths from the project root (e.g., "*.py", "src/**/*.ts").
            Only matches files, not directories. If left empty, all non-ignored files will be included.
        :param paths_exclude_glob: optional glob pattern specifying files to exclude from the search.
            Matches against relative file paths from the project root (e.g., "*test*", "**/*_generated.py").
            Takes precedence over paths_include_glob. Only matches files, not directories. If left empty, no files are excluded.
        :param relative_path: only subpaths of this path (relative to the repo root) will be analyzed. If a path to a single
            file is passed, only that will be searched. The path must exist, otherwise a `FileNotFoundError` is raised.
        :param max_answer_chars: if the output is longer than this number of characters,
            no content will be returned.
            -1 means the default value from the config will be used.
            Don't adjust unless there is really no other way to get the content
            required for the task. Instead, if the output is too long, you should
            make a stricter query.
        :param restrict_search_to_code_files: whether to restrict the search to only those files where
            analyzed code symbols can be found. Otherwise, will search all non-ignored files.
            Set this to True if your search is only meant to discover code that can be manipulated with symbolic tools.
            For example, for finding classes or methods from a name pattern.
            Setting to False is a better choice if you also want to search in non-code files, like in html or yaml files,
            which is why it is the default.
        :return: A mapping of file paths to lists of matched consecutive lines.
        """
        try:
            abs_path = os.path.join(self.project_root, relative_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Relative path {relative_path} does not exist.")

            if os.path.isfile(abs_path):
                rel_paths_to_search = [relative_path]
            else:
                dirs, rel_paths_to_search = scan_directory(
                    path=abs_path,
                    recursive=True,
                    is_ignored_dir=self._is_ignored_path,
                    is_ignored_file=self._is_ignored_path,
                    relative_to=self.project_root,
                )
            
            # Filter by code files if requested
            if restrict_search_to_code_files:
                code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs', '.go', '.rb', '.php', '.cs', '.swift', '.kt'}
                rel_paths_to_search = [
                    path for path in rel_paths_to_search 
                    if Path(path).suffix.lower() in code_extensions
                ]

            matches = search_files(
                rel_paths_to_search,
                substring_pattern,
                root_path=self.project_root,
                context_lines_before=context_lines_before,
                context_lines_after=context_lines_after,
                paths_include_glob=paths_include_glob,
                paths_exclude_glob=paths_exclude_glob,
            )
            
            # group matches by file
            file_to_matches: Dict[str, List[str]] = defaultdict(list)
            for match in matches:
                if match.source_file_path:
                    file_to_matches[match.source_file_path].append(match.to_display_string())

            result = json.dumps(dict(file_to_matches))
            return self._limit_length(result, max_answer_chars)
            
        except Exception as e:
            return f"Error searching for pattern '{substring_pattern}': {str(e)}"

    def _is_ignored_path(self, path: str) -> bool:
        """Simple ignore logic for common patterns."""
        path_obj = Path(path)
        ignore_patterns = [
            '.git', '__pycache__', '.pytest_cache', 'node_modules', 
            '.venv', 'venv', '.env', 'dist', 'build', '.DS_Store'
        ]
        return any(pattern in path_obj.parts for pattern in ignore_patterns)

    def _limit_length(self, content: str, max_chars: int) -> str:
        """Limit content length if specified."""
        if max_chars > 0 and len(content) > max_chars:
            return f"Error: Content too long ({len(content)} chars, max {max_chars})"
        return content
