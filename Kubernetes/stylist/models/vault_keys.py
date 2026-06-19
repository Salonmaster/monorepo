import typer

class VaultKeys:
    """
    Class to manage Hashicorp Vault keys.
    """
    unseal_keys: list[str] = []
    root_token: str = ""

    def __init__(self, unseal_keys: list[str], root_token: str):
        self.unseal_keys = unseal_keys
        self.root_token = root_token

    def print_keys(self):
        """
        Print the unseal keys and root token.
        """
        for i, key in enumerate(self.unseal_keys, 1):
            typer.secho(f"🔑 Unseal Key {i}: {key}")
        typer.secho(f"🔑 Root Token: {self.root_token}")

