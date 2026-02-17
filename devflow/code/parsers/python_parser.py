"""
Python-specific parser using the ast module.

Provides deep analysis of Python code including:
- Functions and methods with full signatures
- Classes with inheritance and decorators
- Import statements and dependencies
- Call graph extraction
- Type annotation parsing
"""

import ast
import logging
from pathlib import Path
from typing import Any

from ..models import (
    ClassEntity,
    CodeEntity,
    CodeEntityType,
    FunctionEntity,
    ImportEntity,
    ModuleEntity,
    Parameter,
    Property,
)
from .base import BaseParser

logger = logging.getLogger(__name__)


class PythonParser(BaseParser):
    """Parser for Python source code using the ast module."""

    SUPPORTED_LANGUAGES = ["python"]
    SUPPORTED_EXTENSIONS = [".py", ".pyi", ".pyw"]

    def __init__(self):
        """Initialize the Python parser."""
        super().__init__()
        self._current_file: str = ""
        self._source_lines: list[str] = []

    def parse_file(self, file_path: str | Path) -> list[CodeEntity]:
        """Parse a Python file and extract all entities."""
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []

        if not self.can_parse(path):
            logger.warning(f"Not a Python file: {file_path}")
            return []

        try:
            source = path.read_text(encoding="utf-8")
            return self.parse_source(source, str(path), "python")
        except UnicodeDecodeError:
            logger.error(f"Unable to decode file: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []

    def parse_source(
        self,
        source: str,
        file_path: str = "<string>",
        language: str | None = None,
    ) -> list[CodeEntity]:
        """Parse Python source code and extract entities."""
        self._current_file = file_path
        self._source_lines = source.splitlines()

        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return []

        entities: list[CodeEntity] = []

        # Extract module-level entity
        module_entity = self._extract_module(tree, file_path, source)
        entities.append(module_entity)

        # Extract all entities from the tree
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                # Skip methods (they're extracted with classes)
                if not self._is_method(node, tree):
                    entity = self._extract_function(node, file_path)
                    if entity:
                        entities.append(entity)
                        module_entity.functions.append(entity.qualified_name)

            elif isinstance(node, ast.ClassDef):
                entity = self._extract_class(node, file_path)
                if entity:
                    entities.append(entity)
                    module_entity.classes.append(entity.qualified_name)

                    # Extract methods
                    for method in self._extract_methods(node, file_path):
                        entities.append(method)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                entity = self._extract_import(node, file_path)
                if entity:
                    entities.append(entity)
                    module_entity.imports.append(entity.module or entity.name)

        return entities

    def _extract_module(
        self, tree: ast.Module, file_path: str, source: str
    ) -> ModuleEntity:
        """Extract module-level entity."""
        path = Path(file_path)
        name = path.stem
        is_init = name == "__init__"
        is_package = is_init

        if is_init:
            name = path.parent.name

        # Get module docstring
        docstring = ast.get_docstring(tree)

        # Extract __all__ for exports
        exports: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(
                                    elt.value, str
                                ):
                                    exports.append(elt.value)

        entity_id = CodeEntity.generate_id(file_path, 1, name)

        return ModuleEntity(
            id=entity_id,
            name=name,
            qualified_name=name,
            entity_type=CodeEntityType.MODULE,
            file_path=file_path,
            line_start=1,
            line_end=len(self._source_lines),
            language="python",
            source_code="",  # Don't store entire module source
            docstring=docstring,
            tags=self._get_module_tags(is_package, is_init),
            exports=exports,
            is_package=is_package,
            is_init=is_init,
        )

    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
        parent_class: str | None = None,
    ) -> FunctionEntity | None:
        """Extract a function or method entity."""
        try:
            name = node.name
            is_async = isinstance(node, ast.AsyncFunctionDef)
            is_method = parent_class is not None

            # Get qualified name
            qualified_name = self.get_qualified_name(name, file_path, parent_class)

            # Generate ID
            entity_id = CodeEntity.generate_id(file_path, node.lineno, qualified_name)

            # Extract parameters
            parameters = self._extract_parameters(node)

            # Extract return type
            return_type = None
            if node.returns:
                return_type = self._get_annotation_string(node.returns)

            # Extract decorators
            decorators = [self._get_decorator_string(d) for d in node.decorator_list]

            # Check for special method types
            is_static = "staticmethod" in decorators
            is_classmethod = "classmethod" in decorators
            is_property = "property" in decorators or any(
                d.endswith(".setter") or d.endswith(".deleter") for d in decorators
            )

            # Check if generator
            is_generator = self._is_generator(node)

            # Extract function calls
            calls = self._extract_calls(node)

            # Calculate complexity
            complexity = self._calculate_function_complexity(node)

            # Get source code
            source_code = self._get_source_segment(node.lineno, node.end_lineno or node.lineno)

            # Get docstring
            docstring = ast.get_docstring(node)

            # Build tags
            tags = self._get_function_tags(
                is_async, is_generator, is_method, is_static, is_classmethod, is_property
            )

            return FunctionEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.METHOD if is_method else CodeEntityType.FUNCTION,
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                language="python",
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                parameters=parameters,
                return_type=return_type,
                decorators=decorators,
                is_async=is_async,
                is_generator=is_generator,
                is_method=is_method,
                is_static=is_static,
                is_classmethod=is_classmethod,
                is_property=is_property,
                parent_class=parent_class,
                calls=calls,
                complexity=complexity,
            )

        except Exception as e:
            logger.error(f"Error extracting function {node.name}: {e}")
            return None

    def _extract_class(
        self, node: ast.ClassDef, file_path: str
    ) -> ClassEntity | None:
        """Extract a class entity."""
        try:
            name = node.name
            qualified_name = self.get_qualified_name(name, file_path)
            entity_id = CodeEntity.generate_id(file_path, node.lineno, qualified_name)

            # Extract base classes
            base_classes = [self._get_annotation_string(base) for base in node.bases]

            # Extract decorators
            decorators = [self._get_decorator_string(d) for d in node.decorator_list]

            # Check for special class types
            is_dataclass = "dataclass" in decorators or any(
                "dataclass" in d for d in decorators
            )
            is_abstract = self._is_abstract_class(node)
            is_protocol = "Protocol" in base_classes

            # Extract metaclass
            metaclass = None
            for keyword in node.keywords:
                if keyword.arg == "metaclass":
                    metaclass = self._get_annotation_string(keyword.value)

            # Extract properties/attributes
            properties = self._extract_class_properties(node)

            # Get method names (full entities stored separately)
            methods = [
                f"{qualified_name}.{n.name}"
                for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

            # Get source code
            source_code = self._get_source_segment(node.lineno, node.end_lineno or node.lineno)

            # Get docstring
            docstring = ast.get_docstring(node)

            # Build tags
            tags = self._get_class_tags(is_dataclass, is_abstract, is_protocol)

            return ClassEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.CLASS,
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                language="python",
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                base_classes=base_classes,
                decorators=decorators,
                methods=methods,
                properties=properties,
                is_abstract=is_abstract,
                is_dataclass=is_dataclass,
                is_protocol=is_protocol,
                metaclass=metaclass,
            )

        except Exception as e:
            logger.error(f"Error extracting class {node.name}: {e}")
            return None

    def _extract_methods(
        self, class_node: ast.ClassDef, file_path: str
    ) -> list[FunctionEntity]:
        """Extract all methods from a class."""
        methods: list[FunctionEntity] = []
        class_name = self.get_qualified_name(class_node.name, file_path)

        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_function(node, file_path, class_name)
                if method:
                    methods.append(method)

        return methods

    def _extract_import(
        self, node: ast.Import | ast.ImportFrom, file_path: str
    ) -> ImportEntity | None:
        """Extract an import statement entity."""
        try:
            if isinstance(node, ast.Import):
                # import x, y, z
                names = [alias.name for alias in node.names]
                aliases = {
                    alias.name: alias.asname
                    for alias in node.names
                    if alias.asname
                }
                module = names[0] if len(names) == 1 else ""
                name = ", ".join(names)
                is_relative = False
                level = 0

            else:
                # from x import y, z
                module = node.module or ""
                names = [alias.name for alias in node.names]
                aliases = {
                    alias.name: alias.asname
                    for alias in node.names
                    if alias.asname
                }
                name = f"from {module} import {', '.join(names)}"
                is_relative = node.level > 0
                level = node.level

            qualified_name = f"import:{module}:{','.join(names)}"
            entity_id = CodeEntity.generate_id(file_path, node.lineno, qualified_name)

            source_code = self._get_source_segment(node.lineno, node.end_lineno or node.lineno)

            return ImportEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.IMPORT,
                file_path=file_path,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                language="python",
                source_code=source_code,
                module=module,
                names=names,
                aliases=aliases,
                is_relative=is_relative,
                level=level,
            )

        except Exception as e:
            logger.error(f"Error extracting import: {e}")
            return None

    def _extract_parameters(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[Parameter]:
        """Extract function parameters."""
        parameters: list[Parameter] = []
        args = node.args

        # Calculate defaults offset
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        defaults_offset = num_args - num_defaults

        # Regular arguments
        for i, arg in enumerate(args.args):
            default_idx = i - defaults_offset
            default_value = None
            if default_idx >= 0 and default_idx < len(args.defaults):
                default_value = self._get_constant_value(args.defaults[default_idx])

            parameters.append(
                Parameter(
                    name=arg.arg,
                    type_annotation=self._get_annotation_string(arg.annotation)
                    if arg.annotation
                    else None,
                    default_value=default_value,
                )
            )

        # *args
        if args.vararg:
            parameters.append(
                Parameter(
                    name=args.vararg.arg,
                    type_annotation=self._get_annotation_string(args.vararg.annotation)
                    if args.vararg.annotation
                    else None,
                    is_variadic=True,
                )
            )

        # Keyword-only arguments
        kw_defaults_offset = len(args.kwonlyargs) - len(args.kw_defaults)
        for i, arg in enumerate(args.kwonlyargs):
            default_idx = i - kw_defaults_offset
            default_value = None
            if (
                default_idx >= 0
                and default_idx < len(args.kw_defaults)
                and args.kw_defaults[default_idx] is not None
            ):
                default_value = self._get_constant_value(args.kw_defaults[default_idx])

            parameters.append(
                Parameter(
                    name=arg.arg,
                    type_annotation=self._get_annotation_string(arg.annotation)
                    if arg.annotation
                    else None,
                    default_value=default_value,
                )
            )

        # **kwargs
        if args.kwarg:
            parameters.append(
                Parameter(
                    name=args.kwarg.arg,
                    type_annotation=self._get_annotation_string(args.kwarg.annotation)
                    if args.kwarg.annotation
                    else None,
                    is_keyword=True,
                )
            )

        return parameters

    def _extract_class_properties(self, node: ast.ClassDef) -> list[Property]:
        """Extract class-level properties and attributes."""
        properties: list[Property] = []

        for item in node.body:
            # Class-level assignments
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                prop = Property(
                    name=item.target.id,
                    type_annotation=self._get_annotation_string(item.annotation)
                    if item.annotation
                    else None,
                    default_value=self._get_constant_value(item.value)
                    if item.value
                    else None,
                    is_class_var=self._is_class_var(item.annotation),
                )
                properties.append(prop)

            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Check if it's a constant (UPPER_CASE)
                        is_class_var = target.id.isupper()
                        properties.append(
                            Property(
                                name=target.id,
                                default_value=self._get_constant_value(item.value),
                                is_class_var=is_class_var,
                            )
                        )

        return properties

    def _extract_calls(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[str]:
        """Extract function calls made within a function."""
        calls: list[str] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child.func)
                if call_name and call_name not in calls:
                    calls.append(call_name)

        return calls

    def _get_call_name(self, node: ast.expr) -> str | None:
        """Get the name of a function call."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_call_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return None

    def _get_annotation_string(self, node: ast.expr | None) -> str | None:
        """Convert an annotation AST node to string."""
        if node is None:
            return None

        try:
            return ast.unparse(node)
        except Exception:
            # Fallback for older Python versions
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Constant):
                return repr(node.value)
            elif isinstance(node, ast.Subscript):
                value = self._get_annotation_string(node.value)
                slice_val = self._get_annotation_string(node.slice)
                return f"{value}[{slice_val}]"
            elif isinstance(node, ast.Attribute):
                value = self._get_annotation_string(node.value)
                return f"{value}.{node.attr}"
            return None

    def _get_decorator_string(self, node: ast.expr) -> str:
        """Convert a decorator AST node to string."""
        try:
            return ast.unparse(node)
        except Exception:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Call):
                func = self._get_decorator_string(node.func)
                return func
            elif isinstance(node, ast.Attribute):
                value = self._get_decorator_string(node.value)
                return f"{value}.{node.attr}"
            return "unknown"

    def _get_constant_value(self, node: ast.expr | None) -> str | None:
        """Get string representation of a constant value."""
        if node is None:
            return None

        try:
            return ast.unparse(node)
        except Exception:
            if isinstance(node, ast.Constant):
                return repr(node.value)
            return None

    def _get_source_segment(self, start_line: int, end_line: int) -> str:
        """Get source code for a line range."""
        if not self._source_lines:
            return ""

        start_idx = max(0, start_line - 1)
        end_idx = min(len(self._source_lines), end_line)

        return "\n".join(self._source_lines[start_idx:end_idx])

    def _is_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef, tree: ast.Module) -> bool:
        """Check if a function node is a method inside a class."""
        for class_node in ast.walk(tree):
            if isinstance(class_node, ast.ClassDef):
                for item in class_node.body:
                    if item is node:
                        return True
        return False

    def _is_generator(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if a function is a generator."""
        for child in ast.walk(node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _is_abstract_class(self, node: ast.ClassDef) -> bool:
        """Check if a class is abstract."""
        # Check for ABC base class
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ("ABC", "ABCMeta"):
                return True
            if isinstance(base, ast.Attribute) and base.attr in ("ABC", "ABCMeta"):
                return True

        # Check for abstract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in item.decorator_list:
                    dec_str = self._get_decorator_string(decorator)
                    if "abstractmethod" in dec_str:
                        return True

        return False

    def _is_class_var(self, annotation: ast.expr | None) -> bool:
        """Check if an annotation indicates a ClassVar."""
        if annotation is None:
            return False

        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id == "ClassVar"
            if isinstance(annotation.value, ast.Attribute):
                return annotation.value.attr == "ClassVar"

        return False

    def _calculate_function_complexity(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)

        return complexity

    def _get_module_tags(self, is_package: bool, is_init: bool) -> list[str]:
        """Get tags for a module entity."""
        tags = []
        if is_package:
            tags.append("package")
        if is_init:
            tags.append("init")
        return tags

    def _get_function_tags(
        self,
        is_async: bool,
        is_generator: bool,
        is_method: bool,
        is_static: bool,
        is_classmethod: bool,
        is_property: bool,
    ) -> list[str]:
        """Get tags for a function entity."""
        tags = []
        if is_async:
            tags.append("async")
        if is_generator:
            tags.append("generator")
        if is_method:
            tags.append("method")
        if is_static:
            tags.append("static")
        if is_classmethod:
            tags.append("classmethod")
        if is_property:
            tags.append("property")
        return tags

    def _get_class_tags(
        self, is_dataclass: bool, is_abstract: bool, is_protocol: bool
    ) -> list[str]:
        """Get tags for a class entity."""
        tags = []
        if is_dataclass:
            tags.append("dataclass")
        if is_abstract:
            tags.append("abstract")
        if is_protocol:
            tags.append("protocol")
        return tags
