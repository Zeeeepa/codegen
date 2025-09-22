#!/usr/bin/env python3
"""
Enhanced Chinese to English Translation Tool - CLI Version
Command-line version of the enhanced multithreaded translator for server environments.
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

# Import the web-ui-python-sdk components (now in current directory)
try:
    from client import ZAIClient
    from models import ChatCompletionResponse
    print("✓ Successfully imported web-ui-python-sdk")
except ImportError as e:
    print(f"❌ Failed to import web-ui-python-sdk: {e}")
    print("Please ensure the web-ui-python-sdk is available")
    exit(1)


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
    """CLI version of the enhanced multithreaded translator"""
    
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
        print("Usage: python enhanced_translator_cli.py <directory_path>")
        print("Example: python enhanced_translator_cli.py /path/to/gpt_academic")
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