"""
Universal parser using tree-sitter for multiple languages.

Provides AST parsing for JavaScript, TypeScript, Go, Rust, and other languages
supported by tree-sitter. Falls back to basic parsing when tree-sitter is
not available.
"""

import logging
import re
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

# Try to import tree-sitter
try:
    from tree_sitter_language_pack import get_language, get_parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    try:
        # Try alternative package name
        from tree_sitter_languages import get_language, get_parser

        TREE_SITTER_AVAILABLE = True
    except ImportError:
        TREE_SITTER_AVAILABLE = False
        get_language = None
        get_parser = None
        logger.warning(
            "tree-sitter not available. Install tree-sitter-language-pack for "
            "multi-language support: pip install tree-sitter-language-pack"
        )


# Language configuration: extension -> (language_name, tree_sitter_name)
LANGUAGE_CONFIG: dict[str, tuple[str, str]] = {
    ".js": ("javascript", "javascript"),
    ".jsx": ("javascript", "javascript"),
    ".ts": ("typescript", "typescript"),
    ".tsx": ("typescript", "tsx"),
    ".go": ("go", "go"),
    ".rs": ("rust", "rust"),
    ".java": ("java", "java"),
    ".kt": ("kotlin", "kotlin"),
    ".swift": ("swift", "swift"),
    ".c": ("c", "c"),
    ".h": ("c", "c"),
    ".cpp": ("cpp", "cpp"),
    ".hpp": ("cpp", "cpp"),
    ".cc": ("cpp", "cpp"),
    ".rb": ("ruby", "ruby"),
    ".php": ("php", "php"),
    ".lua": ("lua", "lua"),
}


