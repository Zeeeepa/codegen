#!/usr/bin/env python3
"""
Enhanced Chinese to English Translation Tool - Standalone Version
Standalone multithreaded CLI version with embedded ZAI SDK for maximum compatibility.
"""

import os
import json
import re
import shutil
import ast
import time
import random
import uuid
import threading
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin


# ============================================================================
# Embedded Z.AI SDK - Essential components only
# ============================================================================

class ZAIError(Exception):
    """Base exception for Z.AI API errors."""
    pass


class ChatCompletionResponse:
    """Complete chat completion response."""
    def __init__(self, content: str, thinking: str = "", usage: Dict = None, 
                 message_id: str = "", done: bool = True):
        self.content = content
        self.thinking = thinking
        self.usage = usage or {}
        self.message_id = message_id
        self.done = done


class HTTPClient:
    """HTTP Client for Z.AI API requests."""
    
    def __init__(self, base_url: str, timeout: int, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a new session with default headers."""
        session = requests.Session()
        session.headers.update({
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "referer": "https://chat.z.ai/",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        })
        return session
    
    def set_auth_header(self, token: str):
        """Set authorization header."""
        self.session.headers["authorization"] = f"Bearer {token}"
    
    def update_headers(self, headers: Dict[str, str]):
        """Update session headers."""
        self.session.headers.update(headers)
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    stream: bool = False) -> requests.Response:
        """Make HTTP request to API."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            timeout = (30, 60) if stream else self.timeout
            
            if stream:
                headers = dict(self.session.headers)
                headers.pop('accept-encoding', None)
                response = self.session.request(
                    method=method, url=url, json=data if data else None,
                    timeout=timeout, stream=stream, headers=headers
                )
            else:
                response = self.session.request(
                    method=method, url=url, json=data if data else None,
                    timeout=timeout, stream=stream
                )
            
            if self.verbose:
                print(f"[DEBUG] Request to {url}")
                print(f"[DEBUG] Status: {response.status_code}")
            
            response.raise_for_status()
            
            if response.cookies:
                self.session.cookies.update(response.cookies)
            
            return response
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.text
                    error_msg += f" - Response: {error_detail}"
                except:
                    pass
            raise ZAIError(error_msg)


class AuthManager:
    """Manages authentication for Z.AI API."""
    
    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
        self.token: Optional[str] = None
        self.auth_data: Optional[Dict] = None
    
    def get_guest_token(self) -> str:
        """Get a guest token from Z.AI auth endpoint."""
        try:
            response = self.http_client.make_request("GET", "/api/v1/auths/")
            auth_data = response.json()
            token = auth_data.get("token")
            
            if not token:
                raise ZAIError("No token found in auth response")
            
            self.auth_data = auth_data
            self.token = token
            return token
            
        except Exception as e:
            raise ZAIError(f"Failed to get guest token: {e}")
    
    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token
        self.http_client.set_auth_header(token)
    
    def get_auth_data(self) -> Optional[Dict]:
        """Get stored authentication data."""
        return self.auth_data


class ZAIClient:
    """Z.AI API Client - Simplified version for translation."""
    
    def __init__(self, token: str = None, base_url: str = "https://chat.z.ai", 
                 timeout: int = 180, auto_auth: bool = True, verbose: bool = False):
        self.base_url = base_url
        self.timeout = timeout
        self.verbose = verbose
        
        self.http_client = HTTPClient(base_url, timeout, verbose=verbose)
        self.auth_manager = AuthManager(self.http_client)
        
        if not token and auto_auth:
            token = self.auth_manager.get_guest_token()
        
        if token:
            self.auth_manager.set_token(token)
    
    @property
    def token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.auth_manager.token
    
    def simple_chat(self, message: str, model: str = "glm-4.5v", 
                   enable_thinking: bool = True, chat_title: str = "Simple Chat",
                   temperature: float = None, top_p: float = None,
                   max_tokens: int = None) -> ChatCompletionResponse:
        """Simple one-shot chat completion."""
        chat_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        # Build chat creation payload
        chat_payload = {
            "chat": {
                "id": "",
                "title": chat_title,
                "models": [model],
                "params": {},
                "history": {
                    "messages": {
                        message_id: {
                            "id": message_id,
                            "parentId": None,
                            "childrenIds": [],
                            "role": "user",
                            "content": message,
                            "timestamp": timestamp,
                            "models": [model]
                        }
                    },
                    "currentId": message_id
                },
                "messages": [{
                    "id": message_id,
                    "parentId": None,
                    "childrenIds": [],
                    "role": "user",
                    "content": message,
                    "timestamp": timestamp,
                    "models": [model]
                }],
                "tags": [],
                "flags": [],
                "features": [
                    {"type": "mcp", "server": "vibe-coding", "status": "hidden"},
                    {"type": "mcp", "server": "ppt-maker", "status": "hidden"},
                    {"type": "mcp", "server": "image-search", "status": "hidden"}
                ],
                "mcp_servers": [],
                "enable_thinking": enable_thinking,
                "timestamp": int(time.time() * 1000)
            }
        }
        
        self.http_client.update_headers({"x-fe-version": "prod-fe-1.0.70"})
        
        try:
            # Create chat
            response = self.http_client.make_request("POST", "/api/v1/chats/new", chat_payload)
            chat_data = response.json()
            actual_chat_id = chat_data.get("id")
            
            if not actual_chat_id:
                raise ZAIError("Failed to create chat - no chat ID returned")
            
            # Get completion via streaming (simplified - just collect all content)
            completion_payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "params": {},
                "features": {
                    "image_generation": False,
                    "web_search": False,
                    "auto_web_search": False,
                    "preview_mode": True,
                    "flags": [],
                    "features": [
                        {"type": "mcp", "server": "vibe-coding", "status": "hidden"},
                        {"type": "mcp", "server": "ppt-maker", "status": "hidden"},
                        {"type": "mcp", "server": "image-search", "status": "hidden"}
                    ],
                    "enable_thinking": enable_thinking
                },
                "variables": {
                    "{{USER_NAME}}": "Guest",
                    "{{USER_LOCATION}}": "Unknown",
                    "{{CURRENT_DATETIME}}": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "model_item": {
                    "id": model,
                    "name": model.upper(),
                    "owned_by": "openai",
                    "info": {
                        "id": model,
                        "params": {
                            "temperature": temperature if temperature is not None else 0.8,
                            "top_p": top_p if top_p is not None else 0.6,
                            "max_tokens": max_tokens if max_tokens is not None else 80000
                        }
                    }
                },
                "chat_id": actual_chat_id,
                "id": str(uuid.uuid4())
            }
            
            # Add optional parameters to params dict
            if temperature is not None:
                completion_payload["params"]["temperature"] = temperature
            if top_p is not None:
                completion_payload["params"]["top_p"] = top_p  
            if max_tokens is not None:
                completion_payload["params"]["max_tokens"] = max_tokens
            
            # Update referer header  
            original_referer = self.http_client.session.headers.get("referer")
            self.http_client.session.headers["referer"] = f"https://chat.z.ai/c/{actual_chat_id}"
            
            try:
                # Make streaming request and collect response
                response = self.http_client.make_request(
                    "POST", 
                    "/api/chat/completions", 
                    completion_payload,
                    stream=True
                )
                
                content = ""
                thinking = ""
                current_phase = None
                
                # Process streaming response  
                line_count = 0
                for line in response.iter_lines():
                    line_count += 1
                        
                    if line:
                        # Decode bytes to string if needed
                        if isinstance(line, bytes):
                            line = line.decode('utf-8')
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue
                            
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip():
                                try:
                                    data = json.loads(data_str)
                                    
                                    # Extract the actual data from the wrapper
                                    if 'data' in data and isinstance(data['data'], dict):
                                        actual_data = data['data']
                                        
                                        # Handle phase information
                                        if 'phase' in actual_data:
                                            current_phase = actual_data['phase']
                                        
                                        # Handle complete message content (first response with choices)
                                        if 'choices' in actual_data and len(actual_data['choices']) > 0:
                                            choice = actual_data['choices'][0]
                                            if 'message' in choice:
                                                message = choice['message']
                                                if 'content' in message:
                                                    msg_content = message['content']
                                                    # Remove box markers if present
                                                    msg_content = msg_content.replace('<|begin_of_box|>', '').replace('<|end_of_box|>', '')
                                                    content = msg_content  # Replace, don't append
                                                if 'reasoning_content' in message:
                                                    reasoning = message['reasoning_content']
                                                    thinking = reasoning  # Replace, don't append
                                        
                                        # Check for done signal
                                        if actual_data.get('done', False):
                                            break
                                        
                                except json.JSONDecodeError:
                                    continue
                    
                    # Add safety break for long streams
                    if line_count > 1000:
                        break
            
                return ChatCompletionResponse(
                    content=content.strip(),
                    thinking=thinking.strip(),
                    usage={},
                    message_id=str(uuid.uuid4()),
                    done=True
                )
            finally:
                # Restore original referer
                if original_referer:
                    self.http_client.session.headers["referer"] = original_referer
            
        except Exception as e:
            raise ZAIError(f"Simple chat failed: {e}")


# ============================================================================
# End of Embedded Z.AI SDK
# ============================================================================


class ProgressReporter:
    """Simple progress reporting for CLI"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_update = 0
    
    def update(self, percentage: float, status: str = ""):
        current_time = time.time()
        if current_time - self.last_update > 2:  # Update every 2 seconds
            elapsed = current_time - self.start_time
            print(f"[{elapsed:.1f}s] Progress: {percentage:.1f}% - {status}")
            self.last_update = current_time
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")


class EnhancedChineseTranslatorCLI:
    """Enhanced multithreaded translator CLI with embedded SDK"""
    
    def __init__(self):
        self.blacklist = [
            'multi-language', '.git', 'private_upload', 'build', '.github', 
            '.vscode', '__pycache__', 'venv', '.env', 'node_modules', 'dist',
            '__pycache__', '.pyc', '_translated', '_translate_cache.json'
        ]
        
        # Threading configuration  
        self.num_workers = 10  # 10 worker threads
        self.large_batch_size = (100, 500)  # Large batch sizes
        
        # Progress reporting
        self.progress = ProgressReporter()
        self.cancel_flag = threading.Event()
        
        # Translation state
        self.client = None
        self.translation_cache = {}
        self.cache_file_path = None
        self.total_items = 0
        self.completed_items = 0
        
        # Thread safety
        self.cache_lock = threading.Lock()
        self.stats_lock = threading.Lock()
    
    def init_client(self) -> bool:
        """Initialize the ZAI client"""
        try:
            self.client = ZAIClient(auto_auth=True, verbose=False)
            token_preview = self.client.token[:20] if self.client.token else 'None'
            self.progress.log(f"✓ ZAI client initialized with token: {token_preview}...")
            return True
        except Exception as e:
            self.progress.log(f"❌ Failed to initialize ZAI client: {e}", "ERROR")
            return False
    
    def contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        chinese_regex = re.compile(r'[\u4e00-\u9fff]+')
        return chinese_regex.search(text) is not None
    
    def extract_chinese_from_file(self, file_path: str) -> Tuple[List[str], List[str]]:
        """Extract Chinese characters from a Python file"""
        identifiers = []
        string_literals = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST for identifiers
            try:
                root = ast.parse(content)
                for node in ast.walk(root):
                    # Function and class names
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if self.contains_chinese(node.name):
                            identifiers.append(node.name)
                    
                    # Variable names
                    elif isinstance(node, ast.Name):
                        if self.contains_chinese(node.id):
                            identifiers.append(node.id)
                    
                    # Import names
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if self.contains_chinese(alias.name):
                                identifiers.append(alias.name)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and self.contains_chinese(node.module):
                            identifiers.append(node.module)
                        for alias in node.names:
                            if self.contains_chinese(alias.name):
                                identifiers.append(alias.name)
                    
                    # String literals
                    elif isinstance(node, ast.Str):
                        if self.contains_chinese(node.s):
                            string_literals.append(node.s)
                    
                    # For Python 3.8+
                    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                        if self.contains_chinese(node.value):
                            string_literals.append(node.value)
            
            except SyntaxError:
                self.progress.log(f"Syntax error in {file_path}, skipping AST parsing", "WARNING")
            
            # Extract comments
            for line_no, line in enumerate(content.splitlines(), 1):
                comment_match = re.search(r'#.*$', line)
                if comment_match:
                    comment = comment_match.group(0)
                    if self.contains_chinese(comment):
                        string_literals.append(comment)
        
        except Exception as e:
            self.progress.log(f"Error processing file {file_path}: {e}", "ERROR")
        
        return identifiers, string_literals
    
    def extract_chinese_from_directory(self, directory_path: str) -> Tuple[Set[str], Set[str]]:
        """Extract all Chinese characters from Python files in directory"""
        all_identifiers = set()
        all_string_literals = set()
        file_count = 0
        
        self.progress.log(f"📂 Scanning directory: {directory_path}")
        
        for root, dirs, files in os.walk(directory_path):
            # Skip blacklisted directories
            dirs[:] = [d for d in dirs if not any(blacklisted in d for blacklisted in self.blacklist)]
            
            if any(blacklisted in root for blacklisted in self.blacklist):
                continue
            
            python_files = [f for f in files if f.endswith('.py')]
            file_count += len(python_files)
            
            for file in python_files:
                if self.cancel_flag.is_set():
                    return all_identifiers, all_string_literals
                
                file_path = os.path.join(root, file)
                if file_count < 20:  # Show first 20 files being processed
                    self.progress.log(f"Processing: {file_path}")
                identifiers, string_literals = self.extract_chinese_from_file(file_path)
                all_identifiers.update(identifiers)
                all_string_literals.update(string_literals)
        
        self.progress.log(f"✓ Processed {file_count} Python files")
        self.progress.log(f"✓ Found {len(all_identifiers)} unique Chinese identifiers")
        self.progress.log(f"✓ Found {len(all_string_literals)} unique Chinese string literals")
        
        return all_identifiers, all_string_literals
    
    def load_cache(self, cache_file: str) -> Dict[str, str]:
        """Load translation cache from JSON file"""
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    # Filter out None values and ensure keys contain Chinese
                    return {k: v for k, v in cache.items() 
                           if v is not None and self.contains_chinese(k)}
            except Exception as e:
                self.progress.log(f"Error loading cache: {e}", "WARNING")
        return {}
    
    def save_cache(self, cache_file: str, cache_data: Dict[str, str]):
        """Thread-safe cache saving"""
        with self.cache_lock:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                self.progress.log(f"Error saving cache: {e}", "ERROR")
    
    def translate_batch_worker(self, texts: List[str], is_identifier: bool = False) -> Dict[str, str]:
        """Worker function for translating a batch of texts"""
        if not texts or self.cancel_flag.is_set():
            return {}
        
        thread_id = threading.current_thread().name
        batch_size = len(texts)
        
        translations = {}
        
        try:
            if is_identifier:
                # For identifiers, use CamelCase naming convention
                prompt = f"""Translate the following Chinese programming identifiers to English using CamelCase naming convention.
Return only the translations in the same order, one per line.
Do not include explanations, numbers, or extra text.

Chinese identifiers to translate:
{json.dumps(texts, ensure_ascii=False)}"""
            else:
                # For string literals and comments
                prompt = f"""Translate the following Chinese text to English.
Return the translations in JSON format: {{"original_text": "translated_text"}}
Keep the same number of items and maintain the structure.

Chinese texts to translate:
{json.dumps(texts, ensure_ascii=False)}"""
            
            # Make API call
            response = self.client.simple_chat(
                message=prompt,
                model="glm-4.5v",
                temperature=0.3,
                max_tokens=4000
            )
            
            if response and hasattr(response, 'content'):
                result = response.content.strip()
                
                if is_identifier:
                    # Parse line-by-line results for identifiers
                    translated_lines = [line.strip() for line in result.split('\n') if line.strip()]
                    for orig, trans in zip(texts, translated_lines):
                        # Clean up the translation
                        clean_trans = re.sub(r'^["\']|["\']$', '', trans)
                        clean_trans = re.sub(r'[^a-zA-Z0-9_]', '', clean_trans)
                        if clean_trans:
                            translations[orig] = clean_trans
                        else:
                            translations[orig] = None
                else:
                    # Parse JSON results for string literals
                    try:
                        json_result = json.loads(result)
                        for key, value in json_result.items():
                            if isinstance(value, str):
                                translations[key] = value
                            elif isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
                                translations[key] = value[0]
                            else:
                                translations[key] = None
                    except json.JSONDecodeError:
                        # Mark all items as failed
                        for orig in texts:
                            translations[orig] = None
        
        except Exception as e:
            self.progress.log(f"❌ [{thread_id}] Batch translation error: {e}", "ERROR")
            # Mark all items as failed
            for item in texts:
                translations[item] = None
        
        # Update progress
        with self.stats_lock:
            self.completed_items += batch_size
            progress_pct = (self.completed_items / self.total_items) * 100 if self.total_items > 0 else 0
            self.progress.update(progress_pct, f"Translated {self.completed_items}/{self.total_items} items")
        
        successful = sum(1 for v in translations.values() if v is not None)
        if successful > 0:
            self.progress.log(f"✓ [{thread_id}] Completed batch: {successful}/{batch_size} successful")
        
        return translations
    
    def get_missing_translations(self, all_texts: Set[str], cache: Dict[str, str]) -> List[str]:
        """Get list of texts that need translation"""
        missing = []
        for text in all_texts:
            if text not in cache or cache[text] is None:
                missing.append(text)
        return missing
    
    def translate_with_multithreading(self, texts: List[str], is_identifier: bool = False) -> Dict[str, str]:
        """Translate texts using multithreading with large batches"""
        if not texts:
            return {}
        
        self.progress.log(f"🚀 Starting multithreaded translation of {len(texts)} items")
        self.progress.log(f"Using {self.num_workers} worker threads")
        
        all_translations = {}
        
        # Create large batches
        batches = []
        batch_size = random.randint(*self.large_batch_size)
        
        for i in range(0, len(texts), batch_size):
            if self.cancel_flag.is_set():
                break
            batch = texts[i:i + batch_size]
            batches.append(batch)
            # Vary batch size for each batch
            batch_size = random.randint(*self.large_batch_size)
        
        self.progress.log(f"Created {len(batches)} batches with sizes {self.large_batch_size[0]}-{self.large_batch_size[1]}")
        
        # Process batches with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.num_workers, thread_name_prefix="TranslateWorker") as executor:
            # Submit all batches
            future_to_batch = {}
            for i, batch in enumerate(batches):
                if self.cancel_flag.is_set():
                    break
                future = executor.submit(self.translate_batch_worker, batch, is_identifier)
                future_to_batch[future] = i
            
            # Collect results
            completed_batches = 0
            for future in as_completed(future_to_batch):
                if self.cancel_flag.is_set():
                    # Cancel remaining futures
                    for f in future_to_batch:
                        f.cancel()
                    break
                
                batch_idx = future_to_batch[future]
                try:
                    batch_translations = future.result(timeout=300)  # 5 minute timeout per batch
                    all_translations.update(batch_translations)
                    
                    completed_batches += 1
                    self.progress.log(f"✅ Completed batch {completed_batches}/{len(batches)}")
                    
                    # Update cache periodically
                    with self.cache_lock:
                        self.translation_cache.update(batch_translations)
                        if completed_batches % 5 == 0:  # Save every 5 batches
                            self.save_cache(self.cache_file_path, self.translation_cache)
                    
                except Exception as e:
                    self.progress.log(f"❌ Batch {batch_idx} failed: {e}", "ERROR")
        
        self.progress.log(f"🎯 Multithreaded translation completed: {len(all_translations)} items processed")
        return all_translations
    
    def translate_codebase(self, source_dir: str, target_dir: str):
        """Apply translations to create translated codebase"""
        self.progress.log(f"📝 Creating translated codebase at: {target_dir}")
        
        # Copy entire directory structure
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        def ignore_function(dir, files):
            ignored = []
            for item in files:
                if any(blacklisted in item for blacklisted in self.blacklist):
                    ignored.append(item)
            return ignored
        
        shutil.copytree(source_dir, target_dir, ignore=ignore_function)
        
        # Sort cache by length (longest first) for proper replacement
        sorted_cache = dict(sorted(self.translation_cache.items(), key=lambda x: -len(x[0])))
        
        # Apply translations to all Python files
        file_count = 0
        for root, dirs, files in os.walk(target_dir):
            # Skip blacklisted directories
            dirs[:] = [d for d in dirs if not any(blacklisted in d for blacklisted in self.blacklist)]
            
            for file in files:
                if file.endswith('.py'):
                    if self.cancel_flag.is_set():
                        return
                    
                    file_path = os.path.join(root, file)
                    self.translate_file(file_path, sorted_cache)
                    file_count += 1
        
        self.progress.log(f"✅ Applied translations to {file_count} Python files")
    
    def translate_file(self, file_path: str, translation_cache: Dict[str, str]):
        """Apply translations to a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply translations
            for chinese_text, english_text in translation_cache.items():
                if english_text is None or not isinstance(english_text, str):
                    continue
                
                # Handle quotes in translations
                safe_translation = english_text
                if '"' in safe_translation:
                    safe_translation = safe_translation.replace('"', '`')
                if "'" in safe_translation:
                    safe_translation = safe_translation.replace("'", '`')
                
                content = content.replace(chinese_text, safe_translation)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        except Exception as e:
            self.progress.log(f"Error translating file {file_path}: {e}", "ERROR")
    
    def translate_directory(self, source_dir: str) -> bool:
        """Main translation workflow"""
        try:
            print("🚀 Enhanced Chinese to English Translation Tool - CLI")
            print("=" * 60)
            
            # Initialize client
            if not self.init_client():
                return False
            
            # Setup paths
            source_path = Path(source_dir)
            target_dir = str(source_path.parent / f"{source_path.name}_translated")
            self.cache_file_path = os.path.join(target_dir, "_translate_cache.json")
            
            # Create target directory
            os.makedirs(target_dir, exist_ok=True)
            
            # Load existing cache
            self.translation_cache = self.load_cache(self.cache_file_path)
            cached_count = len(self.translation_cache)
            self.progress.log(f"📋 Loaded {cached_count} cached translations")
            
            # Extract Chinese characters
            self.progress.update(10, "Scanning Python files...")
            identifiers, string_literals = self.extract_chinese_from_directory(source_dir)
            
            if self.cancel_flag.is_set():
                return False
            
            # Calculate total items to translate
            missing_identifiers = self.get_missing_translations(identifiers, self.translation_cache)
            missing_literals = self.get_missing_translations(string_literals, self.translation_cache)
            self.total_items = len(missing_identifiers) + len(missing_literals)
            self.completed_items = 0
            
            self.progress.log(f"📊 Translation needed: {len(missing_identifiers)} identifiers + {len(missing_literals)} literals = {self.total_items} total")
            
            if self.total_items == 0:
                self.progress.log("✅ All items already translated!")
                self.progress.update(50, "All items already cached, applying translations...")
            
            # Translate missing identifiers
            if missing_identifiers and not self.cancel_flag.is_set():
                self.progress.log(f"🔤 Translating {len(missing_identifiers)} code identifiers...")
                identifier_translations = self.translate_with_multithreading(missing_identifiers, is_identifier=True)
                self.translation_cache.update(identifier_translations)
                self.save_cache(self.cache_file_path, self.translation_cache)
            
            # Translate missing literals
            if missing_literals and not self.cancel_flag.is_set():
                self.progress.log(f"📝 Translating {len(missing_literals)} string literals...")
                literal_translations = self.translate_with_multithreading(missing_literals, is_identifier=False)
                self.translation_cache.update(literal_translations)
                self.save_cache(self.cache_file_path, self.translation_cache)
            
            if self.cancel_flag.is_set():
                self.progress.log("⏹️ Translation cancelled")
                return False
            
            # Apply translations to create translated codebase
            self.progress.update(90, "Applying translations to codebase...")
            self.translate_codebase(source_dir, target_dir)
            
            if self.cancel_flag.is_set():
                return False
            
            # Final statistics
            successful_translations = sum(1 for v in self.translation_cache.values() if v is not None)
            failed_translations = len(self.translation_cache) - successful_translations
            
            self.progress.update(100, "Translation completed!")
            
            print("\n" + "=" * 60)
            print("🎉 TRANSLATION COMPLETE!")
            print(f"• Source: {source_dir}")
            print(f"• Target: {target_dir}")
            print(f"• Cache: {self.cache_file_path}")
            print(f"• Total translations: {len(self.translation_cache)}")
            print(f"• Successful: {successful_translations}")
            print(f"• Failed: {failed_translations}")
            print(f"• Success rate: {(successful_translations/len(self.translation_cache)*100):.1f}%")
            print("=" * 60)
            
            return True
        
        except Exception as e:
            self.progress.log(f"❌ Translation failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python enhanced_translator_standalone.py <directory_path>")
        print("Example: python enhanced_translator_standalone.py gpt_academic")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    if not os.path.isdir(directory_path):
        print(f"❌ Error: '{directory_path}' is not a valid directory")
        sys.exit(1)
    
    try:
        translator = EnhancedChineseTranslatorCLI()
        success = translator.translate_directory(directory_path)
        
        if success:
            print("✅ Translation completed successfully!")
            sys.exit(0)
        else:
            print("❌ Translation failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ Translation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()