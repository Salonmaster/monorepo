import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
import asyncio

# Setup path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STYLIST_DIR = ROOT / "stylist"
if str(STYLIST_DIR) not in sys.path:
    sys.path.insert(0, str(STYLIST_DIR))

from stylist.tests.test_utils import ensure_sqlcipher3_stub
ensure_sqlcipher3_stub()

from typer.testing import CliRunner
import core
from stylist.models import vault_keys, vault_secret

# Ensure Backbone is initialized
_ = core.Backbone()

# Import commands after setup
from stylist.commands.vault import status, list_secrets, read_secret, write_secret, unseal, init
# Also import the modules for patching (these are the actual module objects)
import stylist.commands.vault.status as status_module
import stylist.commands.vault.list_secrets as list_secrets_module
import stylist.commands.vault.read_secret as read_secret_module
import stylist.commands.vault.write_secret as write_secret_module
import stylist.commands.vault.unseal as unseal_module
import stylist.commands.vault.init as init_module

runner = CliRunner()


# Helper class for mocking typer.Exit
class MockExit(SystemExit):
    """Mock typer.Exit that accepts code parameter."""
    def __init__(self, code=0):
        super().__init__(code)


# Helper function for creating port_forward_vault mock
def create_port_forward_mock():
    """Create a mock port_forward_vault context manager."""
    from contextlib import contextmanager

    @contextmanager
    def mock_port_forward(namespace=None, pod_name=None):
        yield "http://localhost:8200"

    return mock_port_forward


@pytest.fixture
def mock_context(monkeypatch):
    """Mock the core.Backbone context."""
    # Get or create the Backbone instance
    backbone = core.Backbone()

    # Ensure context exists
    if backbone.context is None:
        from core.context import Context
        backbone.context = Context()

    # Set vault-specific context attributes
    backbone.context.vault_namespace = "vault"
    backbone.context.vault_pod_name = "vault-0"

    return backbone.context


@pytest.fixture
def mock_vault_helper(monkeypatch):
    """Mock vault helper functions."""
    import sys
    mock_helper = MagicMock()
    # Patch the actual vault helper module that all commands import from
    monkeypatch.setattr("stylist.helpers.vault", mock_helper)
    # Also patch the imported reference in command modules using sys.modules
    # to get the actual module objects
    module_paths = [
        "stylist.commands.vault.read_secret",
        "stylist.commands.vault.write_secret",
        "stylist.commands.vault.list_secrets",
        "stylist.commands.vault.unseal",
        "stylist.commands.vault.init",
        "stylist.commands.vault.status",
    ]
    for module_path in module_paths:
        if module_path in sys.modules:
            module = sys.modules[module_path]
            if hasattr(module, 'vault_helper'):
                monkeypatch.setattr(module, "vault_helper", mock_helper)
    return mock_helper


class TestVaultStatus:
    """Tests for vault status command."""

    @pytest.mark.asyncio
    async def test_status_success(self, mock_context, mock_vault_helper):
        """Test successful vault status check."""
        mock_vault_helper.check_vault_connection = AsyncMock(return_value=True)

        with patch("stylist.commands.vault.status.asyncio.run") as mock_run:
            mock_run.return_value = True

            # Mock typer to capture output
            with patch("stylist.commands.vault.status.typer") as mock_typer:
                status()

                # Verify vault connection was checked
                mock_run.assert_called_once()
                mock_typer.secho.assert_any_call(
                    "🔍 Checking Vault status...",
                    fg=mock_typer.colors.BRIGHT_BLUE
                )

    @pytest.mark.asyncio
    async def test_status_failure(self, mock_context, mock_vault_helper):
        """Test vault status check when vault is not accessible."""
        mock_vault_helper.check_vault_connection = AsyncMock(return_value=False)

        with patch("stylist.commands.vault.status.asyncio.run") as mock_run:
            mock_run.return_value = False

            with patch("stylist.commands.vault.status.typer") as mock_typer:
                mock_typer.Exit = SystemExit

                try:
                    status()
                    assert False, "Should have raised SystemExit"
                except SystemExit:
                    pass

                mock_typer.secho.assert_any_call(
                    "❌ Vault is not accessible",
                    fg=mock_typer.colors.RED
                )


