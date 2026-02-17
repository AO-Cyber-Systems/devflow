"""
Data models for code entities.

These models represent parsed code structures from various languages,
providing a unified representation for indexing and search.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import hashlib


class CodeEntityType(str, Enum):
    """Type of code entity."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    MODULE = "module"
    VARIABLE = "variable"
    CONSTANT = "constant"
    TYPE_ALIAS = "type_alias"
    INTERFACE = "interface"
    ENUM = "enum"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            CodeEntityType.FUNCTION: "Function",
            CodeEntityType.CLASS: "Class",
            CodeEntityType.METHOD: "Method",
            CodeEntityType.IMPORT: "Import",
            CodeEntityType.MODULE: "Module",
            CodeEntityType.VARIABLE: "Variable",
            CodeEntityType.CONSTANT: "Constant",
            CodeEntityType.TYPE_ALIAS: "Type Alias",
            CodeEntityType.INTERFACE: "Interface",
            CodeEntityType.ENUM: "Enum",
        }
        return names.get(self, self.value.title())

    @property
    def icon(self) -> str:
        """Icon identifier for UI."""
        icons = {
            CodeEntityType.FUNCTION: "function",
            CodeEntityType.CLASS: "cube",
            CodeEntityType.METHOD: "function.fill",
            CodeEntityType.IMPORT: "arrow.down.doc",
            CodeEntityType.MODULE: "folder",
            CodeEntityType.VARIABLE: "character",
            CodeEntityType.CONSTANT: "k.circle",
            CodeEntityType.TYPE_ALIAS: "t.circle",
            CodeEntityType.INTERFACE: "rectangle.3.offgrid",
            CodeEntityType.ENUM: "list.bullet",
        }
        return icons.get(self, "doc")


class CodeRelationType(str, Enum):
    """Types of relationships between code entities."""

    # Standard relationships
    IMPORTS = "imports"
    CALLS = "calls"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    USES = "uses"
    DEFINES = "defines"

    # Code-specific relationships
    CALLED_BY = "called_by"
    OVERRIDES = "overrides"
    CONTAINS = "contains"
    TYPED_AS = "typed_as"
    DECORATES = "decorates"
    RETURNS = "returns"
    INSTANTIATES = "instantiates"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return self.value.replace("_", " ").title()

    @property
    def inverse(self) -> "CodeRelationType | None":
        """Get the inverse relationship type if applicable."""
        inverses = {
            CodeRelationType.CALLS: CodeRelationType.CALLED_BY,
            CodeRelationType.CALLED_BY: CodeRelationType.CALLS,
            CodeRelationType.EXTENDS: None,  # No inverse
            CodeRelationType.IMPORTS: None,
            CodeRelationType.CONTAINS: None,
        }
        return inverses.get(self)


@dataclass
class Parameter:
    """Function or method parameter."""

    name: str
    type_annotation: str | None = None
    default_value: str | None = None
    is_variadic: bool = False  # *args
    is_keyword: bool = False  # **kwargs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type_annotation": self.type_annotation,
            "default_value": self.default_value,
            "is_variadic": self.is_variadic,
            "is_keyword": self.is_keyword,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Parameter":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type_annotation=data.get("type_annotation"),
            default_value=data.get("default_value"),
            is_variadic=data.get("is_variadic", False),
            is_keyword=data.get("is_keyword", False),
        )

    def __str__(self) -> str:
        """String representation."""
        prefix = ""
        if self.is_variadic:
            prefix = "*"
        elif self.is_keyword:
            prefix = "**"

        result = f"{prefix}{self.name}"
        if self.type_annotation:
            result += f": {self.type_annotation}"
        if self.default_value:
            result += f" = {self.default_value}"
        return result


@dataclass
class Property:
    """Class property or attribute."""

    name: str
    type_annotation: str | None = None
    default_value: str | None = None
    is_class_var: bool = False
    is_readonly: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type_annotation": self.type_annotation,
            "default_value": self.default_value,
            "is_class_var": self.is_class_var,
            "is_readonly": self.is_readonly,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Property":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type_annotation=data.get("type_annotation"),
            default_value=data.get("default_value"),
            is_class_var=data.get("is_class_var", False),
            is_readonly=data.get("is_readonly", False),
        )


@dataclass
class CodeEntity:
    """Base class for all code entities."""

    id: str
    name: str
    qualified_name: str
    entity_type: CodeEntityType
    file_path: str
    line_start: int
    line_end: int
    language: str
    source_code: str
    docstring: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def generate_id(cls, file_path: str, line: int, name: str) -> str:
        """Generate a unique ID for the entity."""
        content = f"{file_path}:{line}:{name}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self, include_source: bool = True) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "entity_type": self.entity_type.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "language": self.language,
            "docstring": self.docstring,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_source:
            result["source_code"] = self.source_code
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeEntity":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            qualified_name=data["qualified_name"],
            entity_type=CodeEntityType(data["entity_type"]),
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            language=data["language"],
            source_code=data.get("source_code", ""),
            docstring=data.get("docstring"),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
        )


