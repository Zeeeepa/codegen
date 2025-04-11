"""
AI Service for PR Review Agent.
This module provides functionality for generating AI-powered reviews and analysis.
"""
import os
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class AIService:
    """
    Service for generating AI-powered reviews and analysis.
    
    Provides functionality for using LLMs (Claude or GPT-4) to analyze code changes
    and provide detailed feedback.
    """
    
    def __init__(
        self, 
        provider: str = "anthropic", 
        model: str = "claude-3-opus-20240229", 
        api_key: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000
    ):
        """
        Initialize the AI service.
        
        Args:
            provider: AI provider (anthropic, openai)
            model: Model to use
            api_key: API key
            temperature: Temperature for generation
            max_tokens: Max tokens for generation
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize client
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the AI client based on the provider."""
        try:
            if self.provider == "anthropic":
                self._initialize_anthropic()
            elif self.provider == "openai":
                self._initialize_openai()
            else:
                logger.warning(f"Provider {self.provider} not supported")
        except ImportError as e:
            logger.warning(f"Failed to initialize AI client: {e}")
            logger.warning("AI-powered reviews will not be available")
    
    def _initialize_anthropic(self) -> None:
        """Initialize the Anthropic client."""
        try:
            from anthropic import Anthropic
            
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Initialized Anthropic client with model {self.model}")
        except ImportError:
            logger.warning("Failed to import anthropic. Please install it with 'pip install anthropic'")
            self.client = None
    
    def _initialize_openai(self) -> None:
        """Initialize the OpenAI client."""
        try:
            from openai import OpenAI
            
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI client with model {self.model}")
        except ImportError:
            logger.warning("Failed to import openai. Please install it with 'pip install openai'")
            self.client = None
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using the AI model.
        
        Args:
            prompt: Prompt to generate text from
            
        Returns:
            Generated text
        """
        try:
            if self.client is None:
                logger.warning("AI client not initialized")
                return "AI client not initialized"
            
            if self.provider == "anthropic":
                return self._generate_anthropic(prompt)
            elif self.provider == "openai":
                return self._generate_openai(prompt)
            else:
                logger.warning(f"Provider {self.provider} not supported")
                return f"Provider {self.provider} not supported"
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating text: {str(e)}"
    
    def _generate_anthropic(self, prompt: str) -> str:
        """
        Generate text using the Anthropic model.
        
        Args:
            prompt: Prompt to generate text from
            
        Returns:
            Generated text
        """
        try:
            from anthropic import Anthropic
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are a code reviewer reviewing a pull request. Provide detailed, constructive feedback.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating text with Anthropic: {str(e)}"
    
    def _generate_openai(self, prompt: str) -> str:
        """
        Generate text using the OpenAI model.
        
        Args:
            prompt: Prompt to generate text from
            
        Returns:
            Generated text
        """
        try:
            from openai import OpenAI
            
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": "You are a code reviewer reviewing a pull request. Provide detailed, constructive feedback."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating text with OpenAI: {str(e)}"
    
    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze code using the AI model.
        
        Args:
            code: Code to analyze
            language: Programming language
            
        Returns:
            Analysis results
        """
        prompt = f"""
        Please analyze the following {language} code and provide feedback:
        
        ```{language}
        {code}
        ```
        
        Please provide a detailed analysis, including:
        1. Code quality issues
        2. Potential bugs or issues
        3. Suggestions for improvement
        4. Overall assessment
        
        Format your response as a JSON object with the following structure:
        {{
            "quality_issues": [
                {{"description": "Issue description", "line": line_number, "severity": "high/medium/low"}}
            ],
            "potential_bugs": [
                {{"description": "Bug description", "line": line_number, "severity": "high/medium/low"}}
            ],
            "suggestions": [
                {{"description": "Suggestion description", "line": line_number}}
            ],
            "overall_assessment": "Your overall assessment"
        }}
        """
        
        response = self.generate(prompt)
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            import re
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from AI response")
                    return {
                        "quality_issues": [],
                        "potential_bugs": [],
                        "suggestions": [],
                        "overall_assessment": "Failed to parse AI response"
                    }
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                "quality_issues": [],
                "potential_bugs": [],
                "suggestions": [],
                "overall_assessment": f"Error parsing AI response: {str(e)}"
            }
    
    def analyze_pr(self, pr_details: Dict[str, Any], diff: str) -> Dict[str, Any]:
        """
        Analyze a PR using the AI model.
        
        Args:
            pr_details: PR details
            diff: PR diff
            
        Returns:
            Analysis results
        """
        prompt = f"""
        You are a code reviewer reviewing a pull request. Please analyze the following PR and provide feedback.
        
        Repository: {pr_details.get('repo_name', 'Unknown')}
        PR Number: {pr_details.get('number', 'Unknown')}
        PR Title: {pr_details.get('title', 'Unknown')}
        PR Description: {pr_details.get('body', 'No description provided')}
        
        Files changed: {', '.join(pr_details.get('files', []))}
        
        PR Diff:
        ```diff
        {diff}
        ```
        
        Please provide a detailed review of this PR, including:
        1. Overall assessment
        2. Code quality issues
        3. Potential bugs or issues
        4. Suggestions for improvement
        5. Whether the PR should be approved or needs changes
        
        Format your response as a JSON object with the following structure:
        {{
            "passed": true/false,
            "overall_assessment": "Your overall assessment",
            "issues": [
                {{"type": "code_quality", "message": "Issue description", "file": "file_path", "line": line_number}},
                ...
            ],
            "suggestions": [
                {{"description": "Suggestion description", "file": "file_path", "line": line_number}},
                ...
            ],
            "approval_recommendation": "approve" or "request_changes",
            "review_comment": "Your detailed review comment"
        }}
        """
        
        response = self.generate(prompt)
        
        # Parse JSON response
        try:
            # Try to extract JSON from the response
            import re
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from AI response")
                    return {
                        "passed": False,
                        "overall_assessment": "Failed to parse AI response",
                        "issues": [],
                        "suggestions": [],
                        "approval_recommendation": "request_changes",
                        "review_comment": "Failed to parse AI response"
                    }
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                "passed": False,
                "overall_assessment": f"Error parsing AI response: {str(e)}",
                "issues": [],
                "suggestions": [],
                "approval_recommendation": "request_changes",
                "review_comment": f"Error parsing AI response: {str(e)}"
            }