class TestVaultListSecrets:
    """Tests for vault list command."""

    def test_list_secrets_success(self, mock_context, mock_vault_helper, tmp_path):
        """Test successful listing of secrets."""
        # Mock secrets
        mock_secrets = [
            vault_secret.VaultSecret(
                namespace="database-system",
                name="cluster-credentials",
                key="password",
                value="secret123"
            ),
            vault_secret.VaultSecret(
                namespace="database-system",
                name="cluster-credentials",
                key="username",
                value="admin"
            ),
        ]

        mock_vault_helper.read_secrets = MagicMock(return_value=mock_secrets)
        # Create a proper context manager mock using contextlib
        from contextlib import contextmanager

        @contextmanager
        def mock_port_forward(namespace=None, pod_name=None):
            yield "http://localhost:8200"

        mock_vault_helper.port_forward_vault = mock_port_forward

        # Mock database helper
        with patch("stylist.helpers.database") as mock_db:
            with patch("stylist.helpers.remote_db") as mock_remote_db:
                mock_remote_db.prepare_secrets_db.return_value = (str(tmp_path / "test.db"), None)
                mock_db.get_credentials.return_value = [
                    MagicMock(name="Vault Root Token", password="test-token")
                ]

                with patch("stylist.commands.vault.list_secrets.typer") as mock_typer:
                    # Create a proper Exit exception that accepts code parameter
                    class MockExit(SystemExit):
                        def __init__(self, code=0):
                            super().__init__(code)
                    mock_typer.Exit = MockExit
                    # Also patch vault_helper in the module where it's used
                    with patch("stylist.commands.vault.list_secrets.vault_helper", mock_vault_helper):
                        list_secrets(
                            secrets_db=str(tmp_path / "test.db"),
                            root_token="test-token"
                        )

                        mock_vault_helper.read_secrets.assert_called_once()
                        mock_typer.secho.assert_any_call(
                            "📋 Listing secrets from Vault...",
                            fg=mock_typer.colors.BRIGHT_BLUE
                        )

    def test_list_secrets_empty(self, mock_context, mock_vault_helper):
        """Test listing when no secrets are found."""
        mock_vault_helper.read_secrets = MagicMock(return_value=[])
        mock_vault_helper.port_forward_vault = MagicMock()
        mock_vault_helper.port_forward_vault.return_value.__enter__ = MagicMock(return_value="http://localhost:8200")
        mock_vault_helper.port_forward_vault.return_value.__exit__ = MagicMock(return_value=None)

        with patch("stylist.commands.vault.list_secrets.typer") as mock_typer:
            list_secrets(root_token="test-token")

            mock_typer.secho.assert_any_call(
                "📭 No secrets found",
                fg=mock_typer.colors.YELLOW
            )


class TestVaultReadSecret:
    """Tests for vault read command."""

    def test_read_secret_success(self, mock_context, mock_vault_helper):
        """Test successful reading of a secret."""
        mock_secrets = [
            vault_secret.VaultSecret(
                namespace="database-system",
                name="cluster-credentials",
                key="password",
                value="secret123"
            ),
        ]

        # Configure the mock to return our test secrets
        mock_vault_helper.read_secrets.return_value = mock_secrets
        # Create a proper context manager mock using contextlib
        from contextlib import contextmanager

        @contextmanager
        def mock_port_forward(namespace=None, pod_name=None):
            yield "http://localhost:8200"

        mock_vault_helper.port_forward_vault = mock_port_forward

        with patch("stylist.commands.vault.read_secret.typer") as mock_typer:
            mock_typer.Exit = SystemExit
            read_secret(
                namespace="database-system",
                name="cluster-credentials",
                root_token="test-token",
                key=None  # Explicitly set to None to avoid any typer.Option issues
            )

            mock_vault_helper.read_secrets.assert_called_once()
            mock_typer.secho.assert_any_call(
                "📖 Reading secret: database-system/cluster-credentials",
                fg=mock_typer.colors.BRIGHT_BLUE
            )

    def test_read_secret_not_found(self, mock_context, mock_vault_helper):
        """Test reading a secret that doesn't exist."""
        mock_vault_helper.read_secrets = MagicMock(return_value=[])
        mock_vault_helper.port_forward_vault = MagicMock()
        mock_vault_helper.port_forward_vault.return_value.__enter__ = MagicMock(return_value="http://localhost:8200")
        mock_vault_helper.port_forward_vault.return_value.__exit__ = MagicMock(return_value=None)

        with patch("stylist.commands.vault.read_secret.typer") as mock_typer:
            mock_typer.Exit = SystemExit

            try:
                read_secret(
                    namespace="database-system",
                    name="nonexistent",
                    root_token="test-token"
                )
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass

            mock_typer.secho.assert_any_call(
                "❌ Secret not found: database-system/nonexistent",
                fg=mock_typer.colors.RED
            )

    def test_read_secret_with_key_filter(self, mock_context, mock_vault_helper):
        """Test reading a specific key from a secret."""
        mock_secrets = [
            vault_secret.VaultSecret(
                namespace="database-system",
                name="cluster-credentials",
                key="password",
                value="secret123"
            ),
            vault_secret.VaultSecret(
                namespace="database-system",
                name="cluster-credentials",
                key="username",
                value="admin"
            ),
        ]

        # Configure the mock to return our test secrets
        mock_vault_helper.read_secrets.return_value = mock_secrets
        # Create a proper context manager mock using contextlib
        from contextlib import contextmanager

        @contextmanager
        def mock_port_forward(namespace=None, pod_name=None):
            yield "http://localhost:8200"

        mock_vault_helper.port_forward_vault = mock_port_forward

        with patch("stylist.commands.vault.read_secret.typer") as mock_typer:
            mock_typer.Exit = SystemExit
            read_secret(
                namespace="database-system",
                name="cluster-credentials",
                key="password",
                root_token="test-token"
            )

            # Should filter to only password key
            assert len([s for s in mock_secrets if s.key == "password"]) == 1


