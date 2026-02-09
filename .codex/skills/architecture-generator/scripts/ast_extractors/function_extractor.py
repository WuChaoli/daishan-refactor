#!/usr/bin/env python3
"""
Function extractor for enhanced AST analysis.

Extracts comprehensive function information including parameters,
decorators, generators, and async patterns.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import ast

from .base_extractor import BaseExtractor


@dataclass
class ParameterInfo:
    """Function parameter information"""
    name: str
    type_annotation: Optional[str]
    default_value: Optional[str]
    is_positional_only: bool
    is_keyword_only: bool
    is_var_positional: bool  # *args
    is_var_keyword: bool     # **kwargs


@dataclass
class FunctionInfo:
    """Comprehensive function information"""
    name: str
    decorators: List[str]
    parameters: List[ParameterInfo]
    return_type: Optional[str]
    docstring: Optional[str]
    line_range: Dict[str, int]
    is_async: bool
    is_method: bool
    is_static_method: bool
    is_class_method: bool
    is_property: bool
    is_generator: bool
    is_async_generator: bool
    nested_functions: List['FunctionInfo']
    await_count: int


class FunctionExtractor(BaseExtractor):
    """Extract comprehensive function information"""

    def extract(self) -> List[FunctionInfo]:
        """
        Extract all top-level functions from file.

        Returns:
            List of FunctionInfo objects
        """
        functions = []
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._extract_function(node, is_method=False)
                functions.append(func_info)
        return functions

    def _extract_function(self, node: ast.FunctionDef, is_method: bool = False) -> FunctionInfo:
        """
        Extract information from a FunctionDef or AsyncFunctionDef node.

        Args:
            node: AST function node
            is_method: Whether this is a class method

        Returns:
            FunctionInfo object
        """
        is_async = isinstance(node, ast.AsyncFunctionDef)

        return FunctionInfo(
            name=node.name,
            decorators=self._extract_decorators(node.decorator_list),
            parameters=self._extract_parameters(node.args),
            return_type=ast.unparse(node.returns) if node.returns else None,
            docstring=self.extract_docstring(node),
            line_range=self.get_line_range(node),
            is_async=is_async,
            is_method=is_method,
            is_static_method=self._is_static_method(node),
            is_class_method=self._is_class_method(node),
            is_property=self._is_property(node),
            is_generator=self._is_generator(node),
            is_async_generator=self._is_async_generator(node),
            nested_functions=self._extract_nested_functions(node),
            await_count=self._count_await_expressions(node)
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

    def _extract_parameters(self, args: ast.arguments) -> List[ParameterInfo]:
        """
        Extract function parameters.

        Args:
            args: AST arguments node

        Returns:
            List of ParameterInfo objects
        """
        parameters = []

        # Positional-only parameters (Python 3.8+)
        if hasattr(args, 'posonlyargs'):
            for arg in args.posonlyargs:
                parameters.append(ParameterInfo(
                    name=arg.arg,
                    type_annotation=ast.unparse(arg.annotation) if arg.annotation else None,
                    default_value=None,
                    is_positional_only=True,
                    is_keyword_only=False,
                    is_var_positional=False,
                    is_var_keyword=False
                ))

        # Regular positional arguments
        for i, arg in enumerate(args.args):
            default = None
            if i >= len(args.args) - len(args.defaults):
                default_idx = i - (len(args.args) - len(args.defaults))
                default = ast.unparse(args.defaults[default_idx])

            parameters.append(ParameterInfo(
                name=arg.arg,
                type_annotation=ast.unparse(arg.annotation) if arg.annotation else None,
                default_value=default,
                is_positional_only=False,
                is_keyword_only=False,
                is_var_positional=False,
                is_var_keyword=False
            ))

        # *args
        if args.vararg:
            parameters.append(ParameterInfo(
                name=args.vararg.arg,
                type_annotation=ast.unparse(args.vararg.annotation) if args.vararg.annotation else None,
                default_value=None,
                is_positional_only=False,
                is_keyword_only=False,
                is_var_positional=True,
                is_var_keyword=False
            ))

        # Keyword-only arguments
        for i, arg in enumerate(args.kwonlyargs):
            default = None
            if i < len(args.kw_defaults) and args.kw_defaults[i]:
                default = ast.unparse(args.kw_defaults[i])

            parameters.append(ParameterInfo(
                name=arg.arg,
                type_annotation=ast.unparse(arg.annotation) if arg.annotation else None,
                default_value=default,
                is_positional_only=False,
                is_keyword_only=True,
                is_var_positional=False,
                is_var_keyword=False
            ))

        # **kwargs
        if args.kwarg:
            parameters.append(ParameterInfo(
                name=args.kwarg.arg,
                type_annotation=ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None,
                default_value=None,
                is_positional_only=False,
                is_keyword_only=False,
                is_var_positional=False,
                is_var_keyword=True
            ))

        return parameters

    def _is_static_method(self, node: ast.FunctionDef) -> bool:
        """Check if function is a static method"""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == 'staticmethod':
                return True
        return False

    def _is_class_method(self, node: ast.FunctionDef) -> bool:
        """Check if function is a class method"""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == 'classmethod':
                return True
        return False

    def _is_property(self, node: ast.FunctionDef) -> bool:
        """Check if function is a property"""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in ['property', 'cached_property']:
                return True
        return False

    def _is_generator(self, node: ast.FunctionDef) -> bool:
        """Check if function is a generator (contains yield)"""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _is_async_generator(self, node: ast.FunctionDef) -> bool:
        """Check if function is an async generator (contains async yield)"""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        if not is_async:
            return False

        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _extract_nested_functions(self, node: ast.FunctionDef) -> List['FunctionInfo']:
        """Extract nested functions"""
        nested = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested.append(self._extract_function(child))
        return nested

    def _count_await_expressions(self, node: ast.FunctionDef) -> int:
        """Count number of await expressions in function"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Await):
                count += 1
        return count
