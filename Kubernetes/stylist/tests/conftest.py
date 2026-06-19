import pytest
import sys
from unittest.mock import MagicMock

# Mock console module VERY EARLY to prevent hanging on Textual imports
# This must happen before any test collection that might import commands
mock_console = MagicMock()
mock_database_editor = MagicMock()
mock_console.database_editor = mock_database_editor
sys.modules['console'] = mock_console
sys.modules['console.database_editor'] = mock_database_editor

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)
