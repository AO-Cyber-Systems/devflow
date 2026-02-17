"""Tests for the Python parser."""

import pytest
import tempfile
from pathlib import Path

from devflow.code.parsers.python_parser import PythonParser
from devflow.code.models import CodeEntityType, FunctionEntity, ClassEntity


class TestPythonParser:
    """Tests for PythonParser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return PythonParser()

    def test_supported_languages(self, parser):
        """Test that Python is listed as supported."""
        assert "python" in parser.SUPPORTED_LANGUAGES

    def test_supported_extensions(self, parser):
        """Test supported file extensions."""
        assert ".py" in parser.SUPPORTED_EXTENSIONS
        assert ".pyi" in parser.SUPPORTED_EXTENSIONS

    def test_can_parse_python_files(self, parser):
        """Test can_parse for Python files."""
        assert parser.can_parse("test.py")
        assert parser.can_parse("test.pyi")
        assert parser.can_parse(Path("test.py"))
        assert not parser.can_parse("test.js")
        assert not parser.can_parse("test.txt")

    def test_parse_simple_function(self, parser):
        """Test parsing a simple function."""
        source = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        entities = parser.parse_source(source, "test.py", "python")

        # Should have module + function
        assert len(entities) >= 2

        # Find the function
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
        assert len(funcs) == 1

        func = funcs[0]
        assert isinstance(func, FunctionEntity)
        assert func.name == "hello"
        assert func.docstring == "Say hello."
        assert func.return_type == "str"
        assert len(func.parameters) == 1
        assert func.parameters[0].name == "name"
        assert func.parameters[0].type_annotation == "str"

    def test_parse_async_function(self, parser):
        """Test parsing an async function."""
        source = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    pass
'''
        entities = parser.parse_source(source, "test.py", "python")
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
        assert len(funcs) == 1

        func = funcs[0]
        assert func.is_async
        assert "async" in func.tags

    def test_parse_generator_function(self, parser):
        """Test parsing a generator function."""
        source = '''
def generate_numbers(n: int):
    """Generate numbers."""
    for i in range(n):
        yield i
'''
        entities = parser.parse_source(source, "test.py", "python")
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
        assert len(funcs) == 1

        func = funcs[0]
        assert func.is_generator
        assert "generator" in func.tags

    def test_parse_decorated_function(self, parser):
        """Test parsing a decorated function."""
        source = '''
@staticmethod
@cache
def compute(x: int) -> int:
    return x * 2
'''
        entities = parser.parse_source(source, "test.py", "python")
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
        assert len(funcs) == 1

        func = funcs[0]
        assert "staticmethod" in func.decorators
        assert "cache" in func.decorators
        assert func.is_static

    def test_parse_simple_class(self, parser):
        """Test parsing a simple class."""
        source = '''
class MyClass:
    """A simple class."""

    def __init__(self, value: int):
        self.value = value

    def get_value(self) -> int:
        return self.value
'''
        entities = parser.parse_source(source, "test.py", "python")

        classes = [e for e in entities if e.entity_type == CodeEntityType.CLASS]
        assert len(classes) == 1

        cls = classes[0]
        assert isinstance(cls, ClassEntity)
        assert cls.name == "MyClass"
        assert cls.docstring == "A simple class."
        assert len(cls.methods) == 2

        methods = [e for e in entities if e.entity_type == CodeEntityType.METHOD]
        assert len(methods) == 2
        method_names = [m.name for m in methods]
        assert "__init__" in method_names
        assert "get_value" in method_names

    def test_parse_class_with_inheritance(self, parser):
        """Test parsing a class with inheritance."""
        source = '''
class Child(Parent, Mixin):
    """Child class."""
    pass
'''
        entities = parser.parse_source(source, "test.py", "python")
        classes = [e for e in entities if e.entity_type == CodeEntityType.CLASS]
        assert len(classes) == 1

        cls = classes[0]
        assert "Parent" in cls.base_classes
        assert "Mixin" in cls.base_classes

    def test_parse_dataclass(self, parser):
        """Test parsing a dataclass."""
        source = '''
from dataclasses import dataclass

@dataclass
class Point:
    """A point in 2D space."""
    x: int
    y: int
    label: str = "default"
'''
        entities = parser.parse_source(source, "test.py", "python")
        classes = [e for e in entities if e.entity_type == CodeEntityType.CLASS]
        assert len(classes) == 1

        cls = classes[0]
        assert cls.is_dataclass
        assert "dataclass" in cls.tags
        assert len(cls.properties) == 3

        prop_names = [p.name for p in cls.properties]
        assert "x" in prop_names
        assert "y" in prop_names
        assert "label" in prop_names

    def test_parse_abstract_class(self, parser):
        """Test parsing an abstract class."""
        source = '''
from abc import ABC, abstractmethod

class Base(ABC):
    """Abstract base class."""

    @abstractmethod
    def process(self) -> None:
        pass
'''
        entities = parser.parse_source(source, "test.py", "python")
        classes = [e for e in entities if e.entity_type == CodeEntityType.CLASS]
        assert len(classes) == 1

        cls = classes[0]
        assert cls.is_abstract
        assert "abstract" in cls.tags

    def test_parse_imports(self, parser):
        """Test parsing import statements."""
        source = '''
import os
import sys
from typing import List, Dict
from collections import defaultdict as dd
from . import utils
from ..core import base
'''
        entities = parser.parse_source(source, "test.py", "python")
        imports = [e for e in entities if e.entity_type == CodeEntityType.IMPORT]

        # Should have multiple imports
        assert len(imports) >= 4

        # Find specific imports
        os_import = next((i for i in imports if "os" in i.names), None)
        assert os_import is not None

        typing_import = next((i for i in imports if i.module == "typing"), None)
        assert typing_import is not None
        assert "List" in typing_import.names
        assert "Dict" in typing_import.names

        dd_import = next((i for i in imports if "defaultdict" in i.names), None)
        assert dd_import is not None
        assert dd_import.aliases.get("defaultdict") == "dd"

        relative_import = next((i for i in imports if i.is_relative and i.level == 1), None)
        assert relative_import is not None

    def test_parse_function_with_args_kwargs(self, parser):
        """Test parsing function with *args and **kwargs."""
        source = '''
def flexible(*args, kwonly: int = 0, **kwargs) -> None:
    pass
'''
        entities = parser.parse_source(source, "test.py", "python")
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
        assert len(funcs) == 1

        func = funcs[0]
        param_names = [p.name for p in func.parameters]
        assert "args" in param_names
        assert "kwonly" in param_names
        assert "kwargs" in param_names

        args_param = next(p for p in func.parameters if p.name == "args")
        assert args_param.is_variadic

        kwargs_param = next(p for p in func.parameters if p.name == "kwargs")
        assert kwargs_param.is_keyword

    def test_parse_function_calls(self, parser):
        """Test extraction of function calls."""
        source = '''
def process():
    helper()
    result = transform(data)
    obj.method()
    return result
'''
        entities = parser.parse_source(source, "test.py", "python")
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
        assert len(funcs) == 1

        func = funcs[0]
        assert "helper" in func.calls
        assert "transform" in func.calls
        assert "obj.method" in func.calls

    def test_parse_complexity(self, parser):
        """Test complexity calculation."""
        source = '''
def simple():
    return 1

def complex_func(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
    else:
        while x < 0:
            x += 1
    return x
'''
        entities = parser.parse_source(source, "test.py", "python")
        funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]

        simple = next(f for f in funcs if f.name == "simple")
        complex_f = next(f for f in funcs if f.name == "complex_func")

        assert simple.complexity == 1
        assert complex_f.complexity > simple.complexity

    def test_parse_module_docstring(self, parser):
        """Test module docstring extraction."""
        source = '''"""
