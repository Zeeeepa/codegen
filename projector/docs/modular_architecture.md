# Projector: Modular Architecture Proposal

## Overview

This document outlines a comprehensive plan to refactor the Projector application into a more modular, maintainable, and extensible architecture. The proposed changes aim to reduce coupling between components, improve error handling, enhance configurability, and establish clear separation of concerns.

## Current Architecture Issues

1. **Tight Coupling**: Components have direct dependencies on implementation details
2. **Limited Error Handling**: Basic error handling without robust recovery mechanisms
3. **Hardcoded Configuration**: Many settings are hardcoded rather than configurable
4. **Monolithic Components**: Some components handle multiple responsibilities
5. **Simple Data Persistence**: Basic JSON storage without optimization
6. **Synchronous Operations**: Many operations that could be asynchronous are blocking

## Proposed Modular Architecture

### 1. Core Module Structure

```
projector/
├── api/                  # API layer
│   ├── endpoints/        # API endpoints
│   ├── schemas/          # API data schemas
│   └── middleware/       # API middleware
├── core/                 # Core domain logic
│   ├── models/           # Domain models
│   ├── services/         # Business logic services
│   ├── interfaces/       # Abstract interfaces
│   └── exceptions/       # Custom exceptions
├── infrastructure/       # External system integrations
│   ├── database/         # Database adapters
│   ├── github/           # GitHub integration
│   ├── slack/            # Slack integration
│   ├── ai/               # AI service integrations
│   └── config/           # Configuration management
├── application/          # Application services
│   ├── commands/         # Command handlers
│   ├── queries/          # Query handlers
│   ├── events/           # Event handlers
│   └── workflows/        # Complex workflows
├── ui/                   # User interfaces
│   ├── web/              # Web UI (Streamlit)
│   ├── cli/              # Command-line interface
│   └── components/       # Shared UI components
├── utils/                # Utility functions
│   ├── logging/          # Logging utilities
│   ├── concurrency/      # Concurrency utilities
│   ├── validation/       # Validation utilities
│   └── serialization/    # Serialization utilities
└── tests/                # Test suite
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── fixtures/         # Test fixtures
```

### 2. Dependency Inversion

Implement dependency inversion to reduce coupling:

1. Define interfaces in the `core/interfaces` module
2. Implement concrete classes in appropriate modules
3. Use dependency injection to provide implementations

Example:

```python
# core/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models.project import Project

class ProjectRepository(ABC):
    @abstractmethod
    def save(self, project: Project) -> bool:
        pass
    
    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Project]:
        pass
    
    @abstractmethod
    def list_all(self) -> List[Project]:
        pass
    
    @abstractmethod
    def delete(self, project_id: str) -> bool:
        pass
```

```python
# infrastructure/database/json_repository.py
import json
import os
from typing import List, Optional
from core.interfaces.repository import ProjectRepository
from core.models.project import Project

class JsonProjectRepository(ProjectRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        # Implementation details...
    
    def save(self, project: Project) -> bool:
        # Implementation...
        pass
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        # Implementation...
        pass
    
    def list_all(self) -> List[Project]:
        # Implementation...
        pass
    
    def delete(self, project_id: str) -> bool:
        # Implementation...
        pass
```

### 3. Service Layer

Create service classes that encapsulate business logic:

```python
# core/services/project_service.py
from typing import List, Optional
from core.interfaces.repository import ProjectRepository
from core.models.project import Project

class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    def create_project(self, name: str, git_url: str, slack_channel: Optional[str] = None) -> str:
        project = Project(None, name, git_url, slack_channel)
        success = self.project_repository.save(project)
        if not success:
            raise Exception("Failed to save project")
        return project.id
    
    def get_project(self, project_id: str) -> Optional[Project]:
        return self.project_repository.get_by_id(project_id)
    
    def list_projects(self) -> List[Project]:
        return self.project_repository.list_all()
    
    def delete_project(self, project_id: str) -> bool:
        return self.project_repository.delete(project_id)
    
    def update_project_plan(self, project_id: str, plan: dict) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        
        project.implementation_plan = plan
        return self.project_repository.save(project)
```

### 4. Configuration Management

Create a centralized configuration system:

