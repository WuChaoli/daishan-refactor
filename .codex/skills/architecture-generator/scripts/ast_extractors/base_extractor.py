#!/usr/bin/env python3
"""
Base extractor class for AST analysis.

Provides common functionality for all AST extractors.
"""

from abc import ABC, abstractmethod
import ast
from pathlib import Path
from typing import Dict, Optional


class BaseExtractor(ABC):
    """Base class for all AST extractors"""

    def __init__(self, file_path: Path, root_path: Path):
        """
        Initialize base extractor.

        Args:
            file_path: Path to the file to analyze
            root_path: Project root path
        """
        self.file_path = file_path
        self.root_path = root_path
        self.source = self._load_source()
        self.tree = self._parse_ast()

    def _load_source(self) -> str:
        """
        Load source code from file.

        Returns:
            Source code as string
        """
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_ast(self) -> ast.Module:
        """
        Parse source code into AST.

        Returns:
            AST module node
        """
        return ast.parse(self.source, filename=str(self.file_path))

    @abstractmethod
    def extract(self) -> Dict:
        """
        Extract information from AST.

        Returns:
            Dictionary containing extracted information
        """
        pass

    def extract_docstring(self, node: ast.AST) -> Optional[str]:
        """
        Extract docstring from AST node.

        Args:
            node: AST node

        Returns:
            Docstring if present, None otherwise
        """
        docstring = ast.get_docstring(node)
        return docstring if docstring else None

    def get_line_range(self, node: ast.AST) -> Dict[str, int]:
        """
        Get line number range for a node.

        Args:
            node: AST node

        Returns:
            Dictionary with 'start_line' and 'end_line' keys
        """
        return {
            'start_line': node.lineno,
            'end_line': getattr(node, 'end_lineno', node.lineno)
        }