This is the module docstring.

It has multiple lines.
"""

def func():
    pass
'''
        entities = parser.parse_source(source, "test.py", "python")
        modules = [e for e in entities if e.entity_type == CodeEntityType.MODULE]
        assert len(modules) == 1

        mod = modules[0]
        assert "module docstring" in mod.docstring

    def test_parse_class_properties(self, parser):
        """Test class property extraction."""
        source = '''
class Config:
    DEBUG: bool = False
    MAX_SIZE: int = 100
    name: str
'''
        entities = parser.parse_source(source, "test.py", "python")
        classes = [e for e in entities if e.entity_type == CodeEntityType.CLASS]
        assert len(classes) == 1

        cls = classes[0]
        prop_names = [p.name for p in cls.properties]
        assert "DEBUG" in prop_names
        assert "MAX_SIZE" in prop_names
        assert "name" in prop_names

    def test_parse_file(self, parser):
        """Test parsing a real file."""
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('''
"""Test module."""

def test_func(x: int) -> int:
    """Test function."""
    return x * 2

class TestClass:
    """Test class."""
    value: int = 0
''')
            f.flush()
            temp_path = f.name

        try:
            entities = parser.parse_file(temp_path)
            assert len(entities) >= 3  # module, function, class

            funcs = [e for e in entities if e.entity_type == CodeEntityType.FUNCTION]
            assert len(funcs) == 1
            assert funcs[0].file_path == temp_path

        finally:
            Path(temp_path).unlink()

    def test_parse_invalid_syntax(self, parser):
        """Test parsing invalid Python code."""
        source = '''
def broken(
    # Missing closing paren
'''
        entities = parser.parse_source(source, "test.py", "python")
        # Should return empty list on syntax error
        assert entities == []

    def test_parse_nonexistent_file(self, parser):
        """Test parsing a nonexistent file."""
        entities = parser.parse_file("/nonexistent/path/file.py")
        assert entities == []
