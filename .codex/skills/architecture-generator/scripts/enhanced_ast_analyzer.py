#!/usr/bin/env python3
"""
Enhanced AST analyzer - Main orchestrator for all extractors.

Provides a unified interface for comprehensive Python code analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ast_extractors.class_extractor import ClassExtractor
from ast_extractors.function_extractor import FunctionExtractor
from ast_extractors.dependency_extractor import DependencyExtractor
from ast_extractors.variable_extractor import VariableExtractor, VariableInfo
from ast_extractors.pattern_extractor import PatternExtractor


class EnhancedASTAnalyzer:
    """Enhanced AST analyzer that orchestrates all extractors"""

    def __init__(self, project_path: Path, db_path: str = "symbols.db"):
        """
        Initialize enhanced AST analyzer.

        Args:
            project_path: Path to project root
            db_path: Path to SQLite database for call graph
        """
        self.project_path = project_path.resolve()

    def analyze_file(self, file_path: Path) -> Dict:
        """
        Analyze a single file with enhanced extraction.

        Args:
            file_path: Path to file to analyze

        Returns:
            Dictionary containing all extracted information
        """
        file_path = file_path.resolve()
        rel_path = str(file_path.relative_to(self.project_path))

        result = {
            'file_path': rel_path,
            'classes': [],
            'functions': [],
            'dependencies': {},
            'variables': {},
            'patterns': {}
        }

        try:
            # Extract classes
            class_extractor = ClassExtractor(file_path, self.project_path)
            classes = class_extractor.extract()
            result['classes'] = [self._class_to_dict(c, rel_path) for c in classes]

            # Extract functions
            func_extractor = FunctionExtractor(file_path, self.project_path)
            functions = func_extractor.extract()
            result['functions'] = [self._function_to_dict(f, rel_path) for f in functions]

            # Extract dependencies
            dep_extractor = DependencyExtractor(file_path, self.project_path)
            dependencies = dep_extractor.extract()
            result['dependencies'] = self._dependencies_to_dict(dependencies, rel_path)

            # Extract variables
            var_extractor = VariableExtractor(file_path, self.project_path)
            variables = var_extractor.extract()
            result['variables'] = self._variables_to_dict(variables, rel_path)

            # Extract patterns
            pattern_extractor = PatternExtractor(file_path, self.project_path)
            patterns = pattern_extractor.extract()
            result['patterns'] = self._patterns_to_dict(patterns, rel_path)

        except Exception as e:
            result['error'] = str(e)

        return result

    def _class_to_dict(self, class_info, rel_path: str) -> Dict:
        """
        Convert class info to dictionary.

        Args:
            class_info: ClassInfo object
            rel_path: Relative file path

        Returns:
            Dictionary representation
        """
        return {
            'name': class_info.name,
            'file_path': rel_path,
            'line_number': class_info.line_range['start_line'],
            'end_line_number': class_info.line_range['end_line'],
            'decorators': class_info.decorators,
            'bases': class_info.bases,
            'methods': [self._function_to_dict(m, rel_path) for m in class_info.methods],
            'class_variables': class_info.class_variables,
            'nested_classes': [self._class_to_dict(c, rel_path) for c in class_info.nested_classes],
            'docstring': class_info.docstring,
            'is_abstract': class_info.is_abstract,
            'is_dataclass': class_info.is_dataclass,
            'is_exception': class_info.is_exception
        }

    def _function_to_dict(self, func_info, rel_path: str) -> Dict:
        """
        Convert function info to dictionary.

        Args:
            func_info: FunctionInfo object
            rel_path: Relative file path

        Returns:
            Dictionary representation
        """
        return {
            'name': func_info.name,
            'file_path': rel_path,
            'line_number': func_info.line_range['start_line'],
            'end_line_number': func_info.line_range['end_line'],
            'decorators': func_info.decorators,
            'parameters': [
                {
                    'name': p.name,
                    'type_annotation': p.type_annotation,
                    'default_value': p.default_value,
                    'is_positional_only': p.is_positional_only,
                    'is_keyword_only': p.is_keyword_only,
                    'is_var_positional': p.is_var_positional,
                    'is_var_keyword': p.is_var_keyword
                }
                for p in func_info.parameters
            ],
            'return_type': func_info.return_type,
            'docstring': func_info.docstring,
            'is_async': func_info.is_async,
            'is_method': func_info.is_method,
            'is_static_method': func_info.is_static_method,
            'is_class_method': func_info.is_class_method,
            'is_property': func_info.is_property,
            'is_generator': func_info.is_generator,
            'is_async_generator': func_info.is_async_generator,
            'nested_functions': [self._function_to_dict(f, rel_path) for f in func_info.nested_functions],
            'await_count': func_info.await_count
        }

    def _dependencies_to_dict(self, dependencies: Dict, rel_path: str) -> Dict:
        """
        Convert dependencies to dictionary.

        Args:
            dependencies: Dependencies dictionary
            rel_path: Relative file path

        Returns:
            Dictionary representation
        """
        result = {}
        for key, deps in dependencies.items():
            result[key] = [
                {
                    'name': d.name,
                    'dep_type': d.dep_type,
                    'line_number': d.line_number,
                    'is_external': d.is_external,
                    'module_path': d.module_path,
                    'source_file': rel_path
                }
                for d in deps
            ]
        return result

    def _variables_to_dict(self, variables: Dict[str, List[VariableInfo]], rel_path: str) -> Dict:
        """
        Convert variables to dictionary.

        Args:
            variables: Variables dictionary
            rel_path: Relative file path

        Returns:
            Dictionary representation
        """
        result = {}
        for key, vars in variables.items():
            result[key] = [
                {
                    'name': v.name,
                    'type_annotation': v.type_annotation,
                    'value': v.value,
                    'is_class_variable': v.is_class_variable,
                    'is_global': v.is_global,
                    'line_number': v.line_number,
                    'source_file': rel_path
                }
                for v in vars
            ]
        return result

    def _patterns_to_dict(self, patterns: Dict, rel_path: str) -> Dict:
        """
        Convert patterns to dictionary.

        Args:
            patterns: Patterns dictionary
            rel_path: Relative file path

        Returns:
            Dictionary representation
        """
        result = {}
        for key, items in patterns.items():
            if key == 'exception_handlers':
                result[key] = [
                    {
                        'exception_types': e.exception_types,
                        'variable_name': e.variable_name,
                        'line_number': e.line_number,
                        'source_file': rel_path
                    }
                    for e in items
                ]
            elif key == 'context_managers':
                result[key] = [
                    {
                        'context_expr': c.context_expr,
                        'variable_names': c.variable_names,
                        'line_number': c.line_number,
                        'source_file': rel_path
                    }
                    for c in items
                ]
            elif key == 'lambdas':
                result[key] = [
                    {
                        'arguments': l.arguments,
                        'body': l.body,
                        'line_number': l.line_number,
                        'source_file': rel_path
                    }
                    for l in items
                ]
        return result


def main():
    """CLI for enhanced AST analyzer"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: enhanced_ast_analyzer.py <file-path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File does not exist: {file_path}")
        sys.exit(1)

    # Analyze file
    analyzer = EnhancedASTAnalyzer(file_path.parent)
    result = analyzer.analyze_file(file_path)

    # Output JSON
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
