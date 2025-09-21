#!/usr/bin/env python3
"""
Z.ai Client Integration for AutoGenLib
Provides z.ai AI functionality as a replacement for OpenAI
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
import json

logger = logging.getLogger(__name__)

try:
    # Import z.ai SDK from the cloned repository
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'z_ai_sdk', 'src'))
    from zai import ZaiClient
    ZAI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Z.ai SDK not available: {e}")
    ZAI_AVAILABLE = False


class ZAIWrapper:
    """
    Z.ai client wrapper that provides OpenAI-compatible interface
    for seamless integration with existing autogenlib code
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize Z.ai client wrapper."""
        if not ZAI_AVAILABLE:
            raise ImportError("Z.ai SDK is not available. Please ensure it's properly installed.")
        
        self.api_key = api_key or os.environ.get("ZAI_API_KEY") or os.environ.get("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("Z.ai API key not found. Set ZAI_API_KEY or ZHIPU_API_KEY environment variable.")
        
        self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4/"
        self.client = ZaiClient(api_key=self.api_key, base_url=self.base_url)
        
        # OpenAI-compatible interface
        self.chat = ChatCompletions(self.client)

class ChatCompletions:
    """OpenAI-compatible chat completions interface using z.ai"""
    
    def __init__(self, client: ZaiClient):
        self.client = client
    
    def create(self, 
               model: str = "glm-4",
               messages: List[Dict[str, str]] = None,
               temperature: float = 0.95,
               max_tokens: Optional[int] = None,
               response_format: Optional[Dict[str, str]] = None,
               stream: bool = False,
               **kwargs) -> Dict[str, Any]:
        """
        Create chat completion with z.ai, compatible with OpenAI format
        
        Args:
            model: Model name (glm-4, charglm-3, etc.)
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Response format (e.g., {"type": "json_object"})
            stream: Whether to stream response
            **kwargs: Additional parameters
        
        Returns:
            OpenAI-compatible response format
        """
        if not messages:
            messages = []
        
        try:
            # Map parameters to z.ai format
            zai_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
            }
            
            if max_tokens:
                zai_params["max_tokens"] = max_tokens
            
            # Handle JSON response format
            if response_format and response_format.get("type") == "json_object":
                # Add system message to enforce JSON output
                json_instruction = {
                    "role": "system", 
                    "content": "You must respond with valid JSON format only. Do not include any text outside of the JSON object."
                }
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] += " " + json_instruction["content"]
                else:
                    messages.insert(0, json_instruction)
            
            # Make request to z.ai
            if stream:
                return self._handle_stream_response(self.client.chat.completions.create(**zai_params))
            else:
                response = self.client.chat.completions.create(**zai_params)
                return self._convert_to_openai_format(response)
                
        except Exception as e:
            logger.error(f"Z.ai API error: {e}")
            # Return error in OpenAI format
            return {
                "error": {
                    "message": str(e),
                    "type": "z_ai_error",
                    "code": "api_error"
                }
            }
    
    def _convert_to_openai_format(self, zai_response) -> Dict[str, Any]:
        """Convert z.ai response to OpenAI format"""
        try:
            # Handle different response types from z.ai
            if hasattr(zai_response, 'choices') and zai_response.choices:
                choice = zai_response.choices[0]
                content = choice.message.content if hasattr(choice.message, 'content') else str(choice)
            else:
                content = str(zai_response)
            
            # Create OpenAI-compatible response
            return {
                "id": getattr(zai_response, 'id', 'zai-completion'),
                "object": "chat.completion",
                "created": getattr(zai_response, 'created', 0),
                "model": getattr(zai_response, 'model', 'glm-4'),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": getattr(getattr(zai_response, 'choices', [{}])[0] if hasattr(zai_response, 'choices') else {}, 'finish_reason', 'stop')
                }],
                "usage": getattr(zai_response, 'usage', {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                })
            }
        except Exception as e:
            logger.error(f"Error converting z.ai response: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant", 
                        "content": str(zai_response)
                    },
                    "finish_reason": "stop"
                }]
            }
    
    def _handle_stream_response(self, stream):
        """Handle streaming response from z.ai"""
        for chunk in stream:
            try:
                # Convert chunk to OpenAI format
                yield {
                    "id": getattr(chunk, 'id', 'zai-stream'),
                    "object": "chat.completion.chunk",
                    "created": getattr(chunk, 'created', 0),
                    "model": getattr(chunk, 'model', 'glm-4'),
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": getattr(getattr(chunk, 'choices', [{}])[0], 'delta', {}).get('content', '')
                        },
                        "finish_reason": getattr(getattr(chunk, 'choices', [{}])[0], 'finish_reason', None)
                    }]
                }
            except Exception as e:
                logger.error(f"Error in stream chunk: {e}")
                continue


def get_z_ai_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> ZAIWrapper:
    """
    Get configured z.ai client for autogenlib
    
    Args:
        api_key: Z.ai API key (optional, will use env var if not provided)
        base_url: Custom base URL (optional)
    
    Returns:
        Configured ZAIWrapper instance
    """
    return ZAIWrapper(api_key=api_key, base_url=base_url)


def is_zai_available() -> bool:
    """Check if z.ai SDK is available and properly configured"""
    if not ZAI_AVAILABLE:
        return False
    
    api_key = os.environ.get("ZAI_API_KEY") or os.environ.get("ZHIPU_API_KEY")
    return bool(api_key)


def test_zai_connection() -> Dict[str, Any]:
    """Test z.ai connection and return status"""
    try:
        if not is_zai_available():
            return {
                "status": "error",
                "message": "Z.ai not available or API key not configured",
                "available": False
            }
        
        client = get_z_ai_client()
        
        # Test with simple message
        test_response = client.chat.create(
            model="glm-4",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        if "error" in test_response:
            return {
                "status": "error",
                "message": test_response["error"]["message"],
                "available": True
            }
        
        return {
            "status": "success",
            "message": "Z.ai connection successful",
            "available": True,
            "model": test_response.get("model", "glm-4")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {e}",
            "available": ZAI_AVAILABLE
        }


# Export main interface
__all__ = ['ZAIWrapper', 'get_z_ai_client', 'is_zai_available', 'test_zai_connection']