class TestVaultWriteSecret:
    """Tests for vault write command."""

    def test_write_secret_success(self, mock_context, mock_vault_helper):
        """Test successful writing of a secret."""
        # Configure the mock
        mock_vault_helper.store_secrets.return_value = True
        from contextlib import contextmanager

        @contextmanager
        def mock_port_forward(namespace=None, pod_name=None):
            yield "http://localhost:8200"

        mock_vault_helper.port_forward_vault = mock_port_forward

        with patch("stylist.commands.vault.write_secret.typer") as mock_typer:
            mock_typer.Exit = SystemExit
            write_secret(
                namespace="database-system",
                name="test-secret",
                key="password",
                value="secret123",
                root_token="test-token"
            )

            mock_vault_helper.store_secrets.assert_called_once()
            call_args = mock_vault_helper.store_secrets.call_args
            # call_args can be (args, kwargs) or just args
            if isinstance(call_args, tuple) and len(call_args) == 2:
                args, kwargs = call_args
            else:
                args = call_args
            # Check if args is a tuple or list
            if args and len(args) > 0:
                secrets_list = args[0] if isinstance(args[0], (list, tuple)) else [args[0]]
                assert len(secrets_list) == 1  # One secret
                assert secrets_list[0].namespace == "database-system"
                assert secrets_list[0].name == "test-secret"
                assert secrets_list[0].key == "password"
                assert secrets_list[0].value == "secret123"
            else:
                # Try kwargs
                if 'secrets' in kwargs:
                    secrets_list = kwargs['secrets']
                    assert len(secrets_list) == 1
                    assert secrets_list[0].namespace == "database-system"
                    assert secrets_list[0].name == "test-secret"
                    assert secrets_list[0].key == "password"
                    assert secrets_list[0].value == "secret123"
                else:
                    raise AssertionError(f"Could not find secrets in call_args: {call_args}")

            mock_typer.secho.assert_any_call(
                "✅ Successfully wrote secret: database-system/test-secret/password",
                fg=mock_typer.colors.GREEN
            )

    def test_write_secret_failure(self, mock_context, mock_vault_helper):
        """Test writing a secret when it fails."""
        mock_vault_helper.store_secrets = MagicMock(return_value=False)
        mock_vault_helper.port_forward_vault = MagicMock()
        mock_vault_helper.port_forward_vault.return_value.__enter__ = MagicMock(return_value="http://localhost:8200")
        mock_vault_helper.port_forward_vault.return_value.__exit__ = MagicMock(return_value=None)

        with patch("stylist.commands.vault.write_secret.typer") as mock_typer:
            mock_typer.Exit = SystemExit

            try:
                write_secret(
                    namespace="database-system",
                    name="test-secret",
                    key="password",
                    value="secret123",
                    root_token="test-token"
                )
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass

            mock_typer.secho.assert_any_call(
                "❌ Failed to write secret: database-system/test-secret/password",
                fg=mock_typer.colors.RED
            )


