"""Shared test utilities for stylist tests."""
import sys
import types
import sqlite3


class MockSqliteConnection:
    """Mock SQLite connection that ignores encryption pragmas."""
    def __init__(self, path):
        self._conn = sqlite3.connect(path)

    def execute(self, sql, *args, **kwargs):
        if sql.strip().lower().startswith("pragma key"):
            return None
        return self._conn.execute(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _create_cipher_stub(module_name: str):
    """Create a stub module for sqlcipher-like packages."""
    if module_name not in sys.modules:
        module = types.ModuleType(module_name)

        def connect(path):
            return MockSqliteConnection(path)

        module.dbapi2 = types.SimpleNamespace(connect=connect, Connection=sqlite3.Connection)
        sys.modules[module_name] = module


def ensure_pysqlcipher3_stub():
    """Provide a stub for pysqlcipher3 if it's not installed."""
    _create_cipher_stub('pysqlcipher3')


def ensure_sqlcipher3_stub():
    """Provide a stub for sqlcipher3 if it's not installed."""
    _create_cipher_stub('sqlcipher3')
