"""
Class model for MCP.

This module defines the Class model class that represents a class in code.
"""

from typing import Any, Dict, List, Optional

from .symbol import Symbol


class Class(Symbol):
    """Model representing a class in code."""

    def __init__(
        self,
        name: str,
        methods: Optional[List[Dict[str, Any]]] = None,
        properties: Optional[List[Dict[str, Any]]] = None,
        attributes: Optional[List[Dict[str, Any]]] = None,
        is_abstract: bool = False,
        parent_class_names: Optional[List[str]] = None,
        decorators: Optional[List[str]] = None,
        **kwargs,
    ):
        """Initialize a Class.

        Args:
            name (str): Name of the class.
            methods (Optional[List[Dict[str, Any]]], optional): Class methods.
                Defaults to None.
            properties (Optional[List[Dict[str, Any]]], optional): Class properties.
                Defaults to None.
            attributes (Optional[List[Dict[str, Any]]], optional): Class attributes.
                Defaults to None.
            is_abstract (bool, optional): Whether the class is abstract.
                Defaults to False.
            parent_class_names (Optional[List[str]], optional): Parent class names.
                Defaults to None.
            decorators (Optional[List[str]], optional): Class decorators.
                Defaults to None.
        """
        super().__init__(
            name=name,
            symbol_type="class",
            methods=methods or [],
            properties=properties or [],
            attributes=attributes or [],
            is_abstract=is_abstract,
            parent_class_names=parent_class_names or [],
            decorators=decorators or [],
            **kwargs,
        )

    @property
    def methods(self) -> List[Dict[str, Any]]:
        """Get the methods of the class.

        Returns:
            List[Dict[str, Any]]: List of methods.
        """
        return self._methods

    @methods.setter
    def methods(self, value: List[Dict[str, Any]]) -> None:
        """Set the methods of the class.

        Args:
            value (List[Dict[str, Any]]): New methods.
        """
        self._methods = value

    @property
    def properties(self) -> List[Dict[str, Any]]:
        """Get the properties of the class.

        Returns:
            List[Dict[str, Any]]: List of properties.
        """
        return self._properties

    @properties.setter
    def properties(self, value: List[Dict[str, Any]]) -> None:
        """Set the properties of the class.

        Args:
            value (List[Dict[str, Any]]): New properties.
        """
        self._properties = value

    @property
    def attributes(self) -> List[Dict[str, Any]]:
        """Get the attributes of the class.

        Returns:
            List[Dict[str, Any]]: List of attributes.
        """
        return self._attributes

    @attributes.setter
    def attributes(self, value: List[Dict[str, Any]]) -> None:
        """Set the attributes of the class.

        Args:
            value (List[Dict[str, Any]]): New attributes.
        """
        self._attributes = value

    @property
    def is_abstract(self) -> bool:
        """Check if the class is abstract.

        Returns:
            bool: True if abstract, False otherwise.
        """
        return self._is_abstract

    @is_abstract.setter
    def is_abstract(self, value: bool) -> None:
        """Set whether the class is abstract.

        Args:
            value (bool): New abstract status.
        """
        self._is_abstract = value

    @property
    def parent_class_names(self) -> List[str]:
        """Get the parent class names.

        Returns:
            List[str]: List of parent class names.
        """
        return self._parent_class_names

    @parent_class_names.setter
    def parent_class_names(self, value: List[str]) -> None:
        """Set the parent class names.

        Args:
            value (List[str]): New parent class names.
        """
        self._parent_class_names = value

    @property
    def decorators(self) -> List[str]:
        """Get the decorators of the class.

        Returns:
            List[str]: List of decorators.
        """
        return self._decorators

    @decorators.setter
    def decorators(self, value: List[str]) -> None:
        """Set the decorators of the class.

        Args:
            value (List[str]): New decorators.
        """
        self._decorators = value

    def is_subclass_of(self, parent: str) -> bool:
        """Check if the class is a subclass of a specific parent.

        Args:
            parent (str): Parent class name.

        Returns:
            bool: True if subclass, False otherwise.
        """
        return parent in self.parent_class_names

    def add_method(self, method: Dict[str, Any]) -> bool:
        """Add a method to the class.

        Args:
            method (Dict[str, Any]): Method to add.

        Returns:
            bool: True if successful, False otherwise.
        """
        method_name = method.get("name")
        if method_name and not any(m.get("name") == method_name for m in self.methods):
            self.methods.append(method)
            return True
        return False

    def remove_method(self, method_name: str) -> bool:
        """Remove a method from the class.

        Args:
            method_name (str): Name of the method to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        initial_length = len(self.methods)
        self.methods = [m for m in self.methods if m.get("name") != method_name]
        return len(self.methods) < initial_length

    def add_attribute(
        self, name: str, type_str: Optional[str] = None, value: Optional[str] = None
    ) -> bool:
        """Add an attribute to the class.

        Args:
            name (str): Attribute name.
            type_str (Optional[str], optional): Attribute type.
                Defaults to None.
            value (Optional[str], optional): Attribute value.
                Defaults to None.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not any(a.get("name") == name for a in self.attributes):
            attr = {"name": name}
            if type_str:
                attr["type"] = type_str
            if value:
                attr["value"] = value
            self.attributes.append(attr)
            return True
        return False

    def remove_attribute(self, name: str) -> bool:
        """Remove an attribute from the class.

        Args:
            name (str): Name of the attribute to remove.

        Returns:
            bool: True if successful, False otherwise.
        """
        initial_length = len(self.attributes)
        self.attributes = [a for a in self.attributes if a.get("name") != name]
        return len(self.attributes) < initial_length

    def convert_to_protocol(self) -> bool:
        """Convert the class to a protocol.

        Returns:
            bool: True if successful, False otherwise.
        """
        # This would be implemented to interact with the actual codebase
        # For now, set is_abstract to True and return True as a placeholder
        self.is_abstract = True
        return True