class TreeSitterParser(BaseParser):
    """Universal parser using tree-sitter."""

    SUPPORTED_LANGUAGES = list({cfg[0] for cfg in LANGUAGE_CONFIG.values()})
    SUPPORTED_EXTENSIONS = list(LANGUAGE_CONFIG.keys())

    def __init__(self):
        """Initialize the tree-sitter parser."""
        super().__init__()
        self._parsers: dict[str, Any] = {}
        self._languages: dict[str, Any] = {}
        self._current_file: str = ""
        self._source_bytes: bytes = b""
        self._source_lines: list[str] = []

    def _get_parser(self, language: str) -> Any | None:
        """Get or create a parser for a language."""
        if not TREE_SITTER_AVAILABLE:
            return None

        if language not in self._parsers:
            try:
                parser = get_parser(language)
                self._parsers[language] = parser
                self._languages[language] = get_language(language)
            except Exception as e:
                logger.warning(f"Failed to load tree-sitter parser for {language}: {e}")
                return None

        return self._parsers.get(language)

    def can_parse(self, file_path: str | Path) -> bool:
        """Check if this parser can handle the given file."""
        if not TREE_SITTER_AVAILABLE:
            return False
        path = Path(file_path)
        return path.suffix.lower() in LANGUAGE_CONFIG

    def parse_file(self, file_path: str | Path) -> list[CodeEntity]:
        """Parse a source file and extract code entities."""
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return []

        if not self.can_parse(path):
            logger.warning(f"Unsupported file type: {file_path}")
            return []

        try:
            source = path.read_text(encoding="utf-8")
            language, ts_lang = LANGUAGE_CONFIG.get(
                path.suffix.lower(), (None, None)
            )
            return self.parse_source(source, str(path), language)
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
        """Parse source code and extract entities."""
        if not TREE_SITTER_AVAILABLE:
            logger.warning("tree-sitter not available")
            return []

        # Detect language from file extension if not provided
        if not language:
            path = Path(file_path)
            config = LANGUAGE_CONFIG.get(path.suffix.lower())
            if config:
                language, ts_lang = config
            else:
                logger.warning(f"Unknown language for {file_path}")
                return []
        else:
            # Map language to tree-sitter language name
            ts_lang = language
            for ext, (lang, ts) in LANGUAGE_CONFIG.items():
                if lang == language:
                    ts_lang = ts
                    break

        self._current_file = file_path
        self._source_bytes = source.encode("utf-8")
        self._source_lines = source.splitlines()

        parser = self._get_parser(ts_lang)
        if not parser:
            return []

        try:
            tree = parser.parse(self._source_bytes)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return []

        entities: list[CodeEntity] = []

        # Extract module entity
        module_entity = self._extract_module(tree.root_node, file_path, language)
        entities.append(module_entity)

        # Language-specific extraction
        if language in ("javascript", "typescript"):
            entities.extend(
                self._extract_js_ts_entities(tree.root_node, file_path, language)
            )
        elif language == "go":
            entities.extend(
                self._extract_go_entities(tree.root_node, file_path, language)
            )
        elif language == "rust":
            entities.extend(
                self._extract_rust_entities(tree.root_node, file_path, language)
            )
        else:
            # Generic extraction
            entities.extend(
                self._extract_generic_entities(tree.root_node, file_path, language)
            )

        # Update module entity with collected info
        for entity in entities:
            if entity.entity_type == CodeEntityType.FUNCTION:
                module_entity.functions.append(entity.qualified_name)
            elif entity.entity_type == CodeEntityType.CLASS:
                module_entity.classes.append(entity.qualified_name)
            elif entity.entity_type == CodeEntityType.IMPORT:
                if isinstance(entity, ImportEntity):
                    module_entity.imports.append(entity.module or entity.name)

        return entities

    def _extract_module(
        self, root_node: Any, file_path: str, language: str
    ) -> ModuleEntity:
        """Extract module-level entity."""
        path = Path(file_path)
        name = path.stem

        # Get module-level comment/docstring
        docstring = self._extract_leading_comment(root_node)

        entity_id = CodeEntity.generate_id(file_path, 1, name)

        return ModuleEntity(
            id=entity_id,
            name=name,
            qualified_name=name,
            entity_type=CodeEntityType.MODULE,
            file_path=file_path,
            line_start=1,
            line_end=len(self._source_lines),
            language=language,
            source_code="",
            docstring=docstring,
            tags=[language],
        )

    def _extract_js_ts_entities(
        self, root_node: Any, file_path: str, language: str
    ) -> list[CodeEntity]:
        """Extract entities from JavaScript/TypeScript code."""
        entities: list[CodeEntity] = []

        def visit(node: Any, parent_class: str | None = None):
            # Function declarations
            if node.type in ("function_declaration", "method_definition", "arrow_function"):
                entity = self._extract_js_function(node, file_path, language, parent_class)
                if entity:
                    entities.append(entity)

            # Class declarations
            elif node.type == "class_declaration":
                entity = self._extract_js_class(node, file_path, language)
                if entity:
                    entities.append(entity)
                    # Visit class body for methods
                    body = node.child_by_field_name("body")
                    if body:
                        for child in body.children:
                            visit(child, entity.qualified_name)
                return  # Don't recurse further

            # Import statements
            elif node.type == "import_statement":
                entity = self._extract_js_import(node, file_path, language)
                if entity:
                    entities.append(entity)

            # Export statements with declarations
            elif node.type in ("export_statement", "export_default_declaration"):
                for child in node.children:
                    visit(child, parent_class)
                return

            # Variable declarations (for arrow functions)
            elif node.type == "variable_declaration":
                for decl in node.children:
                    if decl.type == "variable_declarator":
                        value = decl.child_by_field_name("value")
                        if value and value.type == "arrow_function":
                            name_node = decl.child_by_field_name("name")
                            if name_node:
                                entity = self._extract_js_arrow_function(
                                    name_node, value, file_path, language
                                )
                                if entity:
                                    entities.append(entity)

            # Recurse into children
            for child in node.children:
                if child.type not in ("class_body", "statement_block"):
                    visit(child, parent_class)

        visit(root_node)
        return entities

    def _extract_js_function(
        self,
        node: Any,
        file_path: str,
        language: str,
        parent_class: str | None = None,
    ) -> FunctionEntity | None:
        """Extract a JavaScript/TypeScript function."""
        try:
            # Get function name
            name_node = node.child_by_field_name("name")
            if not name_node:
                # Method definition
                for child in node.children:
                    if child.type == "property_identifier":
                        name_node = child
                        break

            if not name_node:
                return None

            name = self._get_node_text(name_node)
            is_method = parent_class is not None

            qualified_name = self.get_qualified_name(name, file_path, parent_class)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            # Extract parameters
            parameters = self._extract_js_parameters(node)

            # Check for async
            is_async = any(
                child.type == "async" for child in node.children
            )

            # Extract return type (TypeScript)
            return_type = None
            return_type_node = node.child_by_field_name("return_type")
            if return_type_node:
                return_type = self._get_node_text(return_type_node).lstrip(": ")

            # Get source code
            source_code = self._get_node_text(node)

            # Get docstring (JSDoc comment)
            docstring = self._extract_jsdoc(node)

            tags = []
            if is_async:
                tags.append("async")
            if is_method:
                tags.append("method")

            return FunctionEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.METHOD if is_method else CodeEntityType.FUNCTION,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                parameters=parameters,
                return_type=return_type,
                is_async=is_async,
                is_method=is_method,
                parent_class=parent_class,
                calls=self._extract_js_calls(node),
                complexity=self._calculate_js_complexity(node),
            )

        except Exception as e:
            logger.error(f"Error extracting JS function: {e}")
            return None

    def _extract_js_arrow_function(
        self,
        name_node: Any,
        arrow_node: Any,
        file_path: str,
        language: str,
    ) -> FunctionEntity | None:
        """Extract an arrow function assigned to a variable."""
        try:
            name = self._get_node_text(name_node)
            qualified_name = self.get_qualified_name(name, file_path)
            entity_id = CodeEntity.generate_id(
                file_path, arrow_node.start_point[0] + 1, qualified_name
            )

            parameters = self._extract_js_parameters(arrow_node)
            is_async = any(child.type == "async" for child in arrow_node.children)

            source_code = f"const {name} = {self._get_node_text(arrow_node)}"
            docstring = self._extract_jsdoc(arrow_node)

            tags = ["arrow"]
            if is_async:
                tags.append("async")

            return FunctionEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.FUNCTION,
                file_path=file_path,
                line_start=arrow_node.start_point[0] + 1,
                line_end=arrow_node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                parameters=parameters,
                is_async=is_async,
                calls=self._extract_js_calls(arrow_node),
                complexity=self._calculate_js_complexity(arrow_node),
            )

        except Exception as e:
            logger.error(f"Error extracting arrow function: {e}")
            return None

    def _extract_js_class(
        self, node: Any, file_path: str, language: str
    ) -> ClassEntity | None:
        """Extract a JavaScript/TypeScript class."""
        try:
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            name = self._get_node_text(name_node)
            qualified_name = self.get_qualified_name(name, file_path)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            # Extract base classes
            base_classes: list[str] = []
            heritage = node.child_by_field_name("heritage")
            if heritage:
                for child in heritage.children:
                    if child.type == "extends_clause":
                        for c in child.children:
                            if c.type == "identifier":
                                base_classes.append(self._get_node_text(c))

            # Get method names
            methods: list[str] = []
            body = node.child_by_field_name("body")
            if body:
                for child in body.children:
                    if child.type == "method_definition":
                        method_name = None
                        for c in child.children:
                            if c.type == "property_identifier":
                                method_name = self._get_node_text(c)
                                break
                        if method_name:
                            methods.append(f"{qualified_name}.{method_name}")

            source_code = self._get_node_text(node)
            docstring = self._extract_jsdoc(node)

            return ClassEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.CLASS,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                base_classes=base_classes,
                methods=methods,
            )

        except Exception as e:
            logger.error(f"Error extracting JS class: {e}")
            return None

    def _extract_js_import(
        self, node: Any, file_path: str, language: str
    ) -> ImportEntity | None:
        """Extract a JavaScript/TypeScript import statement."""
        try:
            source_code = self._get_node_text(node)

            # Parse the module path
            module = ""
            for child in node.children:
                if child.type == "string":
                    module = self._get_node_text(child).strip("'\"")

            # Parse imported names
            names: list[str] = []
            aliases: dict[str, str] = {}

            for child in node.children:
                if child.type == "import_clause":
                    for c in child.children:
                        if c.type == "identifier":
                            names.append(self._get_node_text(c))
                        elif c.type == "named_imports":
                            for spec in c.children:
                                if spec.type == "import_specifier":
                                    name = None
                                    alias = None
                                    for s in spec.children:
                                        if s.type == "identifier":
                                            if name is None:
                                                name = self._get_node_text(s)
                                            else:
                                                alias = self._get_node_text(s)
                                    if name:
                                        names.append(name)
                                        if alias:
                                            aliases[name] = alias

            name = f"import {module}"
            qualified_name = f"import:{module}:{','.join(names)}"
            entity_id = CodeEntity.generate_id(
                file_path, node.start_point[0] + 1, qualified_name
            )

            return ImportEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.IMPORT,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                module=module,
                names=names,
                aliases=aliases,
                is_relative=module.startswith("."),
            )

        except Exception as e:
            logger.error(f"Error extracting JS import: {e}")
            return None

    def _extract_js_parameters(self, node: Any) -> list[Parameter]:
        """Extract parameters from a JS/TS function."""
        parameters: list[Parameter] = []

        params_node = node.child_by_field_name("parameters")
        if not params_node:
            # Arrow function might have parameters differently
            for child in node.children:
                if child.type == "formal_parameters":
                    params_node = child
                    break

        if not params_node:
            return parameters

        for child in params_node.children:
            if child.type in ("identifier", "required_parameter", "optional_parameter"):
                name = self._get_node_text(child.child_by_field_name("name") or child)
                type_annotation = None
                type_node = child.child_by_field_name("type")
                if type_node:
                    type_annotation = self._get_node_text(type_node).lstrip(": ")

                parameters.append(
                    Parameter(
                        name=name,
                        type_annotation=type_annotation,
                    )
                )
            elif child.type == "rest_parameter":
                name = ""
                for c in child.children:
                    if c.type == "identifier":
                        name = self._get_node_text(c)
                parameters.append(Parameter(name=name, is_variadic=True))

        return parameters

    def _extract_js_calls(self, node: Any) -> list[str]:
        """Extract function calls from a JS/TS node."""
        calls: list[str] = []

        def visit(n: Any):
            if n.type == "call_expression":
                func = n.child_by_field_name("function")
                if func:
                    call_name = self._get_node_text(func)
                    if call_name and call_name not in calls:
                        calls.append(call_name)

            for child in n.children:
                visit(child)

        visit(node)
        return calls

    def _calculate_js_complexity(self, node: Any) -> int:
        """Calculate cyclomatic complexity for JS/TS."""
        complexity = 1

        def visit(n: Any):
            nonlocal complexity
            if n.type in (
                "if_statement",
                "while_statement",
                "for_statement",
                "for_in_statement",
                "catch_clause",
                "conditional_expression",
            ):
                complexity += 1
            elif n.type == "binary_expression":
                op_node = n.child_by_field_name("operator")
                if op_node and self._get_node_text(op_node) in ("&&", "||"):
                    complexity += 1

            for child in n.children:
                visit(child)

        visit(node)
        return complexity

    def _extract_go_entities(
        self, root_node: Any, file_path: str, language: str
    ) -> list[CodeEntity]:
        """Extract entities from Go code."""
        entities: list[CodeEntity] = []

        def visit(node: Any):
            if node.type == "function_declaration":
                entity = self._extract_go_function(node, file_path, language)
                if entity:
                    entities.append(entity)

            elif node.type == "method_declaration":
                entity = self._extract_go_method(node, file_path, language)
                if entity:
                    entities.append(entity)

            elif node.type == "type_declaration":
                for child in node.children:
                    if child.type == "type_spec":
                        entity = self._extract_go_type(child, file_path, language)
                        if entity:
                            entities.append(entity)

            elif node.type == "import_declaration":
                for spec in node.children:
                    if spec.type == "import_spec":
                        entity = self._extract_go_import(spec, file_path, language)
                        if entity:
                            entities.append(entity)
                    elif spec.type == "import_spec_list":
                        for child in spec.children:
                            if child.type == "import_spec":
                                entity = self._extract_go_import(child, file_path, language)
                                if entity:
                                    entities.append(entity)

            for child in node.children:
                visit(child)

        visit(root_node)
        return entities

    def _extract_go_function(
        self, node: Any, file_path: str, language: str
    ) -> FunctionEntity | None:
        """Extract a Go function."""
        try:
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            name = self._get_node_text(name_node)
            qualified_name = self.get_qualified_name(name, file_path)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            parameters = self._extract_go_parameters(node)

            # Extract return type
            return_type = None
            result = node.child_by_field_name("result")
            if result:
                return_type = self._get_node_text(result)

            source_code = self._get_node_text(node)
            docstring = self._extract_leading_comment(node)

            # Check if exported (starts with uppercase)
            tags = []
            if name[0].isupper():
                tags.append("exported")

            return FunctionEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.FUNCTION,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                parameters=parameters,
                return_type=return_type,
                calls=self._extract_go_calls(node),
            )

        except Exception as e:
            logger.error(f"Error extracting Go function: {e}")
            return None

    def _extract_go_method(
        self, node: Any, file_path: str, language: str
    ) -> FunctionEntity | None:
        """Extract a Go method (function with receiver)."""
        try:
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            name = self._get_node_text(name_node)

            # Get receiver type
            receiver = node.child_by_field_name("receiver")
            parent_class = None
            if receiver:
                for child in receiver.children:
                    if child.type == "parameter_declaration":
                        type_node = child.child_by_field_name("type")
                        if type_node:
                            parent_class = self._get_node_text(type_node).lstrip("*")

            qualified_name = self.get_qualified_name(name, file_path, parent_class)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            parameters = self._extract_go_parameters(node)

            return_type = None
            result = node.child_by_field_name("result")
            if result:
                return_type = self._get_node_text(result)

            source_code = self._get_node_text(node)
            docstring = self._extract_leading_comment(node)

            tags = ["method"]
            if name[0].isupper():
                tags.append("exported")

            return FunctionEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.METHOD,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                parameters=parameters,
                return_type=return_type,
                is_method=True,
                parent_class=parent_class,
                calls=self._extract_go_calls(node),
            )

        except Exception as e:
            logger.error(f"Error extracting Go method: {e}")
            return None

    def _extract_go_type(
        self, node: Any, file_path: str, language: str
    ) -> ClassEntity | None:
        """Extract a Go type (struct/interface)."""
        try:
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            name = self._get_node_text(name_node)
            qualified_name = self.get_qualified_name(name, file_path)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            # Determine type kind
            type_node = node.child_by_field_name("type")
            is_interface = False
            if type_node and type_node.type == "interface_type":
                is_interface = True

            # Extract properties/fields
            properties: list[Property] = []
            if type_node and type_node.type == "struct_type":
                body = type_node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type == "field_declaration":
                            field_name = ""
                            field_type = ""
                            for c in child.children:
                                if c.type == "field_identifier":
                                    field_name = self._get_node_text(c)
                                elif c.type in ("type_identifier", "pointer_type", "slice_type"):
                                    field_type = self._get_node_text(c)
                            if field_name:
                                properties.append(
                                    Property(name=field_name, type_annotation=field_type)
                                )

            source_code = self._get_node_text(node)
            docstring = self._extract_leading_comment(node)

            tags = []
            if name[0].isupper():
                tags.append("exported")
            if is_interface:
                tags.append("interface")
            else:
                tags.append("struct")

            return ClassEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.INTERFACE if is_interface else CodeEntityType.CLASS,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                properties=properties,
                is_protocol=is_interface,
            )

        except Exception as e:
            logger.error(f"Error extracting Go type: {e}")
            return None

    def _extract_go_import(
        self, node: Any, file_path: str, language: str
    ) -> ImportEntity | None:
        """Extract a Go import statement."""
        try:
            path_node = node.child_by_field_name("path")
            if not path_node:
                return None

            module = self._get_node_text(path_node).strip('"')

            # Check for alias
            name_node = node.child_by_field_name("name")
            alias = self._get_node_text(name_node) if name_node else None

            source_code = self._get_node_text(node)

            name = f"import {module}"
            qualified_name = f"import:{module}"
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            aliases = {}
            if alias:
                aliases[module] = alias

            return ImportEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.IMPORT,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                module=module,
                names=[module.split("/")[-1]],
                aliases=aliases,
            )

        except Exception as e:
            logger.error(f"Error extracting Go import: {e}")
            return None

    def _extract_go_parameters(self, node: Any) -> list[Parameter]:
        """Extract parameters from a Go function."""
        parameters: list[Parameter] = []

        params_node = node.child_by_field_name("parameters")
        if not params_node:
            return parameters

        for child in params_node.children:
            if child.type == "parameter_declaration":
                names: list[str] = []
                type_annotation = None

                for c in child.children:
                    if c.type == "identifier":
                        names.append(self._get_node_text(c))
                    elif c.type in ("type_identifier", "pointer_type", "slice_type", "map_type"):
                        type_annotation = self._get_node_text(c)

                for name in names:
                    parameters.append(
                        Parameter(name=name, type_annotation=type_annotation)
                    )

        return parameters

    def _extract_go_calls(self, node: Any) -> list[str]:
        """Extract function calls from a Go node."""
        calls: list[str] = []

        def visit(n: Any):
            if n.type == "call_expression":
                func = n.child_by_field_name("function")
                if func:
                    call_name = self._get_node_text(func)
                    if call_name and call_name not in calls:
                        calls.append(call_name)

            for child in n.children:
                visit(child)

        visit(node)
        return calls

    def _extract_rust_entities(
        self, root_node: Any, file_path: str, language: str
    ) -> list[CodeEntity]:
        """Extract entities from Rust code."""
        entities: list[CodeEntity] = []

        def visit(node: Any, parent: str | None = None):
            if node.type == "function_item":
                entity = self._extract_rust_function(node, file_path, language, parent)
                if entity:
                    entities.append(entity)

            elif node.type in ("struct_item", "enum_item"):
                entity = self._extract_rust_type(node, file_path, language)
                if entity:
                    entities.append(entity)

            elif node.type == "impl_item":
                # Get the type being implemented
                impl_type = None
                for child in node.children:
                    if child.type == "type_identifier":
                        impl_type = self._get_node_text(child)
                        break

                # Visit methods
                for child in node.children:
                    if child.type == "declaration_list":
                        for item in child.children:
                            visit(item, impl_type)

            elif node.type == "use_declaration":
                entity = self._extract_rust_use(node, file_path, language)
                if entity:
                    entities.append(entity)

            else:
                for child in node.children:
                    visit(child, parent)

        visit(root_node)
        return entities

    def _extract_rust_function(
        self, node: Any, file_path: str, language: str, parent: str | None = None
    ) -> FunctionEntity | None:
        """Extract a Rust function."""
        try:
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            name = self._get_node_text(name_node)
            is_method = parent is not None

            qualified_name = self.get_qualified_name(name, file_path, parent)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            # Check visibility
            is_pub = any(child.type == "visibility_modifier" for child in node.children)

            # Check for async
            is_async = any(child.type == "async" for child in node.children)

            # Extract parameters
            parameters = self._extract_rust_parameters(node)

            # Extract return type
            return_type = None
            return_node = node.child_by_field_name("return_type")
            if return_node:
                return_type = self._get_node_text(return_node).lstrip("-> ").strip()

            source_code = self._get_node_text(node)
            docstring = self._extract_leading_comment(node)

            tags = []
            if is_pub:
                tags.append("pub")
            if is_async:
                tags.append("async")
            if is_method:
                tags.append("method")

            return FunctionEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.METHOD if is_method else CodeEntityType.FUNCTION,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                parameters=parameters,
                return_type=return_type,
                is_async=is_async,
                is_method=is_method,
                parent_class=parent,
            )

        except Exception as e:
            logger.error(f"Error extracting Rust function: {e}")
            return None

    def _extract_rust_type(
        self, node: Any, file_path: str, language: str
    ) -> ClassEntity | None:
        """Extract a Rust struct or enum."""
        try:
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            name = self._get_node_text(name_node)
            qualified_name = self.get_qualified_name(name, file_path)
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            is_enum = node.type == "enum_item"
            is_pub = any(child.type == "visibility_modifier" for child in node.children)

            # Extract fields for structs
            properties: list[Property] = []
            body = node.child_by_field_name("body")
            if body and node.type == "struct_item":
                for child in body.children:
                    if child.type == "field_declaration":
                        field_name = ""
                        field_type = ""
                        for c in child.children:
                            if c.type == "field_identifier":
                                field_name = self._get_node_text(c)
                            elif c.type == "type_identifier":
                                field_type = self._get_node_text(c)
                        if field_name:
                            properties.append(
                                Property(name=field_name, type_annotation=field_type)
                            )

            source_code = self._get_node_text(node)
            docstring = self._extract_leading_comment(node)

            tags = []
            if is_pub:
                tags.append("pub")
            if is_enum:
                tags.append("enum")
            else:
                tags.append("struct")

            return ClassEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.ENUM if is_enum else CodeEntityType.CLASS,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                docstring=docstring,
                tags=tags,
                properties=properties,
            )

        except Exception as e:
            logger.error(f"Error extracting Rust type: {e}")
            return None

    def _extract_rust_use(
        self, node: Any, file_path: str, language: str
    ) -> ImportEntity | None:
        """Extract a Rust use statement."""
        try:
            source_code = self._get_node_text(node)

            # Simple parsing of use statement
            match = re.search(r"use\s+([^;]+)", source_code)
            if not match:
                return None

            path = match.group(1).strip()
            module = path.split("::")[0]

            name = f"use {path}"
            qualified_name = f"use:{path}"
            entity_id = CodeEntity.generate_id(file_path, node.start_point[0] + 1, qualified_name)

            return ImportEntity(
                id=entity_id,
                name=name,
                qualified_name=qualified_name,
                entity_type=CodeEntityType.IMPORT,
                file_path=file_path,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                language=language,
                source_code=source_code,
                module=module,
                names=[path],
            )

        except Exception as e:
            logger.error(f"Error extracting Rust use: {e}")
            return None

    def _extract_rust_parameters(self, node: Any) -> list[Parameter]:
        """Extract parameters from a Rust function."""
        parameters: list[Parameter] = []

        params_node = node.child_by_field_name("parameters")
        if not params_node:
            return parameters

        for child in params_node.children:
            if child.type == "parameter":
                name = ""
                type_annotation = None

                pattern = child.child_by_field_name("pattern")
                if pattern:
                    name = self._get_node_text(pattern)

                type_node = child.child_by_field_name("type")
                if type_node:
                    type_annotation = self._get_node_text(type_node)

                if name:
                    parameters.append(
                        Parameter(name=name, type_annotation=type_annotation)
                    )

            elif child.type == "self_parameter":
                parameters.append(Parameter(name="self"))

        return parameters

    def _extract_generic_entities(
        self, root_node: Any, file_path: str, language: str
    ) -> list[CodeEntity]:
        """Generic entity extraction for unsupported languages."""
        entities: list[CodeEntity] = []

        # Look for common patterns across languages
        def visit(node: Any):
            # Function-like nodes
            if "function" in node.type or "method" in node.type:
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self._get_node_text(name_node)
                    qualified_name = self.get_qualified_name(name, file_path)
                    entity_id = CodeEntity.generate_id(
                        file_path, node.start_point[0] + 1, qualified_name
                    )

                    entities.append(
                        FunctionEntity(
                            id=entity_id,
                            name=name,
                            qualified_name=qualified_name,
                            entity_type=CodeEntityType.FUNCTION,
                            file_path=file_path,
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            language=language,
                            source_code=self._get_node_text(node),
                        )
                    )

            # Class-like nodes
            elif "class" in node.type or "struct" in node.type:
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = self._get_node_text(name_node)
                    qualified_name = self.get_qualified_name(name, file_path)
                    entity_id = CodeEntity.generate_id(
                        file_path, node.start_point[0] + 1, qualified_name
                    )

                    entities.append(
                        ClassEntity(
                            id=entity_id,
                            name=name,
                            qualified_name=qualified_name,
                            entity_type=CodeEntityType.CLASS,
                            file_path=file_path,
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            language=language,
                            source_code=self._get_node_text(node),
                        )
                    )

            for child in node.children:
                visit(child)

        visit(root_node)
        return entities

    def _get_node_text(self, node: Any) -> str:
        """Get the text content of a node."""
        if node is None:
            return ""
        start = node.start_byte
        end = node.end_byte
        return self._source_bytes[start:end].decode("utf-8")

    def _extract_leading_comment(self, node: Any) -> str | None:
        """Extract comment before a node as docstring."""
        # Look at previous sibling
        if node.prev_sibling and node.prev_sibling.type == "comment":
            text = self._get_node_text(node.prev_sibling)
            # Clean up comment markers
            text = re.sub(r"^//\s*", "", text, flags=re.MULTILINE)
            text = re.sub(r"^/\*\s*|\s*\*/$", "", text)
            text = re.sub(r"^\s*\*\s?", "", text, flags=re.MULTILINE)
            return text.strip() or None
        return None

    def _extract_jsdoc(self, node: Any) -> str | None:
        """Extract JSDoc comment for a node."""
        # Look for comment node before this one
        if node.prev_sibling and node.prev_sibling.type == "comment":
            text = self._get_node_text(node.prev_sibling)
            if text.startswith("/**"):
                # Parse JSDoc
                text = re.sub(r"^/\*\*\s*|\s*\*/$", "", text)
                text = re.sub(r"^\s*\*\s?", "", text, flags=re.MULTILINE)
                return text.strip() or None
        return None
