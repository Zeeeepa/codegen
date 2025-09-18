"""
Z.AI client integration for the Codegen Dashboard.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..config import Config
from ..utils.logger import get_logger


@dataclass
class ChatCompletionResponse:
    """Response from Z.AI chat completion."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class ZAIClient:
    """
    Client for integrating with Z.AI API for intelligent responses and analysis.
    """
    
    def __init__(self, config: Config):
        """Initialize the Z.AI client."""
        self.config = config
        self.logger = get_logger(__name__)
        
        # Import Z.AI client from web-ui-python-sdk
        try:
            from web_ui_python_sdk import ZAIClient as WebUIZAIClient
            self.client = WebUIZAIClient(
                token=config.api.zai_token,
                base_url=config.api.zai_base_url,
                auto_auth=config.api.zai_auto_auth
            )
            self.logger.info("Z.AI client initialized successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import Z.AI client: {e}")
            self.client = None
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None,
                            stream: bool = False) -> ChatCompletionResponse:
        """
        Generate a chat completion using Z.AI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to config model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            ChatCompletionResponse with the generated content
        """
        if not self.client:
            raise RuntimeError("Z.AI client not initialized")
        
        try:
            # Use configured model if not specified
            if not model:
                model = self.config.api.zai_model
            
            # Convert messages to Z.AI format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Make the API call
            response = await asyncio.to_thread(
                self._make_chat_request,
                formatted_messages,
                model,
                temperature,
                max_tokens,
                stream
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in Z.AI chat completion: {e}")
            raise
    
    def _make_chat_request(self, messages: List[Dict[str, str]], 
                          model: str, temperature: float,
                          max_tokens: Optional[int], stream: bool) -> ChatCompletionResponse:
        """Make the actual chat request (synchronous)."""
        try:
            # Use the Z.AI client to make the request
            response = self.client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            # Extract response content
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
            else:
                content = str(response)
                finish_reason = "stop"
            
            # Extract usage information
            usage = {}
            if hasattr(response, 'usage'):
                usage = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                }
            
            return ChatCompletionResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            self.logger.error(f"Error making Z.AI request: {e}")
            raise
    
    async def analyze_code(self, code: str, language: str = "python",
                          analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analyze code using Z.AI's capabilities.
        
        Args:
            code: Code to analyze
            language: Programming language
            analysis_type: Type of analysis (general, security, performance, etc.)
            
        Returns:
            Analysis results
        """
        try:
            analysis_prompt = f"""
            Analyze the following {language} code for {analysis_type} insights:
            
            ```{language}
            {code}
            ```
            
            Provide analysis in JSON format:
            {{
                "summary": "Brief summary of the code",
                "complexity": "Low|Medium|High",
                "issues": ["issue1", "issue2"],
                "suggestions": ["suggestion1", "suggestion2"],
                "quality_score": 0.0-1.0,
                "maintainability": "assessment",
                "performance_notes": ["note1", "note2"]
            }}
            """
            
            response = await self.chat_completion(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Error analyzing code: {e}")
            return {
                "summary": "Analysis failed",
                "complexity": "Unknown",
                "issues": [str(e)],
                "suggestions": [],
                "quality_score": 0.0,
                "maintainability": "Unknown",
                "performance_notes": []
            }
    
    async def generate_documentation(self, code: str, language: str = "python") -> str:
        """
        Generate documentation for code using Z.AI.
        
        Args:
            code: Code to document
            language: Programming language
            
        Returns:
            Generated documentation
        """
        try:
            doc_prompt = f"""
            Generate comprehensive documentation for this {language} code:
            
            ```{language}
            {code}
            ```
            
            Include:
            - Purpose and functionality
            - Parameters and return values
            - Usage examples
            - Important notes or warnings
            
            Format as markdown.
            """
            
            response = await self.chat_completion(
                messages=[{"role": "user", "content": doc_prompt}],
                temperature=0.3
            )
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error generating documentation: {e}")
            return f"Documentation generation failed: {str(e)}"
    
    async def explain_error(self, error_message: str, code_context: str = "") -> str:
        """
        Explain an error message with optional code context.
        
        Args:
            error_message: The error message to explain
            code_context: Optional code context where the error occurred
            
        Returns:
            Explanation of the error and suggested fixes
        """
        try:
            context_part = f"\n\nCode context:\n```\n{code_context}\n```" if code_context else ""
            
            error_prompt = f"""
            Explain this error message and provide solutions:
            
            Error: {error_message}{context_part}
            
            Please provide:
            1. What the error means
            2. Common causes
            3. Step-by-step solutions
            4. Prevention tips
            
            Be clear and helpful for developers.
            """
            
            response = await self.chat_completion(
                messages=[{"role": "user", "content": error_prompt}],
                temperature=0.3
            )
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error explaining error: {e}")
            return f"Error explanation failed: {str(e)}"
    
    async def suggest_improvements(self, code: str, language: str = "python") -> List[str]:
        """
        Suggest improvements for code.
        
        Args:
            code: Code to improve
            language: Programming language
            
        Returns:
            List of improvement suggestions
        """
        try:
            improvement_prompt = f"""
            Suggest improvements for this {language} code:
            
            ```{language}
            {code}
            ```
            
            Focus on:
            - Performance optimizations
            - Code readability
            - Best practices
            - Security considerations
            - Maintainability
            
            Respond with JSON array of suggestions:
            ["suggestion1", "suggestion2", ...]
            """
            
            response = await self.chat_completion(
                messages=[{"role": "user", "content": improvement_prompt}],
                temperature=0.3
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Error suggesting improvements: {e}")
            return [f"Improvement suggestion failed: {str(e)}"]
    
    async def validate_requirements(self, requirements: str, implementation: str) -> Dict[str, Any]:
        """
        Validate if implementation meets requirements.
        
        Args:
            requirements: Requirements or PRD content
            implementation: Implementation details or code
            
        Returns:
            Validation results
        """
        try:
            validation_prompt = f"""
            Validate if this implementation meets the requirements:
            
            Requirements:
            {requirements}
            
            Implementation:
            {implementation}
            
            Respond with JSON:
            {{
                "meets_requirements": true/false,
                "confidence": 0.0-1.0,
                "missing_requirements": ["req1", "req2"],
                "implemented_requirements": ["req1", "req2"],
                "suggestions": ["suggestion1", "suggestion2"],
                "overall_assessment": "assessment text"
            }}
            """
            
            response = await self.chat_completion(
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.1
            )
            
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.error(f"Error validating requirements: {e}")
            return {
                "meets_requirements": False,
                "confidence": 0.0,
                "missing_requirements": ["Validation failed"],
                "implemented_requirements": [],
                "suggestions": [f"Validation error: {str(e)}"],
                "overall_assessment": "Validation failed due to error"
            }
    
    def is_available(self) -> bool:
        """Check if Z.AI client is available and configured."""
        return self.client is not None
    
    async def test_connection(self) -> bool:
        """Test the connection to Z.AI API."""
        try:
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello, this is a connection test."}],
                max_tokens=10
            )
            return bool(response.content)
        except Exception as e:
            self.logger.error(f"Z.AI connection test failed: {e}")
            return False
