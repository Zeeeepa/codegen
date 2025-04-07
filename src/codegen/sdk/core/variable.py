"""Variable symbol representation in the SDK."""

from typing import Optional, Any, Dict, List, Union

from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.expressions.expression import Expression


class Variable(Symbol):
    """Represents a variable in code."""

    def __init__(
        self,
        name: str,
        value: Optional[Expression] = None,
        type_annotation: Optional[Expression] = None,
        is_constant: bool = False,
        **kwargs
    ):
        """Initialize a variable.

        Args:
            name: The name of the variable
            value: The initial value of the variable, if any
            type_annotation: The type annotation of the variable, if any
            is_constant: Whether the variable is a constant (e.g., defined with const or UPPERCASE)
            **kwargs: Additional arguments to pass to the Symbol constructor
        """
        super().__init__(name=name, **kwargs)
        self._value = value
        self._type_annotation = type_annotation
        self._is_constant = is_constant

    @property
    def value(self) -> Optional[Expression]:
        """Get the value of the variable."""
        return self._value

    @value.setter
    def value(self, value: Optional[Expression]) -> None:
        """Set the value of the variable."""
        self._value = value

    @property
    def type(self) -> Optional[Expression]:
        """Get the type annotation of the variable."""
        return self._type_annotation

    @type.setter
    def type(self, type_annotation: Optional[Expression]) -> None:
        """Set the type annotation of the variable."""
        self._type_annotation = type_annotation

    @property
    def is_constant(self) -> bool:
        """Check if the variable is a constant."""
        return self._is_constant

    @is_constant.setter
    def is_constant(self, is_constant: bool) -> None:
        """Set whether the variable is a constant."""
        self._is_constant = is_constant

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            "value": self._value.to_dict() if self._value else None,
            "type": self._type_annotation.to_dict() if self._type_annotation else None,
            "is_constant": self._is_constant,
        })
        return result

    def references(self) -> List[Dict[str, Any]]:
        """Get references to this variable in the codebase."""
        # This would typically search the codebase for references to this variable
        # For now, return an empty list as a placeholder
        return []

    def __str__(self) -> str:
        """String representation of the variable."""
        parts = [self.name]
        if self._type_annotation:
            parts.append(f": {self._type_annotation}")
        if self._value:
            parts.append(f" = {self._value}")
        return " ".join(parts)