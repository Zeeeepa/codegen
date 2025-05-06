"""
Implementation rules for PR analysis.

This module provides rules for analyzing implementation details in pull requests,
including performance, error handling, and documentation.
"""

import logging
import re
from typing import Dict, List, Optional, Any, ClassVar, Set

from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule
from codegen_on_oss.analysis.pr_analysis.git.models import File, FileStatus


logger = logging.getLogger(__name__)


class PerformanceRule(BaseRule):
    """
    Rule for checking performance issues.
    
    This rule checks for potential performance issues in the pull request,
    including inefficient algorithms, unnecessary computations, and other
    performance concerns.
    """
    
    rule_id = 'performance'
    name = 'Performance'
    description = 'Checks for potential performance issues in the pull request'
    
    def run(self) -> Dict[str, Any]:
        """
        Run the performance rule.
        
        Returns:
            Rule results
        """
        logger.info(f"Running performance rule for PR #{self.context.pull_request.number}")
        
        # Get files changed in the PR
        files = self.context.pull_request.files
        
        # Filter for code files
        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue
            
            # Check if file is a code file
            if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                filtered_files.append(file)
        
        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for performance issues")
        
        # Check performance for each file
        issues = []
        for file in filtered_files:
            file_issues = self._check_file_performance(file)
            issues.extend(file_issues)
        
        # Return results
        if not issues:
            return self.success("No performance issues found")
        elif len(issues) <= self.get_config('warning_threshold', 3):
            return self.warning(
                f"Found {len(issues)} potential performance issues",
                {'issues': issues}
            )
        else:
            return self.error(
                f"Found {len(issues)} potential performance issues",
                {'issues': issues}
            )
    
    def _check_file_performance(self, file: File) -> List[Dict[str, Any]]:
        """
        Check performance issues for a file.
        
        Args:
            file: File to check
            
        Returns:
            List of performance issues
        """
        # Get file content
        try:
            content = self.context.cache.get(f"file_content_{file.filename}")
            if content is None:
                repo_operator = self.context.cache.get('repo_operator')
                if repo_operator:
                    content = repo_operator.get_file_content(file.filename)
                    self.context.cache[f"file_content_{file.filename}"] = content
        except Exception as e:
            logger.error(f"Failed to get content of file '{file.filename}': {e}")
            return [{
                'file': file.filename,
                'line': 0,
                'message': f"Failed to check file: {str(e)}"
            }]
        
        if content is None:
            return [{
                'file': file.filename,
                'line': 0,
                'message': "Failed to get file content"
            }]
        
        # Check performance issues
        issues = []
        
        if file.filename.endswith('.py'):
            # Check Python performance issues
            
            # Check for nested loops
            nested_loop_pattern = r'for\s+.*\s+in\s+.*:.*\n\s+for\s+.*\s+in\s+.*:'
            nested_loops = re.finditer(nested_loop_pattern, content, re.MULTILINE)
            for match in nested_loops:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Nested loops may cause performance issues for large datasets"
                })
            
            # Check for inefficient list operations
            inefficient_patterns = [
                (r'for\s+.*\s+in\s+range\(len\((.*?)\)\):', "Using range(len(x)) instead of iterating directly"),
                (r'\[.*for\s+.*\s+in\s+.*\s+if\s+.*\]', "List comprehension with filter might be better as a generator expression"),
                (r'\.append\(.*\)\s+.*\.append\(.*\)', "Multiple .append() calls might be better as extend() or a list comprehension"),
            ]
            
            for pattern, message in inefficient_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': file.filename,
                        'line': line_number,
                        'message': message
                    })
        
        elif file.filename.endswith(('.js', '.ts', '.tsx', '.jsx')):
            # Check JavaScript/TypeScript performance issues
            
            # Check for nested loops
            nested_loop_pattern = r'for\s*\(.*\).*\{.*\n.*for\s*\(.*\)'
            nested_loops = re.finditer(nested_loop_pattern, content, re.MULTILINE)
            for match in nested_loops:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Nested loops may cause performance issues for large datasets"
                })
            
            # Check for inefficient array operations
            inefficient_patterns = [
                (r'\.forEach\(.*\).*\.filter\(.*\)', "Chaining .forEach() and .filter() might be inefficient"),
                (r'\.indexOf\(.*\)\s*!=\s*-1', "Using .indexOf() != -1 instead of .includes()"),
                (r'for\s*\(.*\s+of\s+.*\).*\.push\(', "Using for...of with .push() might be better as .map() or .flatMap()"),
            ]
            
            for pattern, message in inefficient_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    issues.append({
                        'file': file.filename,
                        'line': line_number,
                        'message': message
                    })
        
        return issues


