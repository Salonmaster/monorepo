from dataclasses import dataclass

@dataclass
class ArgoCDApp:
    name: str
    cluster: str
    namespace: str
    project: str
    status: str
    health: str
    sync_policy: str
    conditions: str
    repo: str
    path: str
    target: str