```python
# infrastructure/config/config.py
import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        load_dotenv()
        self._config = {
            "slack": {
                "token": os.getenv("SLACK_USER_TOKEN"),
                "default_channel": os.getenv("SLACK_DEFAULT_CHANNEL", "general")
            },
            "github": {
                "token": os.getenv("GITHUB_TOKEN"),
                "username": os.getenv("GITHUB_USERNAME"),
                "default_repo": os.getenv("GITHUB_DEFAULT_REPO")
            },
            "database": {
                "file_path": os.getenv("DB_FILE_PATH", "projects_db.json")
            },
            "app": {
                "max_threads": int(os.getenv("MAX_THREADS", "10")),
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                "port": int(os.getenv("PORT", "8501"))
            }
        }
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        return self._config.get(section, {})
```

### 5. Error Handling

Implement a robust error handling system:

```python
# core/exceptions/exceptions.py
class ProjectorException(Exception):
    """Base exception for all Projector exceptions."""
    pass

class ConfigurationError(ProjectorException):
    """Raised when there's an issue with configuration."""
    pass

class RepositoryError(ProjectorException):
    """Raised when there's an issue with data persistence."""
    pass

class IntegrationError(ProjectorException):
    """Base class for integration errors."""
    pass

class GitHubError(IntegrationError):
    """Raised when there's an issue with GitHub integration."""
    pass

class SlackError(IntegrationError):
    """Raised when there's an issue with Slack integration."""
    pass

class AIServiceError(IntegrationError):
    """Raised when there's an issue with AI service integration."""
    pass

# utils/error_handling.py
import logging
import functools
from typing import Callable, TypeVar, Any
from core.exceptions.exceptions import ProjectorException

T = TypeVar('T')

def handle_exceptions(logger: logging.Logger) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to handle exceptions and log them."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except ProjectorException as e:
                logger.error(f"{type(e).__name__}: {str(e)}")
                raise
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                raise ProjectorException(f"An unexpected error occurred: {str(e)}") from e
        return wrapper
    return decorator
```

### 6. Asynchronous Operations

Implement asynchronous operations for non-blocking I/O:

```python
# utils/concurrency/async_executor.py
import asyncio
import concurrent.futures
from typing import Callable, TypeVar, Any, List, Awaitable

T = TypeVar('T')

class AsyncExecutor:
    def __init__(self, max_workers: int = 10):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.get_event_loop()
    
    async def run_in_executor(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Run a synchronous function in a thread pool."""
        return await self.loop.run_in_executor(
            self.executor,
            lambda: func(*args, **kwargs)
        )
    
    async def gather(self, tasks: List[Awaitable[T]]) -> List[T]:
        """Run multiple tasks concurrently and gather results."""
        return await asyncio.gather(*tasks)
    
    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown()
```

### 7. Dependency Injection Container

Implement a dependency injection container for managing dependencies:

```python
# infrastructure/di/container.py
from typing import Dict, Any, Type, TypeVar, cast

T = TypeVar('T')

class Container:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Any] = {}
    
    def register(self, interface: Type[T], implementation: Type[T], *args: Any, **kwargs: Any) -> None:
        """Register a service implementation."""
        self._services[interface.__name__] = (implementation, args, kwargs)
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a pre-created instance."""
        self._services[interface.__name__] = instance
    
    def register_factory(self, name: str, factory: Any) -> None:
        """Register a factory function."""
        self._factories[name] = factory
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service implementation."""
        if interface.__name__ in self._services:
            service = self._services[interface.__name__]
            if isinstance(service, tuple):
                implementation, args, kwargs = service
                instance = implementation(*args, **kwargs)
                self._services[interface.__name__] = instance
                return cast(T, instance)
            return cast(T, service)
        raise KeyError(f"No implementation registered for {interface.__name__}")
    
    def create(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Create an instance using a factory."""
        if name in self._factories:
            factory = self._factories[name]
            return factory(*args, **kwargs)
        raise KeyError(f"No factory registered for {name}")
```

### 8. Application Bootstrap

Create a bootstrap module to initialize the application:

```python
# application/bootstrap.py
from infrastructure.config.config import Config
from infrastructure.di.container import Container
from core.interfaces.repository import ProjectRepository
from infrastructure.database.json_repository import JsonProjectRepository
from core.services.project_service import ProjectService
from infrastructure.github.github_client import GitHubClient
from infrastructure.slack.slack_client import SlackClient
from utils.concurrency.async_executor import AsyncExecutor

def bootstrap() -> Container:
    """Bootstrap the application and return the DI container."""
    # Create configuration
    config = Config()
    
    # Create container
    container = Container()
    
    # Register configuration
    container.register_instance(Config, config)
    
    # Register database
    db_file_path = config.get("database", "file_path", "projects_db.json")
    container.register(ProjectRepository, JsonProjectRepository, db_file_path)
    
    # Register services
    container.register_factory("project_service", lambda: ProjectService(
        container.resolve(ProjectRepository)
    ))
    
    # Register integrations
    github_token = config.get("github", "token")
    github_username = config.get("github", "username")
    github_default_repo = config.get("github", "default_repo")
    container.register_factory("github_client", lambda: GitHubClient(
        github_token, github_username, github_default_repo
    ))
    
    slack_token = config.get("slack", "token")
    slack_default_channel = config.get("slack", "default_channel")
    container.register_factory("slack_client", lambda: SlackClient(
        slack_token, slack_default_channel
    ))
    
    # Register utilities
    max_threads = config.get("app", "max_threads", 10)
    container.register_factory("async_executor", lambda: AsyncExecutor(max_threads))
    
    return container
```

### 9. Main Application Entry Point

Refactor the main entry point to use the new modular architecture:

```python
# main.py
import argparse
import logging
import signal
import sys
import threading
import time
from application.bootstrap import bootstrap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("projector/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global flag to control the main loop
running = True

def signal_handler(sig, frame):
    """Handle termination signals."""
    global running
    logger.info("Received termination signal. Shutting down...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Projector: Project Management Tool")
    parser.add_argument("--backend-only", action="store_true", help="Run only the backend service")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the frontend (Streamlit)")
    parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit app")
    args = parser.parse_args()
    
    try:
        # Bootstrap the application
        container = bootstrap()
        
        # Get configuration
        config = container.resolve(Config)
        
        # Start components based on arguments
        if args.backend_only:
            # Run only the backend service
            from application.backend_service import run_backend_service
            run_backend_service(container)
        elif args.frontend_only:
            # Run only the Streamlit app
            from ui.web.streamlit_app import run_streamlit
            run_streamlit(container, port=args.port)
        else:
            # Run both backend and frontend
            from application.backend_service import run_backend_service
            from ui.web.streamlit_app import run_streamlit
            
            # Start Streamlit in a separate thread
            streamlit_thread = threading.Thread(
                target=run_streamlit,
                args=(container, args.port)
            )
            streamlit_thread.daemon = True
            streamlit_thread.start()
            
            # Run the backend service in the main thread
            run_backend_service(container)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
    finally:
        logger.info("Application shutdown complete.")

if __name__ == "__main__":
    main()
```

## Migration Strategy

To migrate from the current architecture to the proposed modular architecture, we recommend the following phased approach:

### Phase 1: Refactor Core Domain Models

1. Create the new directory structure
2. Move and refactor the Project model to core/models
3. Define interfaces for repositories and services
4. Implement the JSON repository as an adapter

### Phase 2: Implement Service Layer

1. Create service classes for project management
2. Refactor existing manager classes to use the service layer
3. Implement dependency injection

### Phase 3: Refactor Integrations

1. Create adapter classes for GitHub and Slack
2. Implement error handling for external integrations
3. Add asynchronous operations for I/O-bound tasks

### Phase 4: Enhance Frontend

1. Refactor Streamlit UI to use the new service layer
2. Implement improved error handling and user feedback
3. Add configuration options for UI customization

### Phase 5: Add Testing

1. Implement unit tests for core domain logic
2. Add integration tests for external integrations
3. Create end-to-end tests for critical workflows

## Benefits of the New Architecture

1. **Reduced Coupling**: Components depend on interfaces, not implementations
2. **Improved Testability**: Clear separation of concerns makes testing easier
3. **Enhanced Maintainability**: Modular structure makes code easier to understand and modify
4. **Better Error Handling**: Comprehensive error handling and recovery
5. **Increased Flexibility**: Easy to swap implementations of interfaces
6. **Improved Performance**: Asynchronous operations for I/O-bound tasks
7. **Better Configuration**: Centralized configuration management

## Conclusion

The proposed modular architecture addresses the current limitations of the Projector application while providing a solid foundation for future enhancements. By implementing this architecture, the application will be more maintainable, extensible, and robust.

The migration strategy allows for incremental adoption of the new architecture, minimizing disruption while gradually improving the codebase. Each phase delivers tangible benefits, making the refactoring effort worthwhile even before completion.