class TestVaultUnseal:
    """Tests for vault unseal command."""

    @pytest.mark.asyncio
    async def test_unseal_success(self, mock_context, mock_vault_helper, tmp_path):
        """Test successful unsealing of vault."""
        mock_vault_helper.unseal_vault = AsyncMock(return_value=True)

        with patch("stylist.helpers.database") as mock_db:
            with patch("stylist.helpers.remote_db") as mock_remote_db:
                mock_remote_db.prepare_secrets_db.return_value = (str(tmp_path / "test.db"), None)
                # Create a mock credential object with the required attributes
                mock_cred = MagicMock()
                mock_cred.name = "Vault Unseal Keys"
                mock_cred.password = "key1\nkey2\nkey3\nkey4\nkey5"
                mock_db.get_credentials.return_value = [mock_cred]

                with patch("stylist.commands.vault.unseal.asyncio.run") as mock_run:
                    mock_run.return_value = True

                    with patch("stylist.commands.vault.unseal.typer") as mock_typer:
                        with patch("stylist.commands.vault.unseal.database", mock_db):
                            with patch("stylist.commands.vault.unseal.remote_db", mock_remote_db):
                                with patch("stylist.commands.vault.unseal.vault_helper", mock_vault_helper):
                                    mock_typer.Exit = SystemExit
                                    unseal(secrets_db=str(tmp_path / "test.db"))

                                    mock_run.assert_called_once()
                                    mock_typer.secho.assert_any_call(
                                        "🔓 Unsealing Vault...",
                                        fg=mock_typer.colors.BRIGHT_BLUE
                                    )

    @pytest.mark.asyncio
    async def test_unseal_keys_not_found(self, mock_context, mock_vault_helper, tmp_path):
        """Test unseal when keys are not found in database."""
        with patch("stylist.helpers.database") as mock_db:
            with patch("stylist.helpers.remote_db") as mock_remote_db:
                mock_remote_db.prepare_secrets_db.return_value = (str(tmp_path / "test.db"), None)
                mock_db.get_credentials.return_value = []  # No vault keys

                with patch("stylist.commands.vault.unseal.typer") as mock_typer:
                    with patch("stylist.commands.vault.unseal.database", mock_db):
                        with patch("stylist.commands.vault.unseal.remote_db", mock_remote_db):
                            mock_typer.Exit = SystemExit

                            try:
                                unseal(secrets_db=str(tmp_path / "test.db"))
                                assert False, "Should have raised SystemExit"
                            except SystemExit:
                                pass

                            mock_typer.secho.assert_any_call(
                                "❌ Could not find Vault keys in secrets database",
                                fg=mock_typer.colors.RED
                            )


class TestVaultInit:
    """Tests for vault init command."""

    @pytest.mark.asyncio
    async def test_init_success(self, mock_context, mock_vault_helper):
        """Test successful vault initialization."""
        vault_keys_obj = vault_keys.VaultKeys(
            unseal_keys=["key1", "key2", "key3", "key4", "key5"],
            root_token="root-token-123"
        )

        # Configure the mock - init_vault is async but asyncio.run handles it
        mock_vault_helper.init_vault = AsyncMock(return_value=vault_keys_obj)
        # Mock print_keys to avoid typer calls
        vault_keys_obj.print_keys = MagicMock()

        with patch("stylist.commands.vault.init.asyncio.run") as mock_run:
            # asyncio.run will execute the coroutine and return its result
            mock_run.return_value = vault_keys_obj

            with patch("stylist.commands.vault.init.typer") as mock_typer:
                with patch("stylist.commands.vault.init.vault_helper", mock_vault_helper):
                    mock_typer.Exit = SystemExit
                    # Explicitly set save_to_db=False to avoid database operations
                    init(save_to_db=False, secrets_db=None)

                    mock_run.assert_called_once()
                    mock_typer.secho.assert_any_call(
                        "🔧 Initializing Vault...",
                        fg=mock_typer.colors.BRIGHT_BLUE
                    )
                    mock_typer.secho.assert_any_call(
                        "\n✅ Vault initialized successfully!",
                        fg=mock_typer.colors.GREEN
                    )

    @pytest.mark.asyncio
    async def test_init_failure(self, mock_context, mock_vault_helper):
        """Test vault initialization failure."""
        mock_vault_helper.init_vault = AsyncMock(return_value=None)

        with patch("stylist.commands.vault.init.asyncio.run") as mock_run:
            mock_run.return_value = None

            with patch("stylist.commands.vault.init.typer") as mock_typer:
                mock_typer.Exit = SystemExit

                try:
                    init()
                    assert False, "Should have raised SystemExit"
                except SystemExit:
                    pass

                mock_typer.secho.assert_any_call(
                    "❌ Failed to initialize Vault",
                    fg=mock_typer.colors.RED
                )

    @pytest.mark.asyncio
    async def test_init_save_to_db(self, mock_context, mock_vault_helper, tmp_path):
        """Test vault initialization with saving to database."""
        vault_keys_obj = vault_keys.VaultKeys(
            unseal_keys=["key1", "key2", "key3", "key4", "key5"],
            root_token="root-token-123"
        )

        mock_vault_helper.init_vault = AsyncMock(return_value=vault_keys_obj)

        with patch("stylist.commands.vault.init.asyncio.run") as mock_run:
            mock_run.return_value = vault_keys_obj

            with patch("stylist.helpers.database") as mock_db:
                with patch("stylist.helpers.remote_db") as mock_remote_db:
                    mock_remote_db.prepare_secrets_db.return_value = (str(tmp_path / "test.db"), None)

                    with patch("stylist.commands.vault.init.typer") as mock_typer:
                        init(
                            save_to_db=True,
                            secrets_db=str(tmp_path / "test.db")
                        )

                        # Verify database was called to save credentials
                        assert mock_db.add_credential.call_count == 2  # Keys and token
                        mock_typer.secho.assert_any_call(
                            "✅ Keys saved to secrets database",
                            fg=mock_typer.colors.GREEN
                        )


