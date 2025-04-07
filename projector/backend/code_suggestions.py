import logging
import re
import os
import json
from collections import defaultdict
import ast
import difflib

class CodeSuggestionEngine:
    """Engine for generating intelligent code suggestions based on code analysis."""
    
    def __init__(self, code_analyzer=None):
        """Initialize the code suggestion engine.
        
        Args:
            code_analyzer: An instance of CodeAnalyzer to use for code analysis.
                           If None, the engine will work independently.
        """
        self.logger = logging.getLogger(__name__)
        self.code_analyzer = code_analyzer
        self.patterns_db = {
            "python": self._load_python_patterns(),
            "javascript": self._load_javascript_patterns(),
            "typescript": self._load_typescript_patterns()
        }
    
    def _load_python_patterns(self):
        """Load patterns for Python code suggestions."""
        return {
            "error_handling": {
                "pattern": r"(?<!try:)(?:\n\s+)([^\n]+\.[^\n]+\(.*\))",
                "suggestion": "Consider adding try-except blocks around external calls to handle potential exceptions.",
                "example": """
try:
    result = external_service.fetch_data()
except ExternalServiceError as e:
    logger.error(f"Failed to fetch data: {e}")
    # Handle the error appropriately
"""
            },
            "long_function": {
                "pattern": r"def\s+\w+\([^)]*\):[^}]*?(?:\n\s+[^\n]+){20,}",
                "suggestion": "Consider breaking down this long function into smaller, more focused functions.",
                "example": """
def process_data(data):
    """Process the main data."""
    validated_data = _validate_data(data)
    transformed_data = _transform_data(validated_data)
    return _format_results(transformed_data)

def _validate_data(data):
    """Validate the input data."""
    # Validation logic here
    return validated_data
"""
            },
            "missing_docstring": {
                "pattern": r"def\s+(\w+)\([^)]*\):\s*(?!\s*(?:\"\"\"|'''))",
                "suggestion": "Add docstrings to improve code documentation and maintainability.",
                "example": """
def calculate_total(items):
    """
    Calculate the total price of all items.
    
    Args:
        items: List of items with 'price' attribute
        
    Returns:
        float: The total price
    """
    return sum(item.price for item in items)
"""
            },
            "complex_conditional": {
                "pattern": r"if\s+(?:[^:]+and[^:]+and[^:]+|[^:]+or[^:]+or[^:]+):",
                "suggestion": "Consider simplifying complex conditionals by extracting conditions to named variables or functions.",
                "example": """
# Instead of:
if user.is_active and user.has_permission('edit') and not user.is_temporary():
    # Do something

# Consider:
def can_edit_content(user):
    return user.is_active and user.has_permission('edit') and not user.is_temporary()
    
if can_edit_content(user):
    # Do something
"""
            },
            "magic_number": {
                "pattern": r"(?<!\w)(\d+)(?!\w)(?!\s*[=:])",
                "suggestion": "Replace magic numbers with named constants to improve code readability and maintainability.",
                "example": """
# Instead of:
if status_code >= 500:
    retry_count = min(attempts, 5)
    wait_time = retry_count * 2

# Consider:
MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_FACTOR = 2

if status_code >= HTTP_SERVER_ERROR_CODE:
    retry_count = min(attempts, MAX_RETRY_ATTEMPTS)
    wait_time = retry_count * RETRY_BACKOFF_FACTOR
"""
            }
        }
    
    def _load_javascript_patterns(self):
        """Load patterns for JavaScript code suggestions."""
        return {
            "callback_hell": {
                "pattern": r"(?:\w+\((?:[^()]*|\([^()]*\))*,\s*function\s*\([^)]*\)\s*{[^}]*}\))\s*\.\s*then",
                "suggestion": "Consider using async/await instead of nested callbacks or promise chains.",
                "example": """
// Instead of:
fetchData()
  .then(data => {
    return processData(data);
  })
  .then(result => {
    return saveData(result);
  })
  .catch(error => {
    console.error(error);
  });

// Consider:
async function handleData() {
  try {
    const data = await fetchData();
    const result = await processData(data);
    await saveData(result);
  } catch (error) {
    console.error('Fetch error:', error);
    // Handle error appropriately
  }
}
"""
            },
            "no_error_handling": {
                "pattern": r"fetch\([^)]+\)(?!\.catch)",
                "suggestion": "Add error handling to fetch calls to handle network failures and API errors.",
                "example": """
// Instead of:
fetch('/api/data')
  .then(response => response.json())
  .then(data => {
    // Process data
  });

// Consider:
fetch('/api/data')
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    // Process data
  })
  .catch(error => {
    console.error('Fetch error:', error);
    // Handle error appropriately
  });
"""
            }
        }
    
    def _load_typescript_patterns(self):
        """Load patterns for TypeScript code suggestions."""
        return {
            "any_type": {
                "pattern": r":\s*any",
                "suggestion": "Avoid using 'any' type in TypeScript as it defeats the purpose of type checking.",
                "example": """
// Instead of:
function processData(data: any): any {
  // ...
}

// Consider:
interface DataItem {
  id: number;
  name: string;
  value: number;
}

function processData(data: DataItem[]): ProcessedResult {
  // ...
}
"""
            }
        }
    
    def analyze_code(self, file_path, content, language=None):
        """Analyze code and generate suggestions for improvements.
        
        Args:
            file_path: Path to the file being analyzed
            content: String content of the file
            language: Optional language override. If None, will be detected from file extension
            
        Returns:
            List of suggestion objects with line numbers, descriptions, and examples
        """
        if not language:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.py']:
                language = 'python'
            elif ext in ['.js']:
                language = 'javascript'
            elif ext in ['.ts', '.tsx']:
                language = 'typescript'
            else:
                self.logger.warning(f"Unsupported file extension for code suggestions: {ext}")
                return []
        
        suggestions = []
        
        # Get patterns for the detected language
        patterns = self.patterns_db.get(language, {})
        if not patterns:
            self.logger.warning(f"No suggestion patterns available for language: {language}")
            return []
        
        # Apply each pattern to the code
        for suggestion_type, pattern_info in patterns.items():
            matches = re.finditer(pattern_info["pattern"], content, re.MULTILINE)
            for match in matches:
                # Get line number for the match
                line_number = content[:match.start()].count('\n') + 1
                
                # Create suggestion object
                suggestion = {
                    "type": suggestion_type,
                    "line": line_number,
                    "description": pattern_info["suggestion"],
                    "example": pattern_info["example"].strip(),
                    "match": match.group(0).strip()
                }
                
                suggestions.append(suggestion)
        
        # Add language-specific advanced suggestions
        if language == 'python':
            suggestions.extend(self._analyze_python_specific(content))
        elif language == 'javascript' or language == 'typescript':
            suggestions.extend(self._analyze_js_specific(content))
        
        return suggestions
    
    def _analyze_python_specific(self, content):
        """Perform Python-specific code analysis for advanced suggestions."""
        suggestions = []
        
        try:
            # Parse the Python code into an AST
            tree = ast.parse(content)
            
            # Look for repeated code blocks that could be refactored
            code_blocks = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for similar function bodies
                    function_body = ast.unparse(node).split(':', 1)[1].strip()
                    if len(function_body) > 50:  # Only consider substantial functions
                        for existing_func, existing_body in code_blocks.items():
                            similarity = difflib.SequenceMatcher(None, function_body, existing_body).ratio()
                            if similarity > 0.7:  # High similarity threshold
                                line_number = node.lineno
                                suggestions.append({
                                    "type": "repeated_code",
                                    "line": line_number,
                                    "description": f"This function is very similar to '{existing_func}'. Consider refactoring to eliminate code duplication.",
                                    "example": """
# Instead of similar functions:
def process_users(users):
    # Similar processing logic
    
def process_items(items):
    # Similar processing logic
    
# Consider a more generic function:
def process_entities(entities, entity_type):
    # Generic processing logic with entity_type parameter
""",
                                    "match": node.name
                                })
                                break
                        code_blocks[node.name] = function_body
        except Exception as e:
            self.logger.error(f"Error during Python AST analysis: {e}")
        
        return suggestions
    
    def _analyze_js_specific(self, content):
        """Perform JavaScript/TypeScript-specific analysis for advanced suggestions."""
        suggestions = []
        
        # This would ideally use a JS parser like esprima
        # For now, using regex-based analysis for demonstration
        
        # Check for large component functions (React)
        component_pattern = r"(?:function|const)\s+(\w+)\s*=\s*(?:\([^)]*\)\s*=>|function\s*\([^)]*\))\s*{(?:[^{}]|{[^{}]*})*return\s*\(\s*<"
        matches = re.finditer(component_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            component_name = match.group(1)
            component_body = match.group(0)
            
            # Check if component is large and might need splitting
            if component_body.count('\n') > 50:
                line_number = content[:match.start()].count('\n') + 1
                suggestions.append({
                    "type": "large_component",
                    "line": line_number,
                    "description": f"Component '{component_name}' is quite large. Consider breaking it down into smaller sub-components.",
                    "example": """
// Instead of one large component:
function LargeUserDashboard() {
  // Many states and complex logic
  return (
    <div>
      {/* Many UI elements */}
    </div>
  );
}

// Consider splitting into sub-components:
function UserProfile({ user }) {
  return <div>{/* Profile UI */}</div>;
}

function UserStats({ stats }) {
  return <div>{/* Stats UI */}</div>;
}

function UserDashboard() {
  // Simplified logic
  return (
    <div>
      <UserProfile user={user} />
      <UserStats stats={userStats} />
    </div>
  );
}
""",
                    "match": component_name
                })
        
        return suggestions
    
    def generate_code_improvements(self, file_path, content, language=None):
        """Generate improved code based on suggestions.
        
        Args:
            file_path: Path to the file being analyzed
            content: String content of the file
            language: Optional language override
            
        Returns:
            Dictionary with original code, improved code, and explanation of changes
        """
        suggestions = self.analyze_code(file_path, content, language)
        if not suggestions:
            return {
                "original_code": content,
                "improved_code": content,
                "changes": [],
                "explanation": "No improvements suggested."
            }
        
        # Sort suggestions by line number
        suggestions.sort(key=lambda x: x["line"])
        
        # For now, just provide the suggestions without actually modifying the code
        # In a real implementation, this would apply the changes
        changes = []
        for suggestion in suggestions:
            changes.append({
                "line": suggestion["line"],
                "type": suggestion["type"],
                "description": suggestion["description"],
                "example": suggestion["example"]
            })
        
        return {
            "original_code": content,
            "improved_code": content,  # In a real implementation, this would be the modified code
            "changes": changes,
            "explanation": f"Found {len(suggestions)} potential improvements. See 'changes' for details."
        }
    
    def suggest_architectural_improvements(self, code_structure):
        """Suggest architectural improvements based on code structure analysis.
        
        Args:
            code_structure: Code structure data from CodeAnalyzer
            
        Returns:
            List of architectural suggestions
        """
        suggestions = []
        
        # Check class relationships for potential design patterns
        classes = code_structure.get("classes", [])
        if len(classes) > 5:
            # Look for potential factory pattern opportunities
            similar_classes = []
            for cls in classes:
                similar = [c for c in classes if c["name"] != cls["name"] and 
                          (c["name"].endswith(cls["name"]) or cls["name"].endswith(c["name"]))]
                if len(similar) >= 2:
                    similar_classes.append((cls["name"], [c["name"] for c in similar]))
            
            if similar_classes:
                for base, similar in similar_classes:
                    suggestions.append({
                        "type": "factory_pattern",
                        "description": f"Consider using Factory Pattern for {base} and similar classes: {', '.join(similar)}",
                        "example": """
# Instead of direct instantiation:
if type == "pdf":
    document = PDFDocument()
elif type == "word":
    document = WordDocument()
elif type == "excel":
    document = ExcelDocument()

# Consider a factory:
class DocumentFactory:
    @staticmethod
    def create_document(doc_type):
        if doc_type == "pdf":
            return PDFDocument()
        elif doc_type == "word":
            return WordDocument()
        elif doc_type == "excel":
            return ExcelDocument()
        else:
            raise ValueError(f"Unknown document type: {doc_type}")
            
document = DocumentFactory.create_document(type)
"""
                    })
        
        # Check for potential dependency injection opportunities
        functions = code_structure.get("functions", [])
        direct_instantiations = []
        
        for func in functions:
            if "arguments" in func and not func["arguments"]:
                # Functions with no arguments might be creating their dependencies internally
                direct_instantiations.append(func["name"])
        
        if len(direct_instantiations) > 3:
            suggestions.append({
                "type": "dependency_injection",
                "description": "Consider using Dependency Injection for better testability and flexibility",
                "example": """
# Instead of:
def process_order():
    database = Database()
    email_service = EmailService()
    # Use database and email_service
    
# Consider:
def process_order(database, email_service):
    # Use injected dependencies
    
# Then in the calling code:
db = Database()
email = EmailService()
process_order(db, email)
"""
            })
        
        # Check for potential microservices architecture
        if len(code_structure.get("classes", [])) > 20 and len(code_structure.get("functions", [])) > 50:
            suggestions.append({
                "type": "microservices",
                "description": "The codebase is growing large. Consider evaluating if a microservices architecture would be beneficial.",
                "example": """
Instead of a monolithic application, consider splitting functionality into separate services:

1. User Service - Authentication and user management
2. Product Service - Product catalog and inventory
3. Order Service - Order processing and history
4. Notification Service - Emails, SMS, and other notifications

Each service would have:
- Its own database
- Well-defined API
- Independent deployment
- Focused responsibility
"""
            })
        
        return suggestions
    
    def generate_refactoring_plan(self, code_structure, file_contents):
        """Generate a comprehensive refactoring plan based on code analysis.
        
        Args:
            code_structure: Code structure data from CodeAnalyzer
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            Dictionary with refactoring plan details
        """
        # Collect all suggestions
        all_suggestions = []
        architectural_suggestions = self.suggest_architectural_improvements(code_structure)
        
        file_suggestions = {}
        for file_path, content in file_contents.items():
            suggestions = self.analyze_code(file_path, content)
            if suggestions:
                file_suggestions[file_path] = suggestions
                all_suggestions.extend(suggestions)
        
        # Prioritize suggestions
        critical = []
        important = []
        minor = []
        
        for suggestion in all_suggestions:
            if suggestion["type"] in ["error_handling", "no_error_handling"]:
                critical.append(suggestion)
            elif suggestion["type"] in ["long_function", "complex_conditional", "repeated_code", "large_component"]:
                important.append(suggestion)
            else:
                minor.append(suggestion)
        
        # Generate plan
        plan = {
            "summary": f"Found {len(all_suggestions)} potential code improvements across {len(file_suggestions)} files.",
            "architectural_recommendations": architectural_suggestions,
            "critical_issues": critical,
            "important_improvements": important,
            "minor_improvements": minor,
            "file_breakdown": {
                file_path: len(suggestions) for file_path, suggestions in file_suggestions.items()
            },
            "estimated_effort": {
                "critical": len(critical) * 0.5,  # Estimated hours per critical issue
                "important": len(important) * 0.3,  # Estimated hours per important issue
                "minor": len(minor) * 0.1,  # Estimated hours per minor issue
                "total": len(critical) * 0.5 + len(important) * 0.3 + len(minor) * 0.1
            }
        }
        
        return plan
