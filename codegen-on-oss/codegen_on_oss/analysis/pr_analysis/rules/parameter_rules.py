"""
Parameter rules for PR analysis.

This module provides rules for analyzing parameter validation in pull requests,
including parameter type checking and validation.
"""

import logging
import re
from typing import Dict, List, Optional, Any, ClassVar, Set

from codegen_on_oss.analysis.pr_analysis.rules.base_rule import BaseRule
from codegen_on_oss.analysis.pr_analysis.git.models import File, FileStatus


logger = logging.getLogger(__name__)


class ParameterTypeRule(BaseRule):
    """
    Rule for checking parameter types.
    
    This rule checks for proper type annotations and type checking for
    function parameters in the pull request.
    """
    
    rule_id = 'parameter_type'
    name = 'Parameter Type'
    description = 'Checks for proper type annotations and type checking for function parameters'
    
    def run(self) -> Dict[str, Any]:
        """
        Run the parameter type rule.
        
        Returns:
            Rule results
        """
        logger.info(f"Running parameter type rule for PR #{self.context.pull_request.number}")
        
        # Get files changed in the PR
        files = self.context.pull_request.files
        
        # Filter for Python and TypeScript files
        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue
            
            # Check if file is Python or TypeScript
            if file.filename.endswith(('.py', '.ts', '.tsx')):
                filtered_files.append(file)
        
        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for parameter types")
        
        # Check parameter types for each file
        issues = []
        for file in filtered_files:
            file_issues = self._check_file_parameter_types(file)
            issues.extend(file_issues)
        
        # Return results
        if not issues:
            return self.success("No parameter type issues found")
        elif len(issues) <= self.get_config('warning_threshold', 5):
            return self.warning(
                f"Found {len(issues)} parameter type issues",
                {'issues': issues}
            )
        else:
            return self.error(
                f"Found {len(issues)} parameter type issues",
                {'issues': issues}
            )
    
    def _check_file_parameter_types(self, file: File) -> List[Dict[str, Any]]:
        """
        Check parameter types for a file.
        
        Args:
            file: File to check
            
        Returns:
            List of parameter type issues
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
        
        # Check parameter types
        issues = []
        
        if file.filename.endswith('.py'):
            # Check Python parameter types
            # This is a simplified implementation that looks for function definitions
            # and checks if they have type annotations for parameters
            
            # Regular expression for function definition
            func_def_pattern = r'def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:'
            
            for i, line in enumerate(content.splitlines(), 1):
                match = re.search(func_def_pattern, line)
                if match:
                    func_name = match.group(1)
                    params_str = match.group(2)
                    return_type = match.group(3)
                    
                    # Skip if it's a special method (e.g., __init__)
                    if func_name.startswith('__') and func_name.endswith('__'):
                        continue
                    
                    # Check if return type is missing
                    if not return_type and self.get_config('check_return_types', True):
                        issues.append({
                            'file': file.filename,
                            'line': i,
                            'message': f"Function '{func_name}' is missing return type annotation"
                        })
                    
                    # Check parameter types
                    if params_str.strip():
                        params = [p.strip() for p in params_str.split(',')]
                        for param in params:
                            # Skip self and cls parameters
                            if param in ('self', 'cls'):
                                continue
                            
                            # Check if parameter has type annotation
                            if ':' not in param and not param.startswith('*'):
                                issues.append({
                                    'file': file.filename,
                                    'line': i,
                                    'message': f"Parameter '{param}' in function '{func_name}' is missing type annotation"
                                })
        
        elif file.filename.endswith(('.ts', '.tsx')):
            # Check TypeScript parameter types
            # This is a simplified implementation that looks for function definitions
            # and checks if they have type annotations for parameters
            
            # Regular expression for function definition
            func_def_patterns = [
                r'function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',  # function declaration
                r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',  # export function
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?:=>\s*(?::\s*([^{]+))?\s*{|\s*=>\s*\()',  # arrow function
                r'(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',  # class method
            ]
            
            for i, line in enumerate(content.splitlines(), 1):
                for pattern in func_def_patterns:
                    match = re.search(pattern, line)
                    if match:
                        func_name = match.group(1)
                        params_str = match.group(2)
                        return_type = match.group(3)
                        
                        # Check if return type is missing
                        if not return_type and self.get_config('check_return_types', True):
                            issues.append({
                                'file': file.filename,
                                'line': i,
                                'message': f"Function '{func_name}' is missing return type annotation"
                            })
                        
                        # Check parameter types
                        if params_str.strip():
                            params = [p.strip() for p in params_str.split(',')]
                            for param in params:
                                # Skip rest parameters
                                if param.startswith('...'):
                                    continue
                                
                                # Check if parameter has type annotation
                                if ':' not in param and '=' not in param:
                                    issues.append({
                                        'file': file.filename,
                                        'line': i,
                                        'message': f"Parameter '{param}' in function '{func_name}' is missing type annotation"
                                    })
        
        return issues


class ParameterValidationRule(BaseRule):
    """
    Rule for checking parameter validation.
    
    This rule checks for proper validation of function parameters in the
    pull request, ensuring that parameters are validated before use.
    """
    
    rule_id = 'parameter_validation'
    name = 'Parameter Validation'
    description = 'Checks for proper validation of function parameters'
    
    def run(self) -> Dict[str, Any]:
        """
        Run the parameter validation rule.
        
        Returns:
            Rule results
        """
        logger.info(f"Running parameter validation rule for PR #{self.context.pull_request.number}")
        
        # Get files changed in the PR
        files = self.context.pull_request.files
        
        # Filter for Python and TypeScript files
        filtered_files = []
        for file in files:
            # Skip deleted files
            if file.status == FileStatus.REMOVED:
                continue
            
            # Check if file is Python or TypeScript
            if file.filename.endswith(('.py', '.ts', '.tsx')):
                filtered_files.append(file)
        
        # If no files to check, return success
        if not filtered_files:
            return self.success("No files to check for parameter validation")
        
        # Check parameter validation for each file
        issues = []
        for file in filtered_files:
            file_issues = self._check_file_parameter_validation(file)
            issues.extend(file_issues)
        
        # Return results
        if not issues:
            return self.success("No parameter validation issues found")
        elif len(issues) <= self.get_config('warning_threshold', 5):
            return self.warning(
                f"Found {len(issues)} parameter validation issues",
                {'issues': issues}
            )
        else:
            return self.error(
                f"Found {len(issues)} parameter validation issues",
                {'issues': issues}
            )
    
    def _check_file_parameter_validation(self, file: File) -> List[Dict[str, Any]]:
        """
        Check parameter validation for a file.
        
        Args:
            file: File to check
            
        Returns:
            List of parameter validation issues
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
        
        # Check parameter validation
        issues = []
        
        if file.filename.endswith('.py'):
            # Check Python parameter validation
            # This is a simplified implementation that looks for function definitions
            # and checks if they have validation for parameters
            
            # Regular expression for function definition
            func_def_pattern = r'def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^:]+))?\s*:'
            
            # Find all function definitions
            func_defs = []
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                match = re.search(func_def_pattern, line)
                if match:
                    func_name = match.group(1)
                    params_str = match.group(2)
                    
                    # Skip if it's a special method (e.g., __init__)
                    if func_name.startswith('__') and func_name.endswith('__'):
                        continue
                    
                    # Parse parameters
                    params = []
                    if params_str.strip():
                        for param in [p.strip() for p in params_str.split(',')]:
                            # Skip self and cls parameters
                            if param in ('self', 'cls'):
                                continue
                            
                            # Extract parameter name
                            param_name = param.split(':')[0].split('=')[0].strip()
                            if param_name and not param_name.startswith('*'):
                                params.append(param_name)
                    
                    # Find function body
                    body_start = i
                    body_end = i
                    indent = None
                    for j, body_line in enumerate(lines[i:], i + 1):
                        if not body_line.strip():
                            continue
                        
                        # Determine indentation level
                        if indent is None:
                            indent = len(body_line) - len(body_line.lstrip())
                            body_start = j
                        
                        # Check if we're still in the function body
                        if not body_line.strip() or body_line.startswith(' ' * indent):
                            body_end = j
                        else:
                            break
                    
                    # Check if parameters are validated
                    body = '\n'.join(lines[body_start - 1:body_end])
                    for param in params:
                        # Check for common validation patterns
                        validation_patterns = [
                            rf'if\s+{param}\s+is\s+None',
                            rf'if\s+not\s+{param}',
                            rf'if\s+{param}\s+==\s+None',
                            rf'if\s+{param}\s+!=',
                            rf'if\s+{param}\s+<',
                            rf'if\s+{param}\s+>',
                            rf'if\s+not\s+isinstance\({param},',
                            rf'assert\s+{param}',
                            rf'assert\s+isinstance\({param},',
                            rf'validate_\w+\({param}',
                        ]
                        
                        validated = any(re.search(pattern, body) for pattern in validation_patterns)
                        if not validated:
                            issues.append({
                                'file': file.filename,
                                'line': i,
                                'message': f"Parameter '{param}' in function '{func_name}' may not be properly validated"
                            })
        
        elif file.filename.endswith(('.ts', '.tsx')):
            # Check TypeScript parameter validation
            # This is a simplified implementation that looks for function definitions
            # and checks if they have validation for parameters
            
            # Regular expression for function definition
            func_def_patterns = [
                r'function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',  # function declaration
                r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',  # export function
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?:=>\s*(?::\s*([^{]+))?\s*{|\s*=>\s*\()',  # arrow function
                r'(?:public|private|protected)?\s*(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?\s*{',  # class method
            ]
            
            # Find all function definitions
            func_defs = []
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                for pattern in func_def_patterns:
                    match = re.search(pattern, line)
                    if match:
                        func_name = match.group(1)
                        params_str = match.group(2)
                        
                        # Parse parameters
                        params = []
                        if params_str.strip():
                            for param in [p.strip() for p in params_str.split(',')]:
                                # Extract parameter name
                                param_name = param.split(':')[0].split('=')[0].strip()
                                if param_name and not param_name.startswith('...'):
                                    params.append(param_name)
                        
                        # Find function body
                        body_start = i
                        body_end = i
                        brace_count = 0
                        for j, body_line in enumerate(lines[i:], i + 1):
                            # Count braces to determine function body
                            brace_count += body_line.count('{') - body_line.count('}')
                            body_end = j
                            if brace_count <= 0:
                                break
                        
                        # Check if parameters are validated
                        body = '\n'.join(lines[body_start - 1:body_end])
                        for param in params:
                            # Check for common validation patterns
                            validation_patterns = [
                                rf'if\s*\(\s*{param}\s*===\s*null',
                                rf'if\s*\(\s*{param}\s*!==',
                                rf'if\s*\(\s*!{param}',
                                rf'if\s*\(\s*{param}\s*==\s*null',
                                rf'if\s*\(\s*{param}\s*!=',
                                rf'if\s*\(\s*{param}\s*<',
                                rf'if\s*\(\s*{param}\s*>',
                                rf'assert\({param}',
                                rf'validate\w*\({param}',
                            ]
                            
                            validated = any(re.search(pattern, body) for pattern in validation_patterns)
                            if not validated:
                                issues.append({
                                    'file': file.filename,
                                    'line': i,
                                    'message': f"Parameter '{param}' in function '{func_name}' may not be properly validated"
                                })
        
        return issues