class TestVaultCLI:
    """Integration tests for vault CLI commands."""

    @pytest.fixture(scope="function", autouse=True)
    def register_commands(self):
        """Register CLI commands for testing."""
        # Import commands to ensure they're registered
        # The vault command is registered when the vault.main module is imported
        import stylist.commands.vault.main  # noqa: F401
        # Also ensure the commands module is imported
        import stylist.commands  # noqa: F401
        yield

    @pytest.fixture(autouse=True)
    def mock_vault_setup(self, monkeypatch):
        """Mock vault command setup operations for help tests."""
        # Mock kubeconfig operations
        def mock_prepare_kubeconfig(kubeconfig_input):
            return str(kubeconfig_input), None
        monkeypatch.setattr("stylist.helpers.kubeconfig.prepare_kubeconfig", mock_prepare_kubeconfig)
        monkeypatch.setattr("stylist.helpers.remote_db.is_s3_path", lambda x: False)
        monkeypatch.setattr("stylist.helpers.remote_db.prepare_secrets_db",
                           lambda path, **kwargs: (path, None) if path else (None, None))
        # Mock kubernetes config loading - these are imported at module level
        import kubernetes
        import kubernetes_asyncio
        monkeypatch.setattr(kubernetes.config, "load_kube_config", lambda **kwargs: None)
        # Mock the async config load - need to make it a coroutine that returns None
        async def mock_async_load_kube_config(**kwargs):
            return None
        monkeypatch.setattr(kubernetes_asyncio.config, "load_kube_config", mock_async_load_kube_config)
        # Mock asyncio.run to handle the async call
        original_run = asyncio.run
        def mock_asyncio_run(coro, **kwargs):
            if asyncio.iscoroutine(coro):
                return original_run(coro, **kwargs)
            return coro
        monkeypatch.setattr("stylist.commands.vault.main.asyncio.run", mock_asyncio_run)
        # Mock database test
        monkeypatch.setattr("stylist.helpers.database.test_db_connection", lambda **kwargs: True)

    def test_vault_command_registered(self):
        """Test that vault command is registered in CLI."""
        result = runner.invoke(core.Backbone().typer_app, ["--help"])
        assert result.exit_code == 0
        assert "vault" in result.stdout

    def test_vault_command_help(self):
        """Test vault command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "--help"])
        assert result.exit_code == 0
        assert "Vault management commands" in result.stdout

    def test_vault_status_help(self):
        """Test vault status command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "status", "--help"])
        assert result.exit_code == 0

    def test_vault_list_help(self):
        """Test vault list command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "list", "--help"])
        assert result.exit_code == 0

    def test_vault_read_help(self):
        """Test vault read command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "read", "--help"])
        assert result.exit_code == 0

    def test_vault_write_help(self):
        """Test vault write command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "write", "--help"])
        assert result.exit_code == 0

    def test_vault_unseal_help(self):
        """Test vault unseal command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "unseal", "--help"])
        assert result.exit_code == 0

    def test_vault_init_help(self):
        """Test vault init command help."""
        result = runner.invoke(core.Backbone().typer_app, ["vault", "init", "--help"])
        assert result.exit_code == 0
