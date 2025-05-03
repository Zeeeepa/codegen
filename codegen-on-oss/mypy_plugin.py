"""
Custom mypy plugin for SQLAlchemy models.

This plugin helps mypy understand SQLAlchemy models.
"""

from typing import Callable, Optional, Dict, Any, Type, List, Set, Tuple
from mypy.plugin import Plugin, ClassDefContext
from mypy.nodes import TypeInfo, ClassDef, Block, SymbolTable, SymbolTableNode, MDEF
from mypy.types import Instance, Type as MypyType

class SQLAlchemyPlugin(Plugin):
    """Plugin for SQLAlchemy ORM models."""
    
    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        """Get class decorator hook."""
        if fullname == 'sqlalchemy.ext.declarative.declarative_base':
            return sqlalchemy_declarative_base_hook
        return None

def sqlalchemy_declarative_base_hook(ctx: ClassDefContext) -> None:
    """Process declarative_base() call."""
    # This is a no-op, just to make mypy happy
    pass

def plugin(version: str) -> Type[Plugin]:
    """Return the plugin class."""
    return SQLAlchemyPlugin

