#!/usr/bin/env python3
"""
Variable extractor for enhanced AST analysis.

Extracts global and class-level variables with type annotations.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import ast

from .base_extractor import BaseExtractor


@dataclass
class VariableInfo:
    """Variable information"""
    name: str
    type_annotation: Optional[str]
    value: Optional[str]  # Simplified representation
    is_class_variable: bool
    is_global: bool
    line_number: int


class VariableExtractor(BaseExtractor):
    """Extract variable information"""

    def extract(self) -> Dict[str, List[VariableInfo]]:
        """
        Extract all variables.

        Returns:
            Dictionary with 'global' and 'class' keys
        """
        return {
            'global': self._extract_global_variables(),
            'class': self._extract_class_variables_from_file()
        }

    def extract_class_variables(self, class_node: ast.ClassDef) -> List[VariableInfo]:
        """
        Extract variables from a class node.

        Args:
            class_node: AST ClassDef node

        Returns:
            List of VariableInfo objects
        """
        variables = []

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                # Typed assignment: x: int = 5
                if isinstance(node.target, ast.Name):
                    variables.append(VariableInfo(
                        name=node.target.id,
                        type_annotation=ast.unparse(node.annotation) if node.annotation else None,
                        value=ast.unparse(node.value) if node.value else None,
                        is_class_variable=True,
                        is_global=False,
                        line_number=node.lineno
                    ))

            elif isinstance(node, ast.Assign):
                # Regular assignment: x = 5
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(VariableInfo(
                            name=target.id,
                            type_annotation=None,
                            value=ast.unparse(node.value),
                            is_class_variable=True,
                            is_global=False,
                            line_number=node.lineno
                        ))

        return variables

    def _extract_global_variables(self) -> List[VariableInfo]:
        """
        Extract module-level variables.

        Returns:
            List of VariableInfo objects
        """
        variables = []

        for node in self.tree.body:
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    variables.append(VariableInfo(
                        name=node.target.id,
                        type_annotation=ast.unparse(node.annotation) if node.annotation else None,
                        value=ast.unparse(node.value) if node.value else None,
                        is_class_variable=False,
                        is_global=True,
                        line_number=node.lineno
                    ))

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(VariableInfo(
                            name=target.id,
                            type_annotation=None,
                            value=ast.unparse(node.value),
                            is_class_variable=False,
                            is_global=True,
                            line_number=node.lineno
                        ))

        return variables

    def _extract_class_variables_from_file(self) -> List[VariableInfo]:
        """
        Extract all class variables in file.

        Returns:
            List of VariableInfo objects
        """
        variables = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_vars = self.extract_class_variables(node)
                variables.extend(class_vars)

        return variables
