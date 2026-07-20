import pytest
from pathlib import Path
from EuPs import _Filter, PackageFinder

def test_filter_matching():
    """Test that the glob filtering logic works correctly."""
    f = _Filter("tests*", "temp.*", "venv")
    assert f("tests") is True
    assert f("tests.unit") is True
    assert f("temp.data") is True
    assert f("myapp") is False

def test_package_discovery(tmp_path):
    """Test that PackageFinder correctly identifies directories with __init__.py"""
    # Setup a dummy project structure
    pkg = tmp_path / "mypackage"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    
    no_pkg = tmp_path / "docs"
    no_pkg.mkdir()
    (no_pkg / "index.rst").write_text("")

    # Find packages
    include = _Filter("*")
    exclude = _Filter()
    found = list(PackageFinder._find_iter(tmp_path, exclude, include))
    
    assert "mypackage" in found
    assert "docs" not in found