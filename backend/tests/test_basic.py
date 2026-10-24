"""Test basic application health."""
import pytest


def test_import_main():
    """Test that main module can be imported."""
    from app import main
    assert main.app is not None


def test_import_settings():
    """Test that settings can be imported."""
    from app.settings import settings
    assert settings is not None


def test_import_db():
    """Test that db module can be imported."""
    from app import db
    assert db.engine is not None