@dataclass
class FunctionEntity(CodeEntity):
    """Represents a function or method."""

    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False
    is_method: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    parent_class: str | None = None
    calls: list[str] = field(default_factory=list)
    complexity: int = 1

    def __post_init__(self):
        """Set entity type."""
        if self.entity_type == CodeEntityType.FUNCTION and self.is_method:
            self.entity_type = CodeEntityType.METHOD

    @property
    def signature(self) -> str:
        """Get the function signature."""
        params = ", ".join(str(p) for p in self.parameters)
        prefix = ""
        if self.is_async:
            prefix = "async "
        result = f"{prefix}def {self.name}({params})"
        if self.return_type:
            result += f" -> {self.return_type}"
        return result

    def to_dict(self, include_source: bool = True) -> dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict(include_source)
        result.update(
            {
                "parameters": [p.to_dict() for p in self.parameters],
                "return_type": self.return_type,
                "decorators": self.decorators,
                "is_async": self.is_async,
                "is_generator": self.is_generator,
                "is_method": self.is_method,
                "is_static": self.is_static,
                "is_classmethod": self.is_classmethod,
                "is_property": self.is_property,
                "parent_class": self.parent_class,
                "calls": self.calls,
                "complexity": self.complexity,
                "signature": self.signature,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FunctionEntity":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            qualified_name=data["qualified_name"],
            entity_type=CodeEntityType(data["entity_type"]),
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            language=data["language"],
            source_code=data.get("source_code", ""),
            docstring=data.get("docstring"),
            tags=data.get("tags", []),
            parameters=[Parameter.from_dict(p) for p in data.get("parameters", [])],
            return_type=data.get("return_type"),
            decorators=data.get("decorators", []),
            is_async=data.get("is_async", False),
            is_generator=data.get("is_generator", False),
            is_method=data.get("is_method", False),
            is_static=data.get("is_static", False),
            is_classmethod=data.get("is_classmethod", False),
            is_property=data.get("is_property", False),
            parent_class=data.get("parent_class"),
            calls=data.get("calls", []),
            complexity=data.get("complexity", 1),
        )


@dataclass
class ClassEntity(CodeEntity):
    """Represents a class or interface."""

    base_classes: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    is_abstract: bool = False
    is_dataclass: bool = False
    is_protocol: bool = False
    metaclass: str | None = None

    def to_dict(self, include_source: bool = True) -> dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict(include_source)
        result.update(
            {
                "base_classes": self.base_classes,
                "decorators": self.decorators,
                "methods": self.methods,
                "properties": [p.to_dict() for p in self.properties],
                "is_abstract": self.is_abstract,
                "is_dataclass": self.is_dataclass,
                "is_protocol": self.is_protocol,
                "metaclass": self.metaclass,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassEntity":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            qualified_name=data["qualified_name"],
            entity_type=CodeEntityType(data["entity_type"]),
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            language=data["language"],
            source_code=data.get("source_code", ""),
            docstring=data.get("docstring"),
            tags=data.get("tags", []),
            base_classes=data.get("base_classes", []),
            decorators=data.get("decorators", []),
            methods=data.get("methods", []),
            properties=[Property.from_dict(p) for p in data.get("properties", [])],
            is_abstract=data.get("is_abstract", False),
            is_dataclass=data.get("is_dataclass", False),
            is_protocol=data.get("is_protocol", False),
            metaclass=data.get("metaclass"),
        )


@dataclass
class ImportEntity(CodeEntity):
    """Represents an import statement."""

    module: str = ""
    names: list[str] = field(default_factory=list)
    aliases: dict[str, str] = field(default_factory=dict)
    is_relative: bool = False
    level: int = 0  # Number of dots in relative import

    def to_dict(self, include_source: bool = True) -> dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict(include_source)
        result.update(
            {
                "module": self.module,
                "names": self.names,
                "aliases": self.aliases,
                "is_relative": self.is_relative,
                "level": self.level,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportEntity":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            qualified_name=data["qualified_name"],
            entity_type=CodeEntityType(data["entity_type"]),
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            language=data["language"],
            source_code=data.get("source_code", ""),
            docstring=data.get("docstring"),
            tags=data.get("tags", []),
            module=data.get("module", ""),
            names=data.get("names", []),
            aliases=data.get("aliases", {}),
            is_relative=data.get("is_relative", False),
            level=data.get("level", 0),
        )


@dataclass
class ModuleEntity(CodeEntity):
    """Represents a module (file-level entity)."""

    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    is_package: bool = False
    is_init: bool = False

    def to_dict(self, include_source: bool = True) -> dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict(include_source)
        result.update(
            {
                "imports": self.imports,
                "exports": self.exports,
                "classes": self.classes,
                "functions": self.functions,
                "constants": self.constants,
                "is_package": self.is_package,
                "is_init": self.is_init,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModuleEntity":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            qualified_name=data["qualified_name"],
            entity_type=CodeEntityType(data["entity_type"]),
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            language=data["language"],
            source_code=data.get("source_code", ""),
            docstring=data.get("docstring"),
            tags=data.get("tags", []),
            imports=data.get("imports", []),
            exports=data.get("exports", []),
            classes=data.get("classes", []),
            functions=data.get("functions", []),
            constants=data.get("constants", []),
            is_package=data.get("is_package", False),
            is_init=data.get("is_init", False),
        )


# Type alias for any code entity
AnyCodeEntity = CodeEntity | FunctionEntity | ClassEntity | ImportEntity | ModuleEntity
