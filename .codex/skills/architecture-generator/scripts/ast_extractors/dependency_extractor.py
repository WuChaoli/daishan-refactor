#!/usr/bin/env python3
"""
Dependency extractor for enhanced AST analysis.

Extracts comprehensive dependency information including imports,
function calls, class instantiations, and type annotations.
"""

from dataclasses import dataclass
from typing import List, Set, Optional
import ast

from .base_extractor import BaseExtractor


@dataclass
class DependencyInfo:
    """Dependency information"""
    name: str
    dep_type: str  # 'import', 'from_import', 'call', 'instantiation', 'type_hint'
    line_number: int
    is_external: bool
    module_path: Optional[str]


class DependencyExtractor(BaseExtractor):
    """Enhanced dependency extraction"""

    def __init__(self, file_path, root_path):
        """Initialize dependency extractor"""
        super().__init__(file_path, root_path)
        self._imported_names = None

    def extract(self) -> dict:
        """
        Extract all dependencies.

        Returns:
            Dictionary with different dependency types
        """
        self._imported_names = self._get_imported_names()

        return {
            'imports': self._extract_imports(),
            'calls': self._extract_function_calls(),
            'instantiations': self._extract_class_instantiations(),
            'type_hints': self._extract_type_dependencies()
        }

    def _extract_imports(self) -> List[DependencyInfo]:
        """
        Extract import statements.

        Returns:
            List of import dependencies
        """
        imports = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    imports.append(DependencyInfo(
                        name=module_name,
                        dep_type='import',
                        line_number=node.lineno,
                        is_external=self._is_external_module(module_name),
                        module_path=module_name
                    ))

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module if node.module else ''
                for alias in node.names:
                    imports.append(DependencyInfo(
                        name=f"{module_name}.{alias.name}" if module_name else alias.name,
                        dep_type='from_import',
                        line_number=node.lineno,
                        is_external=self._is_external_module(module_name),
                        module_path=module_name
                    ))

        return imports

    def _extract_function_calls(self) -> List[DependencyInfo]:
        """
        Extract function calls.

        Returns:
            List of function call dependencies
        """
        calls = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                func_name = self._extract_call_name(node.func)
                if func_name and func_name in self._imported_names:
                    calls.append(DependencyInfo(
                        name=func_name,
                        dep_type='call',
                        line_number=node.lineno,
                        is_external=self._is_external_module(func_name),
                        module_path=None
                    ))

        return calls

    def _extract_class_instantiations(self) -> List[DependencyInfo]:
        """
        Extract class instantiations.

        Returns:
            List of class instantiation dependencies
        """
        instantiations = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                func_name = self._extract_call_name(node.func)
                if func_name and func_name[0].isupper():  # Class names typically start with uppercase
                    instantiations.append(DependencyInfo(
                        name=func_name,
                        dep_type='instantiation',
                        line_number=node.lineno,
                        is_external=self._is_external_module(func_name),
                        module_path=None
                    ))

        return instantiations

    def _extract_type_dependencies(self) -> List[DependencyInfo]:
        """
        Extract type annotation dependencies.

        Returns:
            List of type annotation dependencies
        """
        type_deps = []

        for node in ast.walk(self.tree):
            # Check function return type
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns:
                    type_names = self._extract_type_names(node.returns)
                    for type_name in type_names:
                        if type_name and type_name in self._imported_names:
                            type_deps.append(DependencyInfo(
                                name=type_name,
                                dep_type='type_hint',
                                line_number=node.lineno,
                                is_external=self._is_external_module(type_name),
                                module_path=None
                            ))

            # Check parameter annotations
            elif isinstance(node, ast.arguments):
                for arg in node.args + node.posonlyargs + node.kwonlyargs:
                    if arg.annotation:
                        type_names = self._extract_type_names(arg.annotation)
                        for type_name in type_names:
                            if type_name and type_name in self._imported_names:
                                type_deps.append(DependencyInfo(
                                    name=type_name,
                                    dep_type='type_hint',
                                    line_number=node.lineno if hasattr(node, 'lineno') else 0,
                                    is_external=self._is_external_module(type_name),
                                    module_path=None
                                ))

                # Check *args and **kwargs annotations
                if node.vararg and node.vararg.annotation:
                    type_names = self._extract_type_names(node.vararg.annotation)
                    for type_name in type_names:
                        if type_name and type_name in self._imported_names:
                            type_deps.append(DependencyInfo(
                                name=type_name,
                                dep_type='type_hint',
                                line_number=node.lineno if hasattr(node, 'lineno') else 0,
                                is_external=self._is_external_module(type_name),
                                module_path=None
                            ))

                if node.kwarg and node.kwarg.annotation:
                    type_names = self._extract_type_names(node.kwarg.annotation)
                    for type_name in type_names:
                        if type_name and type_name in self._imported_names:
                            type_deps.append(DependencyInfo(
                                name=type_name,
                                dep_type='type_hint',
                                line_number=node.lineno if hasattr(node, 'lineno') else 0,
                                is_external=self._is_external_module(type_name),
                                module_path=None
                            ))

            # Check variable annotations
            elif isinstance(node, ast.AnnAssign):
                if node.annotation:
                    type_names = self._extract_type_names(node.annotation)
                    for type_name in type_names:
                        if type_name and type_name in self._imported_names:
                            type_deps.append(DependencyInfo(
                                name=type_name,
                                dep_type='type_hint',
                                line_number=node.lineno,
                                is_external=self._is_external_module(type_name),
                                module_path=None
                            ))

        return type_deps

    def _get_imported_names(self) -> Set[str]:
        """
        Get all imported names.

        Returns:
            Set of imported names
        """
        names = set()

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name)
                    if alias.asname:
                        names.add(alias.asname)

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.name)
                    if alias.asname:
                        names.add(alias.asname)

        return names

    def _extract_call_name(self, func: ast.expr) -> Optional[str]:
        """
        Extract function name from Call node.

        Args:
            func: Function expression from Call node

        Returns:
            Function name or None
        """
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        elif isinstance(func, ast.Subscript):
            return self._extract_call_name(func.value)
        return None

    def _extract_type_names(self, node: ast.expr) -> List[str]:
        """
        Extract type names from type annotation.

        Args:
            node: Type annotation node

        Returns:
            List of type names
        """
        types = []

        if isinstance(node, ast.Name):
            types.append(node.id)
        elif isinstance(node, ast.Attribute):
            types.append(node.attr)
        elif isinstance(node, ast.Subscript):
            types.extend(self._extract_type_names(node.value))
            if hasattr(node.slice, 'elts'):
                # Python 3.8: Tuple
                types.extend(self._extract_type_names(node.slice))
            elif isinstance(node.slice, ast.Tuple):
                # Python 3.9+: Tuple
                for elt in node.slice.elts:
                    types.extend(self._extract_type_names(elt))
            else:
                types.extend(self._extract_type_names(node.slice))
        elif isinstance(node, ast.Tuple):
            for elt in node.elts:
                types.extend(self._extract_type_names(elt))
        elif isinstance(node, ast.BinOp):
            types.extend(self._extract_type_names(node.left))
            types.extend(self._extract_type_names(node.right))

        return types

    def _is_external_module(self, name: str) -> bool:
        """
        Check if module is external (not from current project).

        Args:
            name: Module name

        Returns:
            True if module is likely external
        """
        # Standard library modules
        stdlib_modules = {
            'os', 'sys', 'json', 're', 'pathlib', 'typing', 'datetime',
            'collections', 'itertools', 'functools', 'math', 'random',
            'time', 'uuid', 'hashlib', 'base64', 'pickle', 'io', 'logging',
            'abc', 'dataclasses', 'enum', 'contextlib', 'asyncio',
            'threading', 'multiprocessing', 'concurrent', 'queue'
        }

        # Check if it's a standard library module
        module_base = name.split('.')[0]
        if module_base in stdlib_modules:
            return True

        # TODO: Could be enhanced to check against project structure
        return False
