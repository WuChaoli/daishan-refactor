#!/usr/bin/env python3
"""
Class extractor for enhanced AST analysis.

Extracts comprehensive class information including decorators,
methods, inheritance chains, and nested classes.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import ast

from .base_extractor import BaseExtractor
from .function_extractor import FunctionExtractor, FunctionInfo


@dataclass
class ClassInfo:
    """Comprehensive class information"""
    name: str
    decorators: List[str]
    bases: List[str]  # Base class names
    methods: List[FunctionInfo]
    class_variables: List[Dict[str, Any]]
    nested_classes: List['ClassInfo']
    docstring: Optional[str]
    line_range: Dict[str, int]
    is_abstract: bool
    is_dataclass: bool
    is_exception: bool


class ClassExtractor(BaseExtractor):
    """Extract comprehensive class information"""

    def extract(self) -> List[ClassInfo]:
        """
        Extract all classes from the file.

        Returns:
            List of ClassInfo objects
        """
        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Only extract top-level classes (not nested ones here)
                if self._is_top_level_class(node):
                    class_info = self._extract_class(node)
                    classes.append(class_info)
        return classes

    def _is_top_level_class(self, node: ast.ClassDef) -> bool:
        """Check if class is at module level (not nested)"""
        for parent in ast.walk(self.tree):
            if isinstance(parent, ast.ClassDef):
                if parent != node and node in ast.walk(parent):
                    return False
            elif isinstance(parent, ast.FunctionDef):
                if node in ast.walk(parent):
                    return False
        return True

    def _extract_class(self, node: ast.ClassDef) -> ClassInfo:
        """
        Extract information from a ClassDef node.

        Args:
            node: AST ClassDef node

        Returns:
            ClassInfo object
        """
        return ClassInfo(
            name=node.name,
            decorators=self._extract_decorators(node.decorator_list),
            bases=self._extract_bases(node.bases),
            methods=self._extract_methods(node),
            class_variables=self._extract_class_vars(node),
            nested_classes=self._extract_nested_classes(node),
            docstring=self.extract_docstring(node),
            line_range=self.get_line_range(node),
            is_abstract=self._is_abstract(node),
            is_dataclass=self._is_dataclass(node),
            is_exception=self._is_exception(node)
        )

    def _extract_decorators(self, decorators: List[ast.expr]) -> List[str]:
        """
        Extract decorator expressions.

        Args:
            decorators: List of decorator nodes

        Returns:
            List of decorator strings
        """
        return [ast.unparse(dec) for dec in decorators]

    def _extract_bases(self, bases: List[ast.expr]) -> List[str]:
        """
        Extract base class names.

        Args:
            bases: List of base class nodes

        Returns:
            List of base class names
        """
        return [ast.unparse(base) for base in bases]

    def _extract_methods(self, class_node: ast.ClassDef) -> List[FunctionInfo]:
        """
        Extract all methods from class.

        Args:
            class_node: AST ClassDef node

        Returns:
            List of FunctionInfo objects
        """
        extractor = FunctionExtractor(self.file_path, self.root_path)
        methods = []

        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = extractor._extract_function(node, is_method=True)
                methods.append(method_info)

        return methods

    def _extract_class_vars(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        """
        Extract class-level variables.

        Args:
            class_node: AST ClassDef node

        Returns:
            List of variable information dictionaries
        """
        variables = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                # Typed assignment: x: int = 5
                if isinstance(node.target, ast.Name):
                    variables.append({
                        'name': node.target.id,
                        'type_annotation': ast.unparse(node.annotation) if node.annotation else None,
                        'value': ast.unparse(node.value) if node.value else None,
                        'line_number': node.lineno
                    })

            elif isinstance(node, ast.Assign):
                # Regular assignment: x = 5
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({
                            'name': target.id,
                            'type_annotation': None,
                            'value': ast.unparse(node.value),
                            'line_number': node.lineno
                        })

        return variables

    def _extract_nested_classes(self, class_node: ast.ClassDef) -> List['ClassInfo']:
        """
        Extract nested classes.

        Args:
            class_node: AST ClassDef node

        Returns:
            List of nested ClassInfo objects
        """
        nested = []
        for node in class_node.body:
            if isinstance(node, ast.ClassDef):
                nested.append(self._extract_class(node))
        return nested

    def _is_abstract(self, node: ast.ClassDef) -> bool:
        """
        Check if class is abstract.

        Args:
            node: AST ClassDef node

        Returns:
            True if class has abstract methods or inherits from ABC
        """
        # Check for ABC in base classes
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'ABC':
                return True
            if isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Name) and base.value.id == 'abc' and base.attr == 'ABC':
                    return True

        # Check for abstractmethod in any method
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in child.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id == 'abstractmethod':
                        return True
                    if isinstance(dec, ast.Attribute):
                        if isinstance(dec.value, ast.Name) and dec.value.id == 'abc' and dec.attr == 'abstractmethod':
                            return True

        return False

    def _is_dataclass(self, node: ast.ClassDef) -> bool:
        """
        Check if class is a dataclass.

        Args:
            node: AST ClassDef node

        Returns:
            True if class has @dataclass decorator
        """
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == 'dataclass':
                return True
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == 'dataclass':
                return True
        return False

    def _is_exception(self, node: ast.ClassDef) -> bool:
        """
        Check if class inherits from Exception.

        Args:
            node: AST ClassDef node

        Returns:
            True if class inherits from Exception or BaseException
        """
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ['Exception', 'BaseException']:
                return True
        return False
