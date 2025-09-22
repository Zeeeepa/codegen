#!/usr/bin/env python3
"""
Enhanced Multithreaded Chinese to English Translation Tool for Python Codebases

This tool extracts Chinese characters from Python files and translates them to English
using the web-ui-python-sdk with multithreading for improved performance.
Features a comprehensive Tkinter GUI for folder/repo selection and progress tracking.

Requirements:
    pip install requests tkinter-modern tqdm
    git clone https://github.com/Zeeeepa/web-ui-python-sdk.git
    # Add the SDK to your Python path or place this script in the SDK directory

System Requirements:
    - Python 3.7+
    - tkinter (usually comes with Python)
    - web-ui-python-sdk package
    - Active internet connection for translation API

Features:
- Modern Tkinter GUI with folder/repo selection
- Multithreaded translation with 10 worker threads
- Large batch processing (100-500 items per batch)
- Real-time progress tracking and status logging
- GitHub repository cloning and processing
- Translation cache management
- Resume capability for interrupted translations

Usage:
    python multiple_language_standalone_enhanced.py

GUI Features:
- Select Folder: Opens file explorer for local directory selection
- Select Repo: Input field for GitHub URLs (username/repo or full URL)
- Progress tracking with detailed status logs
- Cancel/pause functionality
- Statistics display
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
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Union
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import webbrowser

# Import the web-ui-python-sdk components
try:
    # Try to import from the SDK directory structure
    from client import ZAIClient
    from core.exceptions import ZAIError
    from models import ChatCompletionResponse
    print("✓ Successfully imported web-ui-python-sdk")
except ImportError as e:
    print(f"❌ Failed to import web-ui-python-sdk: {e}")
    print("Please ensure the web-ui-python-sdk is in your Python path")
    print("You can:")
    print("1. Clone: git clone https://github.com/Zeeeepa/web-ui-python-sdk.git")
    print("2. Place this script in the SDK directory, or")
    print("3. Add the SDK directory to your PYTHONPATH")
    exit(1)


class TranslationGUI:
    """Modern Tkinter GUI for the translation tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chinese to English Code Translator - Enhanced")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Initialize translator
        self.translator = None
        self.translation_thread = None
        self.cancel_flag = threading.Event()
        
        # GUI Variables
        self.selected_path = tk.StringVar()
        self.repo_url = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready to translate...")
        self.stats_var = tk.StringVar(value="Statistics will appear here")
        
        # Message queue for thread-safe GUI updates
        self.message_queue = Queue()
        
        self.setup_ui()
        self.setup_styles()
        
        # Start message processing
        self.process_messages()
    
    def setup_styles(self):
        """Setup modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom colors
        style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Header
        header_label = ttk.Label(main_frame, text="🚀 Enhanced Chinese to English Code Translator", 
                                style='Header.TLabel')
        header_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Folder Selection Section
        folder_frame = ttk.LabelFrame(main_frame, text="📁 Local Folder Selection", padding="15")
        folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Selected Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.path_entry = ttk.Entry(folder_frame, textvariable=self.selected_path, state='readonly')
        self.path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.browse_btn = ttk.Button(folder_frame, text="Browse Folder", command=self.browse_folder)
        self.browse_btn.grid(row=0, column=2)
        
        # Repository Selection Section
        repo_frame = ttk.LabelFrame(main_frame, text="🔗 GitHub Repository Selection", padding="15")
        repo_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        repo_frame.columnconfigure(1, weight=1)
        
        ttk.Label(repo_frame, text="Repository URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.repo_entry = ttk.Entry(repo_frame, textvariable=self.repo_url, 
                                   font=('Courier', 10))
        self.repo_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.clone_btn = ttk.Button(repo_frame, text="Clone Repo", command=self.clone_repository)
        self.clone_btn.grid(row=0, column=2)
        
        # Help text
        help_text = "Examples: username/repo, https://github.com/username/repo, or https://github.com/binary-husky/gpt_academic"
        ttk.Label(repo_frame, text=help_text, font=('Helvetica', 9), foreground='gray').grid(
            row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Translation Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.translate_btn = ttk.Button(control_frame, text="🚀 Start Translation", 
                                       command=self.start_translation, style='Accent.TButton')
        self.translate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(control_frame, text="⏹️ Cancel", 
                                    command=self.cancel_translation, state='disabled')
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(control_frame, text="🗑️ Clear", command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Translation Progress", padding="15")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, style='TProgressbar')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        self.stats_label = ttk.Label(progress_frame, textvariable=self.stats_var, font=('Courier', 9))
        self.stats_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="📝 Status Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=('Courier', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        ttk.Label(footer_frame, text="Enhanced Multithreaded Translation Tool", 
                 font=('Helvetica', 8), foreground='gray').pack()
        github_label = ttk.Label(footer_frame, text="GitHub: Zeeeepa/web-ui-python-sdk", 
                                font=('Helvetica', 8), foreground='blue', cursor='hand2')
        github_label.pack()
        github_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Zeeeepa/web-ui-python-sdk"))
    
    def log_message(self, message: str, level: str = "INFO"):
        """Thread-safe logging to the message queue"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        self.message_queue.put(('log', formatted_message))
    
    def update_progress(self, percentage: float, status: str = ""):
        """Thread-safe progress update"""
        self.message_queue.put(('progress', (percentage, status)))
    
    def update_stats(self, stats: str):
        """Thread-safe stats update"""
        self.message_queue.put(('stats', stats))
    
    def process_messages(self):
        """Process messages from worker threads"""
        try:
            while True:
                try:
                    message_type, data = self.message_queue.get_nowait()
                    
                    if message_type == 'log':
                        self.log_text.insert(tk.END, data + '\n')
                        self.log_text.see(tk.END)
                    elif message_type == 'progress':
                        percentage, status = data
                        self.progress_var.set(percentage)
                        if status:
                            self.status_var.set(status)
                    elif message_type == 'stats':
                        self.stats_var.set(data)
                    elif message_type == 'complete':
                        self.translation_complete(data)
                    elif message_type == 'error':
                        self.translation_error(data)
                    
                except Empty:
                    break
        except Exception as e:
            print(f"Error processing messages: {e}")
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def browse_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(title="Select the codebase directory to translate")
        if folder:
            self.selected_path.set(folder)
            self.repo_url.set("")  # Clear repo URL when folder is selected
            self.log_message(f"Selected folder: {folder}")
    
    def clone_repository(self):
        """Clone repository from URL"""
        url = self.repo_url.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a repository URL")
            return
        
        # Normalize URL format
        if not url.startswith(('http://', 'https://')):
            if '/' in url and not url.startswith('github.com'):
                url = f"https://github.com/{url}"
            elif not url.startswith('github.com'):
                messagebox.showwarning("Invalid URL", "Please provide a valid GitHub URL or username/repo format")
                return
        
        self.log_message(f"Starting to clone repository: {url}")
        self.clone_btn.config(state='disabled')
        
        # Run cloning in separate thread
        def clone_worker():
            try:
                # Extract repo name
                repo_name = url.rstrip('/').split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                
                # Clone to current directory
                clone_path = os.path.join(os.getcwd(), repo_name)
                
                # Remove existing directory
                if os.path.exists(clone_path):
                    self.log_message(f"Removing existing directory: {clone_path}")
                    shutil.rmtree(clone_path)
                
                # Clone repository
                result = subprocess.run(['git', 'clone', url, clone_path], 
                                     capture_output=True, text=True, check=True)
                
                # Update UI
                self.message_queue.put(('log', f"✓ Successfully cloned to: {clone_path}"))
                self.selected_path.set(clone_path)
                
            except subprocess.CalledProcessError as e:
                self.message_queue.put(('log', f"❌ Git clone failed: {e.stderr}"))
            except Exception as e:
                self.message_queue.put(('log', f"❌ Clone error: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.clone_btn.config(state='normal'))
        
        threading.Thread(target=clone_worker, daemon=True).start()
    
    def start_translation(self):
        """Start the translation process"""
        source_path = self.selected_path.get().strip()
        if not source_path or not os.path.isdir(source_path):
            messagebox.showwarning("Path Error", "Please select a valid folder or clone a repository first")
            return
        
        # Reset cancel flag
        self.cancel_flag.clear()
        
        # Update UI state
        self.translate_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.browse_btn.config(state='disabled')
        self.clone_btn.config(state='disabled')
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        self.status_var.set("Initializing translation...")
        
        self.log_message("🚀 Starting enhanced multithreaded translation")
        self.log_message(f"Source directory: {source_path}")
        self.log_message("Using 10 worker threads with large batch processing")
        
        # Start translation in separate thread
        self.translation_thread = threading.Thread(
            target=self.run_translation,
            args=(source_path,),
            daemon=True
        )
        self.translation_thread.start()
    
    def run_translation(self, source_path: str):
        """Run translation in background thread"""
        try:
            # Initialize translator
            self.translator = EnhancedChineseTranslator(
                progress_callback=self.update_progress,
                log_callback=self.log_message,
                stats_callback=self.update_stats,
                cancel_flag=self.cancel_flag
            )
            
            # Run translation
            success = self.translator.translate_directory(source_path)
            
            if success:
                self.message_queue.put(('complete', True))
            else:
                self.message_queue.put(('complete', False))
                
        except Exception as e:
            self.message_queue.put(('error', str(e)))
    
    def cancel_translation(self):
        """Cancel the current translation"""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the translation?"):
            self.cancel_flag.set()
            self.log_message("⏹️ Cancellation requested...")
            self.status_var.set("Canceling translation...")
    
    def translation_complete(self, success: bool):
        """Handle translation completion"""
        # Reset UI state
        self.translate_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
        self.browse_btn.config(state='normal')
        self.clone_btn.config(state='normal')
        
        if success:
            self.status_var.set("✅ Translation completed successfully!")
            self.log_message("🎉 Translation completed successfully!")
            messagebox.showinfo("Success", "Translation completed successfully!\nCheck the log for details.")
        else:
            self.status_var.set("⚠️ Translation completed with issues")
            self.log_message("⚠️ Translation completed with some issues")
    
    def translation_error(self, error_msg: str):
        """Handle translation error"""
        # Reset UI state
        self.translate_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
        self.browse_btn.config(state='normal')
        self.clone_btn.config(state='normal')
        
        self.status_var.set("❌ Translation failed")
        self.log_message(f"❌ Translation failed: {error_msg}")
        messagebox.showerror("Translation Error", f"Translation failed:\n{error_msg}")
    
    def clear_all(self):
        """Clear all selections and logs"""
        if messagebox.askyesno("Confirm Clear", "Clear all selections and logs?"):
            self.selected_path.set("")
            self.repo_url.set("")
            self.progress_var.set(0)
            self.status_var.set("Ready to translate...")
            self.stats_var.set("Statistics will appear here")
            self.log_text.delete(1.0, tk.END)
            self.log_message("🗑️ Cleared all data")
    
    def run(self):
        """Start the GUI"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("GUI closed by user")


class EnhancedChineseTranslator:
    """Enhanced multithreaded translator with large batch processing"""
    
    def __init__(self, progress_callback=None, log_callback=None, stats_callback=None, cancel_flag=None):
        self.blacklist = [
            'multi-language', '.git', 'private_upload', 'build', '.github', 
            '.vscode', '__pycache__', 'venv', '.env', 'node_modules', 'dist',
            '__pycache__', '.pyc', '_translated', '_translate_cache.json'
        ]
        
        # Threading configuration
        self.num_workers = 10  # 10 worker threads
        self.large_batch_size = (100, 500)  # Large batch sizes
        
        # Callback functions for GUI updates
        self.progress_callback = progress_callback or (lambda p, s="": None)
        self.log_callback = log_callback or (lambda m, l="INFO": print(f"{l}: {m}"))
        self.stats_callback = stats_callback or (lambda s: None)
        self.cancel_flag = cancel_flag or threading.Event()
        
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
            self.log_callback(f"✓ ZAI client initialized with token: {token_preview}...")
            return True
        except Exception as e:
            self.log_callback(f"❌ Failed to initialize ZAI client: {e}", "ERROR")
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
                self.log_callback(f"Syntax error in {file_path}, skipping AST parsing", "WARNING")
            
            # Extract comments
            for line_no, line in enumerate(content.splitlines(), 1):
                comment_match = re.search(r'#.*$', line)
                if comment_match:
                    comment = comment_match.group(0)
                    if self.contains_chinese(comment):
                        string_literals.append(comment)
        
        except Exception as e:
            self.log_callback(f"Error processing file {file_path}: {e}", "ERROR")
        
        return identifiers, string_literals
    
    def extract_chinese_from_directory(self, directory_path: str) -> Tuple[Set[str], Set[str]]:
        """Extract all Chinese characters from Python files in directory"""
        all_identifiers = set()
        all_string_literals = set()
        file_count = 0
        
        self.log_callback(f"📂 Scanning directory: {directory_path}")
        
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
                self.log_callback(f"Processing: {file_path}")
                identifiers, string_literals = self.extract_chinese_from_file(file_path)
                all_identifiers.update(identifiers)
                all_string_literals.update(string_literals)
        
        self.log_callback(f"✓ Processed {file_count} Python files")
        self.log_callback(f"✓ Found {len(all_identifiers)} unique Chinese identifiers")
        self.log_callback(f"✓ Found {len(all_string_literals)} unique Chinese string literals")
        
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
                self.log_callback(f"Error loading cache: {e}", "WARNING")
        return {}
    
    def save_cache(self, cache_file: str, cache_data: Dict[str, str]):
        """Thread-safe cache saving"""
        with self.cache_lock:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                self.log_callback(f"Error saving cache: {e}", "ERROR")
    
    def translate_batch_worker(self, texts: List[str], is_identifier: bool = False) -> Dict[str, str]:
        """Worker function for translating a batch of texts"""
        if not texts or self.cancel_flag.is_set():
            return {}
        
        thread_id = threading.current_thread().name
        batch_size = len(texts)
        
        self.log_callback(f"🔄 [{thread_id}] Processing batch of {batch_size} items")
        
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
            self.log_callback(f"❌ [{thread_id}] Batch translation error: {e}", "ERROR")
            # Mark all items as failed
            for item in texts:
                translations[item] = None
        
        # Update progress
        with self.stats_lock:
            self.completed_items += batch_size
            progress = (self.completed_items / self.total_items) * 100 if self.total_items > 0 else 0
            self.progress_callback(progress, f"Translated {self.completed_items}/{self.total_items} items")
        
        successful = sum(1 for v in translations.values() if v is not None)
        self.log_callback(f"✓ [{thread_id}] Completed batch: {successful}/{batch_size} successful")
        
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
        
        self.log_callback(f"🚀 Starting multithreaded translation of {len(texts)} items")
        self.log_callback(f"Using {self.num_workers} worker threads")
        
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
        
        self.log_callback(f"Created {len(batches)} batches with sizes {self.large_batch_size[0]}-{self.large_batch_size[1]}")
        
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
                    self.log_callback(f"✅ Completed batch {completed_batches}/{len(batches)}")
                    
                    # Update cache periodically
                    with self.cache_lock:
                        self.translation_cache.update(batch_translations)
                        if completed_batches % 5 == 0:  # Save every 5 batches
                            self.save_cache(self.cache_file_path, self.translation_cache)
                    
                except Exception as e:
                    self.log_callback(f"❌ Batch {batch_idx} failed: {e}", "ERROR")
        
        self.log_callback(f"🎯 Multithreaded translation completed: {len(all_translations)} items processed")
        return all_translations
    
    def translate_codebase(self, source_dir: str, target_dir: str):
        """Apply translations to create translated codebase"""
        self.log_callback(f"📝 Creating translated codebase at: {target_dir}")
        
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
        
        self.log_callback(f"✅ Applied translations to {file_count} Python files")
    
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
            self.log_callback(f"Error translating file {file_path}: {e}", "ERROR")
    
    def translate_directory(self, source_dir: str) -> bool:
        """Main translation workflow"""
        try:
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
            self.log_callback(f"📋 Loaded {cached_count} cached translations")
            
            # Extract Chinese characters
            self.progress_callback(10, "Scanning Python files...")
            identifiers, string_literals = self.extract_chinese_from_directory(source_dir)
            
            if self.cancel_flag.is_set():
                return False
            
            # Calculate total items to translate
            missing_identifiers = self.get_missing_translations(identifiers, self.translation_cache)
            missing_literals = self.get_missing_translations(string_literals, self.translation_cache)
            self.total_items = len(missing_identifiers) + len(missing_literals)
            self.completed_items = 0
            
            self.log_callback(f"📊 Translation needed: {len(missing_identifiers)} identifiers + {len(missing_literals)} literals = {self.total_items} total")
            
            if self.total_items == 0:
                self.log_callback("✅ All items already translated!")
                self.progress_callback(50, "All items already cached, applying translations...")
            
            # Update stats
            stats = f"Files: {len(identifiers) + len(string_literals)} | Cached: {cached_count} | To Translate: {self.total_items}"
            self.stats_callback(stats)
            
            # Translate missing identifiers
            if missing_identifiers and not self.cancel_flag.is_set():
                self.log_callback(f"🔤 Translating {len(missing_identifiers)} code identifiers...")
                identifier_translations = self.translate_with_multithreading(missing_identifiers, is_identifier=True)
                self.translation_cache.update(identifier_translations)
                self.save_cache(self.cache_file_path, self.translation_cache)
            
            # Translate missing literals
            if missing_literals and not self.cancel_flag.is_set():
                self.log_callback(f"📝 Translating {len(missing_literals)} string literals...")
                literal_translations = self.translate_with_multithreading(missing_literals, is_identifier=False)
                self.translation_cache.update(literal_translations)
                self.save_cache(self.cache_file_path, self.translation_cache)
            
            if self.cancel_flag.is_set():
                self.log_callback("⏹️ Translation cancelled by user")
                return False
            
            # Apply translations to create translated codebase
            self.progress_callback(90, "Applying translations to codebase...")
            self.translate_codebase(source_dir, target_dir)
            
            if self.cancel_flag.is_set():
                return False
            
            # Final statistics
            successful_translations = sum(1 for v in self.translation_cache.values() if v is not None)
            failed_translations = len(self.translation_cache) - successful_translations
            
            self.progress_callback(100, "Translation completed!")
            
            final_stats = f"""✅ TRANSLATION COMPLETE
• Source: {source_dir}
• Target: {target_dir}
• Cache: {self.cache_file_path}
• Total translations: {len(self.translation_cache)}
• Successful: {successful_translations}
• Failed: {failed_translations}
• Success rate: {(successful_translations/len(self.translation_cache)*100):.1f}%"""
            
            self.log_callback(final_stats)
            self.stats_callback(f"Complete: {successful_translations} success, {failed_translations} failed")
            
            return True
        
        except Exception as e:
            self.log_callback(f"❌ Translation failed: {e}", "ERROR")
            return False


def main():
    """Main entry point"""
    print("🚀 Enhanced Chinese to English Translation Tool")
    print("=" * 60)
    
    # Check for required dependencies
    try:
        import concurrent.futures
        print("✓ Threading support available")
    except ImportError:
        print("❌ Threading support not available")
        return
    
    # Start GUI
    try:
        gui = TranslationGUI()
        gui.run()
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()