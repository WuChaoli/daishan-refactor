#!/usr/bin/env python3
"""
Pattern extractor for enhanced AST analysis.

Extracts advanced Python patterns including exception handlers,
context managers, and lambda functions.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import ast

from .base_extractor import BaseExtractor


@dataclass
class ExceptionHandlerInfo:
    """Exception handler information"""
    exception_types: List[str]
    variable_name: Optional[str]
    line_number: int


@dataclass
class ContextManagerInfo:
    """Context manager information"""
    context_expr: str
    variable_names: List[str]
    line_number: int


@dataclass
class LambdaInfo:
    """Lambda function information"""
    arguments: List[str]
    body: str
    line_number: int


class PatternExtractor(BaseExtractor):
    """Extract Python patterns"""

    def extract(self) -> Dict[str, List]:
        """
        Extract all patterns.

        Returns:
            Dictionary with different pattern types
        """
        return {
            'exception_handlers': self._extract_exception_handlers(),
            'context_managers': self._extract_context_managers(),
            'lambdas': self._extract_lambdas()
        }

    def _extract_exception_handlers(self) -> List[ExceptionHandlerInfo]:
        """
        Extract exception handlers.

        Returns:
            List of ExceptionHandlerInfo objects
        """
        handlers = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    exception_types = []

                    if handler.type:
                        if isinstance(handler.type, ast.Tuple):
                            # Multiple exception types: except (TypeError, ValueError) as e
                            for exc_type in handler.type.elts:
                                exception_types.append(ast.unparse(exc_type))
                        else:
                            # Single exception type: except TypeError as e
                            exception_types.append(ast.unparse(handler.type))

                    handlers.append(ExceptionHandlerInfo(
                        exception_types=exception_types,
                        variable_name=handler.name if handler.name else None,
                        line_number=handler.lineno
                    ))

        return handlers

    def _extract_context_managers(self) -> List[ContextManagerInfo]:
        """
        Extract context managers (with statements).

        Returns:
            List of ContextManagerInfo objects
        """
        managers = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    var_names = []

                    if isinstance(item.optional_vars, ast.Name):
                        var_names.append(item.optional_vars.id)
                    elif isinstance(item.optional_vars, ast.Tuple):
                        for elt in item.optional_vars.elts:
                            if isinstance(elt, ast.Name):
                                var_names.append(elt.id)

                    managers.append(ContextManagerInfo(
                        context_expr=ast.unparse(item.context_expr),
                        variable_names=var_names,
                        line_number=node.lineno
                    ))

        return managers

    def _extract_lambdas(self) -> List[LambdaInfo]:
        """
        Extract lambda functions.

        Returns:
            List of LambdaInfo objects
        """
        lambdas = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Lambda):
                args = [arg.arg for arg in node.args.args]
                lambdas.append(LambdaInfo(
                    arguments=args,
                    body=ast.unparse(node.body),
                    line_number=node.lineno
                ))

        return lambdas