class ErrorHandlingRule(BaseRule):
    """
    Rule for checking error handling.
    
    This rule checks for proper error handling in the pull request,
    including try-except blocks, error propagation, and error logging.
    """
    
    rule_id = 'error_handling'
    name = 'Error Handling'
    description = 'Checks for proper error handling in the pull request'
    
    def run(self) -> Dict[str, Any]:
        """
        Run the error handling rule.
        
        Returns:
            Rule results
        """
        logger.info(f"Running error handling rule for PR #{self.context.pull_request.number}")
        
        # Get files changed in the PR
        files = self.context.pull_request.files
        
        # Filter for code files
        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue
            
            # Check if file is a code file
            if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                filtered_files.append(file)
        
        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for error handling issues")
        
        # Check error handling for each file
        issues = []
        for file in filtered_files:
            file_issues = self._check_file_error_handling(file)
            issues.extend(file_issues)
        
        # Return results
        if not issues:
            return self.success("No error handling issues found")
        elif len(issues) <= self.get_config('warning_threshold', 3):
            return self.warning(
                f"Found {len(issues)} error handling issues",
                {'issues': issues}
            )
        else:
            return self.error(
                f"Found {len(issues)} error handling issues",
                {'issues': issues}
            )
    
    def _check_file_error_handling(self, file: File) -> List[Dict[str, Any]]:
        """
        Check error handling for a file.
        
        Args:
            file: File to check
            
        Returns:
            List of error handling issues
        """
        # Get file content
        try:
            content = self.context.cache.get(f"file_content_{file.filename}")
            if content is None:
                repo_operator = self.context.cache.get('repo_operator')
                if repo_operator:
                    content = repo_operator.get_file_content(file.filename)
                    self.context.cache[f"file_content_{file.filename}"] = content
        except Exception as e:
            logger.error(f"Failed to get content of file '{file.filename}': {e}")
            return [{
                'file': file.filename,
                'line': 0,
                'message': f"Failed to check file: {str(e)}"
            }]
        
        if content is None:
            return [{
                'file': file.filename,
                'line': 0,
                'message': "Failed to get file content"
            }]
        
        # Check error handling issues
        issues = []
        
        if file.filename.endswith('.py'):
            # Check Python error handling issues
            
            # Check for bare except clauses
            bare_except_pattern = r'except\s*:'
            bare_excepts = re.finditer(bare_except_pattern, content)
            for match in bare_excepts:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Bare except clause should specify exception types"
                })
            
            # Check for pass in except blocks
            pass_in_except_pattern = r'except.*:\s*\n\s*pass'
            pass_in_excepts = re.finditer(pass_in_except_pattern, content, re.MULTILINE)
            for match in pass_in_excepts:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Empty except block with pass may hide errors"
                })
            
            # Check for missing logging in except blocks
            missing_logging_pattern = r'except.*:(?!\s*\n\s*(?:logger|logging|print|raise|return|break|continue|sys\.stderr))'
            missing_loggings = re.finditer(missing_logging_pattern, content, re.MULTILINE)
            for match in missing_loggings:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Exception caught but not logged or re-raised"
                })
        
        elif file.filename.endswith(('.js', '.ts', '.tsx', '.jsx')):
            # Check JavaScript/TypeScript error handling issues
            
            # Check for empty catch blocks
            empty_catch_pattern = r'catch\s*\(.*\)\s*\{\s*\}'
            empty_catches = re.finditer(empty_catch_pattern, content)
            for match in empty_catches:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Empty catch block may hide errors"
                })
            
            # Check for missing error handling in promises
            missing_catch_pattern = r'\.then\(.*\)(?!\s*\.catch)'
            missing_catches = re.finditer(missing_catch_pattern, content)
            for match in missing_catches:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Promise chain missing .catch() handler"
                })
            
            # Check for missing error handling in async/await
            missing_try_catch_pattern = r'async\s+function.*\{\s*(?!.*try).*await'
            missing_try_catches = re.finditer(missing_try_catch_pattern, content, re.MULTILINE)
            for match in missing_try_catches:
                line_number = content[:match.start()].count('\n') + 1
                issues.append({
                    'file': file.filename,
                    'line': line_number,
                    'message': "Async function with await but no try/catch block"
                })
        
        return issues


