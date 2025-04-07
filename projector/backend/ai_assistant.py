import logging
import json
import os
import sys
import re
import requests
from concurrent.futures import ThreadPoolExecutor

class AIAssistantAgent:
    """AI assistant agent that uses LLM capabilities."""
    
    def __init__(self, assistant_agent, memory_key="project_memory"):
        """Initialize the AI assistant agent."""
        self.logger = logging.getLogger(__name__)
        self.assistant_agent = assistant_agent
        self.memory_key = memory_key
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def analyze_document(self, document_path):
        """Analyze a document to extract features and requirements."""
        try:
            # Read the document
            with open(document_path, 'r') as f:
                content = f.read()
                
            # Use sequential thinking to analyze the document
            features = self._extract_features_from_document(content)
            return features
        except Exception as e:
            self.logger.error(f"Error analyzing document: {e}")
            return None
    
    def _extract_features_from_document(self, content):
        """Extract features from document content using pattern recognition and AI."""
        features = []
        
        # Look for markdown headers that might indicate features
        feature_pattern = r'^#+\s+(.+)$'
        feature_matches = re.finditer(feature_pattern, content, re.MULTILINE)
        
        for match in feature_matches:
            feature_name = match.group(1).strip()
            
            # Find feature description (text after the header until the next header)
            start_pos = match.end()
            next_match = re.search(r'^#+\s+', content[start_pos:], re.MULTILINE)
            end_pos = start_pos + next_match.start() if next_match else len(content)
            
            feature_description = content[start_pos:end_pos].strip()
            
            # Try to determine priority based on keywords
            priority = "medium"  # default
            if re.search(r'\b(urgent|critical|high priority|important)\b', feature_description, re.IGNORECASE):
                priority = "high"
            elif re.search(r'\b(minor|low priority|optional)\b', feature_description, re.IGNORECASE):
                priority = "low"
            
            # Try to identify dependencies
            dependencies = []
            dependency_pattern = r'(?:depends on|requires|after|following)(?:\s+the)?\s+([^,.]+)'
            dependency_matches = re.finditer(dependency_pattern, feature_description, re.IGNORECASE)
            
            for dep_match in dependency_matches:
                dependency = dep_match.group(1).strip()
                dependencies.append(dependency)
            
            features.append({
                "name": feature_name,
                "description": feature_description,
                "priority": priority,
                "dependencies": dependencies
            })
        
        return {"features": features}
    
    def create_implementation_plan(self, features):
        """Create an implementation plan based on features."""
        if not features or "features" not in features:
            return {"plan": []}
        
        plan = []
        for feature in features["features"]:
            # Generate steps based on feature description
            steps = self._generate_implementation_steps(feature)
            
            # Estimate timeline based on complexity and priority
            timeline = self._estimate_timeline(feature, steps)
            
            plan.append({
                "feature": feature["name"],
                "description": feature.get("description", ""),
                "steps": steps,
                "timeline": timeline,
                "dependencies": feature.get("dependencies", []),
                "priority": feature.get("priority", "medium")
            })
        
        return {"plan": plan}
    
    def _generate_implementation_steps(self, feature):
        """Generate implementation steps for a feature."""
        feature_name = feature["name"]
        feature_desc = feature.get("description", "")
        
        # Basic step generation based on feature type
        if "authentication" in feature_name.lower() or "auth" in feature_name.lower():
            return [
                f"Create user model for {feature_name}",
                f"Implement login/registration endpoints for {feature_name}",
                f"Add authentication middleware for {feature_name}",
                f"Create login/registration UI components for {feature_name}",
                f"Implement session management for {feature_name}",
                f"Add unit tests for {feature_name}"
            ]
        elif "database" in feature_name.lower() or "data" in feature_name.lower():
            return [
                f"Design database schema for {feature_name}",
                f"Create database migration files for {feature_name}",
                f"Implement data access layer for {feature_name}",
                f"Add data validation for {feature_name}",
                f"Implement data backup and recovery for {feature_name}",
                f"Add unit tests for {feature_name}"
            ]
        else:
            # Generic steps for other features
            return [
                f"Design architecture for {feature_name}",
                f"Implement core functionality for {feature_name}",
                f"Create API endpoints for {feature_name}",
                f"Develop UI components for {feature_name}",
                f"Write documentation for {feature_name}",
                f"Add unit tests for {feature_name}"
            ]
    
    def _estimate_timeline(self, feature, steps):
        """Estimate timeline for feature implementation."""
        # Basic estimation: 1 day per step, adjusted by priority
        priority_multiplier = {
            "high": 0.8,  # High priority = shorter timeline
            "medium": 1.0,
            "low": 1.2  # Low priority = longer timeline
        }
        
        days_per_step = 1.0
        total_days = len(steps) * days_per_step * priority_multiplier.get(feature.get("priority", "medium"), 1.0)
        
        if total_days <= 3:
            return "3 days"
        elif total_days <= 7:
            return "1 week"
        elif total_days <= 14:
            return "2 weeks"
        else:
            return f"{int(total_days)} days"
    
    def generate_code_for_feature(self, feature_name, feature_plan):
        """Generate code for a specific feature."""
        # This would typically call an LLM for code generation
        # For this implementation, we'll create template code
        
        feature_files = {}
        
        # Create sanitized feature name for file naming
        file_prefix = feature_name.lower().replace(' ', '_')
        
        # Simple code templates based on feature name
        if "auth" in feature_name.lower():
            # Authentication feature
            feature_files[f"src/auth/{file_prefix}_model.py"] = self._generate_auth_model_code(feature_name)
            feature_files[f"src/auth/{file_prefix}_controller.py"] = self._generate_auth_controller_code(feature_name)
            feature_files[f"src/auth/{file_prefix}_routes.py"] = self._generate_auth_routes_code(feature_name)
        elif "api" in feature_name.lower():
            # API feature
            feature_files[f"src/api/{file_prefix}_routes.py"] = self._generate_api_routes_code(feature_name)
            feature_files[f"src/api/{file_prefix}_controller.py"] = self._generate_api_controller_code(feature_name)
        else:
            # Generic feature
            feature_files[f"src/{file_prefix}/{file_prefix}_model.py"] = self._generate_model_code(feature_name)
            feature_files[f"src/{file_prefix}/{file_prefix}_service.py"] = self._generate_service_code(feature_name)
            feature_files[f"src/{file_prefix}/{file_prefix}_controller.py"] = self._generate_controller_code(feature_name)
        
        # Format for return
        files = []
        for path, content in feature_files.items():
            files.append({
                "path": path,
                "content": content,
                "description": f"{feature_name} implementation file"
            })
        
        return {"files": files}
    
    def _generate_auth_model_code(self, feature_name):
        return f"""# {feature_name} Model
import os
from datetime import datetime, timedelta
import hashlib
import uuid

class User:
    def __init__(self, username, email, password=None, user_id=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = self._hash_password(password) if password else None
        self.created_at = datetime.now()
        self.last_login = None
        self.is_active = True
        
    def _hash_password(self, password):
        # In production, use a proper password hashing library like bcrypt
        salt = os.urandom(16)
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    
    def check_password(self, password):
        # In production, implement proper password verification
        return True  # Placeholder
    
    def to_dict(self):
        return {{
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }}

"""
    
    def _generate_auth_controller_code(self, feature_name):
        return f"""# {feature_name} Controller
from datetime import datetime, timedelta
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-secret-key")

class AuthController:
    def __init__(self, user_repository):
        self.user_repository = user_repository
    
    def register_user(self, username, email, password):
        # Check if user already exists
        existing_user = self.user_repository.find_by_email(email)
        if existing_user:
            return {{"success": False, "message": "User with this email already exists"}}
        
        # Create new user
        new_user = User(username, email, password)
        self.user_repository.save(new_user)
        
        return {{"success": True, "message": "User registered successfully", "user_id": new_user.user_id}}
    
    def login_user(self, email, password):
        user = self.user_repository.find_by_email(email)
        if not user or not user.check_password(password):
            return {{"success": False, "message": "Invalid email or password"}}
        
        # Update last login
        user.last_login = datetime.now()
        self.user_repository.save(user)
        
        # Generate JWT token
        token = self._generate_token(user)
        
        return {{"success": True, "token": token, "user": user.to_dict()}}
    
    def _generate_token(self, user, expiry_days=7):
        payload = {{
            "user_id": user.user_id,
            "username": user.username,
            "exp": datetime.now() + timedelta(days=expiry_days)
        }}
        
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            return self.user_repository.find_by_id(user_id)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

"""

    def _generate_auth_routes_code(self, feature_name):
        return f"""# {feature_name} Routes
from flask import Blueprint, request, jsonify
from .auth_controller import AuthController
from .user_repository import UserRepository

auth_blueprint = Blueprint('auth', __name__)
user_repository = UserRepository()
auth_controller = AuthController(user_repository)

@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({{"success": False, "message": "Missing required fields"}}), 400
    
    result = auth_controller.register_user(username, email, password)
    
    if result["success"]:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({{"success": False, "message": "Missing required fields"}}), 400
    
    result = auth_controller.login_user(email, password)
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@auth_blueprint.route('/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({{"success": False, "message": "Missing or invalid authorization header"}}), 401
    
    token = auth_header.split(' ')[1]
    user = auth_controller.verify_token(token)
    
    if user:
        return jsonify({{"success": True, "user": user.to_dict()}}), 200
    else:
        return jsonify({{"success": False, "message": "Invalid or expired token"}}), 401

def register_routes(app):
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
"""

    def _generate_api_routes_code(self, feature_name):
        return f"""# {feature_name} API Routes
from flask import Blueprint, request, jsonify
from .{feature_name.lower().replace(' ', '_')}_controller import {feature_name.replace(' ', '')}Controller

api_blueprint = Blueprint('{feature_name.lower().replace(' ', '_')}', __name__)
controller = {feature_name.replace(' ', '')}Controller()

@api_blueprint.route('/', methods=['GET'])
def get_all():
    items = controller.get_all()
    return jsonify({{"success": True, "data": items}}), 200

@api_blueprint.route('/<item_id>', methods=['GET'])
def get_by_id(item_id):
    item = controller.get_by_id(item_id)
    if item:
        return jsonify({{"success": True, "data": item}}), 200
    else:
        return jsonify({{"success": False, "message": "Item not found"}}), 404

@api_blueprint.route('/', methods=['POST'])
def create():
    data = request.get_json()
    result = controller.create(data)
    return jsonify(result), 201 if result["success"] else 400

@api_blueprint.route('/<item_id>', methods=['PUT'])
def update(item_id):
    data = request.get_json()
    result = controller.update(item_id, data)
    return jsonify(result), 200 if result["success"] else 400

@api_blueprint.route('/<item_id>', methods=['DELETE'])
def delete(item_id):
    result = controller.delete(item_id)
    return jsonify(result), 200 if result["success"] else 400

def register_routes(app):
    app.register_blueprint(api_blueprint, url_prefix='/api/{feature_name.lower().replace(' ', '_')}')
"""

    def _generate_api_controller_code(self, feature_name):
        return f"""# {feature_name} Controller
import uuid
from datetime import datetime

class {feature_name.replace(' ', '')}Controller:
    def __init__(self):
        self.items = []  # In a real application, this would be a database repository
    
    def get_all(self):
        return self.items
    
    def get_by_id(self, item_id):
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None
    
    def create(self, data):
        item = {{
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **data
        }}
        self.items.append(item)
        return {{"success": True, "message": "Item created successfully", "data": item}}
    
    def update(self, item_id, data):
        for i, item in enumerate(self.items):
            if item["id"] == item_id:
                self.items[i] = {{
                    **item,
                    **data,
                    "updated_at": datetime.now().isoformat()
                }}
                return {{"success": True, "message": "Item updated successfully", "data": self.items[i]}}
        return {{"success": False, "message": "Item not found"}}
    
    def delete(self, item_id):
        for i, item in enumerate(self.items):
            if item["id"] == item_id:
                del self.items[i]
                return {{"success": True, "message": "Item deleted successfully"}}
        return {{"success": False, "message": "Item not found"}}
"""

    def _generate_model_code(self, feature_name):
        return f"""# {feature_name} Model
import uuid
from datetime import datetime

class {feature_name.replace(' ', '')}:
    def __init__(self, name, description=None, item_id=None):
        self.id = item_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.updated_at = self.created_at
    
    def update(self, name=None, description=None):
        if name:
            self.name = name
        if description:
            self.description = description
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {{
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }}
"""

    def _generate_service_code(self, feature_name):
        return f"""# {feature_name} Service
from .{feature_name.lower().replace(' ', '_')}_model import {feature_name.replace(' ', '')}

class {feature_name.replace(' ', '')}Service:
    def __init__(self, repository):
        self.repository = repository
    
    def get_all(self):
        return [item.to_dict() for item in self.repository.find_all()]
    
    def get_by_id(self, item_id):
        item = self.repository.find_by_id(item_id)
        return item.to_dict() if item else None
    
    def create(self, name, description=None):
        new_item = {feature_name.replace(' ', '')}(name, description)
        self.repository.save(new_item)
        return new_item.to_dict()
    
    def update(self, item_id, name=None, description=None):
        item = self.repository.find_by_id(item_id)
        if not item:
            return None
        
        item.update(name, description)
        self.repository.save(item)
        return item.to_dict()
    
    def delete(self, item_id):
        return self.repository.delete(item_id)
"""

    def _generate_controller_code(self, feature_name):
        return f"""# {feature_name} Controller
from .{feature_name.lower().replace(' ', '_')}_service import {feature_name.replace(' ', '')}Service
from .{feature_name.lower().replace(' ', '_')}_repository import {feature_name.replace(' ', '')}Repository

class {feature_name.replace(' ', '')}Controller:
    def __init__(self):
        repository = {feature_name.replace(' ', '')}Repository()
        self.service = {feature_name.replace(' ', '')}Service(repository)
    
    def get_all(self):
        return self.service.get_all()
    
    def get_by_id(self, item_id):
        return self.service.get_by_id(item_id)
    
    def create(self, data):
        name = data.get("name")
        description = data.get("description")
        
        if not name:
            return {{"success": False, "message": "Name is required"}}
        
        item = self.service.create(name, description)
        return {{"success": True, "message": "{feature_name} created successfully", "data": item}}
    
    def update(self, item_id, data):
        name = data.get("name")
        description = data.get("description")
        
        item = self.service.update(item_id, name, description)
        if item:
            return {{"success": True, "message": "{feature_name} updated successfully", "data": item}}
        else:
            return {{"success": False, "message": "{feature_name} not found"}}
    
    def delete(self, item_id):
        success = self.service.delete(item_id)
        if success:
            return {{"success": True, "message": "{feature_name} deleted successfully"}}
        else:
            return {{"success": False, "message": "{feature_name} not found"}}
"""
        
    def analyze_code_repository(self, repo_owner, repo_name):
        """Analyze a code repository for insights."""
        try:
            # In a real implementation, this would use GitHub API
            # For demo purposes, providing a mock response
            return {
                "structure": {
                    "main_language": "Python",
                    "file_count": 42,
                    "key_components": [
                        {"name": "Authentication", "files": ["auth.py", "users.py"]},
                        {"name": "API Layer", "files": ["api.py", "routes.py"]},
                        {"name": "Database", "files": ["models.py", "repositories.py"]},
                        {"name": "Frontend", "files": ["ui.py", "components.py"]}
                    ]
                },
                "recommendations": [
                    "Consider refactoring the authentication module for better encapsulation",
                    "The API layer could benefit from better error handling",
                    "Database models should have more validation",
                    "Frontend components could be made more reusable"
                ]
            }
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {e}")
            return None
    
    def analyze_thread_message(self, message):
        """Analyze a thread message to determine next actions."""
        # This would typically use an LLM to understand the message
        # For demo purposes, providing a simple rule-based analysis
        
        message_lower = message.lower()
        
        # Detect intent
        if "status" in message_lower or "update" in message_lower:
            intent = "status_update"
        elif "problem" in message_lower or "issue" in message_lower or "bug" in message_lower:
            intent = "report_issue"
        elif "question" in message_lower or "how" in message_lower or "why" in message_lower:
            intent = "ask_question"
        elif "done" in message_lower or "complete" in message_lower or "finished" in message_lower:
            intent = "report_completion"
        else:
            intent = "general_message"
        
        # Extract entities
        entities = []
        entity_keywords = {
            "authentication": ["auth", "login", "register", "password"],
            "database": ["database", "data", "model", "schema"],
            "frontend": ["ui", "interface", "component", "display"],
            "backend": ["api", "endpoint", "server", "route"]
        }
        
        for entity, keywords in entity_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                entities.append(entity)
        
        # Determine sentiment
        positive_words = ["good", "great", "excellent", "done", "completed", "success"]
        negative_words = ["bad", "issue", "problem", "bug", "error", "fail"]
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Generate suggested response
        suggested_response = self._generate_response(intent, entities, sentiment)
        
        return {
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "suggested_response": suggested_response
        }
    
    def _generate_response(self, intent, entities, sentiment):
        """Generate a suggested response based on message analysis."""
        if intent == "status_update":
            if sentiment == "positive":
                return f"Great progress on {', '.join(entities) if entities else 'the project'}! What's the next step you're planning to tackle?"
            else:
                return f"Thanks for the update on {', '.join(entities) if entities else 'the project'}. Are there any challenges you're facing that I can help with?"
        
        elif intent == "report_issue":
            return f"I'm sorry to hear you're experiencing issues with {', '.join(entities) if entities else 'this'}. Could you provide more details about what's happening?"
        
        elif intent == "ask_question":
            return f"That's a good question about {', '.join(entities) if entities else 'this topic'}. Let me help clarify that..."
        
        elif intent == "report_completion":
            return f"Excellent work completing {', '.join(entities) if entities else 'this task'}! Should we move on to the next step in the plan?"
        
        else:
            return "Thanks for your message. Let me know if there's anything specific I can help with."
