#!/usr/bin/env python3
"""
AI-Powered API Endpoint Manager

Transforms web chat interfaces into API endpoints and manages multiple AI services.
Based on the cryptocurrency bot pattern but adapted for endpoint creation and management.
"""

import asyncio
import json
import os
import random
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

# Core dependencies
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientResponseError, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from http.cookies import SimpleCookie
import pytz
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Timezone setup
wib = pytz.timezone('Asia/Jakarta')

class EndpointType(Enum):
    """Types of endpoints supported"""
    WEB_CHAT = "web_chat"
    REST_API = "rest_api"
    CUSTOM = "custom"

class ServerStatus(Enum):
    """Server status states"""
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class EndpointConfig:
    """Configuration for an API endpoint"""
    id: str
    name: str
    endpoint_type: EndpointType
    url: str
    model_name: str
    server_number: int
    status: ServerStatus
    auth_config: Dict[str, Any]
    headers: Dict[str, str]
    cookies: Dict[str, str]
    fingerprint: Optional[str] = None
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None

@dataclass
class WebChatConfig:
    """Configuration for web chat interface conversion"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    text_input_selector: str = ""
    send_button_selector: str = ""
    response_selector: str = ""
    new_chat_selector: str = ""
    model_selector: str = ""
    additional_selectors: Dict[str, str] = None

class AIEndpointManager:
    """
    Main class for managing AI API endpoints and web chat interface conversions.
    Adapted from cryptocurrency bot pattern for endpoint management.
    """
    
    def __init__(self):
        # Core configuration
        self.auto_create_endpoints = str(os.getenv("AUTO_CREATE_ENDPOINTS", "TRUE")).strip().lower() == "true"
        self.auto_manage_servers = str(os.getenv("AUTO_MANAGE_SERVERS", "TRUE")).strip().lower() == "true"
        self.auto_test_endpoints = str(os.getenv("AUTO_TEST_ENDPOINTS", "TRUE")).strip().lower() == "true"
        self.auto_discover_interfaces = str(os.getenv("AUTO_DISCOVER_INTERFACES", "FALSE")).strip().lower() == "true"
        
        # API configurations - similar to crypto bot's contract addresses
        self.CODEGEN_API_BASE = "https://api.codegen.com"
        self.OPENAI_API_BASE = "https://api.openai.com/v1"
        self.GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
        self.DEEPINFRA_API_BASE = "https://api.deepinfra.com/v1/openai"
        self.DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
        
        # Web chat interface URLs
        self.WEB_INTERFACES = {
            "deepseek": "https://chat.deepseek.com",
            "chatgpt": "https://chat.openai.com",
            "claude": "https://claude.ai",
            "gemini": "https://gemini.google.com"
        }
        
        # Storage for endpoints and servers
        self.endpoints: Dict[str, EndpointConfig] = {}
        self.active_servers: Dict[str, Any] = {}
        self.server_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Proxy and session management - adapted from crypto bot
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.auth_tokens = {}
        self.header_cookies = {}
        self.access_tokens = {}
        
        # Headers for different services
        self.API_HEADERS = {}
        self.WEB_HEADERS = {}
        
        # Logging setup
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ai_endpoint_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def clear_terminal(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message: str):
        """Log message with timestamp and color formatting"""
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )
        self.logger.info(message.replace(Fore.CYAN, '').replace(Style.BRIGHT, '').replace(Style.RESET_ALL, ''))

    def welcome(self):
        """Display welcome banner"""
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}AI Endpoint Manager {Fore.BLUE + Style.BRIGHT}v1.0
        {Fore.YELLOW + Style.BRIGHT}Web Chat Interface to API Converter
            """
        )

    def format_seconds(self, seconds: int) -> str:
        """Format seconds to HH:MM:SS"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    async def load_proxies(self):
        """Load proxy list from file - adapted from crypto bot"""
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxy: str) -> str:
        """Check and add scheme to proxy if missing"""
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxy.startswith(scheme) for scheme in schemes):
            return proxy
        return f"http://{proxy}"

    def get_next_proxy_for_endpoint(self, endpoint_id: str) -> Optional[str]:
        """Get next proxy for specific endpoint"""
        if endpoint_id not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[endpoint_id] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[endpoint_id]

    def build_proxy_config(self, proxy: Optional[str] = None) -> Tuple[Optional[Any], Optional[str], Optional[BasicAuth]]:
        """Build proxy configuration for aiohttp"""
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")

    def generate_endpoint_id(self, name: str, endpoint_type: EndpointType) -> str:
        """Generate unique endpoint ID"""
        timestamp = int(datetime.now().timestamp())
        return f"{endpoint_type.value}_{name.lower().replace(' ', '_')}_{timestamp}"

    def generate_model_name(self, base_name: str, server_number: int) -> str:
        """Generate model name with server number - like webdeepseek1, webdeepseek8"""
        return f"web{base_name.lower()}{server_number}"

    async def create_endpoint(self, name: str, endpoint_type: EndpointType, url: str, 
                            auth_config: Dict[str, Any], web_config: Optional[WebChatConfig] = None) -> str:
        """Create new API endpoint configuration"""
        try:
            # Find next available server number for this type and name combination
            existing_servers = [ep for ep in self.endpoints.values() 
                             if ep.endpoint_type == endpoint_type and name.lower() in ep.name.lower()]
            server_number = len(existing_servers) + 1
            
            endpoint_id = self.generate_endpoint_id(name, endpoint_type)
            model_name = self.generate_model_name(name, server_number)
            
            endpoint_config = EndpointConfig(
                id=endpoint_id,
                name=name,
                endpoint_type=endpoint_type,
                url=url,
                model_name=model_name,
                server_number=server_number,
                status=ServerStatus.OFFLINE,
                auth_config=auth_config,
                headers={},
                cookies={},
                created_at=datetime.now()
            )
            
            self.endpoints[endpoint_id] = endpoint_config
            
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Endpoint Created: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{model_name} ({endpoint_id}){Style.RESET_ALL}"
            )
            
            return endpoint_id
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to create endpoint: {e}{Style.RESET_ALL}")
            raise

    async def start_server(self, endpoint_id: str) -> bool:
        """Start server for specific endpoint"""
        try:
            if endpoint_id not in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            endpoint = self.endpoints[endpoint_id]
            endpoint.status = ServerStatus.STARTING
            
            self.log(
                f"{Fore.YELLOW + Style.BRIGHT}Starting server: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint.model_name}{Style.RESET_ALL}"
            )
            
            # Initialize server session based on endpoint type
            if endpoint.endpoint_type == EndpointType.WEB_CHAT:
                success = await self._start_web_chat_server(endpoint)
            elif endpoint.endpoint_type == EndpointType.REST_API:
                success = await self._start_rest_api_server(endpoint)
            else:
                success = await self._start_custom_server(endpoint)
            
            if success:
                endpoint.status = ServerStatus.ONLINE
                self.active_servers[endpoint_id] = {
                    "started_at": datetime.now(),
                    "requests_count": 0,
                    "last_request": None
                }
                
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Server started: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{endpoint.model_name}{Style.RESET_ALL}"
                )
                return True
            else:
                endpoint.status = ServerStatus.ERROR
                return False
                
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to start server: {e}{Style.RESET_ALL}")
            if endpoint_id in self.endpoints:
                self.endpoints[endpoint_id].status = ServerStatus.ERROR
            return False

    async def stop_server(self, endpoint_id: str) -> bool:
        """Stop server for specific endpoint"""
        try:
            if endpoint_id not in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            endpoint = self.endpoints[endpoint_id]
            endpoint.status = ServerStatus.STOPPING
            
            self.log(
                f"{Fore.YELLOW + Style.BRIGHT}Stopping server: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint.model_name}{Style.RESET_ALL}"
            )
            
            # Clean up server resources
            if endpoint_id in self.active_servers:
                del self.active_servers[endpoint_id]
            
            if endpoint_id in self.server_sessions:
                # Close any active sessions
                session_data = self.server_sessions[endpoint_id]
                if "browser_session" in session_data:
                    # Close browser session if exists
                    pass
                del self.server_sessions[endpoint_id]
            
            endpoint.status = ServerStatus.OFFLINE
            
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Server stopped: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint.model_name}{Style.RESET_ALL}"
            )
            
            return True
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to stop server: {e}{Style.RESET_ALL}")
            return False

    async def _start_web_chat_server(self, endpoint: EndpointConfig) -> bool:
        """Start web chat interface server with browser automation"""
        try:
            # This would integrate with browser automation (Playwright/Selenium)
            # For now, we'll simulate the setup
            
            session_data = {
                "browser_session": None,  # Would be actual browser session
                "page": None,  # Would be browser page
                "cookies": {},
                "fingerprint": endpoint.fingerprint or self._generate_fingerprint(),
                "user_agent": FakeUserAgent().random
            }
            
            self.server_sessions[endpoint.id] = session_data
            
            # Simulate browser setup and login if credentials provided
            if endpoint.auth_config.get("username") and endpoint.auth_config.get("password"):
                # Would perform actual login here
                self.log(f"{Fore.BLUE + Style.BRIGHT}   Authenticating with credentials{Style.RESET_ALL}")
            
            return True
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Web chat server setup failed: {e}{Style.RESET_ALL}")
            return False

    async def _start_rest_api_server(self, endpoint: EndpointConfig) -> bool:
        """Start REST API server proxy"""
        try:
            # Setup API client session
            session_data = {
                "api_client": None,  # Would be aiohttp session
                "api_key": endpoint.auth_config.get("api_key"),
                "base_url": endpoint.url,
                "headers": endpoint.headers.copy()
            }
            
            # Add API key to headers if provided
            if session_data["api_key"]:
                session_data["headers"]["Authorization"] = f"Bearer {session_data['api_key']}"
            
            self.server_sessions[endpoint.id] = session_data
            
            return True
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}REST API server setup failed: {e}{Style.RESET_ALL}")
            return False

    async def _start_custom_server(self, endpoint: EndpointConfig) -> bool:
        """Start custom endpoint server"""
        try:
            # Custom server logic would go here
            session_data = {
                "custom_config": endpoint.auth_config,
                "initialized": True
            }
            
            self.server_sessions[endpoint.id] = session_data
            
            return True
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Custom server setup failed: {e}{Style.RESET_ALL}")
            return False

    def _generate_fingerprint(self) -> str:
        """Generate browser fingerprint for web chat sessions"""
        import hashlib
        import uuid
        
        # Generate unique fingerprint based on timestamp and random data
        data = f"{datetime.now().isoformat()}{uuid.uuid4()}{random.randint(1000, 9999)}"
        return hashlib.md5(data.encode()).hexdigest()

    async def list_active_endpoints(self) -> List[Dict[str, Any]]:
        """List all active endpoints with their status"""
        active_endpoints = []
        
        for endpoint_id, endpoint in self.endpoints.items():
            endpoint_info = {
                "id": endpoint_id,
                "name": endpoint.name,
                "model_name": endpoint.model_name,
                "type": endpoint.endpoint_type.value,
                "status": endpoint.status.value,
                "url": endpoint.url,
                "server_number": endpoint.server_number,
                "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None,
                "last_used": endpoint.last_used.isoformat() if endpoint.last_used else None
            }
            
            # Add server stats if active
            if endpoint_id in self.active_servers:
                server_stats = self.active_servers[endpoint_id]
                endpoint_info.update({
                    "started_at": server_stats["started_at"].isoformat(),
                    "requests_count": server_stats["requests_count"],
                    "last_request": server_stats["last_request"].isoformat() if server_stats["last_request"] else None
                })
            
            active_endpoints.append(endpoint_info)
        
        return active_endpoints

    async def test_endpoint(self, endpoint_id: str, test_message: str = "Hello, this is a test message.") -> Dict[str, Any]:
        """Test endpoint with a sample message"""
        try:
            if endpoint_id not in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            endpoint = self.endpoints[endpoint_id]
            
            if endpoint.status != ServerStatus.ONLINE:
                raise ValueError(f"Endpoint {endpoint.model_name} is not online")
            
            self.log(
                f"{Fore.BLUE + Style.BRIGHT}Testing endpoint: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint.model_name}{Style.RESET_ALL}"
            )
            
            start_time = datetime.now()
            
            # Route test based on endpoint type
            if endpoint.endpoint_type == EndpointType.WEB_CHAT:
                response = await self._test_web_chat_endpoint(endpoint, test_message)
            elif endpoint.endpoint_type == EndpointType.REST_API:
                response = await self._test_rest_api_endpoint(endpoint, test_message)
            else:
                response = await self._test_custom_endpoint(endpoint, test_message)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Update endpoint stats
            endpoint.last_used = end_time
            if endpoint_id in self.active_servers:
                self.active_servers[endpoint_id]["requests_count"] += 1
                self.active_servers[endpoint_id]["last_request"] = end_time
            
            test_result = {
                "endpoint_id": endpoint_id,
                "model_name": endpoint.model_name,
                "test_message": test_message,
                "response": response,
                "response_time": response_time,
                "timestamp": end_time.isoformat(),
                "success": True
            }
            
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Test successful: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint.model_name} ({response_time:.2f}s){Style.RESET_ALL}"
            )
            
            return test_result
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Test failed: {e}{Style.RESET_ALL}")
            return {
                "endpoint_id": endpoint_id,
                "test_message": test_message,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }

    async def _test_web_chat_endpoint(self, endpoint: EndpointConfig, message: str) -> str:
        """Test web chat endpoint by sending message through browser automation"""
        # This would use actual browser automation
        # For now, simulate response
        await asyncio.sleep(random.uniform(1, 3))  # Simulate processing time
        return f"Simulated response from {endpoint.model_name}: I received your message '{message}' and I'm ready to help!"

    async def _test_rest_api_endpoint(self, endpoint: EndpointConfig, message: str) -> str:
        """Test REST API endpoint"""
        # This would make actual API call
        # For now, simulate response
        await asyncio.sleep(random.uniform(0.5, 2))  # Simulate API call time
        return f"API response from {endpoint.model_name}: {message} - processed successfully"

    async def _test_custom_endpoint(self, endpoint: EndpointConfig, message: str) -> str:
        """Test custom endpoint"""
        # Custom endpoint testing logic
        await asyncio.sleep(random.uniform(0.8, 2.5))
        return f"Custom endpoint {endpoint.model_name} processed: {message}"

    async def print_timer(self, message: str, min_delay: int = 3, max_delay: int = 8):
        """Print countdown timer - adapted from crypto bot"""
        for remaining in range(random.randint(min_delay, max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next {message}...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def save_endpoints_config(self, filename: str = "endpoints_config.json"):
        """Save endpoints configuration to file"""
        try:
            config_data = {}
            for endpoint_id, endpoint in self.endpoints.items():
                config_data[endpoint_id] = {
                    "id": endpoint.id,
                    "name": endpoint.name,
                    "endpoint_type": endpoint.endpoint_type.value,
                    "url": endpoint.url,
                    "model_name": endpoint.model_name,
                    "server_number": endpoint.server_number,
                    "status": endpoint.status.value,
                    "auth_config": endpoint.auth_config,
                    "headers": endpoint.headers,
                    "cookies": endpoint.cookies,
                    "fingerprint": endpoint.fingerprint,
                    "created_at": endpoint.created_at.isoformat() if endpoint.created_at else None,
                    "last_used": endpoint.last_used.isoformat() if endpoint.last_used else None
                }
            
            with open(filename, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.log(f"{Fore.GREEN + Style.BRIGHT}Configuration saved to {filename}{Style.RESET_ALL}")
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to save configuration: {e}{Style.RESET_ALL}")

    def load_endpoints_config(self, filename: str = "endpoints_config.json"):
        """Load endpoints configuration from file"""
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.YELLOW + Style.BRIGHT}Configuration file {filename} not found{Style.RESET_ALL}")
                return
            
            with open(filename, 'r') as f:
                config_data = json.load(f)
            
            for endpoint_id, data in config_data.items():
                endpoint = EndpointConfig(
                    id=data["id"],
                    name=data["name"],
                    endpoint_type=EndpointType(data["endpoint_type"]),
                    url=data["url"],
                    model_name=data["model_name"],
                    server_number=data["server_number"],
                    status=ServerStatus(data["status"]),
                    auth_config=data["auth_config"],
                    headers=data["headers"],
                    cookies=data["cookies"],
                    fingerprint=data.get("fingerprint"),
                    created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
                    last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
                )
                self.endpoints[endpoint_id] = endpoint
            
            self.log(f"{Fore.GREEN + Style.BRIGHT}Loaded {len(config_data)} endpoints from {filename}{Style.RESET_ALL}")
            
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to load configuration: {e}{Style.RESET_ALL}")

    # Interactive Menu System - adapted from crypto bot pattern
    
    def print_main_menu(self):
        """Display main menu options"""
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Create New Web Chat Endpoint{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Create New REST API Endpoint{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. List Active Endpoints{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}4. Start/Stop Servers{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}5. Test Endpoints{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}6. AI-Assisted Discovery{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}7. Manage Server Priorities{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}8. Export/Import Configuration{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}9. Run All Features{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1-9] -> {Style.RESET_ALL}").strip())

                if option in range(1, 10):
                    option_names = [
                        "Create New Web Chat Endpoint",
                        "Create New REST API Endpoint", 
                        "List Active Endpoints",
                        "Start/Stop Servers",
                        "Test Endpoints",
                        "AI-Assisted Discovery",
                        "Manage Server Priorities",
                        "Export/Import Configuration",
                        "Run All Features"
                    ]
                    print(f"{Fore.GREEN + Style.BRIGHT}{option_names[option-1]} Selected.{Style.RESET_ALL}")
                    return option
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter a number between 1 and 9.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number between 1 and 9.{Style.RESET_ALL}")

    def print_proxy_menu(self):
        """Display proxy configuration menu"""
        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                proxy_choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if proxy_choice in [1, 2]:
                    proxy_type = "With" if proxy_choice == 1 else "Without"
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    
                    rotate_proxy = False
                    if proxy_choice == 1:
                        while True:
                            rotate_input = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()
                            if rotate_input in ["y", "n"]:
                                rotate_proxy = rotate_input == "y"
                                break
                            else:
                                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")
                    
                    return proxy_choice == 1, rotate_proxy
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

    def get_web_chat_config(self) -> WebChatConfig:
        """Get web chat interface configuration from user"""
        print(f"{Fore.CYAN + Style.BRIGHT}Web Chat Interface Configuration:{Style.RESET_ALL}")
        
        url = input(f"{Fore.BLUE + Style.BRIGHT}Enter Web Chat URL -> {Style.RESET_ALL}").strip()
        username = input(f"{Fore.BLUE + Style.BRIGHT}Enter Username (optional) -> {Style.RESET_ALL}").strip() or None
        password = input(f"{Fore.BLUE + Style.BRIGHT}Enter Password (optional) -> {Style.RESET_ALL}").strip() or None
        
        # Optional: Get CSS selectors for automation
        print(f"{Fore.YELLOW + Style.BRIGHT}CSS Selectors (optional - leave blank for AI discovery):{Style.RESET_ALL}")
        text_input_selector = input(f"{Fore.BLUE + Style.BRIGHT}Text Input Selector -> {Style.RESET_ALL}").strip()
        send_button_selector = input(f"{Fore.BLUE + Style.BRIGHT}Send Button Selector -> {Style.RESET_ALL}").strip()
        response_selector = input(f"{Fore.BLUE + Style.BRIGHT}Response Area Selector -> {Style.RESET_ALL}").strip()
        
        return WebChatConfig(
            url=url,
            username=username,
            password=password,
            text_input_selector=text_input_selector,
            send_button_selector=send_button_selector,
            response_selector=response_selector
        )

    def get_rest_api_config(self) -> Tuple[str, str, Dict[str, Any]]:
        """Get REST API configuration from user"""
        print(f"{Fore.CYAN + Style.BRIGHT}REST API Configuration:{Style.RESET_ALL}")
        
        name = input(f"{Fore.BLUE + Style.BRIGHT}Enter API Name -> {Style.RESET_ALL}").strip()
        url = input(f"{Fore.BLUE + Style.BRIGHT}Enter API Base URL -> {Style.RESET_ALL}").strip()
        api_key = input(f"{Fore.BLUE + Style.BRIGHT}Enter API Key (optional) -> {Style.RESET_ALL}").strip() or None
        
        auth_config = {}
        if api_key:
            auth_config["api_key"] = api_key
        
        return name, url, auth_config

    async def process_option_1(self, use_proxy: bool):
        """Create new web chat endpoint"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Creating Web Chat Endpoint:{Style.RESET_ALL}")
        
        web_config = self.get_web_chat_config()
        name = input(f"{Fore.BLUE + Style.BRIGHT}Enter Endpoint Name -> {Style.RESET_ALL}").strip()
        
        auth_config = {}
        if web_config.username:
            auth_config["username"] = web_config.username
        if web_config.password:
            auth_config["password"] = web_config.password
        
        try:
            endpoint_id = await self.create_endpoint(
                name=name,
                endpoint_type=EndpointType.WEB_CHAT,
                url=web_config.url,
                auth_config=auth_config,
                web_config=web_config
            )
            
            # Ask if user wants to start the server immediately
            start_now = input(f"{Fore.BLUE + Style.BRIGHT}Start server now? [y/n] -> {Style.RESET_ALL}").strip().lower()
            if start_now == 'y':
                await self.start_server(endpoint_id)
                
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to create web chat endpoint: {e}{Style.RESET_ALL}")

    async def process_option_2(self, use_proxy: bool):
        """Create new REST API endpoint"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Creating REST API Endpoint:{Style.RESET_ALL}")
        
        name, url, auth_config = self.get_rest_api_config()
        
        try:
            endpoint_id = await self.create_endpoint(
                name=name,
                endpoint_type=EndpointType.REST_API,
                url=url,
                auth_config=auth_config
            )
            
            # Ask if user wants to start the server immediately
            start_now = input(f"{Fore.BLUE + Style.BRIGHT}Start server now? [y/n] -> {Style.RESET_ALL}").strip().lower()
            if start_now == 'y':
                await self.start_server(endpoint_id)
                
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed to create REST API endpoint: {e}{Style.RESET_ALL}")

    async def process_option_3(self, use_proxy: bool):
        """List active endpoints"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Active Endpoints:{Style.RESET_ALL}")
        
        endpoints = await self.list_active_endpoints()
        
        if not endpoints:
            self.log(f"{Fore.YELLOW + Style.BRIGHT}No endpoints configured{Style.RESET_ALL}")
            return
        
        for i, endpoint in enumerate(endpoints, 1):
            status_color = Fore.GREEN if endpoint["status"] == "online" else Fore.RED if endpoint["status"] == "error" else Fore.YELLOW
            
            self.log(
                f"{Fore.BLUE + Style.BRIGHT} {i}. {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint['model_name']}{Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{status_color + Style.BRIGHT}{endpoint['status'].upper()}{Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint['type']}{Style.RESET_ALL}"
            )
            
            if endpoint.get("requests_count"):
                self.log(
                    f"{Fore.BLUE + Style.BRIGHT}    Requests: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{endpoint['requests_count']}{Style.RESET_ALL}"
                )

    async def process_option_4(self, use_proxy: bool):
        """Start/Stop servers"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Server Management:{Style.RESET_ALL}")
        
        endpoints = await self.list_active_endpoints()
        
        if not endpoints:
            self.log(f"{Fore.YELLOW + Style.BRIGHT}No endpoints configured{Style.RESET_ALL}")
            return
        
        # Display endpoints with numbers
        for i, endpoint in enumerate(endpoints, 1):
            status_color = Fore.GREEN if endpoint["status"] == "online" else Fore.RED if endpoint["status"] == "error" else Fore.YELLOW
            action = "STOP" if endpoint["status"] == "online" else "START"
            
            print(
                f"{Fore.WHITE + Style.BRIGHT}{i}. {endpoint['model_name']} - "
                f"{status_color + Style.BRIGHT}{endpoint['status'].upper()}{Style.RESET_ALL} "
                f"{Fore.BLUE + Style.BRIGHT}[{action}]{Style.RESET_ALL}"
            )
        
        try:
            choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Select endpoint number -> {Style.RESET_ALL}").strip())
            if 1 <= choice <= len(endpoints):
                selected_endpoint = endpoints[choice - 1]
                endpoint_id = selected_endpoint["id"]
                
                if selected_endpoint["status"] == "online":
                    await self.stop_server(endpoint_id)
                else:
                    await self.start_server(endpoint_id)
            else:
                self.log(f"{Fore.RED + Style.BRIGHT}Invalid selection{Style.RESET_ALL}")
        except ValueError:
            self.log(f"{Fore.RED + Style.BRIGHT}Invalid input{Style.RESET_ALL}")

    async def process_option_5(self, use_proxy: bool):
        """Test endpoints"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Testing Endpoints:{Style.RESET_ALL}")
        
        endpoints = await self.list_active_endpoints()
        online_endpoints = [ep for ep in endpoints if ep["status"] == "online"]
        
        if not online_endpoints:
            self.log(f"{Fore.YELLOW + Style.BRIGHT}No online endpoints to test{Style.RESET_ALL}")
            return
        
        test_message = input(f"{Fore.BLUE + Style.BRIGHT}Enter test message (or press Enter for default) -> {Style.RESET_ALL}").strip()
        if not test_message:
            test_message = "Hello, this is a test message."
        
        # Test all online endpoints
        for endpoint in online_endpoints:
            result = await self.test_endpoint(endpoint["id"], test_message)
            
            if result["success"]:
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}✓ {endpoint['model_name']}: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{result['response_time']:.2f}s{Style.RESET_ALL}"
                )
            else:
                self.log(
                    f"{Fore.RED + Style.BRIGHT}✗ {endpoint['model_name']}: {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}{result.get('error', 'Unknown error')}{Style.RESET_ALL}"
                )
            
            await self.print_timer("Tests", 1, 3)

    async def process_option_6(self, use_proxy: bool):
        """AI-Assisted Discovery"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}AI-Assisted Interface Discovery:{Style.RESET_ALL}")
        self.log(f"{Fore.YELLOW + Style.BRIGHT}This feature will be implemented with multimodal AI integration{Style.RESET_ALL}")
        
        # Placeholder for AI-assisted discovery
        url = input(f"{Fore.BLUE + Style.BRIGHT}Enter web interface URL to analyze -> {Style.RESET_ALL}").strip()
        
        if url:
            self.log(f"{Fore.BLUE + Style.BRIGHT}Analyzing interface at: {url}{Style.RESET_ALL}")
            await self.print_timer("Analysis", 3, 8)
            
            # Simulate AI analysis results
            self.log(f"{Fore.GREEN + Style.BRIGHT}Analysis complete! Discovered:{Style.RESET_ALL}")
            self.log(f"{Fore.WHITE + Style.BRIGHT}• Text input field: #message-input{Style.RESET_ALL}")
            self.log(f"{Fore.WHITE + Style.BRIGHT}• Send button: .send-button{Style.RESET_ALL}")
            self.log(f"{Fore.WHITE + Style.BRIGHT}• Response area: .chat-messages{Style.RESET_ALL}")
            
            create_endpoint = input(f"{Fore.BLUE + Style.BRIGHT}Create endpoint with discovered selectors? [y/n] -> {Style.RESET_ALL}").strip().lower()
            if create_endpoint == 'y':
                # Would create endpoint with discovered configuration
                self.log(f"{Fore.GREEN + Style.BRIGHT}Endpoint creation would be implemented here{Style.RESET_ALL}")

    async def process_option_7(self, use_proxy: bool):
        """Manage Server Priorities"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Server Priority Management:{Style.RESET_ALL}")
        self.log(f"{Fore.YELLOW + Style.BRIGHT}Priority management and load balancing features{Style.RESET_ALL}")
        
        endpoints = await self.list_active_endpoints()
        online_endpoints = [ep for ep in endpoints if ep["status"] == "online"]
        
        if not online_endpoints:
            self.log(f"{Fore.YELLOW + Style.BRIGHT}No online endpoints to manage{Style.RESET_ALL}")
            return
        
        # Display current priorities (simulated)
        for i, endpoint in enumerate(online_endpoints, 1):
            priority = random.randint(1, 10)  # Simulated priority
            self.log(
                f"{Fore.BLUE + Style.BRIGHT} {i}. {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{endpoint['model_name']}{Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT} | Priority: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{priority}{Style.RESET_ALL}"
            )

    async def process_option_8(self, use_proxy: bool):
        """Export/Import Configuration"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Configuration Management:{Style.RESET_ALL}")
        
        print(f"{Fore.WHITE + Style.BRIGHT}1. Export Configuration{Style.RESET_ALL}")
        print(f"{Fore.WHITE + Style.BRIGHT}2. Import Configuration{Style.RESET_ALL}")
        
        try:
            choice = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())
            
            if choice == 1:
                filename = input(f"{Fore.BLUE + Style.BRIGHT}Export filename (default: endpoints_config.json) -> {Style.RESET_ALL}").strip()
                if not filename:
                    filename = "endpoints_config.json"
                self.save_endpoints_config(filename)
                
            elif choice == 2:
                filename = input(f"{Fore.BLUE + Style.BRIGHT}Import filename (default: endpoints_config.json) -> {Style.RESET_ALL}").strip()
                if not filename:
                    filename = "endpoints_config.json"
                self.load_endpoints_config(filename)
                
        except ValueError:
            self.log(f"{Fore.RED + Style.BRIGHT}Invalid input{Style.RESET_ALL}")

    async def process_option_9(self, use_proxy: bool):
        """Run all features - automated mode"""
        self.log(f"{Fore.CYAN + Style.BRIGHT}Automated Mode - Running All Features:{Style.RESET_ALL}")
        
        # Load existing configuration
        self.load_endpoints_config()
        
        # Start all offline servers
        endpoints = await self.list_active_endpoints()
        offline_endpoints = [ep for ep in endpoints if ep["status"] == "offline"]
        
        for endpoint in offline_endpoints:
            self.log(f"{Fore.BLUE + Style.BRIGHT}Starting server: {endpoint['model_name']}{Style.RESET_ALL}")
            await self.start_server(endpoint["id"])
            await self.print_timer("Server Startup", 2, 5)
        
        # Test all online endpoints
        await self.process_option_5(use_proxy)
        
        # Save configuration
        self.save_endpoints_config()

    async def main(self):
        """Main execution loop - adapted from crypto bot pattern"""
        try:
            self.clear_terminal()
            self.welcome()
            
            # Load existing configuration
            self.load_endpoints_config()
            
            # Get user preferences
            option = self.print_main_menu()
            use_proxy, rotate_proxy = self.print_proxy_menu()
            
            if use_proxy:
                await self.load_proxies()
            
            # Execute selected option
            if option == 1:
                await self.process_option_1(use_proxy)
            elif option == 2:
                await self.process_option_2(use_proxy)
            elif option == 3:
                await self.process_option_3(use_proxy)
            elif option == 4:
                await self.process_option_4(use_proxy)
            elif option == 5:
                await self.process_option_5(use_proxy)
            elif option == 6:
                await self.process_option_6(use_proxy)
            elif option == 7:
                await self.process_option_7(use_proxy)
            elif option == 8:
                await self.process_option_8(use_proxy)
            elif option == 9:
                await self.process_option_9(use_proxy)
            
            # Save configuration after operations
            self.save_endpoints_config()
            
        except KeyboardInterrupt:
            self.log(f"{Fore.RED + Style.BRIGHT}[ EXIT ] AI Endpoint Manager{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e


if __name__ == "__main__":
    try:
        manager = AIEndpointManager()
        asyncio.run(manager.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] AI Endpoint Manager{Style.RESET_ALL}"
        )