class DocumentationRule(BaseRule):
    """
    Rule for checking documentation.
    
    This rule checks for proper documentation in the pull request,
    including docstrings, comments, and other documentation.
    """
    
    rule_id = 'documentation'
    name = 'Documentation'
    description = 'Checks for proper documentation in the pull request'
    
    def run(self) -> Dict[str, Any]:
        """
        Run the documentation rule.
        
        Returns:
            Rule results
        """
        logger.info(f"Running documentation rule for PR #{self.context.pull_request.number}")
        
        # Get files changed in the PR
        files = self.context.pull_request.files
        
        # Filter for code files
        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue
            
            # Check if file is a code file
            if file.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx')):
                filtered_files.append(file)
        
        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for documentation issues")
        
        # Check documentation for each file
        issues = []
        for file in filtered_files:
            file_issues = self._check_file_documentation(file)
            issues.extend(file_issues)
        
        # Return results
        if not issues:
            return self.success("No documentation issues found")
        elif len(issues) <= self.get_config('warning_threshold', 5):
            return self.warning(
                f"Found {len(issues)} documentation issues",
                {'issues': issues}
            )
        else:
            return self.error(
                f"Found {len(issues)} documentation issues",
                {'issues': issues}
            )
    
    def _check_file_documentation(self, file: File) -> List[Dict[str, Any]]:
        """
        Check documentation for a file.
        
        Args:
            file: File to check
            
        Returns:
            List of documentation issues
        """
        # Get file content
        try:
            content = self.context.cache.get(f"file_content_{file.filename}")
            if content is None:
                repo_operator = self.context.cache.get('repo_operator')
                if repo_operator:
                    content = repo_operator.get_file_content(file.filename)
                    self.context.cache[f"file_content_{file.filename}"] = content
        except Exception as e:
            logger.error(f"Failed to get content of file '{file.filename}': {e}")
            return [{
                'file': file.filename,
                'line': 0,
                'message': f"Failed to check file: {str(e)}"
            }]
        
        if content is None:
            return [{
                'file': file.filename,
                'line': 0,
                'message': "Failed to get file content"
            }]
        
        # Check documentation issues
        issues = []
        
        if file.filename.endswith('.py'):
            # Check Python documentation issues
            
            # Check for module docstring
            if not re.search(r'^""".*"""', content, re.DOTALL) and not re.search(r'^\'\'\'.*\'\'\'', content, re.DOTALL):
                issues.append({
                    'file': file.filename,
                    'line': 1,
                    'message': "Module is missing a docstring"
                })
            
            # Check for class docstrings
            class_pattern = r'class\s+(\w+).*:'
            class_matches = re.finditer(class_pattern, content)
            for match in class_matches:
                class_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # Check if class has a docstring
                class_pos = match.end()
                next_lines = content[class_pos:class_pos + 200]  # Look at the next 200 characters
                if not re.search(r'^\s*"""', next_lines, re.MULTILINE) and not re.search(r'^\s*\'\'\'', next_lines, re.MULTILINE):
                    issues.append({
                        'file': file.filename,
                        'line': line_number,
                        'message': f"Class '{class_name}' is missing a docstring"
                    })
            
            # Check for function docstrings
            func_pattern = r'def\s+(\w+)\s*\(.*\).*:'
            func_matches = re.finditer(func_pattern, content)
            for match in func_matches:
                func_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # Skip if it's a special method (e.g., __init__)
                if func_name.startswith('__') and func_name.endswith('__'):
                    continue
                
                # Check if function has a docstring
                func_pos = match.end()
                next_lines = content[func_pos:func_pos + 200]  # Look at the next 200 characters
                if not re.search(r'^\s*"""', next_lines, re.MULTILINE) and not re.search(r'^\s*\'\'\'', next_lines, re.MULTILINE):
                    issues.append({
                        'file': file.filename,
                        'line': line_number,
                        'message': f"Function '{func_name}' is missing a docstring"
                    })
        
        elif file.filename.endswith(('.js', '.ts', '.tsx', '.jsx')):
            # Check JavaScript/TypeScript documentation issues
            
            # Check for file-level JSDoc comment
            if not re.search(r'^/\*\*.*\*/', content, re.DOTALL):
                issues.append({
                    'file': file.filename,
                    'line': 1,
                    'message': "File is missing a JSDoc comment"
                })
            
            # Check for class JSDoc comments
            class_pattern = r'(?:export\s+)?class\s+(\w+)'
            class_matches = re.finditer(class_pattern, content)
            for match in class_matches:
                class_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # Check if class has a JSDoc comment
                prev_lines = content[max(0, match.start() - 200):match.start()]  # Look at the previous 200 characters
                if not re.search(r'/\*\*.*\*/', prev_lines, re.DOTALL):
                    issues.append({
                        'file': file.filename,
                        'line': line_number,
                        'message': f"Class '{class_name}' is missing a JSDoc comment"
                    })
            
            # Check for function JSDoc comments
            func_patterns = [
                r'(?:export\s+)?function\s+(\w+)\s*\(',  # function declaration
                r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(',  # export function
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',  # arrow function
                r'(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\(',  # class method
            ]
            
            for pattern in func_patterns:
                func_matches = re.finditer(pattern, content)
                for match in func_matches:
                    func_name = match.group(1)
                    line_number = content[:match.start()].count('\n') + 1
                    
                    # Check if function has a JSDoc comment
                    prev_lines = content[max(0, match.start() - 200):match.start()]  # Look at the previous 200 characters
                    if not re.search(r'/\*\*.*\*/', prev_lines, re.DOTALL):
                        issues.append({
                            'file': file.filename,
                            'line': line_number,
                            'message': f"Function '{func_name}' is missing a JSDoc comment"
                        })
        
        return issues

